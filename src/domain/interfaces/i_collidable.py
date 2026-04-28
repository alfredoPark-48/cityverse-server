"""Interface for collidable entities."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.value_objects.position import Position


class ICollidable(ABC):
    """Abstract interface for entities that can collide."""

    @abstractmethod
    def check_collision(self, other_position: Position) -> bool:
        """Check if this entity collides with the given position."""
        ...
