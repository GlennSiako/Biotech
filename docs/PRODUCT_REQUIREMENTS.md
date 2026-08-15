# PhytoForge Product Requirements


| Field                 | Value                                     |
| --------------------- | ----------------------------------------- |
| Document status       | Draft for product discovery               |
| Product stage         | Simulation-first prototype                |
| Initial domain        | Plant molecular farming                   |
| Initial host          | *Nicotiana benthamiana*                   |
| Initial product class | Research proteins and diagnostic antigens |
| First benchmark       | Research-grade recombinant hEGF           |
| Last updated          | 2026-08-15                                |


## 1. Executive summary

PhytoForge is an autonomous virtual biofoundry for plant-made recombinant proteins. A user supplies a protein specification, production objective, and constraints. Biology agents propose candidate expression systems; an experiment planner selects informative campaigns; virtual robots execute those campaigns in a discrete-event facility; quantitative models return uncertain measurements of yield, quality, cost, and reliability; and the system uses the resulting evidence to choose the next campaign. The first benchmark product is research-grade recombinant human epidermal growth factor (hEGF).

The first release is a scientific hypothesis and workflow simulator. It must not claim to validate a drug, vaccine, manufacturing process, or biological mechanism. Its commercial destination is a closed-loop engineering platform connected to customer or partner laboratories.

## 2. Problem

Developing a plant-based recombinant-protein process requires coupled decisions across protein biology, construct design, host context, plant growth, harvest timing, extraction, purification, and quality control. Results are context-dependent, experimental data are fragmented, and failure in one stage can erase gains made elsewhere.

Existing workflows commonly separate:

- construct and sequence design;
- plant-production operations;
- assay and purification data;
- experimental provenance; and
- selection of the next experiment.

PhytoForge should connect these decisions in one traceable design–build–test–learn system.

## 3. Product vision

Become the control and learning layer for distributed biological manufacturing systems, beginning with contained plant molecular farming.

The long-term product is not a plant animation or a general-purpose chatbot. It is a system in which a digital production specification can be compiled into an experiment, executed by either simulated or physical infrastructure, measured, and used to improve the next design.

## 4. Commercial thesis



### 4.1 Initial customer

The initial customer profile is a small molecular-farming team, recombinant-protein laboratory, plant-biotechnology group, or contract research organization that:

- evaluates multiple protein constructs or process conditions;
- records results across disconnected tools;
- needs to prioritize limited experimental capacity; and
- can provide structured outcome data for calibration.



### 4.2 Initial job to be done

> When I need to express a recombinant protein in plants, help me choose a small, informative set of designs and production conditions so I can reach an acceptable yield and quality profile with fewer failed experimental rounds.



### 4.3 Entry market

The first commercial wedge is research-grade proteins and diagnostic antigens. These provide measurable outcomes and shorter feedback loops than regulated human therapeutics.

Expansion order:

1. research proteins and assay reagents;
2. diagnostic antigens;
3. veterinary biologics;
4. human vaccine components and therapeutic proteins; and
5. additional biological production hosts.

This order is a product hypothesis and must be validated through customer discovery.

### 4.4 Business model hypotheses

- annual enterprise software license;
- paid design and optimization campaigns;
- usage-based execution through laboratory partners;
- licensing of validated expression systems or process packages; and
- milestone-bearing therapeutic partnerships only after prospective validation.

Pricing is intentionally unspecified until buyer interviews establish budget ownership, purchase frequency, and measurable economic value.

### 4.5 Defensibility

The agents and user interface are not durable moats. Potential defensibility comes from:

- paired design–process–measurement datasets;
- calibrated host- and product-specific predictive models;
- validated component and process libraries;
- integrations with laboratory execution and data systems;
- reproducible provenance across every design generation; and
- demonstrated prospective improvement in experimental selection.



## 5. Product principles

1. **Evidence over eloquence:** agent narratives never substitute for model outputs or measurements.
2. **Uncertainty is a result:** every prediction includes calibration status, confidence, and applicable domain.
3. **End-to-end mass balance:** gains cannot appear without a source, and losses propagate through downstream processing.
4. **Reproducibility by default:** seeds, model versions, assumptions, actions, and observations are retained.
5. **Simulation and reality remain distinct:** synthetic, literature-derived, and measured data are visibly labeled.
6. **Human control at consequential boundaries:** users approve external execution and any use involving regulated products.
7. **Contained production first:** the product does not model environmental release or edible-vaccine deployment in its MVP.



## 6. Users



### 6.1 Plant molecular-farming scientist

Defines constructs and assays, inspects biological assumptions, and compares candidate campaigns.

### 6.2 Protein scientist

Specifies the target product profile and evaluates folding, assembly, activity, and quality risks.

### 6.3 Process-development scientist

Optimizes harvest, extraction, purification, cost, and batch robustness.

