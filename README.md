# PhytoForge

**An autonomous virtual biofoundry for plant-made recombinant proteins.**

PhytoForge is a simulation-first platform for designing and optimizing the production of recombinant proteins in plants. It combines biology-focused reasoning agents, quantitative production models, and a virtual robotic facility in a closed design–build–test–learn loop.

The initial product focuses on transient expression in *Nicotiana benthamiana* for research proteins and diagnostic antigens. Human therapeutics and vaccines are long-term applications, not claims of the prototype.

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

## Repository organization

```text
.
├── docs/                   # Product and model specifications
├── drug-studies/           # Pre-existing exploratory case studies
└── README.md
```

Implementation directories will be introduced only after the model interfaces and MVP acceptance criteria are approved.

## Naming

**Product name:** PhytoForge  
**Category:** autonomous plant molecular-farming software  
**Working tagline:** Program plants. Simulate production. Learn from every run.

“PhytoForge” is a working product name and must undergo trademark and domain review before public commercial use.

## Current status

Concept definition and technical specification. No wet-lab or clinical validation has been performed.
