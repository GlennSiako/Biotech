#!/usr/bin/env python3
"""Train and evaluate the PARP1 activity model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from parp1_ml.model import train


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
        "--metrics",
        type=Path,
        default=Path("artifacts/metrics.json"),
    )
    parser.add_argument("--trees", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset = pd.read_csv(args.data)
    model, metrics = train(dataset, n_estimators=args.trees, seed=args.seed)
    model.save(args.model)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"Saved model to {args.model}")


if __name__ == "__main__":
    main()
