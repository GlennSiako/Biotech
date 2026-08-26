"""Stage 2 preparation must handle the messes real entries contain."""

from __future__ import annotations

from pathlib import Path

import pytest
from Bio.PDB import PDBParser

from fixtures import build_pdb
from pipeline.structure.prepare import prepare


@pytest.fixture
def messy_pdb(tmp_path: Path) -> Path:
    path = tmp_path / "TEST.pdb"
    path.write_text(build_pdb())
    return path


def test_selects_requested_chain_only(messy_pdb, tmp_path):
    out, report = prepare(messy_pdb, "A", out_path=tmp_path / "prepared.pdb")

    structure = PDBParser(QUIET=True).get_structure("prep", str(out))
    chains = {c.id for model in structure for c in model}
    assert chains == {"A"}, "chain B leaked into the prepared structure"
    assert report.chain == "A"


def test_unknown_chain_fails_loudly(messy_pdb):
    with pytest.raises(ValueError, match="chain 'Z' not found"):
        prepare(messy_pdb, "Z")


def test_uses_first_model_and_warns(messy_pdb):
    _, report = prepare(messy_pdb, "A")
    assert report.n_models == 2
    assert report.model_used == 0
    assert any("2 models present" in w for w in report.warnings)


def test_detects_chain_break(messy_pdb):
    _, report = prepare(messy_pdb, "A")
    # Residues 10-12 then 16-17: residues 13-15 are unmodelled.
    assert report.gaps == [(13, 15)]
    assert report.has_internal_gaps


def test_gap_inside_region_of_interest_is_warned(messy_pdb):
    _, report = prepare(messy_pdb, "A", region=(10, 17))
    assert any("unmodelled residues inside the region" in w for w in report.warnings)


def test_gap_outside_region_is_not_warned(messy_pdb):
    _, report = prepare(messy_pdb, "A", region=(10, 12))
    assert not any("unmodelled residues inside" in w for w in report.warnings)


def test_removes_waters_and_heteroatoms(messy_pdb, tmp_path):
    out, report = prepare(messy_pdb, "A", out_path=tmp_path / "prepared.pdb")
    assert report.n_waters_removed == 2
    assert report.n_hetero_removed == 1

    text = out.read_text()
    assert "HOH" not in text
    assert "GOL" not in text


def test_keep_hetero_retains_ligand(messy_pdb, tmp_path):
    out, report = prepare(messy_pdb, "A", keep_hetero=True,
                          out_path=tmp_path / "with_ligand.pdb")
    assert report.n_hetero_removed == 0
    assert "GOL" in out.read_text()
    assert "HOH" not in out.read_text(), "waters are dropped even when hetero is kept"


def test_reports_alternate_conformations(messy_pdb):
    _, report = prepare(messy_pdb, "A")
    assert report.n_altloc_residues >= 1


def test_altloc_resolved_to_one_conformer(messy_pdb, tmp_path):
    out, _ = prepare(messy_pdb, "A", out_path=tmp_path / "prepared.pdb")
    structure = PDBParser(QUIET=True).get_structure("prep", str(out))
    residue = next(r for model in structure for c in model for r in c if r.id[1] == 16)
    names = [a.get_name() for a in residue]
    assert len(names) == len(set(names)), "duplicate atoms: altloc was not resolved"


def test_residue_range_and_count(messy_pdb):
    _, report = prepare(messy_pdb, "A")
    assert (report.first_residue, report.last_residue) == (10, 17)
    assert report.n_residues == 5  # 10, 11, 12, 16, 17


def test_short_coverage_is_warned(messy_pdb):
    _, report = prepare(messy_pdb, "A", region=(1, 200))
    assert any("short of the requested region" in w for w in report.warnings)


def test_report_serialises(messy_pdb):
    _, report = prepare(messy_pdb, "A", region=(10, 17))
    data = report.to_dict()
    assert data["gaps"] == [[13, 15]]
    assert data["residue_range"] == [10, 17]
    assert isinstance(report.describe(), str)
