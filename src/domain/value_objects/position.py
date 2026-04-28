"""Position value object for grid coordinates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable 2D grid position."""

    x: int
    y: int

    def manhattan_distance(self, other: Position) -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

    def __add__(self, other: Position) -> Position:
        return Position(self.x + other.x, self.y + other.y)

    def __repr__(self) -> str:
        return f"Position({self.x}, {self.y})"
