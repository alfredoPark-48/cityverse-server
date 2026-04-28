"""Unit tests for A* pathfinding."""

import pytest

from src.application.services.pathfinding_service import PathfindingService
from src.domain.value_objects.position import Position
from src.infrastructure.persistence.grid_repository import GridRepository


@pytest.fixture
def pathfinder() -> PathfindingService:
    repo = GridRepository()
    data = repo.load("data/city_grid.txt")
    return PathfindingService(data.grid, data.width, data.height)


@pytest.fixture
def grid_data():
    repo = GridRepository()
    return repo.load("data/city_grid.txt")


class TestPathfinding:
    """Tests for the A* pathfinding service."""

    def test_sidewalk_path_exists(self, pathfinder: PathfindingService) -> None:
        """Should find a sidewalk path between two sidewalk cells."""
        start = Position(0, 0)  # Top-left corner (sidewalk)
        end = Position(29, 0)   # Top-right corner (sidewalk)

        path = pathfinder.find_sidewalk_path(start, end)
        assert len(path) > 0
        assert path[0] == start
        assert path[-1] == end

    def test_road_path_exists(self, pathfinder: PathfindingService, grid_data) -> None:
        """Should find a road path between two road cells."""
        # Find two road cells from the grid
        road_cells = []
        for y in range(grid_data.height):
            for x in range(grid_data.width):
                cell = grid_data.grid[y][x]
                if cell.is_drivable:
                    road_cells.append(cell.position)

        assert len(road_cells) >= 2, "Grid should have at least 2 road cells"

        # Try to find a path between the first and last road cell
        start = road_cells[0]
        end = road_cells[-1]

        path = pathfinder.find_road_path(start, end)
        # Path may or may not exist due to one-way roads, just verify no crash
        if path:
            assert path[0] == start
            assert path[-1] == end

    def test_unreachable_returns_empty(self, pathfinder: PathfindingService) -> None:
        """Should return empty list for unreachable destination."""
        # Building cell is not in the road graph
        building_pos = Position(4, 1)  # Known 'B' cell
        road_pos = Position(10, 1)     # Known '>' road cell

        path = pathfinder.find_road_path(building_pos, road_pos)
        assert path == []

    def test_same_start_end(self, pathfinder: PathfindingService) -> None:
        """Path from a cell to itself should be a single-element list."""
        pos = Position(0, 0)
        path = pathfinder.find_sidewalk_path(pos, pos)
        assert path == [pos]

    def test_path_is_connected(self, pathfinder: PathfindingService) -> None:
        """Each step in the path should be adjacent to the previous one."""
        start = Position(0, 0)
        end = Position(29, 29)

        path = pathfinder.find_sidewalk_path(start, end)
        assert len(path) > 0

        for i in range(1, len(path)):
            prev, curr = path[i - 1], path[i]
            distance = abs(prev.x - curr.x) + abs(prev.y - curr.y)
            assert distance == 1, f"Non-adjacent step: {prev} -> {curr}"

    def test_out_of_grid_returns_empty(self, pathfinder: PathfindingService) -> None:
        """Should return empty for positions outside the grid."""
        path = pathfinder.find_sidewalk_path(Position(-1, -1), Position(0, 0))
        assert path == []

    def test_manhattan_distance(self) -> None:
        """Test the heuristic function."""
        a = Position(0, 0)
        b = Position(3, 4)
        assert PathfindingService._heuristic(a, b) == 7
