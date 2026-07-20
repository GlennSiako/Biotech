"""Step 2 — cost function J(θ) for linear regression (MSE).

Core idea:
  For one example:  error = hθ(x) - y
  Squared error:    (hθ(x) - y)²
  Cost J(θ):        average squared error over the training set

  J(θ) = (1 / (2m)) * Σ (hθ(x⁽ⁱ⁾) - y⁽ⁱ⁾)²

The 1/(2m) is Andrew Ng's convention:
  - 1/m  → average, so cost doesn't grow just because m is larger
  - 1/2  → cancels the 2 that appears when we differentiate (next step)

Run:
  python3 step2_cost_function.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


DATA = Path(__file__).resolve().parent / "data" / "bathe_metis_tem_angles.csv"


def load_xy() -> tuple[np.ndarray, np.ndarray]:
    """One-feature model: x1 = edge_is_6HB, y = abs_error_deg."""
    rows = list(csv.DictReader(DATA.open()))
    x1 = np.array([1.0 if r["edge_type"] == "6HB" else 0.0 for r in rows])
    y = np.array([float(r["abs_error_deg"]) for r in rows])
    # X columns: [x0=1 bias, x1]
    X = np.column_stack([np.ones(len(rows)), x1])
    return X, y


def hypothesis(X: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """hθ(x) = X @ θ   (linear regression — no sigmoid yet)."""
    return X @ theta


def compute_cost(X: np.ndarray, y: np.ndarray, theta: np.ndarray) -> float:
    """Mean squared error cost J(θ) = (1/(2m)) Σ (h - y)²."""
    m = len(y)
    h = hypothesis(X, theta)
    return float((1.0 / (2 * m)) * np.sum((h - y) ** 2))


def main() -> None:
    X, y = load_xy()
    m = len(y)

    print("=" * 64)
    print("STEP 2: Cost function J(θ)")
    print("=" * 64)
    print(
        f"""
Data: {m} TEM angles from Bathe/METIS Source Data
Model: hθ(x) = θ0 + θ1 * edge_is_6HB
Target y: abs_error_deg

J(θ) asks: "If I pick these θ values, how wrong am I on average?"
"""
    )

    # Three hand-picked θ guesses — no training yet
    candidates = {
        "terrible (wrong sign)": np.array([11.0, +7.0]),
        "roughly sensible": np.array([11.0, -7.0]),
        "all zeros": np.array([0.0, 0.0]),
    }

    print(f"{'guess':28} {'θ0':>8} {'θ1':>8} {'J(θ)':>12}")
    for name, theta in candidates.items():
        j = compute_cost(X, y, theta)
        print(f"{name:28} {theta[0]:8.1f} {theta[1]:8.1f} {j:12.3f}")

    print(
        """
What to notice:
  - Wrong-sign θ1 (positive) → higher cost
  - Sensible negative θ1     → lower cost
  - Training later = search for θ that makes J(θ) as small as possible

YOUR CHECKPOINT:
  In one sentence: what does a smaller J(θ) mean for our origami model?
"""
    )


if __name__ == "__main__":
    main()
