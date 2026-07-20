"""Step 1 — look at the Bathe/METIS data before writing any model.

Run:
  python3 step1_look_at_data.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev


DATA = Path(__file__).resolve().parent / "data" / "bathe_metis_tem_angles.csv"


def main() -> None:
    rows = list(csv.DictReader(DATA.open()))
    print("=" * 64)
    print("STEP 1: What are we predicting?")
    print("=" * 64)
    print(
        """
Paper: Jun et al., Nat Commun 2019 (Bathe lab METIS)
Each row = one internal angle measured from TEM of a wireframe DNA origami.

Continuous target (linear regression):
  y = abs_error_deg = |measured_angle - target_angle|

Design features we can use as x:
  x1 = edge_type   (DX=0, 6HB=1)   — stiffer edges should reduce error
  x2 = n_sides     (3,4,6)         — triangle / square / hexagon
  x3 = edge_length_bp              — how long each edge is

Later (classification):
  label high_fidelity = 1 if abs_error_deg < 8°, else 0
"""
    )
    print(f"Loaded {len(rows)} angle measurements from:\n  {DATA.name}\n")

    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        groups[(r["geometry"], r["edge_type"])].append(float(r["abs_error_deg"]))

    print(f"{'geometry':10} {'edge':5} {'n':>5} {'mean|err|':>10} {'sd|err|':>10}")
    for (geom, edge), errs in sorted(groups.items()):
        print(
            f"{geom:10} {edge:5} {len(errs):5d} {mean(errs):10.2f} {pstdev(errs):10.2f}"
        )

    print(
        """
Observation to hold onto:
  6HB edges have smaller mean angle error than DX edges.
  That is exactly the kind of relationship a linear model can learn.

YOUR CHECKPOINT (reply in your own words):
  If our hypothesis is
      y ≈ θ0 + θ1 * (edge_is_6HB) + ...
  do you expect θ1 to be positive or negative, and why?
"""
    )


if __name__ == "__main__":
    main()
