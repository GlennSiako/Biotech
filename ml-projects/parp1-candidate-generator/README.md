# PARP1 Candidate Generator

An educational, CPU-friendly molecular ML project connected to the repository's
iniparib/PARP1 case study. It downloads public PARP1 measurements, trains an
activity model, recombines fragments from known active molecules, and ranks new
structures.

This is a learning and hypothesis-generation pipeline—not a drug-discovery
result. Predictions require docking, selectivity analysis, synthesis review, and
experimental validation before they can support scientific claims.

## Why this baseline comes before diffusion

A diffusion model needs substantial training data and GPU compute. More
importantly, generation is not useful without a trustworthy scoring and
evaluation pipeline. This project establishes that pipeline with:

- ChEMBL human PARP1 IC50 measurements
- median aggregation of repeated molecule measurements
- Bemis–Murcko scaffold splits to reduce train/test structural leakage
- Morgan fingerprints and an Extra Trees regression model
- tree-ensemble disagreement as a simple uncertainty warning
- BRICS fragment recombination for transparent candidate generation
- PAINS and Rule-of-Five-style property filters
- novelty, QED, and uncertainty-aware candidate ranking

Once this baseline works, its generator can be replaced by a pretrained
conditional graph or SMILES model without changing the evaluation workflow.

## Setup

Python 3.10+ is required. No GPU is needed.

```bash
cd ml-projects/parp1-candidate-generator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the pipeline

```bash
python scripts/download_data.py
python scripts/train_model.py
python scripts/generate_candidates.py
```

For a quick smoke run:

```bash
python scripts/download_data.py --max-records 300
python scripts/train_model.py --trees 50
python scripts/generate_candidates.py --pool-size 100 --top-n 10
```

Outputs are written under `artifacts/`:

- `parp1_activity_model.joblib`: fitted model
- `metrics.json`: scaffold-holdout regression metrics
- `ranked_candidates.csv`: proposed structures and ranking components

Higher `pchembl_value` means stronger measured potency: approximately
`pChEMBL = -log10(molar IC50)`. The generated `predicted_pchembl` values are
model estimates, not measurements.

## Interpreting results

Pay attention to test MAE/RMSE and `tree_std`, not just the highest predicted
potency. Generated compounds far from the training set are extrapolations.
BRICS products can also be chemically impractical even after basic filters.
The next scientifically useful steps are:

1. inspect assay consistency and activity cliffs;
2. compare against a dummy and nearest-neighbor baseline;
3. add protein-family selectivity data;
4. dock a small, diverse shortlist;
5. have a medicinal chemist assess synthesis and liabilities.

## Tests

```bash
pytest
```
