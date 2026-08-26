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

The long-term goal is a **generative neural network, trained by us**, that is
good at proposing binder backbones for a given target surface. The *architecture*
of that network is deliberately left open (§4.1) — the commitment is to training
a generative model ourselves, not to any one model family. Everything else in the
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
| 3 | **Epitope selection** | Prepared structure | Hotspot residue set + surface patch | Known PPI interfaces, PISA, surface curvature/hydrophobicity analysis. **Agent-selected — needs its own benchmark, see §5.1** |
| 4 | **Backbone generation** | Target + hotspots | N binder backbones (Cα/frame coordinates) | *Ours (Phase 3)*; G0 baseline: hallucination (§4.4) |
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

### 4.1 Architecture is an open choice

The project commits to *training a generative neural network ourselves*. It does
not commit to diffusion. The architecture is chosen at G1, on evidence, from:

| Family | Generates | Trade-off |
|--------|-----------|-----------|
| **Flow matching over SE(3) frames** | Backbone geometry | Current field direction. Stabler training and far fewer sampling steps than score-based diffusion. **Default choice absent a reason otherwise.** |
| **Diffusion over frames** | Backbone geometry | Better-documented, more reference implementations to learn from; slower sampling |
| **Autoregressive / masked models** | Sequence | Simpler to train, but yields sequence rather than geometry — changes what stages 5–6 do |
| **VAE over structure** | Backbone geometry | Easiest to train; historically weaker sample quality |

Whichever is chosen, it sits behind the fixed interface in §4.2 and is judged on
the same numbers.

### 4.2 Honest assessment of "from scratch"

Training a target-conditioned generative model from scratch is the hardest thing
in this plan, and the most likely place to lose months. Two facts worth
internalizing:

1. The best-known binder design models were **not trained from scratch** — they
   were fine-tuned from large pretrained structure prediction networks. That
   pretraining is where much of the structural prior comes from.
2. Unconditional backbone generation at modest length is a genuinely tractable
   from-scratch problem on small compute. **Target-conditioned binder design is
   not the same problem** and is considerably harder.

This does not mean don't do it. It means **stage it**, and make sure the
pipeline can measure the model before the model is the thing being measured.

### 4.3 Staged path

| Stage | Goal | Success criterion |
|-------|------|-------------------|
| **G0** | Swappable generator interface + **hallucination baseline** (§4.4) | Pipeline runs end to end; produces numbers |
| **G1** | Unconditional backbone diffusion, monomers ≤100 aa, trained by us | Designability: generated backbones round-trip through inverse folding + structure prediction to low RMSD |
| **G2** | Motif / hotspot conditioning | Generated backbones present the requested motif geometry |
| **G3** | Full target-conditioned binder generation | In-silico success rate competitive with the G0 baseline on the benchmark set |

**The interface is fixed from day one:**
`generate(target_structure, hotspots, n) -> List[Backbone]`
Everything behind it is replaceable — including the model family itself (§4.1). G0 ships first so that G1–G3 have a
scoreboard to beat.

### 4.4 The G0 baseline: hallucination

G0 uses **hallucination** — optimizing a candidate sequence by backpropagating
through a structure predictor's own confidence objective — rather than an
off-the-shelf generative checkpoint.

**Why.** It is a published binder design method that **trains nothing**. No
checkpoint dependency, no GPU requirement, no third-party model whose behaviour
we do not control. It produces a real, defensible number for our own model to
beat, and it makes Phases 1–2 completely independent of the compute question.

### 4.5 Data

- Source: PDB structures; monomers for G1, complexes for G2/G3.
- **Splitting must be by structural cluster, not by chain or by date.** Sequence-
  or chain-level splits leak homologs across the split and produce inflated
  metrics. This is the single easiest way to fool ourselves.
- Hold out benchmark targets entirely — they never appear in training.

---

## 5. Agent model: semi-autonomous

**Human gate at target naming only. Autonomous from there.**

1. Human names a target. That is the whole of the human input.
2. Agent runs stages 1–7 unattended: resolves the target, prepares the
   structure, **selects the epitope**, generates, designs sequences, validates,
   and ranks.
3. Agent returns a report: ranked candidates, metrics, the epitope it chose and
   why, what it filtered and why, and what it would try next.

The agent's judgment is exercised in *orchestration* — retrying failed stages,
adjusting sampling when yield is low, deciding a run is not worth continuing —
not in inventing science. Every scientific step is a deterministic, logged tool
call.

### 5.1 Consequence: epitope selection needs its own benchmark

Epitope selection is the highest-leverage scientific judgment in the pipeline.
Choose the wrong surface patch and the entire campaign is wasted — and **nothing
downstream will report a problem**, because the designs will bind well to a site
that does not matter. Interface confidence is blind to whether the interface was
worth targeting.

Automating it therefore turns it from a step into a component that must be
validated on its own, before it is trusted:

- **Benchmark**: run the selector on held-out complexes whose true interface is
  known experimentally, and measure how often it recovers the real interface
  (residue-level precision/recall, and whether the top-ranked patch is correct).
- **Bar**: the selector must be measurably better than a naive surface-exposure
  baseline before any campaign result that depends on it is believed.
- **Fallback**: where a target has a known, experimentally characterised
  interface, prefer it over a predicted one and record which was used.
- **Reporting**: every run states the chosen epitope, the alternatives
  considered, and the confidence — so a bad campaign is diagnosable after the
  fact rather than mysterious.

This is a Phase 1 work item, not a refinement.

### 5.2 Reproducibility contract

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
| Our from-scratch model underperforms the baseline | High | Staged G0–G3; baseline always available; success defined as beating a measured number, not as "it trained" |
| Data leakage inflates metrics | High | Structural-cluster splits; benchmark targets never in training |
| Compute insufficient for G3 | Medium | G1 scoped for a single GPU; G0 needs none; Vast.ai rental scales on demand — see D-011 |
| Validation metrics don't predict real binding | Medium | Use metrics with published correlation to experimental hit rates; report as confidence, never as truth |
| **Agent selects a plausible but biologically irrelevant epitope** | **High** | Now fully automated (D-010), and downstream metrics cannot detect it. Selector benchmarked against known interfaces before use; every run reports its epitope choice and alternatives — see §5.1 |
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
2. ~~**Compute budget.**~~ **RESOLVED (D-011): hourly GPU rental on Vast.ai**
   for training runs. Phases 1–2 need essentially no GPU regardless. Requires
   checkpoints synced off-instance, since marketplace instances can be
   reclaimed.
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
