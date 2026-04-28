"""Unit tests for CityModel initialization."""

import pytest

from src.infrastructure.models.mesa_model import CityModel


class TestCityModel:
    """Tests for the Mesa CityModel."""

    def test_model_initializes(self) -> None:
        """Model should initialize from the default grid file."""
        model = CityModel()

        assert model.grid_width == 30
        assert model.grid_height == 30
        assert model.tick == 0

    def test_model_has_traffic_lights(self) -> None:
        """Model should have traffic lights loaded."""
        model = CityModel()

        assert len(model.traffic_lights) > 0

    def test_model_has_buildings(self) -> None:
        """Model should have buildings loaded."""
        model = CityModel()

        assert len(model.buildings) > 0

    def test_model_step_increments_tick(self) -> None:
        """Each step should increment the tick counter."""
        model = CityModel()

        model.step()
        assert model.tick == 1

        model.step()
        assert model.tick == 2

    def test_traffic_lights_update_on_step(self) -> None:
        """Traffic lights should update their timers on each step."""
        model = CityModel()
        initial_timers = [tl.timer for tl in model.traffic_lights]

        model.step()

        for i, tl in enumerate(model.traffic_lights):
            assert tl.timer == initial_timers[i] + 1

    def test_get_cell_valid(self) -> None:
        """Should return a cell for valid coordinates."""
        model = CityModel()

        cell = model.get_cell(0, 0)
        assert cell is not None

    def test_get_cell_out_of_bounds(self) -> None:
        """Should return None for out-of-bounds coordinates."""
        model = CityModel()

        assert model.get_cell(-1, 0) is None
        assert model.get_cell(0, -1) is None
        assert model.get_cell(100, 0) is None

    def test_get_state_snapshot(self) -> None:
        """State snapshot should contain expected keys."""
        model = CityModel()

        state = model.get_state_snapshot()
        assert "tick" in state
        assert "agents" in state
        assert "traffic_lights" in state
        assert "grid_width" in state
        assert "grid_height" in state
        assert state["tick"] == 0
