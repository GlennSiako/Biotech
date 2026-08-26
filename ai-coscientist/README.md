# AI Co-Scientist

Agent-orchestrated pipeline for **de novo protein binder design**: take a protein
target, return a ranked set of designed binders with structural evidence and
confidence metrics.

**Status:** Planning. No code yet — the plan is being settled first, deliberately.

## Read these first

- **[docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)** — scope, pipeline
  architecture, the generative model plan, evaluation, phases, risks, and open
  decisions.
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — append-only log of decisions and
  what each one rules out.
- **[docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)** — WSL2 + PyTorch setup for the
  development machine, and why Blackwell needs verifying rather than assuming.

## Running stages 1-2

```bash
python scripts/resolve_target.py CD274 --region 18-134 --prepare
```

Resolves the target through UniProt, ranks every cross-referenced PDB entry for
suitability, prepares the top-ranked chain, and writes
`runs/<run_id>/manifest.json`. The manifest records **every candidate with its
score and reasoning**, not just the winner — a campaign that goes wrong has to
be explainable afterwards.

```bash
python -m pytest tests/ -q      # 51 tests, no network required
```

## Verify your machine

```bash
python scripts/verify_env.py
```

Launches real kernels and a backward pass. On Blackwell, driver-level checks
pass while compute still fails — this is the test that tells the truth.

## The shape of it

```
target ──▶ resolve ──▶ prepare ──▶ epitope ──▶ GENERATE ──▶ sequence ──▶ validate ──▶ rank
           UniProt     structure   hotspot     backbones    inverse      co-fold      report
           PDB/AFDB    cleanup     selection   (our model)  folding      + metrics
                       └── human gate ──┘      └────────── agent-autonomous ──────────┘
```

The generative model at stage 4 is the point of the project. Everything else
exists to pose it well-formed problems and to measure its output honestly.

## Ground rules

1. **The scoreboard comes before the model.** Phases 1–2 build an end-to-end
   pipeline and a measured baseline. Phase 3 trains our model against that
   number.
2. **Every run is reproducible from its manifest.** Seeds, checkpoint versions,
   structure IDs, and all intermediates are recorded per run.
3. **Filtering is half the system, not a postscript.** Published binder campaigns
   pass a small fraction of designs; the pipeline is built for volume and hard
   filters.
4. **Confidence is geometry, not biology.** A high interface score says the
   structure is plausible. It does not say the binder works in a cell — see the
   iniparib note in §11 of the plan.
