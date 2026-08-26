# Decision Log

Append-only record of decisions that shape the project. Newest last.
Each entry: what was decided, why, what it rules out, and how we would know it
was wrong.

Superseding a decision means **adding a new entry that references the old one**,
not editing history.

---

## D-001 — Generate proteins, not small molecules (2026-08-26)

**Decision.** The generative model designs protein binders. Small-molecule
generation, docking, and ADME are out of scope for v1.

**Why.** The stated long-term goal is a model that is good at generating
proteins for a given target. Splitting effort across two modalities would mean
doing neither well.

**Rules out.** AutoDock Vina and small-molecule docking generally — they cannot
score a protein–protein interface. Pocket-detection tools (fpocket, P2Rank) are
tuned for small-molecule cavities and are the wrong instrument for epitope
selection.

**Revisit if.** The pipeline matures and a small-molecule lane becomes cheap to
add behind the same stage interfaces.

---

## D-002 — Boltz endpoints are the validation stage (2026-08-26)

**Decision.** Co-folding the designed binder with the target via the Boltz
`structure_and_binding` / `protein_screen` endpoints is the primary validation
step, supplying interface confidence metrics for ranking.

**Why.** With small-molecule docking removed by D-001, interface confidence from
co-folding is the available signal that correlates with binder success. The
endpoints are already wired into this environment.

**Rules out.** Treating Boltz as an optional rescoring add-on — it is now on the
critical path, and pipeline design must account for its latency, cost, and
failure modes.

**Wrong if.** Interface confidence turns out not to discriminate our designs
(e.g. everything scores high). Mitigation: calibrate against known binder /
non-binder pairs during Phase 2 before trusting it as a ranker.

---

## D-003 — Semi-autonomous agent, gate at target selection (2026-08-26)

**Decision.** A human names the target and approves the resolved structure and
epitope. The agent then runs generation through ranking unattended and reports
results with numbers.

**Why.** Target and epitope choice is where scientific judgment matters most and
where a wrong call wastes an entire campaign. Everything downstream is
mechanical and benefits from running unattended at volume.

**Rules out.** Fully autonomous target selection in v1.

**Revisit if.** Target triage proves reliably automatable after several
campaigns.

---

## D-004 — Fixed generator interface; staged path to our own model (2026-08-26)

**Decision.** `generate(target_structure, hotspots, n) -> List[Backbone]` is
fixed from day one. An off-the-shelf baseline ships first (G0). Our own model
arrives in stages G1 → G2 → G3 and must beat the measured baseline to be
adopted.

**Why.** Training a target-conditioned backbone diffusion model from scratch is
the highest-risk item in the plan. Without a baseline and a scoreboard in place
first, we cannot tell an improvement from a plateau.

**Rules out.** Starting Phase 3 before Phases 1 and 2 are complete.

**Wrong if.** The baseline proves so weak that beating it is uninformative. Then
the benchmark set, not the baseline, becomes the reference.

---

## D-005 — Structural-cluster data splits (2026-08-26)

**Decision.** Training/validation/test splits for our generative model are made
by structural cluster. Benchmark targets are excluded from training entirely.

**Why.** Sequence-level or random splits leak structural homologs across the
split and inflate every metric we would use to judge the model.

**Rules out.** Random or date-based splits, and any post-hoc addition of
benchmark targets to training data.

**Wrong if.** Nothing — this is a correctness requirement, not a trade-off. If
clustering proves expensive, the answer is a cheaper clustering method, not a
weaker split.

---

## D-006 — First target: open (2026-08-26)

**Status.** UNRESOLVED — blocks the start of Phase 1.

PARP1 was proposed. It has real continuity with the existing
`drug-studies/iniparib` analysis in this repo, but its druggable site is the
deep NAD+ catalytic pocket — a small-molecule site that a protein binder cannot
engage. PARP1 is viable as a binder target only by retargeting one of its
protein interaction surfaces instead.

**Recommendation.** Run Phase 1 against a target with a published binder design
campaign, so the pipeline's first numbers are comparable to someone else's.
Keep PARP1 as campaign two, once the pipeline is calibrated and the iniparib
question can be asked properly.

