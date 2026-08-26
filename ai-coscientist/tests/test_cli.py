"""CLI argument handling and run-id construction."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pipeline.run.manifest import RunManifest  # noqa: E402
from resolve_target import make_run_id, parse_region  # noqa: E402


@pytest.mark.parametrize("value,expected", [
    ("18-134", (18, 134)), (" 1 - 290 ", (1, 290)), (None, None), ("", None),
])
def test_region_parsing(value, expected):
    assert parse_region(value) == expected


@pytest.mark.parametrize("bad", ["18", "abc", "134-18", "18-18", "18..134"])
def test_bad_region_rejected(bad):
    with pytest.raises(argparse.ArgumentTypeError):
        parse_region(bad)


def test_run_id_is_slugged_and_timestamped():
    now = dt.datetime(2026, 8, 26, 5, 30, 0)
    assert make_run_id("CD274", now) == "20260826-053000-cd274"
    assert make_run_id("PD-L1 / CD274", now).endswith("pd-l1-cd274")


def test_manifest_round_trips(tmp_path):
    manifest = RunManifest(run_id="r1", created_at="2026-08-26T00:00:00Z",
                           query="CD274", region=(18, 134))
    data = json.loads(manifest.write(tmp_path).read_text())
    assert data["region"] == [18, 134]
    assert data["manifest_version"] == 1
    assert data["candidates"] == [] and data["errors"] == []


def test_manifest_records_alternatives_not_just_winner(tmp_path):
    """A manifest listing only the chosen structure cannot explain a bad campaign."""
    manifest = RunManifest(run_id="r2", created_at="x", query="CD274", region=None,
                           candidates=[{"pdb_id": "AAAA"}, {"pdb_id": "BBBB"}],
                           chosen={"pdb_id": "AAAA"})
    data = json.loads(manifest.write(tmp_path).read_text())
    assert len(data["candidates"]) == 2
    assert data["chosen"]["pdb_id"] == "AAAA"


def test_end_to_end_flow_with_stubbed_network(tmp_path, monkeypatch, capsys):
    """Exercise main() start to finish: resolve -> rank -> manifest.

    The network is stubbed rather than mocked away entirely, so the wiring
    between stages is genuinely exercised.
    """
    import resolve_target
    from fixtures import UNIPROT_PAYLOAD
    from pipeline.resolve.uniprot import parse_structures, parse_target

    def fake_resolve(query, organism_id=9606, session=None):
        return parse_target(UNIPROT_PAYLOAD), parse_structures(UNIPROT_PAYLOAD), "gene_exact"

    monkeypatch.setattr(resolve_target, "resolve", fake_resolve)

    code = resolve_target.main([
        "CD274", "--region", "18-134", "--no-enrich", "--runs-dir", str(tmp_path),
    ])
    assert code == 0

    out = capsys.readouterr().out
    assert "CD274" in out and "4ZQK" in out

    manifest_path = next(tmp_path.glob("*/manifest.json"))
    data = json.loads(manifest_path.read_text())
    assert data["target"]["accession"] == "Q9NZQ7"
    assert data["search_strategy"] == "gene_exact"
    assert data["chosen"]["pdb_id"] in {"4ZQK", "3BIK"}
    assert len(data["candidates"]) == 3
    assert all(c["notes"] for c in data["candidates"]), "reasoning must be recorded"


def test_resolution_failure_still_writes_a_manifest(tmp_path, monkeypatch):
    """A failed run must leave a record, not vanish."""
    import resolve_target
    from pipeline.resolve import ResolutionError

    def failing_resolve(query, organism_id=9606, session=None):
        raise ResolutionError("no reviewed UniProt entry found for 'NOTAGENE'")

    monkeypatch.setattr(resolve_target, "resolve", failing_resolve)
    assert resolve_target.main(["NOTAGENE", "--runs-dir", str(tmp_path)]) == 1

    data = json.loads(next(tmp_path.glob("*/manifest.json")).read_text())
    assert data["errors"] and "NOTAGENE" in data["errors"][0]
