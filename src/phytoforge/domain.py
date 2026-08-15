"""Versioned domain objects shared by simulator components."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True, slots=True)
class Design:
    """A bounded hEGF expression and process design."""

    design_id: str
    study_context: str
    localization: str
    coding_adapted: bool
    silencing_suppression: bool
    tag_position: str
    expression_intensity: str
    plant_age_weeks: int
    harvest_day: int


@dataclass(frozen=True, slots=True)
class CampaignConfig:
    """Runtime configuration for one autonomous campaign."""

    seed: int = 42
    rounds: int = 4
    batch_size: int = 4
    plants_per_design: int = 6
    selector: str = "adaptive"

    def validate(self) -> None:
        if self.rounds < 1:
            raise ValueError("rounds must be at least 1")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1")
        if self.plants_per_design < 1:
            raise ValueError("plants_per_design must be at least 1")
        if self.selector not in {"adaptive", "random"}:
            raise ValueError("selector must be 'adaptive' or 'random'")


@dataclass(frozen=True, slots=True)
class LatentBatchState:
    """Hidden biological state. Agents must never receive this object."""

    biomass_g: float
    target_mass_at_harvest_mg: float
    intact_fraction: float
    host_protein_mass_mg: float
    stress_fraction: float
    batch_failure_probability: float


@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    """True post-process state before measurement error."""

    recovered_target_mg: float
    recovered_intact_mg: float
    purity_fraction: float
    activity_retention_fraction: float
    process_cost: float
    process_hours: float


@dataclass(frozen=True, slots=True)
class Observation:
    """Noisy values available to the autonomous decision system."""

    measured_target_mg: float
    measured_purity_fraction: float
    measured_activity_proxy: float
    measured_stress_fraction: float
    qc_flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FacilityEvent:
    """One operation on a virtual facility resource."""

    operation: str
    device: str
    start_hour: float
    end_hour: float
    cost: float
    status: str = "completed"


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Complete result retained by the engine and reporter."""

    round_index: int
    design: Design
    latent: LatentBatchState
    process: ProcessOutcome
    observation: Observation
    utility: float
    events: tuple[FacilityEvent, ...]
    evidence_ids: tuple[str, ...]


@dataclass(slots=True)
class RunReport:
    """Serializable campaign report."""

    benchmark_id: str
    calibration_tier: str
    config: CampaignConfig
    results: list[ExperimentResult] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    @property
    def best_result(self) -> ExperimentResult | None:
        return max(self.results, key=lambda result: result.utility, default=None)

    def to_dict(self, *, include_latent: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if not include_latent:
            for result in payload["results"]:
                result.pop("latent", None)
        best = self.best_result
        payload["best_design_id"] = best.design.design_id if best else None
        payload["best_utility"] = round(best.utility, 6) if best else None
        return payload

