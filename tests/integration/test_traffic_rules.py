"""Integration tests for traffic rules."""

from src.domain.entities.car_agent import CarAgent
from src.domain.entities.traffic_light import TrafficLight
from src.domain.value_objects.position import Position
from src.infrastructure.models.mesa_model import CityModel
from src.shared.constants import TrafficLightState


class TestTrafficRules:
    """Integration tests for traffic light and agent interaction."""

    def test_traffic_light_cycles(self) -> None:
        """Traffic light should cycle through GREEN -> YELLOW -> RED."""
        model = CityModel()
        light = model.traffic_lights[0]

        # Starts at RED
        assert light.state == TrafficLightState.RED

        # Advance through RED phase (50 ticks)
        for _ in range(50):
            light.update()
        assert light.state == TrafficLightState.GREEN

        # Advance through GREEN phase (40 ticks)
        for _ in range(40):
            light.update()
        assert light.state == TrafficLightState.YELLOW

        # Advance through YELLOW phase (10 ticks)
        for _ in range(10):
            light.update()
        assert light.state == TrafficLightState.RED

    def test_simulation_runs_100_ticks(self) -> None:
        """Model should run 100 ticks without errors."""
        model = CityModel()

        for _ in range(100):
            model.step()

        assert model.tick == 100

        # Should still have agents
        assert len(model.schedule.agents) > 0

    def test_agents_move(self) -> None:
        """Agents should change positions over time."""
        model = CityModel()

        initial_positions = {
            a.unique_id: a.position
            for a in model.schedule.agents
            if hasattr(a, "position")
        }

        for _ in range(20):
            model.step()

        moved = 0
        for agent in model.schedule.agents:
            if hasattr(agent, "position"):
                if agent.unique_id in initial_positions:
                    if agent.position != initial_positions[agent.unique_id]:
                        moved += 1

        assert moved > 0, "At least some agents should have moved"

    def test_state_snapshot_has_agents(self) -> None:
        """State snapshot should include all spawned agents."""
        model = CityModel()
        state = model.get_state_snapshot()

        assert len(state["agents"]) > 0
        assert len(state["traffic_lights"]) > 0