### 6.4 Laboratory automation engineer

Maps abstract operations to device capabilities and validates executable workflows.

### 6.5 Program lead

Sets budgets and advancement criteria, then reviews evidence, uncertainty, and decision history.

## 7. MVP use case



### 7.1 Mission

Given the bounded hEGF target product profile, autonomously identify a robust simulated transient-expression and downstream-processing design in *N. benthamiana*. The benchmark is specified in [`docs/benchmarks/HEGF.md`](benchmarks/HEGF.md).

### 7.2 User inputs

- amino-acid sequence or non-sensitive abstract protein descriptor;
- intended non-clinical use;
- structural and quality requirements;
- acceptable product-quality ranges;
- production budget and campaign limit;
- available component library;
- available virtual equipment;
- objective weights or Pareto preferences; and
- constraints such as maximum cycle time.



### 7.3 System outputs

- ranked candidate designs;
- predicted recoverable yield and uncertainty;
- predicted quality attributes and risks;
- simulated facility schedule and resource consumption;
- cost and cycle-time estimates;
- experiment lineage and decision rationale;
- failed-campaign diagnosis;
- model applicability and evidence grade; and
- machine-readable campaign package.



## 8. Core workflow

1. The user creates a project and target product profile.
2. The system validates required fields and marks unsupported claims.
3. Biology agents retrieve relevant structured evidence and propose candidate designs.
4. Deterministic rules reject infeasible or policy-disallowed candidates.
5. Predictive models estimate outcomes and uncertainty.
6. The experiment planner selects a batch under budget and information constraints.
7. The protocol compiler maps the batch to abstract facility operations.
8. Virtual robots execute operations in simulated time.
9. The biological and process models produce latent outcomes.
10. Measurement models generate realistic observations and quality-control signals.
11. Analysis agents diagnose results and update project memory.
12. The optimizer selects the next batch or stops according to explicit criteria.
13. The system exports a final evidence package.



## 9. Agent system

Agents may reason, retrieve evidence, call models, and propose actions. They may not invent measurements or directly assign scientific scores.


| Agent                      | Responsibility                                           | Required tools                                        | Prohibited behavior                            |
| -------------------------- | -------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| Protein scientist          | Identify folding, assembly, stability, and quality risks | Protein metadata, evidence retrieval, property models | Claim biological activity from sequence alone  |
| Plant-expression scientist | Propose host-compatible expression designs               | Component library, design rules, expression model     | Bypass construct constraints                   |
| Process scientist          | Propose harvest and downstream options                   | Mass-balance and process models                       | Create yield without accounting for recovery   |
| Experimental designer      | Select informative comparisons and controls              | Optimizer, budget, uncertainty estimates              | Select only the current predicted winner       |
| Operations planner         | Compile and schedule facility actions                    | Device registry, scheduler, inventory                 | Execute unsupported device actions             |
| Quality critic             | Detect anomalies and challenge advancement               | QC rules, observations, provenance                    | Rewrite or hide failed results                 |
| Orchestrator               | Manage state transitions and stopping conditions         | Workflow state and policy engine                      | Override scientific gates without recording it |


All agent claims must be categorized as one of:

- measured observation;
- model prediction;
- retrieved evidence;
- inference;
- hypothesis; or
- unresolved uncertainty.



## 10. Functional requirements

Priority definitions:

- **P0:** required for a credible MVP;
- **P1:** required for a useful pilot;
- **P2:** expansion capability.



### 10.1 Project and target specification

- **P0:** Create, edit, clone, archive, and export a project.
- **P0:** Define target product profile, objectives, constraints, and campaign budget.
- **P0:** Validate input completeness and assign an evidence classification.
- **P1:** Import structured protein metadata.
- **P2:** Support organization-specific templates and permissions.



### 10.2 Design generation and validation

- **P0:** Represent candidate designs as versioned, machine-readable objects.
- **P0:** Generate candidates from a bounded, curated component library.
- **P0:** Apply hard feasibility rules before simulation.
- **P0:** Preserve parentage and mutations between design generations.
- **P1:** Support customer-defined components with provenance and access controls.
- **P2:** Export standards-compatible design artifacts where practical.



### 10.3 Quantitative simulation

- **P0:** Simulate plant growth, product accumulation, degradation, harvest, extraction, purification, measurement, and cost.
- **P0:** Propagate biological, process, batch, and measurement uncertainty.
- **P0:** Enforce mass-balance and non-negativity invariants.
- **P0:** Support seeded reproducible runs.
- **P1:** Calibrate parameters against literature or partner data.
- **P2:** Substitute learned surrogate models for selected mechanistic components.



### 10.4 Autonomous experimentation

