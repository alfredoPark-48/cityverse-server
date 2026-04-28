"""Simulation service – orchestrates the CityModel for the API layer."""

from __future__ import annotations

from src.domain.entities.car_agent import CarAgent
from src.domain.entities.pedestrian_agent import PedestrianAgent
from src.infrastructure.models.mesa_model import CityModel
from src.shared.config import GRID_FILE_PATH


class SimulationService:
    """Application service wrapping the CityModel for API use."""

    def __init__(self, grid_file: str | None = None) -> None:
        self._grid_file = grid_file or GRID_FILE_PATH
        self._model = CityModel(self._grid_file)

    @property
    def model(self) -> CityModel:
        return self._model

    def step(self) -> dict:
        """Advance simulation by one tick and return state."""
        self._model.step()
        return self._model.get_state_snapshot()

    def get_state(self) -> dict:
        """Return current simulation state without stepping."""
        return self._model.get_state_snapshot()

    def reset(self) -> dict:
        """Reinitialize the simulation and return initial state."""
        self._model = CityModel(self._grid_file)
        return self._model.get_state_snapshot()

    def get_stats(self) -> dict:
        """Return simulation statistics."""
        agents = self._model.schedule.agents

        active_cars = [a for a in agents if isinstance(a, CarAgent)]
        active_peds = [a for a in agents if isinstance(a, PedestrianAgent)]

        return {
            "tick": self._model.tick,
            "active_cars": len(active_cars),
            "active_pedestrians": len(active_peds),
            "parked_cars": sum(1 for c in active_cars if c.parked),
            "waiting_cars": sum(1 for c in active_cars if c.waiting),
            "waiting_pedestrians": sum(1 for p in active_peds if p.waiting),
            "total_traffic_lights": len(self._model.traffic_lights),
        }

    def get_config(self) -> dict:
        """Return simulation configuration."""
        return {
            "grid_width": self._model.grid_width,
            "grid_height": self._model.grid_height,
            "max_cars": self._model.max_cars,
            "max_pedestrians": self._model.max_peds,
            "car_spawn_count": len(self._model.car_spawns),
            "ped_spawn_count": len(self._model.ped_spawns),
            "building_count": len(self._model.buildings),
            "traffic_light_count": len(self._model.traffic_lights),
        }
