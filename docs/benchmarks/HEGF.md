# hEGF Benchmark Specification

| Field | Value |
|---|---|
| Benchmark ID | `hegf-nb-transient-v0` |
| Status | Approved first benchmark; implementation pending |
| Product | Research-grade recombinant human epidermal growth factor (hEGF) |
| Host | *Nicotiana benthamiana* |
| Production mode | Contained transient expression |
| Calibration ceiling | S1, literature-informed plausibility |
| Intended use | Simulator verification and autonomous experiment-selection research |
| Last updated | 2026-08-15 |

## 1. Decision

hEGF is the first PhytoForge benchmark protein.

The benchmark asks whether PhytoForge can represent context-dependent expression, plant stress, harvest timing, recovery, purification, measurement noise, and autonomous experiment selection for a compact recombinant protein with published plant-expression evidence.

hEGF is not being selected as a clinical-development candidate. Version 0 models production of a non-clinical research reagent and cannot establish biological activity, safety, efficacy, manufacturing suitability, or regulatory acceptability.

## 2. Why hEGF

hEGF offers a useful middle ground between a trivial reporter and a complex biologic:

- mature hEGF is a small 53-amino-acid protein;
- six cysteine residues form three intrachain disulfide bonds that are important to its structure and activity;
- transient expression in *N. benthamiana* has been reported in multiple studies;
- published experiments vary localization, construct context, plant age, harvest time, and downstream processing;
- recovered material can be evaluated through quantity, identity, purity, and cell-response assays;
- plant-produced hEGF has been reported with activity comparable to commercial controls in study-specific in-vitro assays; and
- complex glycosylation is not the primary quality challenge, allowing version 0 to focus on folding, degradation, recovery, and activity retention.

GFP may be used as a simulator and imaging control, but it is not the benchmark product.

## 3. Benchmark question

> Given a bounded library of hEGF expression and process designs, can an autonomous system identify robust simulated campaigns that improve recoverable, quality-adjusted hEGF output under cost, time, and uncertainty constraints?

The benchmark evaluates the software and model behavior. It does not evaluate whether a real production process works.

## 4. Evidence basis

Structured source metadata and extracted claims are maintained in [`data/evidence/hegf_sources.yaml`](../../data/evidence/hegf_sources.yaml).

### 4.1 Thomas and Walmsley, 2014

This peer-reviewed study compared transient hEGF expression across subcellular localizations and optimization choices in *N. benthamiana*.

Reported findings used by the benchmark:

- expression was highest for the study's vacuole-targeted condition;
- codon optimization increased the vacuole-targeted yield by approximately 34% but did not improve the ER-targeted condition;
- P19 silencing suppression increased expression by more than threefold;
- five-week-old plants outperformed four- and six-week-old plants in the tested context;
- combined optimizations produced an average yield of 6.24% of total soluble protein; and
- plant-made hEGF promoted mouse keratinocyte proliferation comparably to the commercial *E. coli*-derived control used in the study.

These observations are context-specific and must not be treated as universal effects.

### 4.2 Hanittinan et al., 2020

This peer-reviewed study used a geminiviral expression system and compared six hEGF construct configurations.

Reported findings used by the benchmark:

- the highest expression among the six tested constructs was observed for an ER-targeted, C-terminal-His-tagged configuration;
- the reported yield for that condition was 15.695 µg/g leaf fresh weight, or 0.499% of total soluble protein;
- the study evaluated harvest observations at 2, 4, and 6 days post-introduction;
- recovered hEGF was purified by nickel-affinity chromatography and identified using electrophoretic and immunodetection methods;
- preliminary downstream results suggested that extraction context, including acidic conditions, affected host-protein removal;
- ammonium-sulfate precipitation was not supported as an effective host-protein-removal step in that study; and
- plant-produced hEGF showed no additional cytotoxic effect relative to the commercial control in the reported HaCaT assay conditions.

The downstream observations were described as preliminary by the authors and remain qualitative benchmark constraints, not calibrated process laws.

### 4.3 Important cross-study conflict

The two primary studies do not identify the same best localization strategy. That is valuable for PhytoForge: the model must condition predictions on vector, construct, plant, assay, and campaign context rather than learning a universal rule that one compartment is always superior.

Direct numerical comparison is also limited because studies report different constructs, contexts, harvest schedules, and yield denominators. Percent total soluble protein can increase when total soluble protein decreases, so it must not be treated as interchangeable with product mass per fresh biomass.

## 5. Evidence grades

