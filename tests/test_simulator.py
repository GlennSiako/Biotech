"""Executable checks for the PhytoForge S0 simulator."""

from __future__ import annotations

import random
import unittest

from phytoforge.benchmarks.hegf import design_library
from phytoforge.domain import CampaignConfig
from phytoforge.engine import SimulationEngine
from phytoforge.models import BiologyModel


class SimulationEngineTests(unittest.TestCase):
    def test_seeded_campaign_replays_exactly(self) -> None:
        config = CampaignConfig(seed=19, rounds=3, batch_size=3)

        first = SimulationEngine().run(config).to_dict(include_latent=True)
        second = SimulationEngine().run(config).to_dict(include_latent=True)

        self.assertEqual(first, second)

    def test_mass_balance_and_fraction_invariants(self) -> None:
        report = SimulationEngine().run(
            CampaignConfig(seed=23, rounds=4, batch_size=4)
        )

        self.assertGreater(len(report.results), 0)
        for result in report.results:
            self.assertGreaterEqual(result.latent.target_mass_at_harvest_mg, 0.0)
            self.assertGreaterEqual(result.process.recovered_target_mg, 0.0)
            self.assertLessEqual(
                result.process.recovered_target_mg,
                result.latent.target_mass_at_harvest_mg,
            )
            self.assertLessEqual(
                result.process.recovered_intact_mg,
                result.process.recovered_target_mg,
            )
            self.assertGreaterEqual(result.process.purity_fraction, 0.0)
            self.assertLessEqual(result.process.purity_fraction, 1.0)
            self.assertGreaterEqual(
                result.process.activity_retention_fraction,
                0.0,
            )
            self.assertLessEqual(
                result.process.activity_retention_fraction,
                1.0,
            )

    def test_selector_does_not_repeat_designs(self) -> None:
        report = SimulationEngine().run(
            CampaignConfig(seed=31, rounds=4, batch_size=3)
        )
        design_ids = [result.design.design_id for result in report.results]

        self.assertEqual(len(design_ids), len(set(design_ids)))

    def test_study_contexts_have_distinct_localization_order(self) -> None:
        designs = {design.design_id: design for design in design_library()}
        model = BiologyModel()

        tw_apoplast = model.simulate(
            designs["tw-apoplast-base"],
            plants=100,
            rng=random.Random(7),
        )
        tw_vacuole = model.simulate(
            designs["tw-vacuole-base"],
            plants=100,
            rng=random.Random(7),
        )
        h20_apoplast = model.simulate(
            designs["h20-apoplast-c-tag"],
            plants=100,
            rng=random.Random(7),
        )
        h20_er = model.simulate(
            designs["h20-er-c-tag"],
            plants=100,
            rng=random.Random(7),
        )

        self.assertGreater(
            tw_vacuole.target_mass_at_harvest_mg,
            tw_apoplast.target_mass_at_harvest_mg,
        )
        self.assertGreater(
            h20_er.target_mass_at_harvest_mg,
            h20_apoplast.target_mass_at_harvest_mg,
        )

    def test_public_report_hides_latent_state(self) -> None:
        report = SimulationEngine().run(
            CampaignConfig(seed=11, rounds=1, batch_size=1)
        )

        public = report.to_dict()
        developer = report.to_dict(include_latent=True)

        self.assertNotIn("latent", public["results"][0])
        self.assertIn("latent", developer["results"][0])


if __name__ == "__main__":
    unittest.main()

