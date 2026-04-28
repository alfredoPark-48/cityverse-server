"""GridCell value object describing a single cell in the city grid."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.position import Position
from src.shared.constants import CellType


@dataclass(frozen=True, slots=True)
class GridCell:
    """Immutable representation of a single grid cell."""

    position: Position
    cell_type: CellType
    raw_char: str

    @property
    def is_drivable(self) -> bool:
        """Whether cars can drive on this cell."""
        return self.cell_type in {
            CellType.ROAD,
            CellType.ROUNDABOUT,
            CellType.PARKING,
        }

    @property
    def is_walkable(self) -> bool:
        """Whether pedestrians can walk on this cell."""
        return self.cell_type in {
            CellType.SIDEWALK,
            CellType.CROSSWALK,
        }

    @property
    def is_crosswalk(self) -> bool:
        """Whether this cell is a crosswalk (shared by cars and peds)."""
        return self.cell_type == CellType.CROSSWALK

    def __repr__(self) -> str:
        return f"GridCell({self.position}, {self.cell_type.value})"
