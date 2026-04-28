"""Unit tests for CarAgent."""

from src.domain.entities.car_agent import CarAgent
from src.domain.value_objects.position import Position
from src.infrastructure.models.mesa_model import CityModel


class TestCarAgent:
    """Tests for the CarAgent."""

    def _create_model(self) -> CityModel:
        return CityModel()

    def test_car_agent_init(self) -> None:
        """Car agent should initialize with a position and destination."""
        model = self._create_model()
        car = CarAgent(999, model, Position(10, 1))

        assert car.position == Position(10, 1)
        assert car.parked is False
        assert car.has_arrived is False

    def test_car_agent_step(self) -> None:
        """Car agent should move or stop without errors."""
        model = self._create_model()

        # Step the model (which steps all agents)
        model.step()

        # Verify agents are present
        car_count = sum(
            1 for a in model.schedule.agents if isinstance(a, CarAgent)
        )
        assert car_count > 0

    def test_car_to_dict(self) -> None:
        """Car agent serialization should include expected keys."""
        model = self._create_model()
        car = CarAgent(999, model, Position(10, 1))

        data = car.to_dict()
        assert "id" in data
        assert "x" in data
        assert "y" in data
        assert "type" in data
        assert "parked" in data
        assert "waiting" in data
        assert data["type"] == "CarAgent"

    def test_car_multiple_steps(self) -> None:
        """Model should handle multiple steps with cars."""
        model = self._create_model()

        for _ in range(10):
            model.step()

        assert model.tick == 10
