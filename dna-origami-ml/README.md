# DNA Origami Folding — Logistic Regression from First Principles

Interactive learning project: build logistic regression the Andrew Ng way, applied to a simplified DNA origami folding problem.

## The scientific question (in plain language)

Given a few experimental / design settings for a DNA origami, can we predict whether the structure is likely to **fold successfully**?

This is a **binary classification** problem:

- \(y = 1\): folds well (clean band / expected shape)
- \(y = 0\): folds poorly (aggregates, incomplete, wrong product)

## Proposed starter model (v0 — keep it explainable)

We intentionally start with **two features** so you can draw the decision boundary and explain every weight out loud.

| Feature | Symbol | Physical intuition |
|--------|--------|--------------------|
| Mg²⁺ concentration (mM) | \(x_1\) | Divalent cations stabilize DNA helices / folding |
| Staple excess (staple:scaffold molar ratio) | \(x_2\) | Enough staples help complete the structure; too little → incomplete |

Model hypothesis (same as the course):

\[
\hat{y} = h_\theta(x) = \sigma(\theta_0 + \theta_1 x_1 + \theta_2 x_2)
\]

where \(\sigma(z) = 1 / (1 + e^{-z})\) is the sigmoid.

Interpretation you should be able to say:

- \(\theta_1 > 0\): higher Mg²⁺ increases predicted fold probability
- \(\theta_2 > 0\): higher staple excess increases predicted fold probability
- \(\theta_0\): bias / baseline log-odds when features are at their scaled zero

## What is synthetic on purpose

Real origami datasets are messy (gel scores, AFM, different labs). For learning derivatives and gradient descent, we generate a **tiny synthetic dataset** from a known “true” folding rule, then ask the model to recover a similar boundary.

That lets you check: *Did my implementation learn something sensible?*

## How we will learn interactively

1. Agree on features + labels (this README is the proposal — push back anytime).
2. Derive cost \(J(\theta)\) and gradients by hand.
3. Implement sigmoid → loss → gradients → gradient descent in NumPy only.
4. Train, inspect \(\theta\), plot decision boundary, explain a few example designs.
5. Only later: more features, regularization, real data.

## Run the starter

```bash
cd dna-origami-ml
python3 train_folding_logistic.py
```

## Files

- `data.py` — synthetic origami folding examples
- `logistic_regression.py` — model math from scratch (NumPy)
- `train_folding_logistic.py` — train + print an explainable report
