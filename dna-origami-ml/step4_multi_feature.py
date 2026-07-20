"""Step 4 — multi-feature linear regression on Bathe TEM angles.

Until now:
  hθ(x) = θ0 + θ1 * edge_is_6HB

Now add a second design feature:
  x2 = n_sides   (3=triangle, 4=square, 6=hexagon)

So:
  hθ(x) = θ0 + θ1 * edge_is_6HB + θ2 * n_sides

New idea: FEATURE SCALING
  edge_is_6HB is 0/1, n_sides is 3–6. Different scales make gradient
  descent slower / zig-zaggy. We standardize continuous-ish features:
      x_scaled = (x - mean) / std

We keep the 0/1 edge flag as-is (already tiny scale).

Run:
  python3 step4_multi_feature.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


DATA = Path(__file__).resolve().parent / "data" / "bathe_metis_tem_angles.csv"


def load_raw() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = list(csv.DictReader(DATA.open()))
    edge_6hb = np.array([1.0 if r["edge_type"] == "6HB" else 0.0 for r in rows])
    n_sides = np.array([float(r["n_sides"]) for r in rows])
    y = np.array([float(r["abs_error_deg"]) for r in rows])
    return edge_6hb, n_sides, y


def standardize(x: np.ndarray) -> tuple[np.ndarray, float, float]:
    mu = float(x.mean())
    sigma = float(x.std())
    if sigma == 0:
        sigma = 1.0
    return (x - mu) / sigma, mu, sigma


def add_bias(X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X])


def compute_cost(X_b: np.ndarray, y: np.ndarray, theta: np.ndarray) -> float:
    m = len(y)
    err = X_b @ theta - y
    return float((1.0 / (2 * m)) * np.sum(err**2))


def gradient_descent(
    X_b: np.ndarray,
    y: np.ndarray,
    alpha: float,
    num_iters: int,
) -> tuple[np.ndarray, list[float]]:
    theta = np.zeros(X_b.shape[1])
    history: list[float] = []
    m = len(y)
    for _ in range(num_iters):
        err = X_b @ theta - y
        grad = (1.0 / m) * (X_b.T @ err)
        theta = theta - alpha * grad
        history.append(compute_cost(X_b, y, theta))
    return theta, history


def main() -> None:
    edge_6hb, n_sides, y = load_raw()
    n_sides_s, mu_n, sig_n = standardize(n_sides)

    # Model A: edge only (Step 3 baseline)
    X1 = add_bias(edge_6hb.reshape(-1, 1))
    theta1, hist1 = gradient_descent(X1, y, alpha=0.3, num_iters=3000)

    # Model B: edge + scaled n_sides
    X2 = add_bias(np.column_stack([edge_6hb, n_sides_s]))
    theta2, hist2 = gradient_descent(X2, y, alpha=0.3, num_iters=3000)

    print("=" * 64)
    print("STEP 4: Two features")
    print("=" * 64)
    print(
        f"""
Features:
  x1 = edge_is_6HB          (0 or 1)
  x2 = n_sides, scaled      (raw mean={mu_n:.2f}, std={sig_n:.2f})

Same math as Step 3 — just a longer θ vector.
"""
    )
    print("Model A  (edge only)")
    print(f"  θ0={theta1[0]:+.3f}  θ1(6HB)={theta1[1]:+.3f}")
    print(f"  final J = {hist1[-1]:.4f}")

    print("\nModel B  (edge + n_sides)")
    print(f"  θ0={theta2[0]:+.3f}  θ1(6HB)={theta2[1]:+.3f}  θ2(n_sides)={theta2[2]:+.3f}")
    print(f"  final J = {hist2[-1]:.4f}")

    print(
        f"""
How to read θ2:
  θ2 is the effect of n_sides *after scaling*.
  Positive θ2 → more sides associated with larger angle error
  Negative θ2 → more sides associated with smaller angle error
  Learned θ2 = {theta2[2]:+.3f}

Did the extra feature help?
  ΔJ = J_A - J_B = {hist1[-1] - hist2[-1]:+.4f}
  (positive ΔJ means Model B fits a bit better)

YOUR CHECKPOINT:
  Look at θ2's sign. In one sentence, what does that say about
  triangles vs hexagons in this Bathe TEM dataset?
"""
    )


if __name__ == "__main__":
    main()
