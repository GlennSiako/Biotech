from __future__ import annotations

import numpy as np
import pandas as pd

from parp1_ml.data import scaffold_for_smiles, scaffold_split
from parp1_ml.model import train


def test_scaffold_split_keeps_scaffolds_together() -> None:
    smiles = [
        "c1ccccc1",
        "Cc1ccccc1",
        "Oc1ccccc1",
        "c1ccncc1",
        "Cc1ccncc1",
        "C1CCCCC1",
        "OC1CCCCC1",
        "CCO",
        "CCN",
        "CCCC",
    ]
    assignments = scaffold_split(smiles, train_fraction=0.6, validation_fraction=0.2)
    split_by_scaffold: dict[str, set[str]] = {}
    for value, split in zip(smiles, assignments, strict=True):
        scaffold = scaffold_for_smiles(value)
        if scaffold:
            split_by_scaffold.setdefault(scaffold, set()).add(split)
    assert all(len(splits) == 1 for splits in split_by_scaffold.values())
    assert set(assignments) == {"train", "validation", "test"}


def test_model_trains_and_reports_holdout_metrics() -> None:
    smiles = [
        "CCO",
        "CCN",
        "CCC",
        "CCCC",
        "CCCO",
        "CCCN",
        "CCCl",
        "CCBr",
        "CCF",
        "CC=O",
        "c1ccccc1",
        "c1ccncc1",
        "C1CCCCC1",
        "C1CCNCC1",
    ]
    dataset = pd.DataFrame(
        {
            "smiles": smiles,
            "pchembl_value": np.linspace(4.5, 8.0, len(smiles)),
            "split": ["train"] * 10 + ["validation"] * 2 + ["test"] * 2,
        }
    )
    model, metrics = train(dataset, n_estimators=10, seed=7)
    prediction, uncertainty = model.predict(["CCO", "c1ccccc1"])

    assert prediction.shape == uncertainty.shape == (2,)
    assert np.all(uncertainty >= 0)
    assert metrics["validation"]["n"] == 2
    assert metrics["test"]["n"] == 2