**Decide before.** Phase 1 begins.

---

## D-007 — First target is a benchmark target; PD-L1 selected (2026-08-26)

**Supersedes the open question in D-006.**

**Decision.** Phase 1 runs against an established benchmark target rather than
PARP1. Selected: **PD-L1** (CD274), targeting the PD-1 binding face.

**Why PD-L1.**
- **Published binder campaigns exist**, so our first in-silico success rate is
  comparable against someone else's numbers rather than only against itself.
- **The epitope is the right shape** — the PD-1 binding face is a flat,
  solvent-exposed PPI surface, which is what a protein binder can actually
  engage. It does not have the deep-pocket problem that disqualified PARP1.
- **Abundant experimental structure**, including complexes with known binding
  partners. No dependence on a predicted model for the first run.
- **A built-in positive control**: the PD-1 ectodomain is a known binder of this
  exact surface. It gives Phase 2 a true positive for calibrating interface
  confidence metrics, and its non-binding variants give negatives. Without a
  known-answer pair, we cannot tell whether our ranking metric discriminates
  anything.

**Rules out.** PARP1 as campaign one. PARP1 remains the intended second
campaign, retargeted onto a protein interaction surface rather than the
catalytic pocket, once the pipeline is calibrated.

**Wrong if.** PD-L1 proves saturated to the point that our results are
uninformative, or the published comparison numbers turn out not to be
reproducible under our filter stack. Alternates in the same class, in order of
preference: IL-7Rα, TrkA, influenza hemagglutinin stem.

**Note.** The benchmark *set* (§6.3 of the plan) is still to be frozen at the
start of Phase 2. This decision fixes only the Phase 1 target.

---

## D-008 — Generator architecture is open; diffusion is not a requirement (2026-08-26)

**Amends D-004.**

**Decision.** The project commits to training a generative neural network
ourselves. It does **not** commit to diffusion. The architecture is selected at
G1, on evidence, from flow matching over SE(3) frames, frame diffusion,
autoregressive/masked sequence models, or a structural VAE.

**Current lean.** Flow matching over SE(3) frames — stabler training and
substantially fewer sampling steps than score-based diffusion, and where the
field has been heading. Not binding.

**Why.** "Diffusion" was shorthand for "generative model" in the original
framing. Fixing the architecture this early would be choosing on fashion rather
than on evidence, and the interface in D-004 already makes the choice
replaceable.

**Rules out.** Nothing yet — that is the point. The one constraint retained: the
model must satisfy `generate(target_structure, hotspots, n) -> List[Backbone]`,
so an architecture generating sequence rather than geometry (autoregressive /
masked) changes the contract of stages 5–6 and must be adopted knowingly.

**Decide by.** Start of G1.

---

## D-009 — Compute deferred; hallucination baseline removes the dependency (2026-08-26)

**Decision.** The compute question is deliberately deferred. Phases 1 and 2 run
with essentially no GPU: they are API calls (Boltz co-folding) and CPU work.
G0's baseline is **hallucination** — optimizing a sequence through a structure
predictor's confidence objective — which trains nothing and therefore needs no
training hardware.

**Why.** This decouples the entire scoreboard-building effort from a hardware
answer we do not have yet. Work starts now; compute is decided with better
information, before G1.

**Compute path when G1 arrives**, in order of preference:
1. **Local machine** — best option if it has ≥16GB VRAM. Persistent disk, no
   timeouts, nothing to babysit. *Spec pending.*
2. **Hourly GPU rental** (RunPod / Vast.ai / Lambda) — recommended for real
   training runs if local is short. Persistent storage, no session death, pay
   only while training. Roughly $0.30–0.50/hr consumer cards, $1–2/hr A100.
3. **Colab Pro** — acceptable for prototyping only. Session timeouts kill long
   runs; viable only if checkpoint/resume is built in from the first commit of
   the training code.
4. **Colab free** — debugging only, not training.

**Regardless of choice.** Training code is written checkpoint-resumable from
step one. This is cheap to do upfront, and it is what makes options 2 and 3
survivable at all.

