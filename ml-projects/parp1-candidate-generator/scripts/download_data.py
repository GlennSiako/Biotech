#!/usr/bin/env python3
"""Download PARP1 activity data from ChEMBL and create scaffold splits."""

from __future__ import annotations

import argparse
from pathlib import Path

from parp1_ml.data import fetch_parp1_activities, save_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/parp1_activities.csv"),
    )
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    frame = fetch_parp1_activities(max_records=args.max_records)
    save_dataset(frame, args.output, seed=args.seed)
    print(f"Saved {len(frame):,} unique molecules to {args.output}")
    print(frame["pchembl_value"].describe().round(2).to_string())


if __name__ == "__main__":
    main()
