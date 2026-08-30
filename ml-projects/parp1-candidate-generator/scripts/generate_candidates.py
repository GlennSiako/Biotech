#!/usr/bin/env python3
"""Generate and rank proposed PARP1 candidates."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from parp1_ml.generate import generate_and_rank
from parp1_ml.model import ActivityModel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/parp1_activities.csv"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/parp1_activity_model.joblib"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/ranked_candidates.csv"),
    )
    parser.add_argument("--pool-size", type=int, default=1000)
    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset = pd.read_csv(args.data)
    model = ActivityModel.load(args.model)
    candidates = generate_and_rank(
        dataset,
        model,
        max_candidates=args.pool_size,
        top_n=args.top_n,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(args.output, index=False)
    print(candidates.head(10).round(3).to_string(index=False))
    print(f"Saved {len(candidates)} ranked candidates to {args.output}")


if __name__ == "__main__":
    main()
