# AI Co-Scientist — De Novo Protein Binder Design

**Status:** Planning (v0.1)
**Last updated:** 2026-08-26
**Owner:** Glenn Siako
**Branch:** `claude/ml-project-home-window-fd60iw`

> This is a living document. It is expected to change as the science and the
> engineering teach us things. Material changes should be recorded in
> [`DECISIONS.md`](./DECISIONS.md) rather than silently edited in here.

---

## 1. Purpose

Build an agent-orchestrated pipeline that takes a **protein target** and returns a
**ranked set of de novo designed protein binders**, each with structural evidence
and quantitative confidence metrics.

The long-term goal is a **generative model, trained by us**, that is good at
proposing binder backbones for a given target surface. Everything else in the
system exists to (a) feed that model well-posed problems and (b) measure honestly
whether its output is any good.

### What this is not (for now)

- **Not small-molecule discovery.** Ligand generation, AutoDock Vina, and
  ADME/tox prediction are explicitly out of scope for v1. See §3.1 for why this
  is a deeper change than it sounds.
- **Not wet-lab validation.** Every metric here is in silico. "Success" means
  *passes computational filters that correlate with experimental success rates
  in published campaigns* — not "works."
- **Not fully autonomous.** See §5.

---

## 2. Scientific framing

De novo binder design asks: given a target protein surface, invent a new protein
that binds it tightly and specifically, with no natural homolog to copy.

The field's working recipe is three stages — **generate a backbone**, **design a
sequence onto it**, **predict whether it actually folds and binds** — followed by
aggressive filtering. Published campaigns report in-silico filters passing a
small single-digit percentage of designs, and of those, experimental hit rates
in the low percent range. The pipeline must therefore be built for **high
throughput and ruthless filtering**, not for producing a handful of precious
candidates.

### 2.1 Design implication

The filter stage is not a postscript. It is the part of the system that
determines whether anything works. Budget engineering effort accordingly:
roughly equal weight to generation and to validation, not 90/10.

---

## 3. Pipeline architecture

Each stage is an independent, testable unit with a typed interface. The agent
orchestrates; it does not do the science inline.

| # | Stage | Input | Output | Candidate tooling |
|---|-------|-------|--------|-------------------|
| 1 | **Target resolution** | Target name / gene symbol | UniProt accession, domain boundaries, candidate structures | UniProt REST, PDBe REST, AlphaFold DB |
| 2 | **Structure preparation** | Structure IDs | Cleaned single-chain target, numbered consistently | Biopython / PDBFixer |
| 3 | **Epitope selection** | Prepared structure | Hotspot residue set + surface patch | Known PPI interfaces, PISA, surface curvature/hydrophobicity analysis |
| 4 | **Backbone generation** | Target + hotspots | N binder backbones (Cα/frame coordinates) | *Ours (Phase 3)*; baseline: pretrained checkpoint / Boltz `protein_design` |
| 5 | **Sequence design** | Backbone | Amino acid sequence per backbone | Inverse folding (ProteinMPNN-class) |
| 6 | **Validation** | Binder sequence + target | Complex structure + interface confidence | Boltz `structure_and_binding`, `protein_screen` |
| 7 | **Ranking & report** | Validated complexes | Ranked candidates + rationale | Consensus scoring (§6) |

### 3.1 What the protein pivot changed

Moving the generator from small molecules to proteins is not a swap of one model
for another — it invalidates the downstream half of the original design:

- **AutoDock Vina is removed.** Vina scores a small ligand in a rigid pocket. It
  has no meaning for a protein–protein interface. Its role is taken by co-folding
  the designed binder together with the target and reading interface confidence.
- **"Pocket finding" becomes "epitope selection."** Binders engage *exposed,
  often flat or convex* surface patches. Deep enzymatic pockets — the classic
  small-molecule sites — are largely inaccessible to a protein binder. Pocket
  detection tools (fpocket, P2Rank) are tuned for the opposite problem and are
  the wrong instrument here.
