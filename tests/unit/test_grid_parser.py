"""Unit tests for GridRepository parser."""

import pytest

from src.infrastructure.persistence.grid_repository import GridRepository
from src.shared.constants import CellType


@pytest.fixture
def repo() -> GridRepository:
    return GridRepository()


class TestGridParser:
    """Tests for loading and parsing the city grid."""

    def test_load_valid_grid(self, repo: GridRepository) -> None:
        """Should load the default city grid without errors."""
        data = repo.load("data/city_grid.txt")

        assert data.width == 30
        assert data.height == 30
        assert len(data.grid) == 30
        assert all(len(row) == 30 for row in data.grid)

    def test_grid_has_traffic_lights(self, repo: GridRepository) -> None:
        """Should detect all traffic light positions."""
        data = repo.load("data/city_grid.txt")

        assert len(data.traffic_lights) > 0
        for tl in data.traffic_lights:
            cell = data.grid[tl.position.y][tl.position.x]
            assert cell.cell_type == CellType.TRAFFIC_LIGHT

    def test_grid_has_buildings(self, repo: GridRepository) -> None:
        """Should group building cells into Building entities."""
        data = repo.load("data/city_grid.txt")

        assert len(data.buildings) > 0
        for building in data.buildings:
            assert len(building.positions) > 0
            for pos in building.positions:
                assert data.grid[pos.y][pos.x].cell_type == CellType.BUILDING

    def test_grid_has_roundabout(self, repo: GridRepository) -> None:
        """Should detect roundabout cells."""
        data = repo.load("data/city_grid.txt")

        assert len(data.roundabout_cells) > 0
        for pos in data.roundabout_cells:
            assert data.grid[pos.y][pos.x].cell_type == CellType.ROUNDABOUT

    def test_grid_has_car_spawns(self, repo: GridRepository) -> None:
        """Should detect car spawn points near grid edges."""
        data = repo.load("data/city_grid.txt")

        assert len(data.car_spawns) > 0
        edge_margin = 2
        for pos in data.car_spawns:
            near_edge = (
                pos.x < edge_margin
                or pos.x >= data.width - edge_margin
                or pos.y < edge_margin
                or pos.y >= data.height - edge_margin
            )
            assert near_edge

    def test_grid_has_ped_spawns(self, repo: GridRepository) -> None:
        """Should detect pedestrian spawn points at grid edges."""
        data = repo.load("data/city_grid.txt")

        assert len(data.ped_spawns) > 0
        for pos in data.ped_spawns:
            assert (
                pos.x == 0
                or pos.x == data.width - 1
                or pos.y == 0
                or pos.y == data.height - 1
            )

    def test_buildings_have_entrances(self, repo: GridRepository) -> None:
        """Most buildings should have an adjacent entrance cell."""
        data = repo.load("data/city_grid.txt")

        buildings_with_entrances = [b for b in data.buildings if b.entrance is not None]
        assert len(buildings_with_entrances) > 0

    def test_load_missing_file_raises(self, repo: GridRepository) -> None:
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            repo.load("data/nonexistent.txt")

    def test_cell_types_correct(self, repo: GridRepository) -> None:
        """Spot-check that specific characters map to correct cell types."""
        data = repo.load("data/city_grid.txt")

        # Top-left corner should be sidewalk 's'
        assert data.grid[0][0].cell_type == CellType.SIDEWALK
        assert data.grid[0][0].raw_char == "s"
