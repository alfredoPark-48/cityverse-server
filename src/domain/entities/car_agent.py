"""Car agent entity."""

from __future__ import annotations

import random
from typing import Optional

import mesa

from src.domain.entities.agent import BaseAgent
from src.domain.value_objects.position import Position
from src.shared.constants import CellType


class CarAgent(BaseAgent):
    """A car that drives along roads, parks at buildings, then picks a new destination."""

    PARKED_DURATION_MIN: int = 5
    PARKED_DURATION_MAX: int = 10

    def __init__(
        self,
        unique_id: int,
        model: mesa.Model,
        position: Position,
    ) -> None:
        super().__init__(unique_id, model, position)
        self.parked: bool = False
        self.parked_ticks: int = 0
        self.parked_duration: int = 0
        self.waiting: bool = False
        self._assign_destination()

    def _assign_destination(self) -> None:
        """Pick a random building entrance as destination."""
        buildings_with_entrances = [
            b for b in self.model.buildings if b.entrance is not None
        ]
        if not buildings_with_entrances:
            return

        target = random.choice(buildings_with_entrances)
        self.destination = target.entrance
        self._compute_path()

    def _compute_path(self) -> None:
        """Compute road path from current position to destination."""
        if self.destination is None:
            return

        from src.application.services.pathfinding_service import PathfindingService

        pf: PathfindingService = self.model.pathfinder
        path = pf.find_road_path(self.position, self.destination)
        if path:
            self.set_path(path)
        else:
            # Fallback: if no path found, try a different destination
            self.destination = None

    def step(self) -> None:
        """Execute one simulation step for this car."""
        if self.parked:
            self._handle_parking()
            return

        if self._should_stop():
            self.waiting = True
            return

        self.waiting = False
        moved = self._follow_path()

        if not moved and self.has_arrived:
            self._start_parking()

    def _handle_parking(self) -> None:
        """Handle parked state: stay for N ticks, then pick new destination."""
        self.parked_ticks += 1
        if self.parked_ticks >= self.parked_duration:
            self.parked = False
            self.parked_ticks = 0
            self.has_arrived = False
            self._assign_destination()

    def _start_parking(self) -> None:
        """Begin parking at current location."""
        self.parked = True
        self.parked_ticks = 0
        self.parked_duration = random.randint(
            self.PARKED_DURATION_MIN, self.PARKED_DURATION_MAX
        )

    def _should_stop(self) -> bool:
        """Check if the car should stop (red light, yielding, or pedestrian ahead)."""
        if not self.path or self._path_index >= len(self.path) - 1:
            return False

        next_pos = self.path[self._path_index + 1]

        # Check traffic light
        light = self.model.get_traffic_light_at(next_pos.x, next_pos.y)
        if light and light.is_red:
            return True

        # Check for pedestrians on crosswalk ahead (scan 2 cells)
        for look_ahead in range(1, min(3, len(self.path) - self._path_index)):
            future_pos = self.path[self._path_index + look_ahead]
            cell = self.model.get_cell(future_pos.x, future_pos.y)
            if cell and cell.is_crosswalk:
                if self._pedestrian_on_crosswalk(future_pos):
                    return True

        # Check roundabout yield (cars from left within 3 cells)
        next_cell = self.model.get_cell(next_pos.x, next_pos.y)
        if next_cell and next_cell.cell_type == CellType.ROUNDABOUT:
            if self._should_yield_at_roundabout(next_pos):
                return True

        return False

    def _pedestrian_on_crosswalk(self, pos: Position) -> bool:
        """Check if any pedestrian is on the given crosswalk position."""
        for agent in self.model.schedule.agents:
            if (
                agent is not self
                and hasattr(agent, "position")
                and agent.position == pos
                and agent.__class__.__name__ == "PedestrianAgent"
            ):
                return True
        return False

    def _should_yield_at_roundabout(self, entry_pos: Position) -> bool:
        """Yield to cars coming from the left within 3 cells in the roundabout."""
        for agent in self.model.schedule.agents:
            if (
                agent is not self
                and isinstance(agent, CarAgent)
                and not agent.parked
            ):
                dist = entry_pos.manhattan_distance(agent.position)
                if dist <= 3:
                    cell = self.model.get_cell(agent.position.x, agent.position.y)
                    if cell and cell.cell_type == CellType.ROUNDABOUT:
                        return True
        return False

    def to_dict(self) -> dict:
        """Serialize car state for API response."""
        data = super().to_dict()
        data.update({
            "parked": self.parked,
            "waiting": self.waiting,
            "destination": {
                "x": self.destination.x,
                "y": self.destination.y,
            } if self.destination else None,
        })
        return data
