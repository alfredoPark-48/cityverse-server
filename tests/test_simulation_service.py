"""Tests for the SimulationService (application layer)."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.application.services.simulation_service import SimulationService
from src.domain.entities import Car, Bus, Pedestrian, Traffic_Light


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_agent(cls, *, moving=True, inDestiny=False, indestiny=False, state=True, timeToChange=15):
    """Create a typed mock agent."""
    agent = MagicMock(spec=cls)
    agent.pos = (0, 0)
    if cls is Car:
        agent.inDestiny = inDestiny
        agent.moving = moving
        agent.destiny = (1, 1)
    elif cls is Pedestrian:
        agent.indestiny = indestiny
    elif cls is Bus:
        agent.moving = moving
    elif cls is Traffic_Light:
        agent.state = state
        agent.timeToChange = timeToChange
    return agent


@pytest.fixture
def service():
    """Return a SimulationService with a mocked CityModel."""
    with patch("src.application.services.simulation_service.CityModel") as MockModel:
        mock_model = MagicMock()
        mock_model.schedule.steps = 5
        mock_model.width = 24
        mock_model.height = 24
        mock_model.num_agents = 30

        # Populate schedule with a variety of agents
        mock_model.schedule.agents = [
            _make_mock_agent(Car, moving=True),
            _make_mock_agent(Car, moving=False),        # waiting car
            _make_mock_agent(Car, inDestiny=True),      # arrived car
            _make_mock_agent(Pedestrian),
            _make_mock_agent(Bus),
            _make_mock_agent(Traffic_Light),
        ]

        mock_model.get_state_snapshot.return_value = {"tick": 5, "agents": []}
        MockModel.return_value = mock_model

        svc = SimulationService()
        svc._model = mock_model
        return svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSimulationServiceStep:
    def test_step_calls_model_step(self, service):
        service.step()
        service._model.step.assert_called_once()

    def test_step_returns_snapshot(self, service):
        result = service.step()
        assert "tick" in result


class TestSimulationServiceReset:
    def test_reset_creates_new_model(self, service):
        with patch("src.application.services.simulation_service.CityModel") as MockNew:
            new_model = MagicMock()
            new_model.get_state_snapshot.return_value = {"tick": 0, "agents": []}
            MockNew.return_value = new_model
            result = service.reset()
        # After reset the model is replaced
        assert service._model is new_model

    def test_reset_returns_snapshot(self, service):
        with patch("src.application.services.simulation_service.CityModel") as MockNew:
            new_model = MagicMock()
            new_model.get_state_snapshot.return_value = {"tick": 0, "agents": []}
            MockNew.return_value = new_model
            result = service.reset()
        assert "tick" in result


class TestSimulationServiceStats:
    def test_stats_keys_present(self, service):
        stats = service.get_stats()
        expected_keys = {
            "tick", "active_cars", "parked_cars", "waiting_cars",
            "active_pedestrians", "waiting_pedestrians",
            "active_buses", "total_traffic_lights",
        }
        assert expected_keys.issubset(stats.keys())

    def test_stats_active_cars_excludes_arrived(self, service):
        stats = service.get_stats()
        # 3 cars total: 1 moving, 1 waiting, 1 arrived → 2 active
        assert stats["active_cars"] == 2

    def test_stats_waiting_cars(self, service):
        stats = service.get_stats()
        # 1 car has moving=False and inDestiny=False
        assert stats["waiting_cars"] == 1

    def test_stats_pedestrian_count(self, service):
        stats = service.get_stats()
        assert stats["active_pedestrians"] == 1

    def test_stats_bus_count(self, service):
        stats = service.get_stats()
        assert stats["active_buses"] == 1

    def test_stats_traffic_light_count(self, service):
        stats = service.get_stats()
        assert stats["total_traffic_lights"] == 1


class TestSimulationServiceConfig:
    def test_config_returns_grid_dimensions(self, service):
        cfg = service.get_config()
        assert cfg["grid_width"] == 24
        assert cfg["grid_height"] == 24
        assert cfg["num_agents"] == 30