| Grade | Meaning | Permitted use |
|---|---|---|
| E1 | Direct quantitative result from a primary source | Retrospective scenario target with source-specific context |
| E2 | Direct qualitative result from a primary source | Directional constraint or prior |
| E3 | Result available only through a secondary source | Hypothesis generation; no calibration |
| S0 | Synthetic assumption introduced by PhytoForge | Software demonstration only |

Every parameter and benchmark assertion must reference an evidence ID or be labeled S0.

## 6. Target product profile

```yaml
target_id: hegfrp_v0
benchmark_id: hegf-nb-transient-v0
intended_use: research_reagent_simulation
host: nicotiana_benthamiana
production_mode: transient_contained
product:
  name: recombinant_human_epidermal_growth_factor
  short_name: hEGF
  mature_length_amino_acids: 53
  structural_features:
    intrachain_disulfide_bonds: 3
  glycosylation_model: not_a_primary_benchmark_dimension
quality_dimensions:
  - identity_proxy
  - intact_fraction
  - aggregate_or_fragment_proxy
  - purity_proxy
  - activity_retention_proxy
optimization_dimensions:
  - recoverable_quality_adjusted_mass
  - batch_failure_probability
  - simulated_cost
  - elapsed_simulated_time
  - information_gain
```

No release specification is implied by this target profile.

## 7. Version 0 design space

The simulator operates on curated categorical components. It does not generate unrestricted nucleotide sequences.

### 7.1 Expression-design factors

| Factor | Version 0 levels | Evidence role |
|---|---|---|
| Study context | `thomas_2014_like`, `hanittinan_2020_like`, `synthetic_generalized` | Prevents invalid pooling across studies |
| Localization strategy | cytosolic, apoplast-targeted, ER-targeted/retained, vacuole-targeted | Primary biological comparison |
| Coding adaptation | baseline, host-adapted | Context-dependent expression modifier |
| Silencing-suppression context | absent, present | Context-dependent expression modifier |
| Affinity-tag position | none, N-terminal, C-terminal | Recovery and detectability modifier |
| Expression intensity | low, medium, high | Synthetic abstraction used by the simulator |

Unsupported component combinations must be rejected or marked out of domain.

### 7.2 Plant and campaign factors

| Factor | Version 0 representation |
|---|---|
| Plant age | categorical bands corresponding to 4, 5, or 6 weeks |
| Harvest observation window | discrete study-supported windows plus a bounded synthetic exploration range |
| Plant-to-plant variation | hierarchical random effect |
| Batch variation | hierarchical random effect |
| Environmental quality | bounded nominal, mild-excursion, and severe-excursion states |
| Expression burden | latent stress contribution |
| Necrosis/stress signal | latent state with an observable imaging proxy |

Plant age and harvest time are conditional on study context. The simulator must not combine them as though all experiments used the same production system.

### 7.3 Downstream factors

| Factor | Version 0 levels |
|---|---|
| Extraction recovery | low, medium, high synthetic efficiency distributions |
| Host-protein carryover | conditional impurity burden |
| Clarification loss | bounded synthetic efficiency |
| Affinity-capture path | supported for compatible tagged designs |
| Acidic host-protein reduction | qualitative optional step with uncertain effect |
| Ammonium-sulfate step | unsupported as a presumed improvement for this benchmark |
| Hold time | short, medium, long with degradation penalty |

These levels represent process abstractions, not laboratory instructions.

## 8. Simulated latent state

Each virtual plant or production unit maintains:

- fresh biomass;
- physiological stress;
- expression activity;
- intact hEGF concentration;
- degraded or fragmented hEGF fraction;
- non-target soluble protein burden;
- harvestability;
- sample identity and lineage; and
- accumulated biological and process costs.

Agents cannot observe this state directly.

## 9. Simulated observations

| Observation | Latent quantity observed | Error model |
|---|---|---|
| Plant image score | biomass and stress | classification error and device drift |
| Fresh biomass | harvestable biomass | scale error and sampling variance |
| Total soluble protein | soluble protein pool | batch and assay noise |
| hEGF quantity proxy | target concentration or mass | bias, quantification limits, and residual noise |
| Identity proxy | expected target detected | false-positive and false-negative rates |
| Purity proxy | target fraction after recovery | process and assay noise |
| Integrity proxy | intact versus fragment/aggregate state | sensitivity and quantification limits |
| Activity-retention proxy | latent correctly folded active fraction | high uncertainty and assay-specific bias |
| Process-control observation | operation or device state | drift and missingness |

