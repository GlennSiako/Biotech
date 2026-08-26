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

from .models import StructureCandidate

# Experimental method. NMR scores zero rather than negative: usable if nothing
# else exists, but ensemble models give poor interface geometry.
METHOD_SCORES = {"X-ray": 3.0, "EM": 2.5, "Neutron": 2.0, "NMR": 0.0, "Model": -5.0}

RESOLUTION_BANDS = ((2.0, 3.0), (2.5, 2.5), (3.0, 2.0), (3.5, 1.0))
COVERAGE_WEIGHT = 3.0
COMPLEX_BONUS = 4.0

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


def score_candidate(candidate: StructureCandidate,
                    region: tuple[int, int] | None = None) -> StructureCandidate:
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

    if candidate.is_complex:
        score += COMPLEX_BONUS
        notes.append(f"co-complex, {candidate.n_polymer_entities} polymer "
                     f"entities ({COMPLEX_BONUS:+.1f}) — observed interface available")
    elif candidate.is_complex is False:
        notes.append("single polymer entity (+0.0) — epitope must be predicted")
    else:
        notes.append("complex status unknown (+0.0) — not enriched from RCSB")

    candidate.score = round(score, 2)
    candidate.notes = notes
    return candidate


def rank(candidates: list[StructureCandidate],
         region: tuple[int, int] | None = None) -> list[StructureCandidate]:
    """Score and sort candidates, best first.

    Ties break on resolution, then PDB ID, so the ordering is deterministic —
    a run must be replayable from its manifest (PROJECT_PLAN.md section 5.2).
    """
    scored = [score_candidate(c, region) for c in candidates]
    return sorted(
        scored,
        key=lambda c: (-c.score, c.resolution if c.resolution is not None else 99.0, c.pdb_id),
    )
