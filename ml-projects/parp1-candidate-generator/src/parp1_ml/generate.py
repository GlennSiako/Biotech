"""Generate BRICS molecules and prioritize them with the PARP1 model."""

from __future__ import annotations

import random

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import BRICS, Crippen, Descriptors, Lipinski, QED, rdFingerprintGenerator
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams

from parp1_ml.model import ActivityModel

_SIMILARITY_GENERATOR = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def _passes_property_filters(mol: Chem.Mol, pains: FilterCatalog) -> bool:
    return (
        150 <= Descriptors.MolWt(mol) <= 550
        and Crippen.MolLogP(mol) <= 5
        and Lipinski.NumHDonors(mol) <= 5
        and Lipinski.NumHAcceptors(mol) <= 10
        and Lipinski.NumRotatableBonds(mol) <= 10
        and pains.GetFirstMatch(mol) is None
    )


def _pains_catalog() -> FilterCatalog:
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
    return FilterCatalog(params)


def generate_and_rank(
    known_data: pd.DataFrame,
    model: ActivityModel,
    max_candidates: int = 1000,
    top_n: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """Recombine fragments from potent molecules and rank novel valid products."""
    if max_candidates < top_n:
        raise ValueError("max_candidates must be greater than or equal to top_n")

    random.seed(seed)
    activity_cutoff = known_data["pchembl_value"].quantile(0.75)
    active_mols = [
        Chem.MolFromSmiles(value)
        for value in known_data.loc[
            known_data["pchembl_value"] >= activity_cutoff, "smiles"
        ]
    ]
    active_mols = [mol for mol in active_mols if mol is not None]
    fragments = {
        fragment
        for mol in active_mols
        for fragment in BRICS.BRICSDecompose(mol, minFragmentSize=3)
    }
    if len(fragments) < 2:
        raise ValueError("The active set did not produce enough BRICS fragments")

    known_smiles = set(known_data["smiles"])
    known_fingerprints = [
        _SIMILARITY_GENERATOR.GetFingerprint(Chem.MolFromSmiles(value))
        for value in known_smiles
    ]
    pains = _pains_catalog()
    accepted: dict[str, Chem.Mol] = {}
    products = BRICS.BRICSBuild(
        [Chem.MolFromSmiles(fragment) for fragment in sorted(fragments)],
        maxDepth=3,
        scrambleReagents=True,
    )
    for mol in products:
        try:
            Chem.SanitizeMol(mol)
        except (ValueError, Chem.rdchem.KekulizeException):
            continue
        smiles = Chem.MolToSmiles(mol)
        if smiles in known_smiles or smiles in accepted:
            continue
        if _passes_property_filters(mol, pains):
            accepted[smiles] = mol
        if len(accepted) >= max_candidates:
            break
    if not accepted:
        raise RuntimeError("No candidates passed the chemistry filters")

    smiles = list(accepted)
    predicted, uncertainty = model.predict(smiles)
    rows: list[dict[str, float | str]] = []
    for index, value in enumerate(smiles):
        mol = accepted[value]
        fingerprint = _SIMILARITY_GENERATOR.GetFingerprint(mol)
        max_similarity = max(
            DataStructs.BulkTanimotoSimilarity(fingerprint, known_fingerprints)
        )
        novelty = 1 - max_similarity
        qed = QED.qed(mol)
        # Penalize uncertain extrapolation. The score is for prioritization only;
        # it is not a calibrated probability of experimental activity.
        priority = predicted[index] - 0.5 * uncertainty[index] + 0.4 * qed + 0.2 * novelty
        rows.append(
            {
                "smiles": value,
                "predicted_pchembl": predicted[index],
                "tree_std": uncertainty[index],
                "qed": qed,
                "novelty": novelty,
                "max_training_similarity": max_similarity,
                "molecular_weight": Descriptors.MolWt(mol),
                "clogp": Crippen.MolLogP(mol),
                "priority_score": priority,
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("priority_score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
