"""Stage 1a: resolve a target name or gene symbol to a UniProt entry.

HTTP and parsing are kept separate on purpose. Parsing is pure and unit-tested
against recorded fixtures; only `fetch_entry` touches the network. That makes
the response-shape logic verifiable without live API access.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

from .models import ChainCoverage, StructureCandidate, Target

log = logging.getLogger(__name__)

UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
HUMAN_TAXON = 9606

# Requesting fields explicitly keeps responses small and stable; without this
# UniProt returns a very large default payload.
FIELDS = "accession,id,protein_name,gene_names,organism_name,organism_id,length,sequence,xref_pdb"

_RESOLUTION_RE = re.compile(r"([\d.]+)\s*A")
# Chain coverage looks like "A/B=18-239", occasionally several comma-separated.
_CHAINS_RE = re.compile(r"([A-Za-z0-9/]+)=(-?\d+)-(-?\d+)")


class ResolutionError(RuntimeError):
    """Raised when a target cannot be resolved to a single UniProt entry."""


def fetch_entry(
    query: str,
    *,
    organism_id: int = HUMAN_TAXON,
    reviewed_only: bool = True,
    session: requests.Session | None = None,
    timeout: float = 30.0,
    retries: int = 3,
) -> dict[str, Any]:
    """Search UniProt and return the raw JSON payload.

    Restricted to reviewed (Swiss-Prot) entries by default: TrEMBL contains many
    unreviewed predictions per gene, and picking among those automatically is
    not a judgement worth making silently.
    """
    terms = [f"({query})", f"organism_id:{organism_id}"]
    if reviewed_only:
        terms.append("reviewed:true")
    params = {"query": " AND ".join(terms), "format": "json", "fields": FIELDS, "size": "10"}

    sess = session or requests.Session()
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = sess.get(UNIPROT_SEARCH, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt < retries - 1:
                delay = 2 ** attempt
                log.warning("UniProt request failed (%s); retrying in %ss", exc, delay)
                time.sleep(delay)
    raise ResolutionError(f"UniProt search failed for {query!r}: {last}") from last


def parse_target(payload: dict[str, Any], *, query: str = "") -> Target:
    """Extract the single best target from a UniProt search payload.

    Raises if the search is ambiguous. An automated pipeline choosing silently
    between several reviewed entries is a failure mode we would rather surface
    at stage 1 than discover after a campaign.
    """
    results = payload.get("results") or []
    if not results:
        raise ResolutionError(f"no reviewed UniProt entry found for {query!r}")
    if len(results) > 1:
        accs = ", ".join(r.get("primaryAccession", "?") for r in results[:5])
        raise ResolutionError(
            f"{query!r} matched {len(results)} reviewed entries ({accs}). "
            "Disambiguate with an accession or a more specific query."
        )

    entry = results[0]
    desc = entry.get("proteinDescription", {})
    name = (desc.get("recommendedName", {}).get("fullName", {}).get("value")
            or next((s.get("fullName", {}).get("value") for s in desc.get("submissionNames", [])), None)
            or "unknown")

    genes = entry.get("genes") or []
    gene = next((g.get("geneName", {}).get("value") for g in genes if g.get("geneName")), "")

    organism = entry.get("organism", {})
    sequence = entry.get("sequence", {})

    return Target(
        accession=entry["primaryAccession"],
        entry_name=entry.get("uniProtkbId", ""),
        protein_name=name,
        gene=gene,
        organism=organism.get("scientificName", ""),
        taxon_id=int(organism.get("taxonId", 0)),
        length=int(sequence.get("length", 0)),
        sequence=sequence.get("value", ""),
    )


def _parse_resolution(value: str | None) -> float | None:
    if not value:
        return None
    match = _RESOLUTION_RE.search(value)
    return float(match.group(1)) if match else None


def _parse_coverage(value: str | None) -> ChainCoverage:
    """Parse UniProt's chain field, e.g. 'A/B=18-239'.

    Where several ranges are listed the widest span is taken, since that is the
    construct most likely to contain the region of interest.
    """
    if not value:
        return ChainCoverage((), None, None)

    chains: list[str] = []
    best: tuple[int, int] | None = None
    for chain_group, start_s, end_s in _CHAINS_RE.findall(value):
        chains.extend(c for c in chain_group.split("/") if c)
        start, end = int(start_s), int(end_s)
        if best is None or (end - start) > (best[1] - best[0]):
            best = (start, end)

    if best is None:
        return ChainCoverage(tuple(dict.fromkeys(chains)), None, None)
    return ChainCoverage(tuple(dict.fromkeys(chains)), best[0], best[1])


def parse_structures(payload: dict[str, Any]) -> list[StructureCandidate]:
    """Extract PDB cross-references from a UniProt entry payload.

    UniProt already carries method, resolution, and chain coverage for every PDB
    entry mapped to the target, so this needs no second API call.
    """
    results = payload.get("results") or []
    if not results:
        return []

    candidates: list[StructureCandidate] = []
    for xref in results[0].get("uniProtKBCrossReferences", []):
        if xref.get("database") != "PDB":
            continue
        props = {p.get("key"): p.get("value") for p in xref.get("properties", [])}
        candidates.append(
            StructureCandidate(
                pdb_id=xref["id"].upper(),
                method=props.get("Method", "unknown"),
                resolution=_parse_resolution(props.get("Resolution")),
                coverage=_parse_coverage(props.get("Chains")),
            )
        )
    return candidates


def resolve(
    query: str,
    *,
    organism_id: int = HUMAN_TAXON,
    session: requests.Session | None = None,
) -> tuple[Target, list[StructureCandidate]]:
    """Resolve a query to a target and its candidate structures."""
    payload = fetch_entry(query, organism_id=organism_id, session=session)
    target = parse_target(payload, query=query)
    structures = parse_structures(payload)
    log.info("resolved %s -> %s with %d PDB entries",
             query, target.accession, len(structures))
    return target, structures
