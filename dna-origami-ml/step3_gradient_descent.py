"""Step 3 — gradients + gradient descent for linear regression.

From Step 2:
  J(θ) = (1/(2m)) Σ (hθ(x⁽ⁱ⁾) - y⁽ⁱ⁾)²
  hθ(x) = θᵀx

Differentiate (Andrew Ng result):
  ∂J/∂θj = (1/m) Σ (hθ(x⁽ⁱ⁾) - y⁽ⁱ⁾) xj⁽ⁱ⁾

In vector form:
  ∇J(θ) = (1/m) Xᵀ (h - y)

Gradient descent update:
  θ := θ - α ∇J(θ)

α = learning rate (step size). Too big → overshoot; too small → slow.

Run:
  python3 step3_gradient_descent.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


DATA = Path(__file__).resolve().parent / "data" / "bathe_metis_tem_angles.csv"


def load_xy() -> tuple[np.ndarray, np.ndarray]:
    rows = list(csv.DictReader(DATA.open()))
    x1 = np.array([1.0 if r["edge_type"] == "6HB" else 0.0 for r in rows])
    y = np.array([float(r["abs_error_deg"]) for r in rows])
    X = np.column_stack([np.ones(len(rows)), x1])
    return X, y


def hypothesis(X: np.ndarray, theta: np.ndarray) -> np.ndarray:
    return X @ theta


def compute_cost(X: np.ndarray, y: np.ndarray, theta: np.ndarray) -> float:
    m = len(y)
    err = hypothesis(X, theta) - y
    return float((1.0 / (2 * m)) * np.sum(err**2))


def compute_gradients(X: np.ndarray, y: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """∂J/∂θj for all j — the downhill direction of the cost bowl."""
    m = len(y)
    err = hypothesis(X, theta) - y
    return (1.0 / m) * (X.T @ err)


def gradient_descent(
    X: np.ndarray,
    y: np.ndarray,
    alpha: float = 0.1,
    num_iters: int = 2000,
) -> tuple[np.ndarray, list[float]]:
    theta = np.zeros(X.shape[1])
    history: list[float] = []
    for _ in range(num_iters):
        theta = theta - alpha * compute_gradients(X, y, theta)
        history.append(compute_cost(X, y, theta))
    return theta, history


def main() -> None:
    X, y = load_xy()

    # Closed-form sanity check for this 1-feature case (group means)
    dx_mean = float(y[X[:, 1] == 0].mean())
    hb_mean = float(y[X[:, 1] == 1].mean())
    theta_analytic = np.array([dx_mean, hb_mean - dx_mean])

    theta, history = gradient_descent(X, y, alpha=0.3, num_iters=3000)

    print("=" * 64)
    print("STEP 3: Gradient descent learns θ")
    print("=" * 64)
    print(
        """
Update rule:  θ := θ - α * ∂J/∂θ

We start at θ = [0, 0] and walk downhill on J until it flattens.
"""
    )
    print(f"Initial cost J(0):     {history[0]:.4f}")
    print(f"Final cost J(θ):       {history[-1]:.4f}")
    print(f"Learned θ0 (DX bias):  {theta[0]:+.3f}°")
    print(f"Learned θ1 (6HB):      {theta[1]:+.3f}°")
    print(f"Analytic θ0 (DX mean): {theta_analytic[0]:+.3f}°")
    print(f"Analytic θ1 (Δ mean):  {theta_analytic[1]:+.3f}°")
    print(
        f"""
Interpretation you can say out loud:
  DX designs: predicted |angle error| ≈ {theta[0]:.1f}°
  6HB designs: predicted |angle error| ≈ {theta[0] + theta[1]:.1f}°
  So 6HB is about {abs(theta[1]):.1f}° better on this metric.

YOUR CHECKPOINT:
  Why do we subtract α * gradient  (instead of adding it)?
"""
    )


if __name__ == "__main__":
    main()
