"""A* pathfinding service for road and sidewalk navigation."""

from __future__ import annotations

import heapq
from functools import lru_cache
from typing import Optional

from src.domain.value_objects.grid_cell import GridCell
from src.domain.value_objects.position import Position
from src.shared.constants import CellType, ROAD_DIRECTION_CHARS


class PathfindingService:
    """Provides A* pathfinding for cars (roads) and pedestrians (sidewalks)."""

    def __init__(self, grid: list[list[GridCell]], width: int, height: int) -> None:
        self._grid = grid
        self._width = width
        self._height = height
        self._road_graph = self._build_road_graph()
        self._sidewalk_graph = self._build_sidewalk_graph()

    def _build_road_graph(self) -> dict[Position, list[Position]]:
        """Build adjacency list for drivable cells, respecting road direction."""
        graph: dict[Position, list[Position]] = {}

        for y in range(self._height):
            for x in range(self._width):
                cell = self._grid[y][x]
                if not cell.is_drivable and not cell.is_crosswalk:
                    continue

                pos = cell.position
                neighbors: list[Position] = []

                # For directional road cells, only allow movement in the road direction
                if cell.raw_char in ROAD_DIRECTION_CHARS:
                    direction_deltas = {
                        "v": (0, 1),
                        "^": (0, -1),
                        ">": (1, 0),
                        "<": (-1, 0),
                    }
                    dx, dy = direction_deltas[cell.raw_char]
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self._width and 0 <= ny < self._height:
                        neighbor = self._grid[ny][nx]
                        if neighbor.is_drivable or neighbor.is_crosswalk:
                            neighbors.append(Position(nx, ny))
                else:
                    # For roundabout, parking, crosswalk: allow all 4 directions
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self._width and 0 <= ny < self._height:
                            neighbor = self._grid[ny][nx]
                            if neighbor.is_drivable or neighbor.is_crosswalk:
                                neighbors.append(Position(nx, ny))

                graph[pos] = neighbors

        return graph

    def _build_sidewalk_graph(self) -> dict[Position, list[Position]]:
        """Build adjacency list for walkable cells (sidewalks + crosswalks)."""
        graph: dict[Position, list[Position]] = {}

        for y in range(self._height):
            for x in range(self._width):
                cell = self._grid[y][x]
                if not cell.is_walkable:
                    continue

                pos = cell.position
                neighbors: list[Position] = []

                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self._width and 0 <= ny < self._height:
                        neighbor = self._grid[ny][nx]
                        if neighbor.is_walkable:
                            neighbors.append(Position(nx, ny))

                graph[pos] = neighbors

        return graph

    @staticmethod
    def _heuristic(a: Position, b: Position) -> int:
        """Manhattan distance heuristic for A*."""
        return a.manhattan_distance(b)

    def _a_star(
        self,
        start: Position,
        end: Position,
        graph: dict[Position, list[Position]],
    ) -> list[Position]:
        """A* search returning a path from start to end, or empty list if unreachable."""
        if start not in graph or end not in graph:
            return []

        # Priority queue: (f_score, counter, position)
        counter = 0
        open_set: list[tuple[int, int, Position]] = [(0, counter, start)]
        came_from: dict[Position, Position] = {}
        g_score: dict[Position, int] = {start: 0}

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == end:
                return self._reconstruct_path(came_from, current)

            for neighbor in graph.get(current, []):
                tentative_g = g_score[current] + 1

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, end)
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor))

        return []  # No path found

    @staticmethod
    def _reconstruct_path(
        came_from: dict[Position, Position],
        current: Position,
    ) -> list[Position]:
        """Reconstruct path from A* came_from map."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def find_road_path(
        self, start: Position, end: Position
    ) -> list[Position]:
        """Find a path along roads from start to end."""
        return self._a_star(start, end, self._road_graph)

    def find_sidewalk_path(
        self, start: Position, end: Position
    ) -> list[Position]:
        """Find a path along sidewalks/crosswalks from start to end."""
        return self._a_star(start, end, self._sidewalk_graph)

    def is_road_reachable(self, start: Position, end: Position) -> bool:
        """Check if a road path exists without computing full path."""
        return len(self.find_road_path(start, end)) > 0

    def is_sidewalk_reachable(self, start: Position, end: Position) -> bool:
        """Check if a sidewalk path exists without computing full path."""
        return len(self.find_sidewalk_path(start, end)) > 0
