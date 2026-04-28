"""TrafficLight entity with cycling state."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.value_objects.direction import Direction
from src.domain.value_objects.position import Position
from src.shared.constants import TrafficLightState


# Cycle durations in ticks
GREEN_DURATION: int = 40
YELLOW_DURATION: int = 10
RED_DURATION: int = 50

_CYCLE_ORDER: list[tuple[TrafficLightState, int]] = [
    (TrafficLightState.GREEN, GREEN_DURATION),
    (TrafficLightState.YELLOW, YELLOW_DURATION),
    (TrafficLightState.RED, RED_DURATION),
]


@dataclass(slots=True)
class TrafficLight:
    """A traffic light that cycles GREEN → YELLOW → RED."""

    light_id: int
    position: Position
    direction: Direction
    state: TrafficLightState = TrafficLightState.RED
    timer: int = 0
    _cycle_index: int = field(default=2, repr=False)  # Start at RED

    def update(self) -> None:
        """Advance the traffic light by one tick."""
        self.timer += 1
        _, duration = _CYCLE_ORDER[self._cycle_index]

        if self.timer >= duration:
            self.timer = 0
            self._cycle_index = (self._cycle_index + 1) % len(_CYCLE_ORDER)
            self.state, _ = _CYCLE_ORDER[self._cycle_index]

    @property
    def is_green(self) -> bool:
        return self.state == TrafficLightState.GREEN

    @property
    def is_red(self) -> bool:
        return self.state == TrafficLightState.RED

    @property
    def is_yellow(self) -> bool:
        return self.state == TrafficLightState.YELLOW

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "id": self.light_id,
            "x": self.position.x,
            "y": self.position.y,
            "direction": self.direction.value,
            "state": self.state.value,
            "timer": self.timer,
        }

    def __repr__(self) -> str:
        return (
            f"TrafficLight(id={self.light_id}, pos={self.position}, "
            f"dir={self.direction.value}, state={self.state.value})"
        )
