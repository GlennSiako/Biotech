"""Stage 1: UniProt parsing, RCSB enrichment parsing, and structure ranking."""

from __future__ import annotations

import pytest

from fixtures import UNIPROT_PAYLOAD
from pipeline.resolve.models import ChainCoverage, StructureCandidate
from pipeline.resolve.ranking import rank, score_candidate
from pipeline.resolve.rcsb import parse_entity_name, parse_entry
from pipeline.resolve.uniprot import (
    ResolutionError, _parse_coverage, _parse_resolution, parse_structures, parse_target,
)


# --- UniProt parsing -------------------------------------------------------

def test_parses_target_fields():
    target = parse_target(UNIPROT_PAYLOAD)
    assert target.accession == "Q9NZQ7"
    assert target.gene == "CD274"
    assert target.taxon_id == 9606
    assert target.length == 290
    assert "PD1L1_HUMAN" in target.summary() or "CD274" in target.summary()


def test_empty_search_raises():
    with pytest.raises(ResolutionError, match="no reviewed UniProt entry"):
        parse_target({"results": []}, query="NOTAGENE")


def test_ambiguous_search_raises_rather_than_guessing():
    payload = {"results": [
        {"primaryAccession": "P00001"}, {"primaryAccession": "P00002"},
    ]}
    with pytest.raises(ResolutionError, match="matched 2 reviewed entries"):
        parse_target(payload, query="ambiguous")


def test_extracts_pdb_xrefs_and_ignores_other_databases():
    structures = parse_structures(UNIPROT_PAYLOAD)
    ids = [s.pdb_id for s in structures]
    assert ids == ["4ZQK", "3BIK", "2K9Z"], "AlphaFoldDB xref must not become a candidate"
    assert all(s.pdb_id.isupper() for s in structures)


def test_nmr_entry_has_no_resolution():
    nmr = next(s for s in parse_structures(UNIPROT_PAYLOAD) if s.pdb_id == "2K9Z")
    assert nmr.resolution is None
    assert nmr.method == "NMR"


@pytest.mark.parametrize("value,chains,start,end", [
    ("A/B=18-239", ("A", "B"), 18, 239),
    ("A=18-134", ("A",), 18, 134),
    ("A=18-134, C/D=1-290", ("A", "C", "D"), 1, 290),   # widest span wins
    ("", (), None, None),
    (None, (), None, None),
])
def test_chain_coverage_parsing(value, chains, start, end):
    coverage = _parse_coverage(value)
    assert coverage.chains == chains
    assert (coverage.start, coverage.end) == (start, end)


@pytest.mark.parametrize("value,expected", [
    ("2.45 A", 2.45), ("1.9 A", 1.9), ("-", None), ("", None), (None, None),
])
def test_resolution_parsing(value, expected):
    assert _parse_resolution(value) == expected


# --- RCSB enrichment parsing ----------------------------------------------

def test_parses_rcsb_entry():
    title, count, ids = parse_entry({
        "struct": {"title": "PD-1/PD-L1 complex"},
        "rcsb_entry_info": {"polymer_entity_count_protein": 2},
        "rcsb_entry_container_identifiers": {"polymer_entity_ids": ["1", "2"]},
    })
    assert (title, count, ids) == ("PD-1/PD-L1 complex", 2, ["1", "2"])


def test_rcsb_parsing_tolerates_missing_fields():
    assert parse_entry({}) == (None, None, [])
    assert parse_entity_name({}) is None


# --- Ranking ---------------------------------------------------------------

def _candidate(pdb_id, method="X-ray", resolution=2.0, start=18, end=134, entities=None):
    return StructureCandidate(pdb_id, method, resolution,
                              ChainCoverage(("A",), start, end),
                              n_polymer_entities=entities)


def test_complex_outranks_better_resolved_monomer():
    """A co-complex gives an observed interface, which D-010 prefers over a
    predicted one -- even at the cost of some resolution."""
    complexed = _candidate("CPLX", resolution=2.8, entities=2)
    monomer = _candidate("MONO", resolution=1.8, entities=1)
    assert rank([monomer, complexed])[0].pdb_id == "CPLX"


def test_xray_outranks_nmr():
    ranked = rank([_candidate("NMRX", method="NMR", resolution=None, entities=1),
                   _candidate("XRAY", entities=1)])
    assert ranked[0].pdb_id == "XRAY"


def test_low_resolution_is_flagged():
    scored = score_candidate(_candidate("LOWR", resolution=3.6, entities=1))
    assert any("side chains unreliable" in n for n in scored.notes)


def test_partial_coverage_scores_lower_and_warns():
    full = score_candidate(_candidate("FULL", start=18, end=134), region=(18, 134))
    part = score_candidate(_candidate("PART", start=60, end=134), region=(18, 134))
    assert full.score > part.score
    assert any("does not fully cover" in n for n in part.notes)


def test_unknown_complex_status_is_stated_not_assumed():
    scored = score_candidate(_candidate("UNKN", entities=None))
    assert any("complex status unknown" in n for n in scored.notes)
    assert scored.is_complex is None


def test_every_candidate_carries_its_reasoning():
    ranked = rank(parse_structures(UNIPROT_PAYLOAD), region=(18, 134))
    assert all(c.notes for c in ranked), "ranking must be auditable"


def test_ranking_is_deterministic():
    """Runs must be replayable from a manifest, so ties cannot break arbitrarily."""
    candidates = [_candidate(x, entities=1) for x in ("BBBB", "AAAA", "CCCC")]
    assert [c.pdb_id for c in rank(list(candidates))] == \
           [c.pdb_id for c in rank(list(reversed(candidates)))]