**Sizing.** G1 as scoped — unconditional backbones ≤100 residues — is a
single-GPU job measured in days, not a cluster job.

**Blocked on.** `nvidia-smi` output from the local machine.

---

## D-010 — Epitope selection is automated; human gate is target naming only (2026-08-26)

**Supersedes D-003.**

**Decision.** The agent performs structure cleanup *and* epitope selection. The
only human input to a campaign is naming the target. Stages 1–7 run unattended.

**Why.** Keeps the loop genuinely autonomous and lets campaigns run at volume
without a human in the path.

**Consequence — this is not a free change.** Epitope selection is the
highest-leverage scientific judgment in the pipeline, and it fails *silently*: a
plausible-but-irrelevant surface patch produces designs that score well on every
downstream metric, because interface confidence measures whether a binder binds,
never whether the site was worth binding. Automating it converts it from a step
into a component that must be validated independently:

- Benchmarked on held-out complexes with experimentally known interfaces,
  measured on recovery of the true interface.
- Must beat a naive surface-exposure baseline before campaign results depending
  on it are believed.
- Known experimental interfaces preferred over predicted ones where available,
  with which was used recorded.
- Every run reports the chosen epitope, the alternatives, and the confidence.

**Rules out.** Treating epitope selection as preprocessing. It is now a Phase 1
deliverable with its own benchmark.

**Wrong if.** The selector cannot beat the naive baseline. Then the human gate
returns for epitope choice until it can.

---

## D-011 — Compute: hourly GPU rental on Vast.ai (2026-08-26)

**Resolves the open question in D-009.**

**Decision.** Training runs use hourly GPU rental on Vast.ai. Phases 1 and 2
still require essentially no GPU, so this affects G1 onward only.

**Why.** Pay only while training, no session timeouts, and consumer-card pricing
well below managed cloud. Scales to a larger card for G3 without a hardware
purchase.

**Caveat that shapes the code.** Vast.ai is a marketplace of individual hosts:
instances can be reclaimed, host reliability varies, and storage is billed while
an instance is stopped. Therefore:

- **Checkpoints sync off-instance** (object storage or a pull to local), not
  merely to the instance's disk. An instance disappearing must cost one
  checkpoint interval, never a training run.
- Checkpoint/resume built in from the first commit of training code, per D-009.
- Prefer hosts with high reliability scores for long runs; treat any single
  instance as disposable.
- Datasets staged reproducibly from a manifest, so a fresh instance is
  self-provisioning.

**Wrong if.** Interruption rates make long runs impractical. Fallback is a
managed provider (Lambda, RunPod) at higher cost for the same work.

---

## D-012 — Flow matching is the first architecture to attempt at G1 (2026-08-26)

**Refines D-008 — does not close it.**

**Decision.** G1 attempts flow matching over SE(3) frames first. The
architecture choice formally remains open per D-008; this fixes only the
starting point, not the answer.

**Why.** Stabler training and substantially fewer sampling steps than
score-based diffusion, and it is where the field has been heading. If it does
not train well at G1 scale, the alternatives in D-008 remain available behind
the same interface, at the cost of G1 time only.

**Rules out.** Nothing permanently. The generator interface (D-004) is what
protects this decision from being expensive to reverse.

---

## D-013 — Local machine is a development box, not a training box (2026-08-26)

**Confirms D-011.** Local hardware measured: **NVIDIA RTX 5070 Laptop, 8GB
VRAM, 50W power cap, Blackwell (sm_120), driver 596.08 / CUDA 13.2, Windows
WDDM.**

**Decision.** Training runs go to Vast.ai as already decided. The local machine
takes a defined and genuinely useful role rather than being sidelined.

**Why.** 8GB VRAM caps model and batch size below what G1 needs, and a 50W
laptop part throttles under sustained load — a multi-day run would be both slow
and unreliable. Neither problem affects development work.

**Division of labour.**

| Local | Vast.ai |
|-------|---------|
| All of Phases 1–2 (no GPU required regardless) | G1 / G2 / G3 training runs |
| Data preparation, structural clustering, dataset staging | Any sustained or memory-hungry job |
| Code development and debugging | |
| Overfit-one-batch sanity tests | |
| Sampling / inference from trained checkpoints | |
| G0 hallucination runs at small scale | |

