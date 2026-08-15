"""Command-line entry point for the PhytoForge simulator."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from phytoforge.domain import CampaignConfig
from phytoforge.engine import SimulationEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phytoforge",
        description="Run the synthetic hEGF autonomous biofoundry benchmark.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--plants-per-design", type=int, default=6)
    parser.add_argument(
        "--selector",
        choices=("adaptive", "random"),
        default="adaptive",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the complete machine-readable report",
    )
    parser.add_argument(
        "--show-latent",
        action="store_true",
        help="include hidden simulator state for model development",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = CampaignConfig(
        seed=args.seed,
        rounds=args.rounds,
        batch_size=args.batch_size,
        plants_per_design=args.plants_per_design,
        selector=args.selector,
    )
    report = SimulationEngine().run(config)

    if args.json:
        print(
            json.dumps(
                report.to_dict(include_latent=args.show_latent),
                indent=2,
                sort_keys=True,
            )
        )
    else:
        _print_summary(report)
    return 0


def _print_summary(report) -> None:
    best = report.best_result
    print("PhytoForge hEGF benchmark")
    print(f"Calibration tier: {report.calibration_tier}")
    print(f"Experiments: {len(report.results)}")
    for decision in report.decisions:
        selected = ", ".join(decision["selected_design_ids"]) or "none"
        print(
            f"Round {decision['round_index'] + 1}: "
            f"{decision['reason']} -> {selected}"
        )
    if best:
        print(f"Best design: {best.design.design_id}")
        print(f"Observed utility: {best.utility:.3f}")
        print(
            "Measured recovered target: "
            f"{best.observation.measured_target_mg:.3f} mg"
        )
        print(
            "Measured activity-retention proxy: "
            f"{best.observation.measured_activity_proxy:.3f}"
        )
        print(f"Facility completion: {best.events[-1].end_hour:.1f} h")
    for warning in report.warnings:
        print(f"Warning: {warning}")


if __name__ == "__main__":
    raise SystemExit(main())

