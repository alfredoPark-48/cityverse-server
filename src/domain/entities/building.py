"""Building entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.domain.value_objects.position import Position


@dataclass(slots=True)
class Building:
    """Represents a building on the city grid.

    A building can span multiple cells. The `positions` list stores every cell
    it occupies, and `entrance` is the adjacent road/sidewalk cell agents
    target when navigating to this building.
    """

    building_id: int
    positions: list[Position]
    entrance: Optional[Position] = None
    building_type: str = "generic"
    name: str = ""

    @property
    def center(self) -> Position:
        """Return the approximate center of the building."""
        avg_x = sum(p.x for p in self.positions) // len(self.positions)
        avg_y = sum(p.y for p in self.positions) // len(self.positions)
        return Position(avg_x, avg_y)

    def __repr__(self) -> str:
        return f"Building(id={self.building_id}, center={self.center})"
