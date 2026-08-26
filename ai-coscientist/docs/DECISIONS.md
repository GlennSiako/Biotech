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
