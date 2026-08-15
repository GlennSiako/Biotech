"""End-to-end synthetic recovery and purification model."""

from __future__ import annotations

import math
import random

from phytoforge.domain import Design, LatentBatchState, ProcessOutcome


class ProcessModel:
    """Apply bounded extraction and purification mass balances."""

    _EXTRACTION_RECOVERY = {
        "cytosol": 0.58,
        "apoplast": 0.72,
        "er": 0.64,
        "vacuole": 0.54,
    }

    def simulate(
        self,
        design: Design,
        latent: LatentBatchState,
        *,
        rng: random.Random,
    ) -> ProcessOutcome:
        extraction = _bounded_efficiency(
            self._EXTRACTION_RECOVERY[design.localization],
            rng,
            spread=0.035,
        )
        clarification = _bounded_efficiency(0.91, rng, spread=0.018)

        if design.tag_position == "c_terminal":
            capture = _bounded_efficiency(0.78, rng, spread=0.035)
            impurity_retention = _bounded_efficiency(0.0025, rng, spread=0.001)
            capture_cost = 720.0
            capture_hours = 6.0
        elif design.tag_position == "n_terminal":
            capture = _bounded_efficiency(0.64, rng, spread=0.045)
            impurity_retention = _bounded_efficiency(0.0045, rng, spread=0.0015)
            capture_cost = 720.0
            capture_hours = 6.0
        else:
            capture = _bounded_efficiency(0.48, rng, spread=0.05)
            impurity_retention = _bounded_efficiency(0.018, rng, spread=0.004)
            capture_cost = 430.0
            capture_hours = 8.0

        recovered_target = (
            latent.target_mass_at_harvest_mg * extraction * clarification * capture
        )
        recovered_target = min(latent.target_mass_at_harvest_mg, recovered_target)
        recovered_intact = recovered_target * latent.intact_fraction

        carried_host_protein = (
            latent.host_protein_mass_mg
            * extraction
            * clarification
            * impurity_retention
        )
        purity = recovered_target / max(
            1e-12, recovered_target + carried_host_protein
        )
        activity_retention = _clip(
            0.96
            - 0.12 * latent.stress_fraction
            - 0.04 * (1.0 - capture)
            + rng.gauss(0.0, 0.012),
            0.0,
            1.0,
        )

        variable_cost = 2.1 * math.sqrt(max(0.0, latent.biomass_g))
        process_cost = 180.0 + capture_cost + variable_cost
        process_hours = 5.5 + capture_hours

        return ProcessOutcome(
            recovered_target_mg=recovered_target,
            recovered_intact_mg=recovered_intact,
            purity_fraction=_clip(purity, 0.0, 1.0),
            activity_retention_fraction=activity_retention,
            process_cost=process_cost,
            process_hours=process_hours,
        )


def _bounded_efficiency(
    mean: float,
    rng: random.Random,
    *,
    spread: float,
) -> float:
    return _clip(rng.gauss(mean, spread), 0.0001, 0.9999)


def _clip(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))

