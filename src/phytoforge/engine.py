"""Autonomous design–simulate–observe–select campaign engine."""

from __future__ import annotations

import random

from phytoforge.benchmarks.hegf import (
    BENCHMARK_ID,
    CALIBRATION_TIER,
    design_library,
    evidence_for,
)
from phytoforge.domain import (
    CampaignConfig,
    ExperimentResult,
    FacilityEvent,
    Observation,
    ProcessOutcome,
    RunReport,
    SelectionObservation,
)
from phytoforge.models import BiologyModel, MeasurementModel, ProcessModel
from phytoforge.optimizer import ExperimentSelector
from phytoforge.simulation import FacilitySimulator


class SimulationEngine:
    """Execute the first runnable PhytoForge benchmark."""

    def __init__(self) -> None:
        self._biology = BiologyModel()
        self._process = ProcessModel()
        self._measurement = MeasurementModel()

    def run(self, config: CampaignConfig | None = None) -> RunReport:
        config = config or CampaignConfig()
        config.validate()

        master_rng = random.Random(config.seed)
        facility = FacilitySimulator()
        selector = ExperimentSelector(config.selector)
        candidates = design_library()
        report = RunReport(
            benchmark_id=BENCHMARK_ID,
            calibration_tier=CALIBRATION_TIER,
            config=config,
            warnings=[
                "S0 synthetic simulator: outputs are not wet-lab predictions.",
                "Activity values are research proxies, not potency or efficacy.",
            ],
        )

        for round_index in range(config.rounds):
            selected, decision = selector.select(
                candidates,
                [
                    SelectionObservation(
                        design=result.design,
                        utility=result.utility,
                    )
                    for result in report.results
                ],
                batch_size=config.batch_size,
                rng=master_rng,
            )
            decision["round_index"] = round_index
            report.decisions.append(decision)
            if not selected:
                report.warnings.append("Campaign stopped: candidate library exhausted.")
                break

            round_start = facility.elapsed_hours
            for design in selected:
                experiment_rng = random.Random(master_rng.randrange(0, 2**63))
                latent = self._biology.simulate(
                    design,
                    plants=config.plants_per_design,
                    rng=experiment_rng,
                )
                process = self._process.simulate(
                    design,
                    latent,
                    rng=experiment_rng,
                )
                events = facility.schedule(design, earliest_start=round_start)
                observation = self._measurement.observe(
                    latent,
                    process,
                    rng=experiment_rng,
                )
                utility = _observed_utility(observation, process, events)
                report.results.append(
                    ExperimentResult(
                        round_index=round_index,
                        design=design,
                        latent=latent,
                        process=process,
                        observation=observation,
                        utility=utility,
                        events=events,
                        evidence_ids=evidence_for(design),
                    )
                )

        return report


def _observed_utility(
    observation: Observation,
    process: ProcessOutcome,
    events: tuple[FacilityEvent, ...],
) -> float:
    """Compute visible utility without consulting latent biological state."""

    facility_cost = sum(event.cost for event in events)
    elapsed_hours = events[-1].end_hour - events[0].start_hour
    quality_adjusted_mass = (
        observation.measured_target_mg * observation.measured_activity_proxy
    )
    qc_penalty = 1.5 * len(observation.qc_flags)
    return (
        20.0 * quality_adjusted_mass
        + 5.0 * observation.measured_purity_fraction
        - (process.process_cost + facility_cost) / 500.0
        - elapsed_hours / 500.0
        - qc_penalty
    )
