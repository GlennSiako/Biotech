"""Morgan-fingerprint activity model with tree-ensemble uncertainty."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FINGERPRINT_SIZE = 2048
_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=FINGERPRINT_SIZE)


def featurize_smiles(smiles: list[str]) -> np.ndarray:
    matrix = np.zeros((len(smiles), FINGERPRINT_SIZE), dtype=np.uint8)
    for index, value in enumerate(smiles):
        mol = Chem.MolFromSmiles(value)
        if mol is None:
            raise ValueError(f"Invalid SMILES at row {index}: {value}")
        DataStructs.ConvertToNumpyArray(_GENERATOR.GetFingerprint(mol), matrix[index])
    return matrix


@dataclass
class ActivityModel:
    estimator: ExtraTreesRegressor

    def predict(self, smiles: list[str]) -> tuple[np.ndarray, np.ndarray]:
        features = featurize_smiles(smiles)
        tree_predictions = np.vstack(
            [tree.predict(features) for tree in self.estimator.estimators_]
        )
        return tree_predictions.mean(axis=0), tree_predictions.std(axis=0)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Path) -> "ActivityModel":
        loaded = joblib.load(path)
        if not isinstance(loaded, cls):
            raise TypeError(f"{path} does not contain an ActivityModel")
        return loaded


def train(
    dataset: pd.DataFrame,
    n_estimators: int = 300,
    seed: int = 42,
) -> tuple[ActivityModel, dict[str, dict[str, float]]]:
    train_rows = dataset["split"] == "train"
    if train_rows.sum() < 10:
        raise ValueError("At least 10 training molecules are required")

    estimator = ExtraTreesRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=2,
        max_features="sqrt",
        n_jobs=-1,
        random_state=seed,
    )
    estimator.fit(
        featurize_smiles(dataset.loc[train_rows, "smiles"].tolist()),
        dataset.loc[train_rows, "pchembl_value"].to_numpy(),
    )
    model = ActivityModel(estimator)

    metrics: dict[str, dict[str, float]] = {}
    for split in ("validation", "test"):
        rows = dataset["split"] == split
        if not rows.any():
            continue
        observed = dataset.loc[rows, "pchembl_value"].to_numpy()
        predicted, uncertainty = model.predict(dataset.loc[rows, "smiles"].tolist())
        metrics[split] = {
            "n": int(rows.sum()),
            "mae": float(mean_absolute_error(observed, predicted)),
            "rmse": float(mean_squared_error(observed, predicted) ** 0.5),
            "r2": float(r2_score(observed, predicted)),
            "mean_tree_std": float(uncertainty.mean()),
        }
    return model, metrics
