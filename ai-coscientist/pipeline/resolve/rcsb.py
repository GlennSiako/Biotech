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

from .models import StructureCandidate

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


def parse_entity_name(payload: dict[str, Any]) -> str | None:
    return (payload.get("rcsb_polymer_entity") or {}).get("pdbx_description")


def enrich(
    candidates: list[StructureCandidate],
    *,
    limit: int = DEFAULT_SHORTLIST,
    session: requests.Session | None = None,
    timeout: float = 30.0,
    fetch_partners: bool = True,
) -> list[StructureCandidate]:
    """Enrich the first `limit` candidates in place with RCSB entry detail.

    `limit` exists because entry-level enrichment is only needed to choose among
    plausible candidates; enriching a hundred entries to pick one wastes calls.
    """
    sess = session or requests.Session()

    for candidate in candidates[:limit]:
        payload = _get_json(RCSB_ENTRY.format(pdb_id=candidate.pdb_id), sess, timeout)
        if payload is None:
            continue

        title, count, entity_ids = parse_entry(payload)
        candidate.title = title
        candidate.n_polymer_entities = count

        if fetch_partners and count and count > 1:
            names: list[str] = []
            for entity_id in entity_ids:
                entity = _get_json(
                    RCSB_ENTITY.format(pdb_id=candidate.pdb_id, entity_id=entity_id),
                    sess, timeout,
                )
                if entity is not None:
                    name = parse_entity_name(entity)
                    if name:
                        names.append(name)
            candidate.partners = tuple(names)

    return candidates
