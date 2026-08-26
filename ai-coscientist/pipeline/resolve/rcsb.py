"""Stage 1c: enrich candidates with entry detail from RCSB.

UniProt's cross-references give method, resolution, and coverage but say nothing
about what else is in the entry. Whether a structure contains a binding partner
is the single most useful fact for epitope selection, so it is worth the extra
calls -- but only for the shortlist, since this costs one request per entry plus
one per polymer entity.

Enrichment degrades gracefully: if RCSB is unreachable the candidates come back
unenriched, ranking records "complex status unknown", and the pipeline continues
rather than failing at stage 1.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .models import Partner, StructureCandidate

log = logging.getLogger(__name__)

RCSB_ENTRY = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
RCSB_ENTITY = "https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/{entity_id}"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"

# Shortlist size for the REST fallback path only; `enrich_all` has no limit.
DEFAULT_SHORTLIST = 5

# Entries per GraphQL request. The endpoint accepts large batches; this keeps
# any single failure cheap to retry.
BATCH_SIZE = 50

# One query returns every entry with its polymer entities, their lengths, and
# their UniProt cross-references -- everything partner classification needs.
GRAPHQL_QUERY = """
query Entries($ids: [String!]!) {
  entries(entry_ids: $ids) {
    rcsb_id
    struct { title }
    rcsb_entry_info { polymer_entity_count_protein }
    polymer_entities {
      rcsb_polymer_entity { pdbx_description }
      entity_poly { rcsb_sample_sequence_length type rcsb_mutation_count }
      rcsb_entity_source_organism { ncbi_taxonomy_id scientific_name }
      rcsb_polymer_entity_container_identifiers {
        reference_sequence_identifiers { database_accession database_name }
      }
    }
  }
}
"""


def _get_json(url: str, session: requests.Session, timeout: float) -> dict[str, Any] | None:
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError) as exc:
        log.warning("RCSB request failed for %s: %s", url, exc)
        return None


def parse_entry(payload: dict[str, Any]) -> tuple[str | None, int | None, list[str]]:
    """Extract (title, protein entity count, entity ids) from an entry payload."""
    title = (payload.get("struct") or {}).get("title")
    info = payload.get("rcsb_entry_info") or {}
    count = info.get("polymer_entity_count_protein")
    ids = (payload.get("rcsb_entry_container_identifiers") or {}).get("polymer_entity_ids") or []
    return title, (int(count) if count is not None else None), [str(i) for i in ids]


def parse_entity(payload: dict[str, Any]) -> Partner:
    """Build a Partner from a polymer entity payload.

    Length, polymer type, and the UniProt cross-reference together separate a
    real protein partner from a co-crystallised peptide or nucleic acid. The
    description alone does not: "PHE-MEA-9KK-SAR-ASP-VAL-..." is a macrocyclic
    inhibitor and reads like nothing in particular.
    """
    entity = payload.get("rcsb_polymer_entity") or {}
    poly = payload.get("entity_poly") or {}
    ids = payload.get("rcsb_polymer_entity_container_identifiers") or {}

    uniprot = None
    for ref in ids.get("reference_sequence_identifiers") or []:
        if (ref.get("database_name") or "").lower() == "uniprot":
            uniprot = ref.get("database_accession")
            break

    # Source organism and engineered mutations both change how good a template
    # an entity is, and neither is visible in its description. A complex between
    # a mouse PD-1 mutant and human PD-L1 reads identically to the human complex.
    sources = payload.get("rcsb_entity_source_organism") or []
    taxon = organism = None
    for source in sources:
        if source and source.get("ncbi_taxonomy_id") is not None:
            taxon = int(source["ncbi_taxonomy_id"])
            organism = source.get("scientific_name")
            break

    length = poly.get("rcsb_sample_sequence_length")
    mutations = poly.get("rcsb_mutation_count") or 0

    return Partner(
        description=entity.get("pdbx_description") or "unnamed entity",
        uniprot=uniprot,
        length=int(length) if length is not None else None,
        polymer_type=poly.get("type"),
        taxon_id=taxon,
        organism=organism,
        mutations=int(mutations),
    )


def parse_entity_name(payload: dict[str, Any]) -> str | None:
    """Backwards-compatible accessor for an entity's description."""
    return (payload.get("rcsb_polymer_entity") or {}).get("pdbx_description")


def parse_graphql(payload: dict[str, Any]) -> dict[str, tuple[str | None, int | None, list[Partner]]]:
    """Parse a batched GraphQL response into {pdb_id: (title, count, partners)}."""
    entries = ((payload.get("data") or {}).get("entries")) or []
    out: dict[str, tuple[str | None, int | None, list[Partner]]] = {}

    for entry in entries:
        if not entry:
            continue
        pdb_id = (entry.get("rcsb_id") or "").upper()
        if not pdb_id:
            continue
        title = (entry.get("struct") or {}).get("title")
        count = (entry.get("rcsb_entry_info") or {}).get("polymer_entity_count_protein")
        partners = [parse_entity(e) for e in (entry.get("polymer_entities") or []) if e]
        out[pdb_id] = (title, int(count) if count is not None else None, partners)

    return out