**Practice: overfit locally before renting.** Training on a single batch until
loss approaches zero catches most training bugs — shape errors, broken masking,
a loss not wired to the parameters — and fits comfortably in 8GB. Rental time
is then spent on training, not debugging.

**Setup constraints this imposes.**

1. **Blackwell requires current PyTorch.** `sm_120` kernels ship in builds
   against CUDA 12.8 and later; an older pinned wheel will not run on this card.
   Local and Vast.ai environments must be pinned *together*, or code that works
   in one place fails in the other.
2. **WSL2 recommended over native Windows.** The structural biology toolchain is
   Linux-first, and WSL2 makes the local and rental environments near-identical
   — which is what keeps the dev/train split from drifting into two codebases.
3. **Training code must be scale-agnostic.** Batch size, gradient accumulation,
   and precision come from config, so the same script runs an 8GB sanity check
   and a rented card unchanged.

**Wrong if.** G1 turns out to fit in 8GB after all, in which case short local
runs become viable and rental is reserved for G2/G3. Worth re-testing once the
model is sized.

**Addendum, 2026-08-26 — verified and measured.** Environment confirmed working:
Ubuntu 24.04 on WSL2, Python 3.12.3, PyTorch 2.11.0+cu128, `sm_120` kernels
present, gradients flowing (`scripts/verify_env.py` reports READY). Measured
**25.3 TFLOP/s bf16**, with **6.7GB of the 8GB actually free** after display
usage.

This makes the rental decision quantitative rather than assumed: a rented
consumer card is roughly 5–6× this throughput and a datacentre card
substantially more, so sustained training on the laptop would be slow rather
than impossible — slow enough that hourly rental pays for itself immediately.
Batch-size planning uses the 6.7GB figure, not 8GB.

---

## D-014 — Rank on partner *kind*, not on polymer entity count (2026-08-26)

**Prompted by the first live run of stage 1.**

**What happened.** Ranking gave a co-complex bonus to any entry with more than
one polymer entity. Run against PD-L1 this put `5O45` (0.99 A, partner: a
14-residue macrocyclic peptide inhibitor) and `8ALX` (1.10 A, a small-molecule
inhibitor) at the top, above the PD-1 complexes. Every note the pipeline printed
was accurate; the conclusion was wrong.

**Why it matters.** Those structures show a *drug-binding site*. For protein
binder design the interface we need is the one PD-1 occupies. Worse, several
PD-L1 small-molecule inhibitors act by inducing PD-L1 to homodimerise, so the
"observed interface" in such an entry is the target against itself. Nothing
downstream would have reported a problem — the campaign would simply have
designed binders against the wrong surface.

**Decision.** Partners are classified and scored by kind, using polymer length,
polymer type, and the UniProt cross-reference:

| Kind | Bonus | Meaning |
|------|-------|---------|
| natural protein | +4.0 | a real biological partner — the interface we want |
| engineered protein | +3.0 | nanobody or designed binder; still protein-protein |
| peptide ligand (<40 aa) | +1.0 | marks a druggable hotspot, not a protein epitope |
| homodimer (same accession) | +0.5 | self-association, often inhibitor-induced |
| nucleic acid | +0.0 | |

The target's own entity is excluded before partners are counted.

**Rules out.** Treating "more than one polymer entity" as evidence of a usable
interface. A description is not enough either:
`PHE-MEA-9KK-SAR-ASP-VAL-...` reads like nothing in particular and is a drug.

**Wrong if.** The 40-residue threshold misclassifies something real. A designed
mini-binder can be ~50 aa, so the margin is not large; if short designed binders
start appearing as partners, the threshold needs revisiting rather than
widening.

**General lesson, recorded because it will recur.** This is the same failure
shape as D-010's epitope risk, arriving two stages earlier than expected: not a
crash, but a confident answer to the wrong question. Every stage where the agent
picks one item from several needs an explicit account of *why the alternatives
lost*, and a guard that refuses rather than guesses. The ambiguity guard at
UniProt resolution caught its case; the ranking had no equivalent and did not.

