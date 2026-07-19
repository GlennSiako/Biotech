"""Logistic regression from first principles (NumPy only).

Notation matches Andrew Ng / Stanford ML style:

  z = θᵀx          (with x0 = 1 for the bias)
  hθ(x) = σ(z) = 1 / (1 + e^{-z})
  J(θ)  = - (1/m) Σ [ y log h + (1-y) log(1-h) ]

Gradients:
  ∂J/∂θj = (1/m) Σ (hθ(x⁽ⁱ⁾) - y⁽ⁱ⁾) xj⁽ⁱ⁾
"""

from __future__ import annotations

import numpy as np


def sigmoid(z: np.ndarray) -> np.ndarray:
    """Map any real number to (0, 1) — our predicted probability."""
    # Clip for numerical stability when z is very large positive/negative
    z = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z))


def add_bias_column(X: np.ndarray) -> np.ndarray:
    """Prepend a column of ones so θ0 is the intercept."""
    m = X.shape[0]
    return np.column_stack([np.ones(m), X])


def hypothesis(X_bias: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """hθ(x) = σ(X θ)."""
    return sigmoid(X_bias @ theta)


def compute_cost(X_bias: np.ndarray, y: np.ndarray, theta: np.ndarray) -> float:
    """Binary cross-entropy / logistic loss J(θ)."""
    m = y.shape[0]
    h = hypothesis(X_bias, theta)
    # eps avoids log(0)
    eps = 1e-12
    h = np.clip(h, eps, 1.0 - eps)
    cost = -(1.0 / m) * np.sum(y * np.log(h) + (1.0 - y) * np.log(1.0 - h))
    return float(cost)


def compute_gradients(X_bias: np.ndarray, y: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Vector of ∂J/∂θj for all j (including bias)."""
    m = y.shape[0]
    h = hypothesis(X_bias, theta)
    # Same elegant result as in the course: (1/m) Xᵀ (h - y)
    return (1.0 / m) * (X_bias.T @ (h - y))


def gradient_descent(
    X: np.ndarray,
    y: np.ndarray,
    alpha: float = 0.1,
    num_iters: int = 2000,
    theta_init: np.ndarray | None = None,
) -> tuple[np.ndarray, list[float]]:
    """Learn θ by repeatedly stepping opposite the gradient.

    Parameters
    ----------
    X : (m, n) features WITHOUT bias column
    y : (m,) labels in {0, 1}
    alpha : learning rate
    num_iters : number of update steps
    """
    X_bias = add_bias_column(X)
    n_with_bias = X_bias.shape[1]
    theta = np.zeros(n_with_bias) if theta_init is None else theta_init.astype(float).copy()

    history: list[float] = []
    for _ in range(num_iters):
        grad = compute_gradients(X_bias, y, theta)
        theta = theta - alpha * grad
        history.append(compute_cost(X_bias, y, theta))

    return theta, history


def predict_proba(X: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Predicted P(y=1 | x)."""
    return hypothesis(add_bias_column(X), theta)


def predict(X: np.ndarray, theta: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Hard class labels from probability threshold."""
    return (predict_proba(X, theta) >= threshold).astype(float)


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(y_true == y_pred))
