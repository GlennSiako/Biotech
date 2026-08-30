"""Download and prepare public PARP1 bioactivity measurements."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold

ACTIVITY_URL = "https://www.ebi.ac.uk/chembl/api/data/activity.json"
PARP1_CHEMBL_ID = "CHEMBL3105"


def _canonicalize(smiles: str | None) -> str | None:
    mol = Chem.MolFromSmiles(smiles or "")
    return Chem.MolToSmiles(mol) if mol is not None else None


def fetch_parp1_activities(max_records: int | None = None) -> pd.DataFrame:
    """Fetch human PARP1 IC50 records with a ChEMBL-normalized pChEMBL value."""
    params: dict[str, object] = {
        "target_chembl_id": PARP1_CHEMBL_ID,
        "target_organism": "Homo sapiens",
        "standard_type": "IC50",
        "standard_relation": "=",
        "pchembl_value__isnull": "false",
        "limit": min(max_records or 1000, 1000),
        "offset": 0,
    }
    records: list[dict[str, object]] = []
    while True:
        response = requests.get(
            ACTIVITY_URL,
            params=params,
            headers={"Accept": "application/json"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        records.extend(payload["activities"])
        if max_records and len(records) >= max_records:
            records = records[:max_records]
            break
        next_url = payload["page_meta"].get("next")
        if not next_url:
            break
        params["offset"] = int(params["offset"]) + int(params["limit"])

    frame = pd.DataFrame(
        {
            "molecule_chembl_id": row.get("molecule_chembl_id"),
            "smiles": row.get("canonical_smiles"),
            "pchembl_value": row.get("pchembl_value"),
            "assay_chembl_id": row.get("assay_chembl_id"),
        }
        for row in records
    )
    frame["smiles"] = frame["smiles"].map(_canonicalize)
    frame["pchembl_value"] = pd.to_numeric(frame["pchembl_value"], errors="coerce")
    frame = frame.dropna(subset=["smiles", "pchembl_value"])

    # Multiple assays often measure the same molecule. Median aggregation limits
    # the influence of individual noisy measurements.
    return (
        frame.groupby(["molecule_chembl_id", "smiles"], as_index=False)
        .agg(
            pchembl_value=("pchembl_value", "median"),
            measurement_count=("pchembl_value", "size"),
        )
        .sort_values("molecule_chembl_id")
        .reset_index(drop=True)
    )


def scaffold_for_smiles(smiles: str) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    return MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)


def scaffold_split(
    smiles: Iterable[str],
    train_fraction: float = 0.8,
    validation_fraction: float = 0.1,
    seed: int = 42,
) -> np.ndarray:
    """Assign whole Bemis–Murcko scaffold groups to train/validation/test."""
    if train_fraction <= 0 or validation_fraction < 0:
        raise ValueError("Split fractions must be non-negative with train > 0")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train and validation fractions must sum to less than 1")

    smiles_list = list(smiles)
    groups: dict[str, list[int]] = {}
    for index, value in enumerate(smiles_list):
        scaffold = scaffold_for_smiles(value) or f"acyclic-{index}"
        groups.setdefault(scaffold, []).append(index)

    rng = np.random.default_rng(seed)
    grouped_indices = list(groups.values())
    rng.shuffle(grouped_indices)
    grouped_indices.sort(key=len, reverse=True)

    labels = np.empty(len(smiles_list), dtype=object)
    targets = {
        "train": train_fraction * len(labels),
        "validation": validation_fraction * len(labels),
    }
    counts = {"train": 0, "validation": 0, "test": 0}
    for indices in grouped_indices:
        if counts["train"] < targets["train"]:
            split = "train"
        elif counts["validation"] < targets["validation"]:
            split = "validation"
        else:
            split = "test"
        labels[indices] = split
        counts[split] += len(indices)
    return labels


def save_dataset(frame: pd.DataFrame, destination: Path, seed: int = 42) -> None:
    output = frame.copy()
    output["split"] = scaffold_split(output["smiles"], seed=seed)
    destination.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(destination, index=False)
