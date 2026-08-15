"""Transparent baseline selectors for autonomous campaign execution."""

from __future__ import annotations

import math
import random
import statistics

from phytoforge.domain import Design, ExperimentResult


class ExperimentSelector:
    """Select untested designs using random or uncertainty-aware arm scores."""

    def __init__(self, strategy: str = "adaptive") -> None:
        if strategy not in {"adaptive", "random"}:
            raise ValueError(f"unsupported selector strategy: {strategy}")
        self.strategy = strategy

    def select(
        self,
        candidates: tuple[Design, ...],
        history: list[ExperimentResult],
        *,
        batch_size: int,
        rng: random.Random,
    ) -> tuple[list[Design], dict[str, object]]:
        tested = {result.design.design_id for result in history}
        remaining = [design for design in candidates if design.design_id not in tested]
        if not remaining:
            return [], {
                "strategy": self.strategy,
                "reason": "candidate_library_exhausted",
                "selected_design_ids": [],
            }

        if self.strategy == "random" or not history:
            rng.shuffle(remaining)
            selected = remaining[:batch_size]
            reason = "seeded_random_coverage" if not history else "seeded_random_baseline"
        else:
            scored = [
                (self._adaptive_score(design, history), rng.random(), design)
                for design in remaining
            ]
            scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
            selected = [item[2] for item in scored[:batch_size]]
            reason = "context_localization_ucb"

        return selected, {
            "strategy": self.strategy,
            "reason": reason,
            "selected_design_ids": [design.design_id for design in selected],
            "history_size": len(history),
        }

    @staticmethod
    def _adaptive_score(
        design: Design,
        history: list[ExperimentResult],
    ) -> float:
        matching = [
            result.utility
            for result in history
            if result.design.study_context == design.study_context
            and result.design.localization == design.localization
        ]
        all_utilities = [result.utility for result in history]
        global_mean = statistics.fmean(all_utilities)
        global_spread = statistics.pstdev(all_utilities) if len(all_utilities) > 1 else 1.0

        if matching:
            predicted = statistics.fmean(matching)
            observations = len(matching)
        else:
            predicted = global_mean
            observations = 0

        exploration = max(1.0, global_spread) / math.sqrt(observations + 1)
        return predicted + 0.75 * exploration

