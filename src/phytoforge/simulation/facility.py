"""Small deterministic discrete-event facility for the executable scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from phytoforge.domain import Design, FacilityEvent


@dataclass(frozen=True, slots=True)
class _OperationSpec:
    operation: str
    device: str
    duration_hours: float
    cost: float


class FacilitySimulator:
    """Schedule abstract operations on capacity-constrained virtual devices."""

    _CAPACITY = {
        "growth_chamber": 4,
        "expression_station": 1,
        "harvest_station": 1,
        "extraction_workcell": 1,
        "purification_skid": 1,
        "analytical_station": 2,
    }

    def __init__(self) -> None:
        self._availability = {
            device: [0.0] * capacity for device, capacity in self._CAPACITY.items()
        }

    @property
    def elapsed_hours(self) -> float:
        return max(
            (available for slots in self._availability.values() for available in slots),
            default=0.0,
        )

    def schedule(self, design: Design, *, earliest_start: float) -> tuple[FacilityEvent, ...]:
        """Compile and schedule one design's abstract production workflow."""

        operations = (
            _OperationSpec("plant_conditioning", "growth_chamber", 48.0, 95.0),
            _OperationSpec("expression_introduction", "expression_station", 1.5, 160.0),
            _OperationSpec(
                "post_introduction_growth",
                "growth_chamber",
                design.harvest_day * 24.0,
                design.harvest_day * 18.0,
            ),
            _OperationSpec("harvest", "harvest_station", 1.0, 75.0),
            _OperationSpec("extract_and_clarify", "extraction_workcell", 5.5, 260.0),
            _OperationSpec(
                "affinity_capture" if design.tag_position != "none" else "generic_capture",
                "purification_skid",
                6.0 if design.tag_position != "none" else 8.0,
                420.0 if design.tag_position != "none" else 300.0,
            ),
            _OperationSpec("analytical_panel", "analytical_station", 3.0, 340.0),
        )

        events: list[FacilityEvent] = []
        ready = earliest_start
        for operation in operations:
            slot_index, slot_ready = min(
                enumerate(self._availability[operation.device]),
                key=lambda item: item[1],
            )
            start = max(ready, slot_ready)
            end = start + operation.duration_hours
            self._availability[operation.device][slot_index] = end
            events.append(
                FacilityEvent(
                    operation=operation.operation,
                    device=operation.device,
                    start_hour=start,
                    end_hour=end,
                    cost=operation.cost,
                )
            )
            ready = end
        return tuple(events)
