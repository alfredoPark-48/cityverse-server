"""Interface for movable entities."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.value_objects.position import Position


class IMovable(ABC):
    """Abstract interface for entities that can move on the grid."""

    @abstractmethod
    def move(self) -> None:
        """Execute one movement step."""
        ...

    @abstractmethod
    def get_position(self) -> Position:
        """Return current position."""
        ...

    @abstractmethod
    def set_path(self, path: list[Position]) -> None:
        """Set the path the entity should follow."""
        ...