Version 0 may use a normalized activity-retention proxy. It must not label this value “potency” or “therapeutic efficacy.”

## 10. Virtual campaign

One campaign contains:

1. candidate selection from the curated design space;
2. protocol compilation into abstract operations;
3. growth-chamber allocation;
4. expression-introduction event;
5. monitored post-introduction interval;
6. harvest;
7. extraction and clarification;
8. optional affinity capture for compatible designs;
9. analytical measurements;
10. quality-control review; and
11. advancement, redesign, or stopping decision.

Version 0 simulates these stages and does not export physical execution instructions.

## 11. Autonomous objective

The primary utility is quality-adjusted recoverable mass:

```math
U_{product}
=
M_{recovered}
\times f_{intact}
\times f_{activity-retained}
\times \mathbb{1}[\text{configured research-quality gates pass}]
```

The campaign optimizer balances:

```math
U
=
w_p U_{product}
- w_f P(\text{batch failure})
- w_c C
- w_t T
+ w_i I
```

Where:

- `C` is simulated cost;
- `T` is elapsed simulated time;
- `I` is expected information gain; and
- all weights are visible and versioned.

The quality gate is a software benchmark threshold, not a real product-release criterion.

## 12. Controls

Every simulated campaign includes:

- non-expressing plant control;
- supported expression-system control;
- process blank;
- analytical reference control;
- at least one replicate structure sufficient to estimate configured variance; and
- GFP imaging control where the scenario tests facility or measurement behavior.

Controls may be abstracted. The benchmark does not prescribe a wet-lab protocol.

## 13. Benchmark scenarios

### H1 — Study-context reconstruction

Verify that each study-specific emulator can reproduce the principal directional findings from its own source without forcing the two contexts to agree.

### H2 — Localization is not universal

Train or optimize in one study context, switch context, and verify that the system raises domain-shift uncertainty instead of confidently transferring the previous winner.

### H3 — Expression versus recovery

Create a high-expression design with poor recovery and a moderate-expression design with better downstream performance. The optimizer should select based on recoverable quality-adjusted mass rather than upstream expression alone.

### H4 — Harvest trade-off

Represent increasing accumulation followed by stress or degradation. The optimizer must identify a robust harvest region rather than always selecting the latest time.

### H5 — Tag and detectability confounding

Introduce a design whose apparent low signal is partly caused by detection or recovery context. The system should retain uncertainty and propose a discriminating comparison.

### H6 — Measurement drift

Inject analytical drift that creates an apparent expression trend. Quality control should detect or flag the trend before advancement.

### H7 — Batch underperformance

Inject a biological batch effect and verify that the system does not attribute all variation to the construct.

### H8 — Sparse budget

Limit campaign capacity so the optimizer must choose between exploiting a current winner and testing a high-uncertainty design family.

### H9 — Out-of-domain product

Replace hEGF descriptors with an unsupported complex protein. The system may simulate exploration but must abstain from an advancement recommendation.

## 14. Literature-emulation checks

The S1 emulator should satisfy the following source-conditioned checks:

### Thomas-2014-like context

- the vacuole-targeted condition ranks above the initial apoplast-targeted condition under nominal settings;
- host-adapted coding improves the vacuole-targeted context but is not forced to improve the ER context;
- the silencing-suppression context has a positive expression effect with wide uncertainty;
- the five-week plant-age band ranks above four and six weeks under the reconstructed scenario; and
- the combined optimized scenario can reproduce the reported 6.24% TSP summary within a deliberately broad literature-emulation interval.

### Hanittinan-2020-like context

- the ER-targeted C-terminal-tagged design ranks highest among the reconstructed six-design set;
- its predicted yield distribution covers the reported 15.695 µg/g leaf fresh weight and 0.499% TSP values;
- the emulator represents observations at 2, 4, and 6 days post-introduction;
- compatible affinity capture reduces target mass while improving the purity proxy;
- acidic extraction is represented as an uncertain host-protein-removal effect; and
- ammonium-sulfate precipitation is not encoded as a guaranteed improvement.

Passing these checks demonstrates implementation consistency with configured summaries, not independent biological validation.

## 15. Baselines

Autonomous selection must be compared with:

- random feasible design selection;
- fixed default design;
- greedy predicted-upstream-expression selection;
- greedy predicted-recoverable-mass selection; and
- balanced categorical coverage.

The agentic system must not receive access to latent simulator state unavailable to the baselines.

## 16. Success criteria

### 16.1 Simulator verification

