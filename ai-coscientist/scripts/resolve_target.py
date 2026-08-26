#!/usr/bin/env python3
"""Stages 1-2: resolve a target and prepare its working structure.

    python scripts/resolve_target.py CD274 --region 18-134 --prepare

Writes runs/<run_id>/manifest.json recording the target, every candidate
structure with its score and reasoning, the choice made, and what preparation
found -- so a campaign can be explained after the fact, not just repeated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.resolve import ResolutionError, rank, resolve          # noqa: E402
from pipeline.resolve.rcsb import enrich_all                         # noqa: E402
from pipeline.run.manifest import RunManifest                        # noqa: E402
from pipeline.structure import FetchError, fetch_structure, prepare  # noqa: E402

RUNS_DIR = Path("runs")


def parse_region(value: str | None) -> tuple[int, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", value.strip())
    if not match:
        raise argparse.ArgumentTypeError(f"region must look like '18-134', got {value!r}")
    lo, hi = int(match.group(1)), int(match.group(2))
    if lo >= hi:
        raise argparse.ArgumentTypeError(f"region start must be below end, got {value!r}")
    return lo, hi


def make_run_id(query: str, now: dt.datetime) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", query).strip("-").lower()[:32]
    return f"{now:%Y%m%d-%H%M%S}-{slug or 'run'}"


def print_candidates(candidates, top: int) -> None:
    print(f"\nCandidate structures (top {min(top, len(candidates))} of {len(candidates)}):")
    for i, c in enumerate(candidates[:top], 1):
        marker = "->" if i == 1 else "  "
        res = f"{c.resolution:.2f} A" if c.resolution is not None else "n/a"
        print(f"\n {marker} {i}. {c.pdb_id}  score {c.score:.2f}  [{c.method}, {res}]")
        if c.title:
            print(f"       {c.title}")

        for note in c.notes:
            print(f"       - {note}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", help="gene symbol or protein name, e.g. CD274")
    ap.add_argument("--region", type=parse_region, default=None,
                    help="residue range of interest, e.g. 18-134")
    ap.add_argument("--organism", type=int, default=9606, help="NCBI taxon id")
    ap.add_argument("--top", type=int, default=5, help="candidates to display")
    ap.add_argument("--no-enrich", action="store_true",
                    help="skip RCSB enrichment (faster; partners unknown)")
    ap.add_argument("--prepare", action="store_true",
                    help="fetch and prepare the top-ranked structure")
    ap.add_argument("--chain", default=None,
                    help="chain to prepare (default: first chain of the top candidate)")
    ap.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    now = dt.datetime.now(dt.timezone.utc)
    manifest = RunManifest(
        run_id=make_run_id(args.query, now),
        created_at=now.isoformat(),
        query=args.query,
        region=args.region,
        errors=[],
    )
    run_dir = args.runs_dir / manifest.run_id

    try:
        target, candidates, strategy = resolve(args.query, organism_id=args.organism)
    except ResolutionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        manifest.errors.append(str(exc))
        manifest.write(run_dir)
        return 1

    manifest.search_strategy = strategy
    manifest.target = dict(target.__dict__)
    print(f"\nTarget: {target.summary()}")
    print(f"        matched via {strategy}")
    if strategy == "full_text":
        print("        NOTE: matched on free text, not a gene name — confirm this "
              "is the intended protein")

    if not candidates:
        print("No PDB structures cross-referenced for this target.", file=sys.stderr)
        manifest.errors.append("no PDB structures found")
        manifest.write(run_dir)
        return 1

    # Rank once to shortlist, enrich the shortlist, then re-rank: enrichment
    # supplies the complex flag, which carries the heaviest weight.
    ranked = rank(candidates, args.region, target.accession, target.taxon_id)
    if not args.no_enrich:
        # Enrich everything, not a shortlist. Partner kind is the heaviest term
        # in the score, so shortlisting on the criteria available beforehand
        # hides the structures that would win on it.
        print(f"Enriching all {len(ranked)} candidates from RCSB ...")
        enrich_all(ranked, target_accession=target.accession)
        ranked = rank(ranked, args.region, target.accession, target.taxon_id)

    manifest.candidates = [c.to_dict() for c in ranked]
    print_candidates(ranked, args.top)

    best = ranked[0]
    manifest.chosen = best.to_dict()

    if not best.protein_partners and not args.no_enrich:
        print("\nNOTE: the top structure has no protein binding partner. The "
              "epitope will have to be predicted rather than read from an "
              "observed interface (see D-010).")

    if args.prepare:
        chain = args.chain or (best.coverage.chains[0] if best.coverage.chains else None)
        if chain is None:
            msg = f"{best.pdb_id}: no chain identifier available; pass --chain"
            print(f"\nERROR: {msg}", file=sys.stderr)
            manifest.errors.append(msg)
            manifest.write(run_dir)
            return 1

        print(f"\nPreparing {best.pdb_id} chain {chain} ...")
        try:
            path = fetch_structure(best.pdb_id)
            out_path = run_dir / f"{best.pdb_id}_{chain}.pdb"
            written, report = prepare(path, chain, pdb_id=best.pdb_id,
                                      region=args.region, out_path=out_path)
        except (FetchError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            manifest.errors.append(str(exc))
            manifest.write(run_dir)
            return 1

        manifest.preparation = report.to_dict()
        manifest.structure_file = str(written)
        print("\n" + report.describe())

    path = manifest.write(run_dir)
    print(f"\nManifest: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
