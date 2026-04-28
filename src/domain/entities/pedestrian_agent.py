"""Pedestrian agent entity."""

from __future__ import annotations

import random
from typing import Optional

import mesa

from src.domain.entities.agent import BaseAgent
from src.domain.value_objects.position import Position
from src.shared.constants import CellType


class PedestrianAgent(BaseAgent):
    """A pedestrian that walks along sidewalks and crosses at crosswalks."""

    RESPAWN_DELAY: int = 5

    def __init__(
        self,
        unique_id: int,
        model: mesa.Model,
        position: Position,
    ) -> None:
        super().__init__(unique_id, model, position)
        self.crossing: bool = False
        self.waiting: bool = False
        self.despawned: bool = False
        self._respawn_timer: int = 0
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
        """Compute sidewalk path from current position to destination."""
        if self.destination is None:
            return

        from src.application.services.pathfinding_service import PathfindingService

        pf: PathfindingService = self.model.pathfinder
        path = pf.find_sidewalk_path(self.position, self.destination)
        if path:
            self.set_path(path)
        else:
            self.destination = None

    def step(self) -> None:
        """Execute one simulation step for this pedestrian."""
        if self.despawned:
            self._handle_respawn()
            return

        if self._should_wait():
            self.waiting = True
            return

        self.waiting = False

        # Check if we're crossing
        cell = self.model.get_cell(self.position.x, self.position.y)
        self.crossing = cell is not None and cell.is_crosswalk

        moved = self._follow_path()

        if not moved and self.has_arrived:
            self._despawn()

    def _handle_respawn(self) -> None:
        """Handle despawned state: wait, then respawn at a spawn point."""
        self._respawn_timer += 1
        if self._respawn_timer >= self.RESPAWN_DELAY:
            self._respawn()

    def _despawn(self) -> None:
        """Mark pedestrian as arrived / despawned."""
        self.despawned = True
        self._respawn_timer = 0

    def _respawn(self) -> None:
        """Respawn at a random pedestrian spawn point with new destination."""
        if self.model.ped_spawns:
            spawn = random.choice(self.model.ped_spawns)
            self.position = spawn
            self.despawned = False
            self.has_arrived = False
            self._respawn_timer = 0
            self._assign_destination()

    def _should_wait(self) -> bool:
        """Check if pedestrian should wait (traffic light, approaching cars)."""
        if not self.path or self._path_index >= len(self.path) - 1:
            return False

        next_pos = self.path[self._path_index + 1]
        next_cell = self.model.get_cell(next_pos.x, next_pos.y)

        if next_cell and next_cell.is_crosswalk:
            # Check traffic light at crosswalk
            light = self.model.get_traffic_light_at(next_pos.x, next_pos.y)
            if light and not light.is_green:
                return True

            # Check approaching cars within 3 cells
            if self._cars_approaching(next_pos):
                return True

        return False

    def _cars_approaching(self, crosswalk_pos: Position) -> bool:
        """Check if any cars are approaching the crosswalk within 3 cells."""
        for agent in self.model.schedule.agents:
            if (
                agent is not self
                and agent.__class__.__name__ == "CarAgent"
                and not getattr(agent, "parked", False)
            ):
                dist = crosswalk_pos.manhattan_distance(agent.position)
                if dist <= 3 and not getattr(agent, "waiting", False):
                    return True
        return False

    def to_dict(self) -> dict:
        """Serialize pedestrian state for API response."""
        data = super().to_dict()
        data.update({
            "crossing": self.crossing,
            "waiting": self.waiting,
            "despawned": self.despawned,
            "destination": {
                "x": self.destination.x,
                "y": self.destination.y,
            } if self.destination else None,
        })
        return data
