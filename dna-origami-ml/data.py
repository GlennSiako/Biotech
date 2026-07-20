"""Synthetic DNA origami folding dataset for learning logistic regression.

Each row is one imagined folding experiment:
  x1 = Mg2+ concentration (mM)
  x2 = staple:scaffold molar excess
  y  = 1 if folds well, else 0

The "true" rule is intentionally simple so you can compare it to what
the trained model learns. It is NOT a claim about real biophysics —
it is a teaching scaffold.
"""

from __future__ import annotations

import numpy as np


FEATURE_NAMES = (
    "Mg2+_mM",
    "staple_excess",
)


def true_fold_probability(mg_mM: np.ndarray, staple_excess: np.ndarray) -> np.ndarray:
    """Known generative rule used only to create labels.

    Rough story:
    - Need enough Mg2+
    - Need enough staple excess
    - Soft threshold via sigmoid so labels are noisy / realistic for ML
    """
    # True weights in raw feature space (chosen for pedagogy, not literature fit)
    z = -6.0 + 0.35 * mg_mM + 0.55 * staple_excess
    return 1.0 / (1.0 + np.exp(-z))


def make_origami_folding_dataset(
    n_samples: int = 200,
    seed: int = 7,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Create (X, y) for binary fold-success classification.

    Returns
    -------
    X : shape (n_samples, 2)
        Columns: [Mg2+_mM, staple_excess]
    y : shape (n_samples,)
        1 = folded well, 0 = folded poorly
    meta : dict
        Ranges and names for explanations / plotting
    """
    rng = np.random.default_rng(seed)

    # Plausible toy ranges for a teaching demo
    mg = rng.uniform(2.0, 20.0, size=n_samples)          # mM
    staple_excess = rng.uniform(1.0, 15.0, size=n_samples)  # molar excess

    p = true_fold_probability(mg, staple_excess)
    y = rng.binomial(1, p).astype(float)

    X = np.column_stack([mg, staple_excess])
    meta = {
        "feature_names": FEATURE_NAMES,
        "mg_range_mM": (2.0, 20.0),
        "staple_excess_range": (1.0, 15.0),
        "positive_meaning": "folds well",
        "negative_meaning": "folds poorly",
    }
    return X, y, meta


def standardize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Feature scaling: (x - mean) / std.

    Why: gradient descent is much happier when features share a scale.
    Mg2+ is ~2-20; staple excess is ~1-15 — close, but we still scale
    so theta values are easier to compare during learning.
    """
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma = np.where(sigma == 0, 1.0, sigma)
    X_norm = (X - mu) / sigma
    return X_norm, mu, sigma
