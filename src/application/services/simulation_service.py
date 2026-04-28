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
        """Reinitialise the simulation from scratch."""
        self._model = CityModel()
        return self._model.get_state_snapshot()

    def get_stats(self) -> dict:
        """Return aggregated simulation statistics."""
        agents = list(self._model.schedule.agents)

        cars        = [a for a in agents if isinstance(a, Car)]
        pedestrians = [a for a in agents if isinstance(a, Pedestrian)]
        buses       = [a for a in agents if isinstance(a, Bus)]
        lights      = [a for a in agents if isinstance(a, Traffic_Light)]

        active_cars   = [c for c in cars if not c.inDestiny]
        waiting_cars  = [c for c in active_cars if not c.moving]

        return {
            "tick":                 self._model.schedule.steps,
            "active_cars":          len(active_cars),
            "parked_cars":          0,          # legacy model removes on arrival
            "waiting_cars":         len(waiting_cars),
            "active_pedestrians":   len(pedestrians),
            "waiting_pedestrians":  0,
            "active_buses":         len(buses),
            "total_traffic_lights": len(lights),
        }

    def get_config(self) -> dict:
        """Return static simulation configuration."""
        return {
            "grid_width":  self._model.width,
            "grid_height": self._model.height,
            "num_agents":  self._model.num_agents,
        }
