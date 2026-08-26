"""Stage 1b: rank candidate structures for suitability as a working structure.

The weights below are explicit and the reasoning is recorded per candidate,
because an agent choosing a structure unattended (D-010) must be able to explain
the choice afterwards. A silent ranking is not auditable, and a campaign built
on the wrong structure fails in ways nothing downstream reports.

The heaviest weight is on co-complexes. A structure solved with a binding
partner shows a real, experimentally observed interface, which is exactly what
epitope selection needs; without one the epitope must be predicted, and D-010
requires us to prefer known interfaces over predicted ones wherever they exist.
"""

from __future__ import annotations

from .models import Partner, StructureCandidate

# Experimental method. NMR scores zero rather than negative: usable if nothing
# else exists, but ensemble models give poor interface geometry.
METHOD_SCORES = {"X-ray": 3.0, "EM": 2.5, "Neutron": 2.0, "NMR": 0.0, "Model": -5.0}

RESOLUTION_BANDS = ((2.0, 3.0), (2.5, 2.5), (3.0, 2.0), (3.5, 1.0))
COVERAGE_WEIGHT = 3.0

# What kind of partner is present matters more than whether one is present.
# Ranking on entity count alone put PD-L1/macrocycle and PD-L1/small-molecule
# structures at the top of the list for a protein binder campaign: those are
# drug-binding sites, and several PD-L1 inhibitors work by inducing the protein
# to homodimerise, so the observed interface is the target against itself.
PARTNER_BONUS = {
    "natural protein": 4.0,     # a real biological partner -- the interface we want
    "engineered protein": 3.0,  # nanobody or designed binder; still protein-protein
    "peptide ligand": 1.0,      # marks a druggable hotspot, not a protein epitope
    "homodimer": 0.5,           # self-association, often inhibitor-induced
    "nucleic acid": 0.0,
}

# Below this resolution, side-chain positions at an interface are unreliable.
RESOLUTION_WARN = 3.0


def _method_score(method: str) -> float:
    for key, value in METHOD_SCORES.items():
        if key.lower() in method.lower():
            return value
    return 1.0


def _resolution_score(resolution: float | None) -> float:
    if resolution is None:
        return 0.0
    for limit, score in RESOLUTION_BANDS:
        if resolution <= limit:
            return score
    return 0.0


def _coverage_fraction(candidate: StructureCandidate,
                       region: tuple[int, int] | None) -> float:
    """Fraction of the region of interest the structure's chains cover."""
    cov = candidate.coverage
    if cov.start is None or cov.end is None:
        return 0.0
    if region is None:
        return 1.0
    lo, hi = region
    overlap = min(cov.end, hi) - max(cov.start, lo) + 1
    return max(0.0, overlap) / (hi - lo + 1)


def _classify(partner: Partner, target_accession: str | None) -> str:
    if target_accession and partner.uniprot == target_accession:
        return "homodimer"
    return partner.kind


def score_candidate(candidate: StructureCandidate,
                    region: tuple[int, int] | None = None,
                    target_accession: str | None = None) -> StructureCandidate:
    """Score one candidate in place, recording the reasoning in `notes`."""
    notes: list[str] = []
    score = 0.0

    method = _method_score(candidate.method)
    score += method
    notes.append(f"method {candidate.method} ({method:+.1f})")

    res = _resolution_score(candidate.resolution)
    score += res
    if candidate.resolution is None:
        notes.append("no resolution reported (+0.0)")
    else:
        notes.append(f"resolution {candidate.resolution:.2f} A ({res:+.1f})")
        if candidate.resolution > RESOLUTION_WARN:
            notes.append(f"WARNING: above {RESOLUTION_WARN} A — interface "
                         "side chains unreliable")

    fraction = _coverage_fraction(candidate, region)
    cov_score = fraction * COVERAGE_WEIGHT
    score += cov_score
    if region is None:
        notes.append(f"covers {candidate.coverage.span} residues ({cov_score:+.1f})")
    else:
        notes.append(f"covers {fraction:.0%} of region {region[0]}-{region[1]} "
                     f"({cov_score:+.1f})")
        if fraction < 1.0:
            notes.append("WARNING: does not fully cover the region of interest")

    if not candidate.enriched:
        notes.append("partners unknown (+0.0) — not enriched from RCSB")
    elif not candidate.partners:
        notes.append("no binding partner (+0.0) — epitope must be predicted")
    else:
        kinds = [(p, _classify(p, target_accession)) for p in candidate.partners]
        best_kind = max(kinds, key=lambda pk: PARTNER_BONUS.get(pk[1], 0.0))
        bonus = PARTNER_BONUS.get(best_kind[1], 0.0)
        score += bonus
        for partner, kind in kinds:
            length = f", {partner.length} aa" if partner.length else ""
            notes.append(f"partner: {partner.description[:60]} [{kind}{length}]")
        if best_kind[1] in ("natural protein", "engineered protein"):
            notes.append(f"protein-protein interface observed ({bonus:+.1f})")
        elif best_kind[1] == "peptide ligand":
            notes.append(f"only peptide/ligand partners ({bonus:+.1f}) — this is a "
                         "drug-binding site, not a protein-protein epitope")
        elif best_kind[1] == "homodimer":
            notes.append(f"self-association only ({bonus:+.1f}) — often "
                         "inhibitor-induced, not a partner interface")
        else:
            notes.append(f"no protein partner ({bonus:+.1f})")

    candidate.score = round(score, 2)
    candidate.notes = notes
    return candidate


def rank(candidates: list[StructureCandidate],
         region: tuple[int, int] | None = None,
         target_accession: str | None = None) -> list[StructureCandidate]:
    """Score and sort candidates, best first.

    Ties break on resolution, then PDB ID, so the ordering is deterministic —
    a run must be replayable from its manifest (PROJECT_PLAN.md section 5.2).
    """
    scored = [score_candidate(c, region, target_accession) for c in candidates]
    return sorted(
        scored,
        key=lambda c: (-c.score, c.resolution if c.resolution is not None else 99.0, c.pdb_id),
    )