- **P0:** Select experiment batches under campaign and resource budgets.
- **P0:** Balance expected performance and information gain.
- **P0:** Include positive, negative, and process controls configured for the simulation.
- **P0:** Stop on budget exhaustion, convergence, infeasibility, or explicit success criteria.
- **P1:** Support multi-objective constrained Bayesian optimization.
- **P2:** Support transfer learning across related protein projects.



### 10.5 Virtual facility

- **P0:** Model devices as capacity-constrained resources with supported actions.
- **P0:** Compile abstract protocols into scheduled operations.
- **P0:** Track lots, samples, consumables, queues, and timestamps.
- **P0:** Simulate recoverable failures and measurement drift.
- **P0:** Expose an event timeline suitable for visualization and replay.
- **P1:** Validate protocols against vendor-neutral device interfaces.
- **P2:** Connect approved protocols to partner-lab APIs.



### 10.6 Evidence and reporting

- **P0:** Record every design, model invocation, action, observation, and decision.
- **P0:** Visibly distinguish synthetic, literature-derived, and measured data.
- **P0:** Report uncertainty and out-of-domain warnings with every prediction.
- **P0:** Export a human-readable report and machine-readable project bundle.
- **P1:** Compare model predictions against imported experimental outcomes.
- **P2:** Generate audit-ready reports for regulated workflow development without claiming regulatory compliance.



### 10.7 User experience

- **P0:** Mission setup with target, constraints, and objective selection.
- **P0:** Candidate table with Pareto and uncertainty views.
- **P0:** Facility timeline showing device activity and failures.
- **P0:** Run comparison and best-so-far trajectory.
- **P0:** Evidence panel showing why an action was proposed.
- **P1:** Visual construct and process editor.
- **P1:** Interactive sensitivity and counterfactual analysis.



## 11. Non-functional requirements



### 11.1 Reproducibility

Given the same project bundle, model versions, and random seed, a run must produce identical event and observation streams.

### 11.2 Traceability

Every displayed value must link to its generating observation, model call, calculation, or source assumption.

### 11.3 Modularity

Biology, process, measurement, optimization, and facility models must communicate through versioned interfaces so that one implementation can be replaced without rewriting the workflow.

### 11.4 Security

- encrypt data in transit and at rest in deployed environments;
- isolate customer projects;
- maintain an immutable audit log;
- avoid sending customer sequences to external models without explicit configuration; and
- support deletion and retention policies.



### 11.5 Performance

An MVP campaign containing hundreds of virtual samples and multiple rounds should run interactively on a developer workstation. Exact service-level objectives will be established after profiling.

### 11.6 Explainability

The system must expose which constraints, model outputs, observations, and objective weights affected an advancement decision.

## 12. Data model

Minimum first-class entities:

- `Project`
- `TargetProductProfile`
- `Design`
- `DesignComponent`
- `Campaign`
- `Protocol`
- `Operation`
- `Device`
- `MaterialLot`
- `Sample`
- `Observation`
- `ModelRun`
- `AgentClaim`
- `Decision`
- `EvidenceSource`
- `CostEvent`

Every entity must include a stable identifier, schema version, creation time, provenance, and owning project.

## 13. Decision policy

Candidate advancement is a constrained multi-objective decision rather than a single opaque score.

Hard gates:

- design feasibility;
- facility executability;
- minimum evidence completeness;
- configured quality limits; and
- absence of critical QC failure.

Soft objectives:

- recoverable yield;
- product-quality proxies;
- estimated cost;
- cycle time;
- robustness to uncertain parameters; and
- expected information gain.

The interface should display a Pareto frontier. If a composite score is offered, its weights and normalization must be visible and versioned.

## 14. Success metrics



### 14.1 Prototype metrics

- percentage of runs reproducible from exported bundles;
- percentage of displayed claims with valid provenance;
- protocol compilation success for supported facility configurations;
- rate of detected injected faults;
- preservation of mass-balance invariants;
- optimization improvement over random and fixed-design baselines; and
- uncertainty calibration on synthetic holdout scenarios.



### 14.2 Pilot metrics

- prospective top-k design hit rate against measured partner outcomes;
- reduction in experiments required to meet a target profile;
- error in recoverable-yield and quality predictions;
- number of customer decisions made using exported evidence packages;
- user correction rate for agent-generated hypotheses; and
- renewal or expansion intent from design partners.



### 14.3 Commercial validation

The initial thesis should be reconsidered if:

- molecular-farming teams do not identify experiment selection as a costly problem;
- prospective predictions do not outperform simple heuristics;
- customers will not share appropriately governed outcome data;
- integration costs exceed the value of the decision support; or
- the market remains too small to support the platform without expanding hosts.



## 15. Safety, regulatory, and claims boundaries

The MVP:

- does not validate drug or vaccine efficacy;
- does not establish safety, purity, potency, or regulatory acceptability;
- does not autonomously execute physical experiments;
- does not support environmental release;
- does not produce clinical manufacturing instructions; and
- does not replace qualified scientific, biosafety, quality, or regulatory review.

