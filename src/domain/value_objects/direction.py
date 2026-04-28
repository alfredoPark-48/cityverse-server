"""Direction value object for agent movement."""

from __future__ import annotations

from enum import Enum

from src.domain.value_objects.position import Position


class Direction(Enum):
    """Cardinal directions with their (dx, dy) deltas.

    Grid convention: y increases downward, x increases rightward.
    """

    N = "N"
    E = "E"
    S = "S"
    W = "W"

    def delta(self) -> Position:
        """Return the (dx, dy) offset for this direction."""
        return _DIRECTION_DELTAS[self]

    @staticmethod
    def from_char(char: str) -> Direction:
        """Convert a grid character to a Direction."""
        return _CHAR_TO_DIRECTION[char]


_DIRECTION_DELTAS: dict[Direction, Position] = {
    Direction.N: Position(0, -1),
    Direction.E: Position(1, 0),
    Direction.S: Position(0, 1),
    Direction.W: Position(-1, 0),
}

_CHAR_TO_DIRECTION: dict[str, Direction] = {
    "^": Direction.N,
    ">": Direction.E,
    "v": Direction.S,
    "<": Direction.W,
    "U": Direction.N,
    "D": Direction.S,
    "R": Direction.E,
    "L": Direction.W,
}
