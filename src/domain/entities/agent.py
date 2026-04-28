"""Base agent entity for the city simulation."""

from __future__ import annotations

from abc import abstractmethod
from typing import Optional

import mesa

from src.domain.interfaces.i_movable import IMovable
from src.domain.value_objects.position import Position


class BaseAgent(mesa.Agent, IMovable):
    """Abstract base agent with common movement logic.

    All agents have a position, a path to follow, and a destination.
    """

    def __init__(
        self,
        unique_id: int,
        model: mesa.Model,
        position: Position,
    ) -> None:
        super().__init__(unique_id, model)
        self.position: Position = position
        self.path: list[Position] = []
        self.destination: Optional[Position] = None
        self.has_arrived: bool = False
        self._path_index: int = 0

    def get_position(self) -> Position:
        """Return current position."""
        return self.position

    def set_path(self, path: list[Position]) -> None:
        """Set the path the agent should follow."""
        self.path = path
        self._path_index = 0
        self.has_arrived = False

    def _follow_path(self) -> bool:
        """Advance one step along the current path.

        Returns True if the agent moved, False if already at end.
        """
        if not self.path or self._path_index >= len(self.path) - 1:
            self.has_arrived = True
            return False

        self._path_index += 1
        self.position = self.path[self._path_index]
        return True

    def move(self) -> None:
        """Default move implementation: follow the path."""
        self._follow_path()

    @abstractmethod
    def step(self) -> None:
        """Mesa step — subclasses implement specific behavior."""
        ...

    def to_dict(self) -> dict:
        """Serialize agent state for API response."""
        return {
            "id": self.unique_id,
            "x": self.position.x,
            "y": self.position.y,
            "type": self.__class__.__name__,
            "has_arrived": self.has_arrived,
        }