- **Boltz moves from optional to load-bearing.** With Vina gone, the Boltz
  endpoints are the validation stage, not a rescoring add-on.
- **AlphaFold's role narrows.** Still useful for a target with no experimental
  structure, but its confidence caveats matter more at an interface than in a
  core.

---

## 4. The generative model (the actual project)

### 4.1 Honest assessment of "from scratch"

Training a target-conditioned protein backbone diffusion model from scratch is
the hardest thing in this plan, and the most likely place to lose months. Two
facts worth internalizing:

1. The best-known binder design diffusion models were **not trained from
   scratch** — they were fine-tuned from large pretrained structure prediction
   networks. That pretraining is where much of the structural prior comes from.
2. Unconditional backbone generation at modest length is a genuinely tractable
   from-scratch problem on small compute. **Target-conditioned binder design is
   not the same problem** and is considerably harder.

This does not mean don't do it. It means **stage it**, and make sure the
pipeline can measure the model before the model is the thing being measured.

### 4.2 Staged path

| Stage | Goal | Success criterion |
|-------|------|-------------------|
| **G0** | Swappable generator interface + trivial baseline | Pipeline runs end to end; produces numbers |
| **G1** | Unconditional backbone diffusion, monomers ≤100 aa, trained by us | Designability: generated backbones round-trip through inverse folding + structure prediction to low RMSD |
| **G2** | Motif / hotspot conditioning | Generated backbones present the requested motif geometry |
| **G3** | Full target-conditioned binder generation | In-silico success rate competitive with the G0 baseline on the benchmark set |

**The interface is fixed from day one:**
`generate(target_structure, hotspots, n) -> List[Backbone]`
Everything behind it is replaceable. G0 ships first so that G1–G3 have a
scoreboard to beat.

### 4.3 Data

- Source: PDB structures; monomers for G1, complexes for G2/G3.
- **Splitting must be by structural cluster, not by chain or by date.** Sequence-
  or chain-level splits leak homologs across the split and produce inflated
  metrics. This is the single easiest way to fool ourselves.
- Hold out benchmark targets entirely — they never appear in training.

---

## 5. Agent model: semi-autonomous

**Human gate at target selection. Autonomous thereafter.**

1. Human names a target and approves the resolved structure + epitope choice.
2. Agent runs stages 4–7 unattended.
3. Agent returns a report: ranked candidates, metrics, what it filtered and why,
   and what it would try next.

The agent's judgment is exercised in *orchestration* — retrying failed stages,
adjusting sampling when yield is low, deciding a run is not worth continuing —
not in inventing science. Every scientific step is a deterministic, logged tool
call.

### 5.1 Reproducibility contract

Every run writes `runs/<run_id>/` containing: input manifest, resolved
structure IDs and versions, all model checkpoints and seeds, every intermediate
artifact, and the final report. A run must be replayable from its manifest
alone. Non-negotiable — without it, no result from this system means anything.

---

## 6. Evaluation

### 6.1 Per-design metrics

- **Interface confidence** — ipTM and interface PAE from co-folding the complex.
- **Self-consistency** — does the designed sequence, re-predicted independently,
  return to the backbone we designed? (RMSD to design)
- **Interface quality** — buried surface area, shape complementarity, polar
  contact satisfaction, no unsatisfied buried charges.
- **Developability** — aggregation-prone patches, free cysteines, N-glycosylation
  motifs, extreme pI. Cheap to compute, expensive to ignore.

### 6.2 Per-campaign metrics

- **In-silico success rate** — fraction of generated designs passing all filters.
  This is the primary number the generative model is judged on.
- **Diversity** — structural clustering of passing designs. A model that emits
  one good binder a thousand times has not solved anything.
- **Novelty** — structural similarity to the nearest natural protein.

### 6.3 Benchmark set

