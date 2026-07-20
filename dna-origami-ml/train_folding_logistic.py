"""Train a tiny logistic model for DNA origami fold success and explain it.

Run:
  python3 train_folding_logistic.py
"""

from __future__ import annotations

import numpy as np

from data import FEATURE_NAMES, make_origami_folding_dataset, standardize
from logistic_regression import (
    accuracy,
    compute_cost,
    add_bias_column,
    gradient_descent,
    predict,
    predict_proba,
)


def explain_example(
    raw_x: np.ndarray,
    mu: np.ndarray,
    sigma: np.ndarray,
    theta: np.ndarray,
    y_true: float | None = None,
) -> None:
    """Print one design in words a human can repeat."""
    x_norm = (raw_x - mu) / sigma
    prob = float(predict_proba(x_norm.reshape(1, -1), theta)[0])
    pred = int(prob >= 0.5)

    print("  Design:")
    print(f"    Mg2+ = {raw_x[0]:.1f} mM")
    print(f"    staple excess = {raw_x[1]:.1f}x")
    print(f"  Model says P(folds well) = {prob:.3f} → predict y={pred}", end="")
    if y_true is not None:
        print(f"  (true y={int(y_true)})")
    else:
        print()


def main() -> None:
    print("=" * 60)
    print("DNA origami folding — logistic regression (from scratch)")
    print("=" * 60)

    X_raw, y, meta = make_origami_folding_dataset(n_samples=200, seed=7)
    X, mu, sigma = standardize(X_raw)

    # Simple hold-out split (no sklearn)
    m = X.shape[0]
    split = int(0.8 * m)
    rng = np.random.default_rng(0)
    idx = rng.permutation(m)
    train_idx, test_idx = idx[:split], idx[split:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    X_train_raw, X_test_raw = X_raw[train_idx], X_raw[test_idx]

    theta, history = gradient_descent(X_train, y_train, alpha=0.5, num_iters=3000)

    y_hat_train = predict(X_train, theta)
    y_hat_test = predict(X_test, theta)

    print("\n1) Dataset")
    print(f"   Features: {meta['feature_names']}")
    print(f"   Samples: {m}  |  train={len(train_idx)}  test={len(test_idx)}")
    print(f"   Class balance (fold well): {y.mean():.2%}")

    print("\n2) Learned parameters θ  (on standardized features)")
    print(f"   θ0 (bias)              = {theta[0]:+.3f}")
    for j, name in enumerate(FEATURE_NAMES):
        print(f"   θ{j+1} ({name:16s}) = {theta[j+1]:+.3f}")

    print("\n3) What the signs mean (first-principles check)")
    print("   If θ1 > 0: higher Mg2+ → higher predicted fold chance")
    print("   If θ2 > 0: higher staple excess → higher predicted fold chance")
    print(
        "   Learned signs:",
        "Mg2+",
        "↑" if theta[1] > 0 else "↓",
        "| staple excess",
        "↑" if theta[2] > 0 else "↓",
    )

    print("\n4) Training diagnostics")
    print(f"   Initial cost ~ {history[0]:.4f}")
    print(f"   Final cost   ~ {history[-1]:.4f}")
    print(f"   Train accuracy: {accuracy(y_train, y_hat_train):.1%}")
    print(f"   Test accuracy:  {accuracy(y_test, y_hat_test):.1%}")
    print(
        f"   Test cost:      {compute_cost(add_bias_column(X_test), y_test, theta):.4f}"
    )

    print("\n5) Example designs you can explain out loud")
    # Hand-picked extremes in raw space
    demos = np.array(
        [
            [4.0, 2.0],    # low Mg, low staples → should be unlikely
            [16.0, 12.0],  # high Mg, high staples → should be likely
            [10.0, 6.0],   # middle
        ]
    )
    for row in demos:
        explain_example(row, mu, sigma, theta)

    print("\n6) A few real rows from the test set")
    for i in range(min(3, len(test_idx))):
        explain_example(X_test_raw[i], mu, sigma, theta, y_true=y_test[i])

    print("\nNext interactive checkpoint for you:")
    print("  Can you write in your own words what θ1 and θ2 are doing?")
    print("  Push back if you want different features (e.g. GC%, anneal time).")


if __name__ == "__main__":
    main()
