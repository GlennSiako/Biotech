"""Stage 2b: prepare a working structure from a raw PDB/mmCIF file.

Real entries are messier than the pipeline diagram suggests, and each mess has a
downstream consequence:

- **Multiple models** (NMR, some cryo-EM). Only one can be the working
  structure; the rest are alternative interpretations of the same data.
- **Alternate conformations.** A residue at an interface may have two modelled
  side-chain positions. Picking silently changes interface geometry.
- **Missing residues.** Disordered loops are absent from the coordinates
  entirely. A gap *inside* the region of interest is a genuine problem: an
  epitope selector reading only coordinates cannot see a residue that was never
  modelled, and will report a confident surface that has a hole in it.
- **Heteroatoms.** Waters, buffer components, and crystallisation additives sit
  in the file alongside real ligands and modified residues.

This module resolves each of those explicitly and reports what it did, rather
than quietly producing a clean-looking file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from Bio.PDB import MMCIFParser, PDBIO, PDBParser, Select
from Bio.PDB.Polypeptide import is_aa

log = logging.getLogger(__name__)


@dataclass
class PreparationReport:
    """What preparation found and did. Written into the run manifest."""

    pdb_id: str
    chain: str
    n_models: int
    model_used: int
    n_residues: int
    first_residue: int | None
    last_residue: int | None
    gaps: list[tuple[int, int]] = field(default_factory=list)
    n_altloc_residues: int = 0
    n_waters_removed: int = 0
    n_hetero_removed: int = 0
    nonstandard_residues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_internal_gaps(self) -> bool:
        return bool(self.gaps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pdb_id": self.pdb_id,
            "chain": self.chain,
            "n_models": self.n_models,
            "model_used": self.model_used,
            "n_residues": self.n_residues,
            "residue_range": [self.first_residue, self.last_residue],
            "gaps": [list(g) for g in self.gaps],
            "n_altloc_residues": self.n_altloc_residues,
            "n_waters_removed": self.n_waters_removed,
            "n_hetero_removed": self.n_hetero_removed,
            "nonstandard_residues": self.nonstandard_residues,
            "warnings": self.warnings,
        }

    def describe(self) -> str:
        lines = [
            f"{self.pdb_id} chain {self.chain}: {self.n_residues} residues "
            f"({self.first_residue}-{self.last_residue})"
        ]
        if self.n_models > 1:
            lines.append(f"  {self.n_models} models present; used model {self.model_used}")
        if self.gaps:
            spans = ", ".join(f"{a}-{b}" for a, b in self.gaps)
            lines.append(f"  {len(self.gaps)} chain break(s): {spans}")
        if self.n_altloc_residues:
            lines.append(f"  {self.n_altloc_residues} residues with alternate "
                         "conformations (highest occupancy kept)")
        if self.n_waters_removed or self.n_hetero_removed:
            lines.append(f"  removed {self.n_waters_removed} waters, "
                         f"{self.n_hetero_removed} heteroatom groups")
        for warning in self.warnings:
            lines.append(f"  WARNING: {warning}")
        return "\n".join(lines)


class _CleanSelect(Select):
    """Keep only amino acid residues of one chain, dropping waters and hetero."""

    def __init__(self, chain_id: str, keep_hetero: bool):
        self.chain_id = chain_id
        self.keep_hetero = keep_hetero

    def accept_model(self, model):
        return model.id == 0

    def accept_chain(self, chain):
        return chain.id == self.chain_id

    def accept_residue(self, residue):
        hetflag, _, _ = residue.id
        if hetflag == "W":
            return False
        if hetflag != " " and not self.keep_hetero:
            return False
        return True

    def accept_atom(self, atom):
        # Biopython marks the highest-occupancy conformer as the default child
        # of a disordered atom; accepting only that resolves altlocs.
        return (not atom.is_disordered()) or atom.get_altloc() in (" ", "A")


def _parser_for(path: Path):
    if path.suffix.lower() in (".cif", ".mmcif"):
        return MMCIFParser(QUIET=True)
    return PDBParser(QUIET=True)


def prepare(
    path: Path,
    chain_id: str,
    *,
    pdb_id: str | None = None,
    region: tuple[int, int] | None = None,
    out_path: Path | None = None,
    keep_hetero: bool = False,
    model_index: int = 0,
) -> tuple[Path | None, PreparationReport]:
    """Prepare a single chain as the working structure.

    Returns the written file (None if `out_path` is not given) and a report.
    A gap falling inside `region` is raised as a warning, not an exception:
    stage 1 may have no better structure available, and the decision to proceed
    belongs to the caller with the report in hand.
    """
    pdb_id = (pdb_id or path.stem).upper()
    structure = _parser_for(path).get_structure(pdb_id, str(path))

    models = list(structure)
    if not models:
        raise ValueError(f"{pdb_id}: no models in {path}")
    model = models[model_index]

    if chain_id not in {c.id for c in model}:
        available = ", ".join(sorted(c.id for c in model))
        raise ValueError(f"{pdb_id}: chain {chain_id!r} not found (available: {available})")
    chain = model[chain_id]

    residues: list[Any] = []
    waters = hetero = altlocs = 0
    nonstandard: list[str] = []

    for residue in chain:
        hetflag, seqid, _ = residue.id
        if hetflag == "W":
            waters += 1
            continue
        if hetflag != " ":
            hetero += 1
            if not keep_hetero:
                continue
        if not is_aa(residue, standard=True):
            name = residue.get_resname()
            if name not in nonstandard:
                nonstandard.append(name)
        if any(atom.is_disordered() for atom in residue):
            altlocs += 1
        residues.append(residue)

    numbers = [r.id[1] for r in residues]
    first, last = (min(numbers), max(numbers)) if numbers else (None, None)

    gaps: list[tuple[int, int]] = []
    for prev, curr in zip(numbers, numbers[1:]):
        if curr - prev > 1:
            gaps.append((prev + 1, curr - 1))

    report = PreparationReport(
        pdb_id=pdb_id,
        chain=chain_id,
        n_models=len(models),
        model_used=model_index,
        n_residues=len(residues),
        first_residue=first,
        last_residue=last,
        gaps=gaps,
        n_altloc_residues=altlocs,
        n_waters_removed=waters,
        n_hetero_removed=0 if keep_hetero else hetero,
        nonstandard_residues=nonstandard,
    )

    if len(models) > 1:
        report.warnings.append(
            f"{len(models)} models present (NMR ensemble or multi-state); "
            f"model {model_index} used and the rest discarded"
        )
    if not residues:
        report.warnings.append("no amino acid residues retained — wrong chain?")

    if region is not None:
        lo, hi = region
        if first is None or first > lo or last is None or last < hi:
            report.warnings.append(
                f"chain covers {first}-{last}, short of the requested region {lo}-{hi}"
            )
        internal = [(a, b) for a, b in gaps if b >= lo and a <= hi]
        if internal:
            spans = ", ".join(f"{a}-{b}" for a, b in internal)
            report.warnings.append(
                f"unmodelled residues inside the region of interest ({spans}) — "
                "epitope selection cannot see these, and a surface computed here "
                "will have a hole in it"
            )

    written: Path | None = None
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        io = PDBIO()
        io.set_structure(structure)
        io.save(str(out_path), _CleanSelect(chain_id, keep_hetero))
        written = out_path
        log.info("wrote prepared structure %s", out_path)

    return written, report
