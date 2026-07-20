# DNA Origami ML — learn by building (Bathe lab data)

Interactive path: **linear regression first principles → then classification**, using real TEM angle measurements from a Mark Bathe lab paper.

## Paper / data

- Jun, Wang, Bricker & Bathe, *Nat Commun* **10**, 5419 (2019) — METIS wireframe DNA origami  
- DOI: https://doi.org/10.1038/s41467-019-13457-y  
- Curated table: `data/bathe_metis_tem_angles.csv` (Source Data Figures 3a–c)

Each row is one **measured internal angle** from TEM for DX vs 6HB wireframe designs.

## Learning sequence (interactive)

| Step | Concept | What you run / do |
|------|---------|-------------------|
| 1 | Hypothesis \(h_\theta(x)\) + look at data | `python3 step1_look_at_data.py` |
| 2 | Cost \(J(\theta)\) (MSE) | `python3 step2_cost_function.py` |
| 3 | Gradients + gradient descent | `python3 step3_gradient_descent.py` |
| 4 | Multi-feature model (+ scaling) | `python3 step4_multi_feature.py` |
| 5 | Classification (logistic regression) | `python3 step5_classification.py` |
| 6 | (optional) You explain the full model end-to-end | |

We go **one step at a time**. Do not skip ahead.

## Important naming note

- **Linear regression** predicts a **number** (here: angle error in degrees).  
- **Classification** predicts a **label** (here: high- vs low-fidelity angle).  
Andrew Ng teaches linear regression first because the same \(\theta\), cost, and gradient ideas carry into logistic regression. We will build both.

## Quick start (Step 1 only)

```bash
cd dna-origami-ml
python3 step1_look_at_data.py
```

## Older synthetic demo (optional)

`train_folding_logistic.py` is an earlier synthetic Mg²⁺ / staple-excess logistic demo. The Bathe path above is the main track now.
