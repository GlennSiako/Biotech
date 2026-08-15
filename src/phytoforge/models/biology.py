"""Synthetic S0 biology model for the hEGF executable scaffold."""

from __future__ import annotations

import math
import random

from phytoforge.domain import Design, LatentBatchState


class BiologyModel:
    """Simulate hidden biomass, expression, integrity, and stress.

    Coefficients are deliberately transparent synthetic priors. They reproduce
    selected qualitative literature relationships but are not fitted biological
    parameters.
    """

    _LOCALIZATION = {
        "thomas_2014_like": {
            "cytosol": 0.12,
            "apoplast": 0.35,
            "er": 0.58,
            "vacuole": 1.0,
        },
        "hanittinan_2020_like": {
            "cytosol": 0.18,
            "apoplast": 0.48,
            "er": 1.0,
            "vacuole": 0.68,
        },
    }
    _BASE_CONCENTRATION_MG_G = {
        "thomas_2014_like": 0.05,
        "hanittinan_2020_like": 0.013,
    }
    _HARVEST_OPTIMUM_DAY = {
        "thomas_2014_like": 13,
        "hanittinan_2020_like": 4,
    }

    def simulate(
        self,
        design: Design,
        *,
        plants: int,
        rng: random.Random,
    ) -> LatentBatchState:
        context = design.study_context
        if context not in self._LOCALIZATION:
            raise ValueError(f"unsupported study context: {context}")
        if design.localization not in self._LOCALIZATION[context]:
            raise ValueError(f"unsupported localization: {design.localization}")

        age_biomass_factor = {4: 0.82, 5: 1.0, 6: 1.12}[design.plant_age_weeks]
        age_expression_factor = {4: 0.76, 5: 1.0, 6: 0.72}[design.plant_age_weeks]
        biomass_noise = math.exp(rng.gauss(0.0, 0.07 / math.sqrt(plants)))
        biomass_g = plants * 18.0 * age_biomass_factor * biomass_noise

        intensity_factor = {"low": 0.7, "medium": 1.0, "high": 1.25}[
            design.expression_intensity
        ]
        intensity_stress = {"low": 0.01, "medium": 0.05, "high": 0.16}[
            design.expression_intensity
        ]
        suppressor_stress = 0.08 if design.silencing_suppression else 0.0
        stress = _clip(
            0.06
            + intensity_stress
            + suppressor_stress
            + rng.gauss(0.0, 0.025 / math.sqrt(plants)),
            0.0,
            0.95,
        )

        coding_factor = self._coding_factor(design)
        suppressor_factor = 3.1 if design.silencing_suppression else 1.0
        tag_factor = self._tag_factor(design)
        optimum = self._HARVEST_OPTIMUM_DAY[context]
        harvest_width = 4.0 if context == "thomas_2014_like" else 2.0
        harvest_factor = math.exp(
            -0.5 * ((design.harvest_day - optimum) / harvest_width) ** 2
        )
        replicate_noise = math.exp(rng.gauss(0.0, 0.14 / math.sqrt(plants)))

        concentration_mg_g = (
            self._BASE_CONCENTRATION_MG_G[context]
            * self._LOCALIZATION[context][design.localization]
            * coding_factor
            * suppressor_factor
            * tag_factor
            * intensity_factor
            * age_expression_factor
            * harvest_factor
            * (1.0 - 0.45 * stress)
            * replicate_noise
        )
        target_mass = max(0.0, biomass_g * concentration_mg_g)

        late_penalty = max(0, design.harvest_day - optimum) * 0.018
        intact_fraction = _clip(
            0.94 - 0.28 * stress - late_penalty + rng.gauss(0.0, 0.012),
            0.45,
            0.99,
        )
        host_protein_mass = max(
            0.0,
            biomass_g * 4.0 * (1.0 - 0.18 * stress) * math.exp(rng.gauss(0, 0.03)),
        )
        failure_probability = _clip(
            0.025 + 0.38 * stress + (0.04 if design.harvest_day > optimum else 0.0),
            0.0,
            0.85,
        )

        return LatentBatchState(
            biomass_g=biomass_g,
            target_mass_at_harvest_mg=target_mass,
            intact_fraction=intact_fraction,
            host_protein_mass_mg=host_protein_mass,
            stress_fraction=stress,
            batch_failure_probability=failure_probability,
        )

    @staticmethod
    def _coding_factor(design: Design) -> float:
        if not design.coding_adapted:
            return 1.0
        if design.study_context == "thomas_2014_like":
            if design.localization == "vacuole":
                return 1.34
            if design.localization == "er":
                return 1.0
        return 1.08

    @staticmethod
    def _tag_factor(design: Design) -> float:
        if design.study_context != "hanittinan_2020_like":
            return 1.0
        if design.tag_position == "c_terminal":
            return 1.12
        if design.tag_position == "n_terminal":
            return 0.72
        return 0.88


def _clip(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))

