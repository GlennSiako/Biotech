"""Step 5 — from linear regression to classification (logistic).

Until now we predicted a NUMBER:
  y = abs_error_deg

Classification predicts a LABEL:
  y = 1  if angle is high-fidelity (|error| < threshold)
  y = 0  otherwise

Why not just use linear regression?
  hθ(x) can be <0 or >1, but a probability should stay in (0,1).

Logistic regression fix (Andrew Ng):
  z = θᵀx
  hθ(x) = σ(z) = 1 / (1 + e^{-z})   ← probability of y=1

Cost (log loss / binary cross-entropy):
  J(θ) = - (1/m) Σ [ y log h + (1-y) log(1-h) ]

Gradient (same elegant form as linear regression!):
  ∂J/∂θj = (1/m) Σ (h - y) xj

Run:
  python3 step5_classification.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


DATA = Path(__file__).resolve().parent / "data" / "bathe_metis_tem_angles.csv"
FIDELITY_THRESHOLD_DEG = 8.0


def load_classification_xy() -> tuple[np.ndarray, np.ndarray, dict]:
    rows = list(csv.DictReader(DATA.open()))
    edge_6hb = np.array([1.0 if r["edge_type"] == "6HB" else 0.0 for r in rows])
    n_sides = np.array([float(r["n_sides"]) for r in rows])
    abs_err = np.array([float(r["abs_error_deg"]) for r in rows])

    # Binary label from the continuous measurement
    y = (abs_err < FIDELITY_THRESHOLD_DEG).astype(float)

    # Scale n_sides; leave 0/1 edge flag alone
    mu, sigma = float(n_sides.mean()), float(n_sides.std()) or 1.0
    n_sides_s = (n_sides - mu) / sigma
    X = np.column_stack([edge_6hb, n_sides_s])

    meta = {
        "mu_n_sides": mu,
        "sigma_n_sides": sigma,
        "threshold_deg": FIDELITY_THRESHOLD_DEG,
        "pos_rate": float(y.mean()),
    }
    return X, y, meta


def sigmoid(z: np.ndarray) -> np.ndarray:
    z = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z))


def add_bias(X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X])


def compute_cost(X_b: np.ndarray, y: np.ndarray, theta: np.ndarray) -> float:
    m = len(y)
    h = sigmoid(X_b @ theta)
    eps = 1e-12
    h = np.clip(h, eps, 1 - eps)
    return float(-(1.0 / m) * np.sum(y * np.log(h) + (1 - y) * np.log(1 - h)))


def gradient_descent(
    X: np.ndarray,
    y: np.ndarray,
    alpha: float = 0.5,
    num_iters: int = 4000,
) -> tuple[np.ndarray, list[float]]:
    X_b = add_bias(X)
    theta = np.zeros(X_b.shape[1])
    history: list[float] = []
    m = len(y)
    for _ in range(num_iters):
        h = sigmoid(X_b @ theta)
        grad = (1.0 / m) * (X_b.T @ (h - y))
        theta = theta - alpha * grad
        history.append(compute_cost(X_b, y, theta))
    return theta, history


def predict_proba(X: np.ndarray, theta: np.ndarray) -> np.ndarray:
    return sigmoid(add_bias(X) @ theta)


def predict(X: np.ndarray, theta: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    return (predict_proba(X, theta) >= threshold).astype(float)


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_true == y_pred))


def main() -> None:
    X, y, meta = load_classification_xy()

    # Hold-out split
    rng = np.random.default_rng(0)
    idx = rng.permutation(len(y))
    split = int(0.8 * len(y))
    train, test = idx[:split], idx[split:]
    X_tr, y_tr = X[train], y[train]
    X_te, y_te = X[test], y[test]

    theta, history = gradient_descent(X_tr, y_tr)

    yhat_tr = predict(X_tr, theta)
    yhat_te = predict(X_te, theta)

    print("=" * 64)
    print("STEP 5: Classification (logistic regression)")
    print("=" * 64)
    print(
        f"""
Label definition (from Bathe TEM angles):
  y = 1  (high fidelity) if |angle error| < {meta['threshold_deg']}°
  y = 0  otherwise

Positive rate in data: {meta['pos_rate']:.1%} high-fidelity

Bridge from linear regression:
  linear:   h = θᵀx           (any real number)
  logistic: h = σ(θᵀx)        (probability between 0 and 1)
"""
    )
    print(f"Learned θ0 (bias):           {theta[0]:+.3f}")
    print(f"Learned θ1 (edge_is_6HB):    {theta[1]:+.3f}")
    print(f"Learned θ2 (n_sides scaled): {theta[2]:+.3f}")
    print(f"Final train cost J:          {history[-1]:.4f}")
    print(f"Train accuracy:              {accuracy(y_tr, yhat_tr):.1%}")
    print(f"Test accuracy:               {accuracy(y_te, yhat_te):.1%}")

    # Example designs in RAW feature space for explanation
    examples = [
        ("triangle DX", 0.0, 3.0),
        ("triangle 6HB", 1.0, 3.0),
        ("hexagon DX", 0.0, 6.0),
        ("hexagon 6HB", 1.0, 6.0),
    ]
    print("\nExample P(high fidelity):")
    mu, sig = meta["mu_n_sides"], meta["sigma_n_sides"]
    for name, e, n in examples:
        x = np.array([[e, (n - mu) / sig]])
        p = float(predict_proba(x, theta)[0])
        print(f"  {name:14}  P(y=1) = {p:.3f}  → predict {int(p >= 0.5)}")

    print(
        """
Sign check (same logic as regression, new meaning):
  θ1 > 0 → 6HB increases P(high fidelity)   [we expect this]
  θ2 < 0 → more sides decreases P(high fidelity)  [matches Step 4]

YOUR CHECKPOINT:
  Why do we put θᵀx through a sigmoid instead of using θᵀx directly
  as the prediction for classification?
"""
    )


if __name__ == "__main__":
    main()