- all mass-balance, unit, non-negativity, and fraction invariants pass;
- seeded campaigns replay identically;
- study-specific literature-emulation checks pass;
- observation noise changes measurements without changing latent biology;
- batch effects and plant effects remain distinguishable in generated provenance; and
- out-of-domain scenarios trigger abstention.

### 16.2 Optimizer evaluation

Across pre-registered synthetic scenarios and seeds:

- constrained autonomous selection has higher median terminal utility than random selection;
- confidence intervals and effect sizes are reported, not only best-run performance;
- performance is reported separately for each scenario;
- failure to outperform a simple greedy baseline is retained as a negative result; and
- simulator loopholes discovered by the optimizer become regression tests.

### 16.3 Agent evaluation

- every scientific claim has a valid evidence or model-run identifier;
- agents never state latent simulator values as observations;
- unsupported numerical claims are rejected by the orchestrator;
- the experimental-design agent includes informative controls; and
- the quality agent identifies injected drift and sample-identity scenarios at a documented rate.

No arbitrary performance percentage is set before the benchmark runner establishes variance and statistical power.

## 17. Abstention criteria

The benchmark must abstain from recommending advancement when:

- a design uses unsupported components;
- required evidence or controls are missing;
- the product is outside the hEGF applicability domain;
- uncertainty crosses the configured decision boundary;
- critical measurements fail QC;
- study context is unknown but materially changes ranking;
- mass-balance or provenance checks fail; or
- the optimizer identifies an unverified region of the simulator.

## 18. Initial synthetic priors

Version 0 starts at calibration tier S0. Priors are selected to produce testable qualitative behavior and must not be presented as experimentally estimated parameters.

Parameter families:

- biomass growth and carrying capacity;
- plant and batch variability;
- design-conditioned synthesis;
- stress-conditioned degradation;
- localization-conditioned recovery;
- extraction and clarification efficiency;
- affinity-capture recovery and impurity removal;
- activity-retention fraction;
- assay bias and variance;
- device drift and failure hazards; and
- event cost and duration.

The parameter registry must cite this benchmark, an evidence claim ID, or a future calibrated dataset for every value.

## 19. Dataset plan

### Dataset A — source summaries

Manually reviewed, structured claims from primary publications. This supports traceability but is not sufficient for fitting a high-capacity predictive model.

### Dataset B — synthetic factorial corpus

Generated from versioned S0/S1 simulator configurations with complete latent state and observation streams. Latent fields remain unavailable to agents.

### Dataset C — retrospective experimental table

Created only if source-level replicate data and sufficient metadata can be legally and reliably obtained. Study and batch groups must remain intact across evaluation splits.

### Dataset D — prospective partner data

Future blinded measurements from a qualified partner. This is required before any S3 decision-support claim.

## 20. Required implementation artifacts

```text
src/phytoforge/benchmarks/hegf/
├── target_profile.yaml
├── component_library.yaml
├── scenario_registry.yaml
├── parameter_priors.yaml
└── benchmark.py

tests/benchmarks/hegf/
├── test_invariants.py
├── test_literature_emulation.py
├── test_fault_scenarios.py
├── test_optimizer_baselines.py
└── test_replay.py
```

These paths are planned interfaces, not files created by this documentation change.

## 21. Open scientific questions

- Can source-level replicate measurements be recovered for either primary study?
- How should `% TSP` and `µg/g fresh weight` be jointly modeled without assuming a fixed conversion?
- Which activity assay is sufficiently standardized for a future partner-validation benchmark?
- Which construct factors can be represented without conflating vector system and localization?
- How should affinity-tag effects be separated from detection bias and true biological stability?
- What minimum data support is required before replacing a mechanistic component with a learned surrogate?

## 22. References

1. Thomas DR, Walmsley AM. Improved expression of recombinant plant-made hEGF. *Plant Cell Reports*. 2014;33:1801–1814. <https://doi.org/10.1007/s00299-014-1658-8>
2. Hanittinan O, Oo Y, Chaotham C, Rattanapisit K, Shanmugaraj B, Phoolcharoen W. Expression optimization, purification and in vitro characterization of human epidermal growth factor produced in *Nicotiana benthamiana*. *Biotechnology Reports*. 2020;28:e00524. <https://doi.org/10.1016/j.btre.2020.e00524>
3. Hanittinan O. Development of recombinant human epidermal growth factor production in *Nicotiana benthamiana*. Chulalongkorn University thesis. 2020. <https://doi.org/10.58837/CHULA.THE.2020.374>
