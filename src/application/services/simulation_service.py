"""Simulation service — thin orchestration layer over CityModel."""

from src.infrastructure.models.mesa_model import CityModel
from src.domain.entities import Car, Bus, Pedestrian, Traffic_Light


class SimulationService:
    """Manages the lifecycle of a CityModel simulation."""

    def __init__(self) -> None:
        self._model: CityModel = CityModel()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(self) -> dict:
        """Advance simulation by one tick and return updated state."""
        self._model.step()
        return self._model.get_state_snapshot()

    def get_state(self) -> dict:
        """Return current state without advancing."""
        return self._model.get_state_snapshot()

    def reset(self) -> dict:
        """Reinitialise the simulation from scratch, preserving current config."""
        config = self._model.get_config()
        self._model = CityModel(
            target_cars=config["target_cars"],
            target_peds=config["target_peds"],
            target_buses=config["target_buses"]
        )
        return self._model.get_state_snapshot()

    def get_stats(self) -> dict:
        """Return aggregated simulation statistics."""
        agents = list(self._model.schedule.agents)

        cars        = [a for a in agents if isinstance(a, Car)]
        pedestrians = [a for a in agents if isinstance(a, Pedestrian)]
        buses       = [a for a in agents if isinstance(a, Bus)]
        lights      = [a for a in agents if isinstance(a, Traffic_Light)]

        # Leverage the model's snapshot metrics for consistency
        snapshot = self._model.get_state_snapshot()
        stats = snapshot["stats"]
        stats["tick"] = self._model.schedule.steps
        return stats

    def set_config(self, config: dict):
        """Update simulation configuration."""
        print(f"DEBUG: SimulationService.set_config called with {config}")
        self._model.set_config(config)

    def get_config(self) -> dict:
        """Return simulation configuration."""
        config = self._model.get_config()
        config.update({
            "grid_width":  self._model.width,
            "grid_height": self._model.height,
        })
        return config