External laboratory execution must require explicit human approval, access controls, a supported protocol adapter, and complete logging.

## 16. Risks and mitigations


| Risk                                    | Consequence                                      | Mitigation                                              |
| --------------------------------------- | ------------------------------------------------ | ------------------------------------------------------- |
| Sparse comparable data                  | Predictions appear precise but are unreliable    | Evidence grades, wide uncertainty, partner calibration  |
| Simulator exploitation                  | Optimizer finds unrealistic model loopholes      | Invariants, adversarial scenarios, independent critics  |
| LLM hallucination                       | Unsupported biological rationale                 | Tool-grounded claims and typed evidence                 |
| Domain shift                            | Performance fails for new proteins or facilities | Applicability checks and abstention                     |
| Plant-specific variability              | Poor reproducibility                             | Hierarchical batch effects and robustness objectives    |
| Downstream bottlenecks ignored          | High expression does not yield usable product    | End-to-end mass balance                                 |
| Human-therapeutic positioning too early | Regulatory and credibility risk                  | Begin with non-clinical proteins                        |
| Small initial market                    | Limited standalone scale                         | Design architecture for additional hosts                |
| Customer data restrictions              | Weak data flywheel                               | Private calibration, federated options, explicit rights |




## 17. Delivery stages



### Stage A — deterministic demonstrator

- curated component library;
- mechanistic synthetic simulator;
- scripted agents using tools;
- discrete-event virtual facility;
- baseline optimization algorithms; and
- local evidence dashboard.



### Stage B — scientific prototype

- literature-informed parameter priors;
- sensitivity and uncertainty analysis;
- fault-injection benchmark suite;
- imported experimental datasets; and
- retrospective validation reports.



### Stage C — design-partner pilot

- organization-specific component library;
- partner assay import;
- prospective, blinded candidate ranking;
- private model calibration; and
- workflow integration.



### Stage D — execution integration

- approved partner-lab adapter;
- human authorization gates;
- reconciliation of planned and observed actions; and
- continuous model monitoring.



## 18. MVP acceptance criteria

The MVP is complete when a user can:

1. load the versioned hEGF target product profile and define an explicit campaign budget;
2. launch an autonomous multi-round simulation;
3. observe agents propose designs using typed evidence;
4. watch virtual devices execute compiled operations;
5. inspect noisy biological and process results;
6. see the optimizer improve against documented baselines;
7. trace every decision to inputs and evidence;
8. replay the run from a seed and versioned bundle; and
9. export a report that clearly states the simulation’s limitations.



## 19. Open product decisions

- Which public datasets contain sufficiently paired design and outcome information?
- Which hEGF activity assay is sufficiently standardized for future partner validation?
- Should the first external partner be a plant-expression laboratory, protein supplier, or diagnostic-antigen developer?
- Which design standard should be the canonical interchange format?
- Which laboratory protocol abstraction offers the best future hardware portability?
- Which customer data rights are required to train shared models?



## 20. Discovery questions for customer interviews

1. How many construct and process variants are evaluated per program?
2. Where do programs most often fail: expression, quality, recovery, or scale-up?
3. What decision triggers another experimental round?
4. Which measurements are available early enough to change that decision?
5. What is the cost of a failed campaign in materials, facility time, and delay?
6. How are construct, protocol, and assay data linked today?
7. Would the team trust a ranking, an uncertainty estimate, or only a mechanistic explanation?
8. What evidence would be required before using prospective recommendations?
9. Can historical outcomes be shared privately for evaluation?
10. Who owns the budget for this problem?



## 21. References

- Peyret, H. et al. “Plant molecular farming for pharmaceuticals: the state of the art.” *npj Science of Plants* (2026). [https://www.nature.com/articles/s44383-026-00035-7](https://www.nature.com/articles/s44383-026-00035-7)
- U.S. Food and Drug Administration. Elelyso approval summary (2012). [https://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/022458Orig1s000SumR.pdf](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2012/022458Orig1s000SumR.pdf)
- Synthetic Biology Open Language (SBOL). [https://sbolstandard.org/](https://sbolstandard.org/)
- Thomas, D.R. and Walmsley, A.M. “Improved expression of recombinant plant-made hEGF.” *Plant Cell Reports* (2014). [https://doi.org/10.1007/s00299-014-1658-8](https://doi.org/10.1007/s00299-014-1658-8)
- Hanittinan, O. et al. “Expression optimization, purification and in vitro characterization of human epidermal growth factor produced in *Nicotiana benthamiana*.” *Biotechnology Reports* (2020). [https://doi.org/10.1016/j.btre.2020.e00524](https://doi.org/10.1016/j.btre.2020.e00524)
