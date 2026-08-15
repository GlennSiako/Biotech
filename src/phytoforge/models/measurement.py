"""Noisy observation model that protects latent simulator state."""

from __future__ import annotations

import math
import random

from phytoforge.domain import LatentBatchState, Observation, ProcessOutcome


class MeasurementModel:
    """Generate synthetic assays with bias, noise, limits, and QC flags."""

    def observe(
        self,
        latent: LatentBatchState,
        process: ProcessOutcome,
        *,
        rng: random.Random,
        device_drift: float = 0.0,
    ) -> Observation:
        quantity_noise = math.exp(rng.gauss(0.0, 0.055))
        measured_target = max(
            0.0,
            process.recovered_target_mg * quantity_noise * (1.0 + device_drift),
        )
        measured_purity = _clip(
            process.purity_fraction + rng.gauss(0.0, 0.018) + device_drift * 0.15,
            0.0,
            1.0,
        )
        measured_activity = _clip(
            latent.intact_fraction
            * process.activity_retention_fraction
            + rng.gauss(0.0, 0.035),
            0.0,
            1.0,
        )
        measured_stress = _clip(
            latent.stress_fraction + rng.gauss(0.0, 0.025),
            0.0,
            1.0,
        )

        flags: list[str] = []
        if measured_target < 0.05:
            flags.append("below_quantity_limit")
        if measured_purity < 0.70:
            flags.append("low_purity_proxy")
        if measured_activity < 0.60:
            flags.append("low_activity_retention_proxy")
        if measured_stress > 0.25:
            flags.append("high_plant_stress")
        if abs(device_drift) > 0.08:
            flags.append("analytical_drift_suspected")

        return Observation(
            measured_target_mg=measured_target,
            measured_purity_fraction=measured_purity,
            measured_activity_proxy=measured_activity,
            measured_stress_fraction=measured_stress,
            qc_flags=tuple(flags),
        )


def _clip(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))
