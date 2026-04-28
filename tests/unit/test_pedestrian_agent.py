"""Unit tests for PedestrianAgent."""

from src.domain.entities.pedestrian_agent import PedestrianAgent
from src.domain.value_objects.position import Position
from src.infrastructure.models.mesa_model import CityModel


class TestPedestrianAgent:
    """Tests for the PedestrianAgent."""

    def _create_model(self) -> CityModel:
        return CityModel()

    def test_ped_agent_init(self) -> None:
        """Pedestrian agent should initialize with position."""
        model = self._create_model()
        ped = PedestrianAgent(999, model, Position(0, 0))

        assert ped.position == Position(0, 0)
        assert ped.crossing is False
        assert ped.despawned is False

    def test_ped_agent_step(self) -> None:
        """Pedestrian should step without errors."""
        model = self._create_model()

        model.step()

        ped_count = sum(
            1 for a in model.schedule.agents if isinstance(a, PedestrianAgent)
        )
        assert ped_count > 0

    def test_ped_to_dict(self) -> None:
        """Pedestrian serialization should include expected keys."""
        model = self._create_model()
        ped = PedestrianAgent(999, model, Position(0, 0))

        data = ped.to_dict()
        assert "id" in data
        assert "type" in data
        assert "crossing" in data
        assert "waiting" in data
        assert "despawned" in data
        assert data["type"] == "PedestrianAgent"

    def test_ped_multiple_steps(self) -> None:
        """Model should handle multiple steps with peds."""
        model = self._create_model()

        for _ in range(10):
            model.step()

        assert model.tick == 10