---

## D-015 — Enrich every candidate, never a shortlist (2026-08-26)

**Prompted by the second live run of stage 1. Same failure shape as D-014.**

**What happened.** After D-014 fixed partner classification, the top five PD-L1
structures were all *engineered* binders — VHH nanobodies, an antibody, a
designed cystine-dense peptide. PD-1 itself did not appear. `4ZQK` (PD-L1 with
PD-1, 2.45 A) scores 12.5 and should have led.

**Why.** Enrichment ran on the top 15 candidates *as ranked before enrichment* —
and before enrichment the only terms available are method, resolution, and
coverage. At 2.45 A the natural complex sat below a crowd of sub-2 A structures,
fell outside the shortlist, was never enriched, and so never received the
partner bonus that would have put it first. **The heaviest-weighted criterion
was computed only for candidates that already scored well without it.**

**Decision.** Every candidate is enriched, via batched GraphQL against the RCSB
Data API: one request covers fifty entries with their polymer entities, lengths,
and UniProt cross-references. Enriching all 72 PD-L1 entries now costs fewer
requests than the per-entry REST path cost for five. The REST path remains as a
fallback when GraphQL is unavailable.

**Rules out.** Any shortlist computed on a subset of the ranking criteria. If a
term contributes to the score, it is computed for every candidate before
ranking, or it is not in the score.

**Wrong if.** A target has so many structures that batched enrichment becomes
slow. The answer is more batching, not a shortlist — restoring one reintroduces
exactly this bias.

**Third instance of the same lesson.** D-010 predicted silent failure at epitope
selection. D-014 found it in partner classification. This is it in candidate
enrichment. In all three the pipeline ran clean and reported confidently; only
the question was wrong. Two rules are now earning their keep: *account for why
the alternatives lost*, and *never let an optimisation decide what gets
evaluated*.

---

## D-016 — Score partner species and engineered mutations (2026-08-26)

**Prompted by the third live run of stage 1. Fourth instance of the D-014 shape.**

**What happened.** With enrichment fixed by D-015, PD-1 complexes reached the
top — but the winner was `3SBW`, *"complex between the extracellular domains of
mouse PD-1 mutant and human PD-L1"*, beating `4ZQK` (human PD-1 / human PD-L1)
by 0.02 points on slightly better resolution and coverage.

**Why it matters.** Mouse and human PD-1 bind PD-L1 through a related but not
identical interface, and `3SBW`'s PD-1 carries engineered mutations on top of
that. As a template for the epitope a *human* binder should target, it is
clearly worse — yet it scored higher, and nothing in the output said so. The
entity description reads "Programmed cell death protein 1" either way.

**Decision.** Source organism and mutation count are read from RCSB per entity
and scored:

| Condition | Penalty |
|-----------|---------|
| natural partner from another organism | −1.5 |
| target chain from another organism | −2.0 |
| partner carries engineered mutations | −0.75 |
| target chain carries engineered mutations | −1.0 |

Two deliberate exclusions. **Engineered partners take no species penalty** — a
designed VHH is a "synthetic construct" and penalising that would be nonsense.
**Missing organism data is never read as a mismatch**; unknown is unknown.

**Rules out.** Treating a partner's identity as established by its description.
"Programmed cell death protein 1" names mouse and human, wild type and mutant,
identically.

**Wrong if.** A cross-species complex is the only structure available for some
target. The penalty demotes it rather than excluding it, so it still wins when
nothing better exists — which is the intended behaviour.

**Fourth instance, and the pattern is now the finding.** D-010 predicted it,
D-014 found it in partner classification, D-015 in enrichment coverage, D-016 in
partner provenance. Every one: the pipeline ran clean, printed accurate notes,
and answered a question adjacent to the one asked. None was caught by a test —
all four were caught by *looking at real output for a target whose right answer
was independently known*.

That is the argument for the D-010 benchmark in its strongest form. Stage 3 has
no equivalent of "PD-1 should have won" available by inspection; the benchmark
is the only thing that will play that role.
