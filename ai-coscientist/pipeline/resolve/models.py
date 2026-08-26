"""Data types for target resolution.

These are the contract between stage 1 (resolve) and everything downstream.
They are deliberately plain and serialisable: every run must be replayable from
its manifest alone (PROJECT_PLAN.md section 5.2), which means no live objects
and no hidden state.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Target:
    """A resolved protein target."""

    accession: str          # UniProt accession, e.g. Q9NZQ7
    entry_name: str         # e.g. PD1L1_HUMAN
    protein_name: str       # recommended full name
    gene: str               # primary gene symbol
    organism: str
    taxon_id: int
    length: int             # residues in the canonical sequence
    sequence: str

    def summary(self) -> str:
        return (f"{self.gene} ({self.accession}) — {self.protein_name}, "
                f"{self.organism}, {self.length} aa")


@dataclass(frozen=True)
class ChainCoverage:
    """Which residues of the target a structure's chains actually cover."""

    chains: tuple[str, ...]
    start: int | None
    end: int | None

    @property
    def span(self) -> int:
        if self.start is None or self.end is None:
            return 0
        return self.end - self.start + 1


@dataclass
class StructureCandidate:
    """A PDB entry that might serve as the working structure for a target.

    `score` and `notes` are populated by the ranking step so a run can explain,
    after the fact, why a given structure was chosen over the alternatives.
    """

    pdb_id: str
    method: str                     # X-ray, EM, NMR, ...
    resolution: float | None        # angstroms; None for NMR
    coverage: ChainCoverage
    title: str | None = None
    n_polymer_entities: int | None = None   # >1 suggests a complex
    partners: tuple[str, ...] = ()          # other polymers in the entry
    score: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def is_complex(self) -> bool | None:
        """True if the entry contains a binding partner, None if not yet known."""
        if self.n_polymer_entities is None:
            return None
        return self.n_polymer_entities > 1

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["is_complex"] = self.is_complex
        return d
