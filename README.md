# PhytoForge

**An autonomous virtual biofoundry for plant-made recombinant proteins.**

PhytoForge is a simulation-first platform for designing and optimizing the production of recombinant proteins in plants. It combines biology-focused reasoning agents, quantitative production models, and a virtual robotic facility in a closed design–build–test–learn loop.

The initial product focuses on transient expression in *Nicotiana benthamiana* for research proteins and diagnostic antigens. Human therapeutics and vaccines are long-term applications, not claims of the prototype.

The first benchmark product is research-grade recombinant human epidermal growth factor (hEGF). It was selected because multiple plant-expression studies expose meaningful, context-dependent trade-offs across construct design, localization, harvest timing, recovery, and quality.

## Product thesis

Given a protein specification and manufacturing constraints, PhytoForge should:

1. propose alternative expression and process designs;
2. compile those designs into simulated production campaigns;
3. execute campaigns through a virtual plant factory;
4. return noisy estimates of yield, quality, cost, and reliability;
5. select informative follow-up experiments; and
6. preserve the evidence and uncertainty behind every decision.

Simulation results generate hypotheses. They do not establish biological activity, safety, efficacy, manufacturability, or regulatory suitability without experimental validation.

## Initial scope

- **Host:** *Nicotiana benthamiana*
- **Mode:** contained, transient expression
- **Products:** non-clinical research proteins and diagnostic antigens
- **Objectives:** recoverable yield, quality, cost, cycle time, and robustness
- **Execution:** virtual facility first; partner-lab integration later

## Documentation

- [Product requirements](docs/PRODUCT_REQUIREMENTS.md)
- [Scientific and simulation model specification](docs/MODEL_SPECIFICATION.md)
- [Software architecture](docs/ARCHITECTURE.md)
- [hEGF benchmark specification](docs/benchmarks/HEGF.md)
- [hEGF evidence manifest](data/evidence/hegf_sources.yaml)

## Run the simulator

Python 3.11 or newer is required. The executable scaffold has no runtime dependencies.

```bash
PYTHONPATH=src python3 -m phytoforge --seed 42 --rounds 4 --batch-size 4
```

Generate a machine-readable report:

```bash
PYTHONPATH=src python3 -m phytoforge --json
```

Run the test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Repository organization

```text
.
├── data/evidence/          # Reviewed, structured evidence manifests
├── docs/                   # Product, model, and benchmark specifications
├── drug-studies/           # Pre-existing exploratory case studies
├── src/phytoforge/         # Executable simulator package
├── tests/                  # Replay, isolation, and scientific invariants
└── pyproject.toml
```

The current implementation is a standard-library S0 simulator. Its coefficients are transparent synthetic priors designed to test software behavior and qualitative relationships—not fitted biological predictions.

## Naming

**Product name:** PhytoForge

**Category:** autonomous plant molecular-farming software

**Working tagline:** Program plants. Simulate production. Learn from every run.

“PhytoForge” is a working product name and must undergo trademark and domain review before public commercial use.

## Current status

Executable hEGF simulator scaffold with deterministic campaign replay, bounded design selection, biology and process models, noisy observations, and capacity-constrained virtual facility events. No wet-lab or clinical validation has been performed.
