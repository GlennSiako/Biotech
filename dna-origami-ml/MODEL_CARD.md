# Model card — Bathe METIS angle fidelity (what we built)

Say this out loud. If a sentence fails, that is the gap to restudy.

## What X is (inputs / features)
From each TEM angle measurement we use design features, for example:
- \(x_1\): edge is 6HB? (0 = DX, 1 = 6HB)
- \(x_2\): number of sides (3, 4, or 6), often standardized

\(X\) is **not** the prediction. It is what we feed the model.

## What y is (the target from data)
Two different problems we trained:

1. **Linear regression:** \(y = |\text{measured angle} - \text{target angle}|\) (a number, degrees)
2. **Classification:** \(y = 1\) if that error \(< 8^\circ\) (high fidelity), else \(y = 0\)

Important: \(y\) is the **true label/value in the dataset**.  
\(h_\theta(x)\) is the **model’s prediction**. Do not mix them up.

## Linear regression prediction
\[
h_\theta(x) = \theta_0 + \theta_1 x_1 + \theta_2 x_2
\]
Predicts continuous angle error.  
Learned pattern: \(\theta_1 < 0\) means 6HB lowers predicted error.

## Logistic classification prediction
Same linear score, then sigmoid:
\[
z = \theta^T x, \qquad h_\theta(x) = \sigma(z) = \frac{1}{1+e^{-z}} = P(y=1 \mid x)
\]
Predicts **probability of high fidelity**, not “probability of error.”

## What each tool is for
| Tool | Purpose |
|------|---------|
| \(\theta\) | parameters we learn by lowering cost \(J\) |
| Cost \(J\) | how wrong the current \(\theta\) is |
| Gradient descent | update \(\theta := \theta - \alpha \nabla J\) |
| Feature scaling \((x-\mu)/\sigma\) | put features on similar numeric scales |
| Sigmoid \(\sigma(z)\) | turn score \(z\) into a probability in (0,1) |

Sigmoid is **not** feature scaling.
