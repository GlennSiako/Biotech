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


# Below this length a polymer entity is a peptide ligand, not a protein partner.
# PD-1's ectodomain is ~110 residues and designed mini-binders start around 50;
# macrocyclic peptide inhibitors are ~10-20.
MIN_PROTEIN_LENGTH = 40


@dataclass(frozen=True)
class Partner:
    """A polymer entity in a structure that is not the target itself.

    What kind of partner it is decides whether the structure shows an interface
    worth designing against. A co-crystallised macrocycle marks a druggable spot
    but says nothing about where a *protein* binder should bind.
    """

    description: str
    uniprot: str | None = None
    length: int | None = None
    polymer_type: str | None = None

    @property
    def kind(self) -> str:
        if self.polymer_type and "polypeptide" not in self.polymer_type.lower():
            return "nucleic acid"
        if self.length is not None and self.length < MIN_PROTEIN_LENGTH:
            return "peptide ligand"
        if self.uniprot:
            return "natural protein"
        return "engineered protein"

    @property
    def is_protein(self) -> bool:
        return self.kind in ("natural protein", "engineered protein")


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
    n_polymer_entities: int | None = None   # >1 means more than one polymer
    partners: tuple[Partner, ...] = ()      # polymer entities other than the target
    enriched: bool = False                  # RCSB detail actually retrieved
    score: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def protein_partners(self) -> tuple[Partner, ...]:
        """Partners that are actual proteins, not ligands or nucleic acids."""
        return tuple(p for p in self.partners if p.is_protein)

    @property
    def has_protein_partner(self) -> bool | None:
        """True if a genuine protein partner is present, None if not yet known.

        Deliberately not "more than one polymer entity". A macrocyclic peptide
        inhibitor is a polymer entity and counted as one by RCSB, but the
        interface it reveals is a drug-binding site, not a protein-protein
        epitope. Ranking on entity count alone selected exactly those structures.
        """
        if not self.enriched:
            return None
        return bool(self.protein_partners)

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["has_protein_partner"] = self.has_protein_partner
        d["partner_kinds"] = [p.kind for p in self.partners]
        return d
