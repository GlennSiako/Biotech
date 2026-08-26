"""Stage 1: UniProt parsing, RCSB enrichment parsing, and structure ranking."""

from __future__ import annotations

import pytest

from fixtures import UNIPROT_PAYLOAD
from pipeline.resolve.models import ChainCoverage, Partner, StructureCandidate
from pipeline.resolve.ranking import rank, score_candidate
from pipeline.resolve.rcsb import (
    _drop_target_entity, parse_entity, parse_entity_name, parse_entry, parse_graphql,
)
from pipeline.resolve.uniprot import (
    ResolutionError, _parse_coverage, _parse_resolution, build_queries,
    parse_structures, parse_target,
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


def test_ambiguity_error_names_the_genes_it_matched():
    """The first live run returned ten accessions with no hint which was which."""
    payload = {"results": [
        {"primaryAccession": "Q9NZQ7", "genes": [{"geneName": {"value": "CD274"}}]},
        {"primaryAccession": "Q15116", "genes": [{"geneName": {"value": "PDCD1"}}]},
    ]}
    with pytest.raises(ResolutionError, match=r"Q9NZQ7=CD274.*Q15116=PDCD1"):
        parse_target(payload, query="CD274", strategy="full_text")


# --- Query construction ----------------------------------------------------

def test_gene_symbol_tries_exact_gene_before_free_text():
    """A bare term is a full-text search in UniProt: 'CD274' matched ten reviewed
    entries including PDCD1, the receptor its product binds."""
    strategies = [s for s, _ in build_queries("CD274")]
    assert strategies == ["gene_exact", "gene", "full_text"]
    assert build_queries("CD274")[0][1] == "gene_exact:CD274"


@pytest.mark.parametrize("accession", ["Q9NZQ7", "q9nzq7", "P40763", "A0A123B4C5"])
def test_accession_queries_the_accession_field(accession):
    strategies = build_queries(accession)
    assert len(strategies) == 1
    assert strategies[0][0] == "accession"
    assert strategies[0][1] == f"accession:{accession.upper()}"


def test_multiword_name_uses_free_text_only():
    assert [s for s, _ in build_queries("programmed cell death 1 ligand")] == ["full_text"]


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

TARGET = "Q9NZQ7"          # PD-L1
PD1 = Partner("Programmed cell death protein 1", "Q15116", 110, "polypeptide(L)")
MACROCYCLE = Partner("PHE-MEA-9KK-SAR-ASP-VAL-MEA-TYR", None, 14, "polypeptide(L)")
NANOBODY = Partner("single-domain antibody", None, 125, "polypeptide(L)")
SELF = Partner("Programmed cell death 1 ligand 1", TARGET, 120, "polypeptide(L)")


def _candidate(pdb_id, method="X-ray", resolution=2.0, start=18, end=134,
               partners=(), enriched=True):
    c = StructureCandidate(pdb_id, method, resolution,
                           ChainCoverage(("A",), start, end),
                           n_polymer_entities=1 + len(partners))
    c.partners = tuple(partners)
    c.enriched = enriched
    return c


def test_protein_complex_outranks_better_resolved_monomer():
    """A real protein interface is worth more than resolution: D-010 requires
    preferring an observed interface over a predicted one."""
    complexed = _candidate("CPLX", resolution=2.8, partners=[PD1])
    monomer = _candidate("MONO", resolution=1.8)
    assert rank([monomer, complexed], target_accession=TARGET)[0].pdb_id == "CPLX"


def test_protein_partner_outranks_macrocycle_inhibitor():
    """The bug the first live run exposed.

    Ranking on polymer-entity count put a 0.99 A PD-L1/macrocycle structure above
    the PD-1 complex. A macrocyclic inhibitor is a polymer entity, but the
    interface it reveals is a drug-binding site, not a protein-protein epitope.
    """
    drug = _candidate("5O45", resolution=0.99, partners=[MACROCYCLE])
    real = _candidate("4ZQK", resolution=2.45, partners=[PD1])
    ranked = rank([drug, real], region=(18, 134), target_accession=TARGET)
    assert ranked[0].pdb_id == "4ZQK"
    assert any("drug-binding site" in n for n in ranked[1].notes)


def test_homodimer_is_not_counted_as_a_partner_interface():
    """Several PD-L1 inhibitors work by inducing homodimerisation; the observed
    interface is then the target against itself."""
    dimer = _candidate("DIMR", resolution=1.8, partners=[SELF])
    real = _candidate("4ZQK", resolution=2.45, partners=[PD1])
    ranked = rank([dimer, real], target_accession=TARGET)
    assert ranked[0].pdb_id == "4ZQK"
    demoted = next(c for c in ranked if c.pdb_id == "DIMR")
    assert any("self-association" in n for n in demoted.notes)


def test_engineered_protein_binder_counts_as_a_protein_interface():
    nb = _candidate("NANO", resolution=2.0, partners=[NANOBODY])
    assert nb.protein_partners == (NANOBODY,)
    assert any("protein-protein interface" in n
               for n in rank([nb], target_accession=TARGET)[0].notes)


def test_peptide_ligand_is_not_a_protein_partner():
    drug = _candidate("5O45", partners=[MACROCYCLE])
    assert drug.protein_partners == ()
    assert drug.has_protein_partner is False


def test_xray_outranks_nmr():
    ranked = rank([_candidate("NMRX", method="NMR", resolution=None),
                   _candidate("XRAY")])
    assert ranked[0].pdb_id == "XRAY"


def test_low_resolution_is_flagged():
    scored = score_candidate(_candidate("LOWR", resolution=3.6))
    assert any("side chains unreliable" in n for n in scored.notes)


def test_partial_coverage_scores_lower_and_warns():
    full = score_candidate(_candidate("FULL", start=18, end=134), region=(18, 134))
    part = score_candidate(_candidate("PART", start=60, end=134), region=(18, 134))
    assert full.score > part.score
    assert any("does not fully cover" in n for n in part.notes)


def test_unenriched_candidate_states_partners_are_unknown():
    scored = score_candidate(_candidate("UNKN", enriched=False))
    assert any("partners unknown" in n for n in scored.notes)
    assert scored.has_protein_partner is None


def test_parses_partner_from_entity_payload():
    partner = parse_entity({
        "rcsb_polymer_entity": {"pdbx_description": "Programmed cell death protein 1"},
        "entity_poly": {"rcsb_sample_sequence_length": 110, "type": "polypeptide(L)"},
        "rcsb_polymer_entity_container_identifiers": {
            "reference_sequence_identifiers": [
                {"database_name": "UniProt", "database_accession": "Q15116"}]},
    })
    assert partner.uniprot == "Q15116" and partner.length == 110
    assert partner.kind == "natural protein"


def test_short_polymer_is_classified_as_a_peptide_ligand():
    partner = parse_entity({
        "rcsb_polymer_entity": {"pdbx_description": "PHE-MEA-9KK-SAR"},
        "entity_poly": {"rcsb_sample_sequence_length": 14, "type": "polypeptide(L)"},
    })
    assert partner.kind == "peptide ligand" and not partner.is_protein


def test_every_candidate_carries_its_reasoning():
    ranked = rank(parse_structures(UNIPROT_PAYLOAD), region=(18, 134))
    assert all(c.notes for c in ranked), "ranking must be auditable"


def test_ranking_is_deterministic():
    """Runs must be replayable from a manifest, so ties cannot break arbitrarily."""
    candidates = [_candidate(x) for x in ("BBBB", "AAAA", "CCCC")]
    assert [c.pdb_id for c in rank(list(candidates))] == \
           [c.pdb_id for c in rank(list(reversed(candidates)))]


# --- Batched GraphQL enrichment --------------------------------------------

def _gql_entity(description, accession, length, poly_type="polypeptide(L)"):
    entity = {
        "rcsb_polymer_entity": {"pdbx_description": description},
        "entity_poly": {"rcsb_sample_sequence_length": length, "type": poly_type},
    }
    if accession:
        entity["rcsb_polymer_entity_container_identifiers"] = {
            "reference_sequence_identifiers": [
                {"database_name": "UniProt", "database_accession": accession}]}
    return entity


GQL_RESPONSE = {"data": {"entries": [
    {"rcsb_id": "4zqk", "struct": {"title": "PD-1/PD-L1 complex"},
     "rcsb_entry_info": {"polymer_entity_count_protein": 2},
     "polymer_entities": [_gql_entity("PD-L1", TARGET, 115),
                          _gql_entity("PD-1", "Q15116", 110)]},
    {"rcsb_id": "5O45", "struct": {"title": "PD-L1 with inhibitor"},
     "rcsb_entry_info": {"polymer_entity_count_protein": 2},
     "polymer_entities": [_gql_entity("PD-L1", TARGET, 115),
                          _gql_entity("PHE-MEA-9KK-SAR", None, 15)]},
]}}


def test_graphql_batch_is_parsed_and_ids_normalised():
    parsed = parse_graphql(GQL_RESPONSE)
    assert set(parsed) == {"4ZQK", "5O45"}, "PDB ids must be upper-cased"
    title, count, partners = parsed["4ZQK"]
    assert title == "PD-1/PD-L1 complex" and count == 2
    assert len(partners) == 2


def test_graphql_parsing_tolerates_empty_and_null_entries():
    assert parse_graphql({}) == {}
    assert parse_graphql({"data": {"entries": [None]}}) == {}
    assert parse_graphql({"data": {"entries": [{"rcsb_id": ""}]}}) == {}


def test_target_own_entity_is_dropped_once():
    _, _, partners = parse_graphql(GQL_RESPONSE)["4ZQK"]
    kept = _drop_target_entity(partners, TARGET)
    assert [p.description for p in kept] == ["PD-1"]


def test_second_target_copy_survives_as_a_homodimer():
    """Dropping every copy would hide inhibitor-induced self-association."""
    partners = [Partner("PD-L1", TARGET, 115, "polypeptide(L)"),
                Partner("PD-L1", TARGET, 115, "polypeptide(L)")]
    kept = _drop_target_entity(partners, TARGET)
    assert len(kept) == 1 and kept[0].uniprot == TARGET


def test_enriching_only_a_shortlist_would_hide_the_natural_complex():
    """The bug the second live run exposed.

    Partner kind carries the heaviest weight, but it is unknown before
    enrichment. Ranking unenriched candidates orders them on resolution alone,
    so a 2.45 A natural complex sits below sub-2 A engineered-binder structures
    and never gets enriched -- the one interface the campaign wants, dropped.
    """
    natural = _candidate("4ZQK", resolution=2.45, partners=[PD1])
    engineered = [_candidate(f"VHH{i}", resolution=1.5 + i / 100, partners=[NANOBODY])
                  for i in range(5)]

    unenriched = [_candidate(c.pdb_id, resolution=c.resolution, enriched=False)
                  for c in [natural, *engineered]]
    order = [c.pdb_id for c in rank(unenriched, target_accession=TARGET)]
    assert order.index("4ZQK") == len(order) - 1, "natural complex ranks last unenriched"

    fully = rank([natural, *engineered], target_accession=TARGET)
    assert fully[0].pdb_id == "4ZQK", "and first once every candidate is enriched"
