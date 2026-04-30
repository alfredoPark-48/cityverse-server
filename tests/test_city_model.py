"""Tests for the CityModel (Mesa model)."""

import pytest
from unittest.mock import patch

from src.infrastructure.models.mesa_model import CityModel
from src.domain.entities import Car, Bus, Pedestrian, Traffic_Light, Road


MAP_CONTENT = """\
>>+<<
B B B
S B s
B B B
>>+<<
"""


@pytest.fixture
def model(tmp_path):
    """Provide a CityModel built from a minimal in-memory map file."""
    map_file = tmp_path / "test_map.txt"
    map_file.write_text(MAP_CONTENT)

    dict_file = tmp_path / "mapDictionary.json"
    dict_file.write_text(
        '{">" : "Right","<" : "Left","S" : 15,"s" : 7,'
        '"#" : "Vegetation","v" : "Down","^" : "Up","W" : "Water",'
        '"D" : "Destination","B" : "Building","Z" : "Pedestrian",'
        '"z" : "Pedestrian","+" : "Intersection","A" : "Angel"}'
    )

    # Patch config path so CityModel finds the dictionary next to the map
    with patch("src.infrastructure.models.mesa_model.GRID_FILE_PATH", str(map_file)):
        with patch("os.path.dirname", return_value=str(tmp_path)):
            m = CityModel.__new__(CityModel)
            # Use a real, small model init
            m.__init__(grid_file=str(map_file))
    return m


class TestCityModelInit:
    """Verify model initialises its grid and schedule correctly."""

    def test_grid_dimensions_match_map(self, model):
        assert model.width == 5
        assert model.height == 5

    def test_schedule_has_traffic_lights(self, model):
        lights = [a for a in model.schedule.agents if isinstance(a, Traffic_Light)]
        assert len(lights) >= 1, "At least one traffic light expected"

    def test_traffic_lights_registered(self, model):
        assert len(model.traffic_lights) >= 1

    def test_build_edges_list_returns_list(self, model):
        assert isinstance(model.list_of_edges, list)


class TestCityModelStep:
    """Verify the step() method advances the model correctly."""

    def test_step_increments_tick(self, model):
        before = model.schedule.steps
        model.step()
        assert model.schedule.steps == before + 1

    def test_lights_toggle_at_interval(self, model):
        """Traffic lights must toggle exactly at step 15."""
        initial_states = {tl.unique_id: tl.state for tl in model.traffic_lights}
        for _ in range(15):
            model.step()
        for tl in model.traffic_lights:
            assert tl.state != initial_states[tl.unique_id], (
                f"Light {tl.unique_id} should have toggled at step 15"
            )

    def test_step_returns_valid_snapshot(self, model):
        snapshot = model.get_state_snapshot()
        assert "tick" in snapshot
        assert "agents" in snapshot
        assert "traffic_lights" in snapshot
        assert "grid_width" in snapshot
        assert "grid_height" in snapshot
        assert "grid" in snapshot


class TestStateSnapshot:
    """Verify the snapshot schema is frontend-compatible."""

    def test_snapshot_grid_dimensions(self, model):
        snap = model.get_state_snapshot()
        assert snap["grid_width"] == model.width
        assert snap["grid_height"] == model.height
        assert len(snap["grid"]) == model.height

    def test_snapshot_traffic_light_schema(self, model):
        snap = model.get_state_snapshot()
        for tl in snap["traffic_lights"]:
            assert "id" in tl
            assert "x" in tl
            assert "y" in tl
            assert tl["state"] in ("red", "green")