def _split_target_entity(
    partners: list[Partner], target_accession: str | None
) -> tuple[tuple[Partner, ...], Partner | None]:
    """Separate one copy of the target from its partners.

    Returns (partners, the target's own entity). The target entity is kept
    rather than discarded because its mutation count and organism describe the
    quality of the template itself -- a structure of a point mutant is a worse
    starting point than one of the wild-type protein.

    Further copies of the target stay in `partners` and register as homodimers.
    """
    if not target_accession:
        return tuple(partners), None
    kept: list[Partner] = []
    target: Partner | None = None
    for partner in partners:
        if target is None and partner.uniprot == target_accession:
            target = partner
            continue
        kept.append(partner)
    return tuple(kept), target


def _drop_target_entity(partners: list[Partner], target_accession: str | None) -> tuple[Partner, ...]:
    """Backwards-compatible wrapper returning only the partners."""
    return _split_target_entity(partners, target_accession)[0]


def enrich_all(
    candidates: list[StructureCandidate],
    *,
    target_accession: str | None = None,
    session: requests.Session | None = None,
    timeout: float = 60.0,
) -> list[StructureCandidate]:
    """Enrich every candidate via batched GraphQL.

    Enriching only a shortlist biases the result: partner kind carries the
    heaviest weight in ranking, so shortlisting on the criteria available
    *before* enrichment (method, resolution, coverage) hides the best structures
    behind worse ones that merely resolve better. Run against PD-L1 that dropped
    the PD-1 complexes entirely -- the one interface the campaign actually wants.

    One request covers fifty entries, so enriching all of them costs less than
    the per-entry REST calls cost for five.
    """
    sess = session or requests.Session()
    by_id = {c.pdb_id: c for c in candidates}
    ids = list(by_id)

    for start in range(0, len(ids), BATCH_SIZE):
        chunk = ids[start:start + BATCH_SIZE]
        try:
            resp = sess.post(RCSB_GRAPHQL,
                             json={"query": GRAPHQL_QUERY, "variables": {"ids": chunk}},
                             timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("GraphQL enrichment failed for %d entries (%s); "
                        "falling back to REST", len(chunk), exc)
            enrich([by_id[i] for i in chunk], target_accession=target_accession,
                   limit=len(chunk), session=sess, timeout=timeout)
            continue

        if payload.get("errors"):
            log.warning("GraphQL reported errors: %s", payload["errors"])

        parsed = parse_graphql(payload)
        for pdb_id in chunk:
            if pdb_id not in parsed:
                continue
            title, count, partners = parsed[pdb_id]
            candidate = by_id[pdb_id]
            candidate.title = title
            candidate.n_polymer_entities = count
            candidate.partners, own = _split_target_entity(partners, target_accession)
            if own is not None:
                candidate.target_taxon = own.taxon_id
                candidate.target_mutations = own.mutations
            candidate.enriched = True

    enriched = sum(1 for c in candidates if c.enriched)
    log.info("enriched %d/%d candidates", enriched, len(candidates))
    return candidates


def enrich(
    candidates: list[StructureCandidate],
    *,
    target_accession: str | None = None,
    limit: int = DEFAULT_SHORTLIST,
    session: requests.Session | None = None,
    timeout: float = 30.0,
) -> list[StructureCandidate]:
    """Enrich the first `limit` candidates in place with RCSB entry detail.

    `target_accession` identifies the target's own entity so it is not counted as
    its own binding partner. Without it, an entity sharing the target's UniProt
    accession is reported as a homodimer partner, which is true but is a
    different claim from "a partner protein binds here".

    This per-entry REST path is the fallback for when GraphQL is unavailable;
    `enrich_all` is the normal route and has no shortlist.
    """
    sess = session or requests.Session()

    for candidate in candidates[:limit]:
        payload = _get_json(RCSB_ENTRY.format(pdb_id=candidate.pdb_id), sess, timeout)
        if payload is None:
            continue

        title, count, entity_ids = parse_entry(payload)
        candidate.title = title
        candidate.n_polymer_entities = count
        candidate.enriched = True

        partners: list[Partner] = []
        for entity_id in entity_ids:
            entity = _get_json(
                RCSB_ENTITY.format(pdb_id=candidate.pdb_id, entity_id=entity_id),
                sess, timeout,
            )
            if entity is not None:
                partners.append(parse_entity(entity))

        candidate.partners, own = _split_target_entity(partners, target_accession)
        if own is not None:
            candidate.target_taxon = own.taxon_id
            candidate.target_mutations = own.mutations

    return candidates