Fixed set of targets with **published binder design campaigns**, so our numbers
are comparable to someone else's rather than to our own hopes. Held out of
training entirely. Frozen before Phase 2 begins; changing it later invalidates
comparisons and must be recorded in `DECISIONS.md`.

---

## 7. Repository layout

```
ai-coscientist/
  docs/
    PROJECT_PLAN.md       # this file
    DECISIONS.md          # decision log — append-only
  agent/                  # orchestrator, stage policies, run manifests
  pipeline/
    resolve/              # stage 1: target -> UniProt/PDB/AFDB
    structure/            # stage 2: fetch, clean, prepare
    epitope/              # stage 3: hotspot + surface patch selection
    generate/             # stage 4: backbone generation (swappable)
    sequence/             # stage 5: inverse folding
    validate/             # stage 6: co-folding + interface metrics
    rank/                 # stage 7: consensus scoring + filters
  models/                 # our diffusion model: training, data, checkpoints
  eval/                   # benchmark targets, metrics, campaign reports
  runs/                   # per-run artifacts (gitignored except manifests)
```

---

## 8. Phases

### Phase 1 — Skeleton (no ML of our own)
End-to-end run on one approved target, using off-the-shelf components at every
stage including generation. Deliverable: a run directory with a ranked candidate
list and real numbers. **Purpose: establish the scoreboard.**

### Phase 2 — Measurement
Benchmark set frozen. Consensus ranking and filter stack built and calibrated.
Deliverable: baseline in-silico success rate per benchmark target. **Nothing we
build afterward is trusted without a delta against this.**

### Phase 3 — Our generative model
G1 → G2 → G3 per §4.2, each swapped in behind the fixed interface and measured
against the Phase 2 baseline.

### Phase 4 — Agent autonomy
Tighten the semi-autonomous loop: retry policies, sampling adaptation, report
quality, cost control.

**Phases 1 and 2 are prerequisites for Phase 3, not parallel tracks.** Building
the generator before the scoreboard exists means training blind.

---

## 9. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| From-scratch conditioned diffusion underperforms baseline | High | Staged G0–G3; baseline always available; success defined as beating a measured number, not as "it trained" |
| Data leakage inflates metrics | High | Structural-cluster splits; benchmark targets never in training |
| Compute insufficient for G3 | High | **Open — see §10.** G1 scoped to be feasible on modest compute |
| Validation metrics don't predict real binding | Medium | Use metrics with published correlation to experimental hit rates; report as confidence, never as truth |
| Epitope selection is the real bottleneck | Medium | Treat as a first-class stage with its own evaluation, not a preprocessing detail |
| Chosen target has no bindable surface epitope | Medium | Target triage before committing a campaign; resolved for Phase 1 by D-007 |

---

## 10. Open decisions

1. ~~**First target.**~~ **RESOLVED (D-007): PD-L1**, targeting the PD-1
   binding face. Chosen as an established benchmark target with published binder
   campaigns, a flat and genuinely bindable PPI epitope, abundant experimental
   structure, and a known-binder positive control (PD-1 ectodomain) for
   calibrating interface metrics in Phase 2. PARP1 becomes campaign two,
   retargeted onto a protein interaction surface rather than its catalytic
   pocket.
2. **Compute budget.** GPU access determines whether G3 is reachable and how
   large the training set can be. Needs an answer before Phase 3 is scoped.
3. **Binder class.** Unconstrained mini-binders (50–120 aa) versus a fixed
   scaffold class. Unconstrained is more general; scaffolded is far easier to
   validate and express.
4. **Benchmark set composition.** To be frozen at the start of Phase 2.

---

## 11. Connection to existing work

The `drug-studies/iniparib` analysis in this repo is a useful adversarial test
case. Iniparib reached Phase III as a purported PARP1 inhibitor and failed
because **it does not engage PARP1 in cells** — a target engagement failure that
every affinity-focused metric in a pipeline like this would miss. It is a
standing reminder that a high interface confidence score is a statement about
geometry, not about biology.
