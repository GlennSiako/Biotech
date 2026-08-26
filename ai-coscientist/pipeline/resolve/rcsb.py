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

DEFAULT_SHORTLIST = 5


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

    length = poly.get("rcsb_sample_sequence_length")
    return Partner(
        description=entity.get("pdbx_description") or "unnamed entity",
        uniprot=uniprot,
        length=int(length) if length is not None else None,
        polymer_type=poly.get("type"),
    )


def parse_entity_name(payload: dict[str, Any]) -> str | None:
    """Backwards-compatible accessor for an entity's description."""
    return (payload.get("rcsb_polymer_entity") or {}).get("pdbx_description")


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

    `limit` exists because enrichment costs one request per entry plus one per
    polymer entity; enriching seventy entries to choose one wastes calls.
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
            if entity is None:
                continue
            partner = parse_entity(entity)
            # Skip the target's own entity; keep everything else, including a
            # second copy of the target, which is flagged as a homodimer.
            if target_accession and partner.uniprot == target_accession and not partners:
                continue
            partners.append(partner)

        candidate.partners = tuple(partners)

    return candidates
