"""Mesa CityModel – the core simulation model."""

from __future__ import annotations

import random

import mesa
from mesa.time import RandomActivation

from src.application.services.pathfinding_service import PathfindingService
from src.domain.entities.building import Building
from src.domain.entities.car_agent import CarAgent
from src.domain.entities.pedestrian_agent import PedestrianAgent
from src.domain.entities.traffic_light import TrafficLight
from src.domain.value_objects.grid_cell import GridCell
from src.domain.value_objects.position import Position
from src.infrastructure.persistence.grid_repository import GridData, GridRepository
from src.shared.config import GRID_FILE_PATH, MAX_CARS, MAX_PEDESTRIANS


class CityModel(mesa.Model):
    """Agent-based city traffic simulation model."""

    def __init__(self, grid_file: str | None = None) -> None:
        super().__init__()
        self.schedule = RandomActivation(self)

        repo = GridRepository()
        self.grid_data: GridData = repo.load(grid_file or GRID_FILE_PATH)

        # Grid accessors
        self.grid: list[list[GridCell]] = self.grid_data.grid
        self.grid_width: int = self.grid_data.width
        self.grid_height: int = self.grid_data.height

        # Domain objects
        self.traffic_lights: list[TrafficLight] = self.grid_data.traffic_lights
        self.buildings: list[Building] = self.grid_data.buildings
        self.roundabout_cells: list[Position] = self.grid_data.roundabout_cells
        self.car_spawns: list[Position] = self.grid_data.car_spawns
        self.ped_spawns: list[Position] = self.grid_data.ped_spawns

        # Simulation state
        self.max_cars: int = MAX_CARS
        self.max_peds: int = MAX_PEDESTRIANS
        self.tick: int = 0
        self._next_id: int = 0

        # Pathfinding service
        self.pathfinder = PathfindingService(
            self.grid, self.grid_width, self.grid_height
        )

        # Traffic light lookup by position for fast queries
        self._light_map: dict[tuple[int, int], TrafficLight] = {
            (tl.position.x, tl.position.y): tl for tl in self.traffic_lights
        }

        # Initial spawn
        self._spawn_agents()

    def _get_next_id(self) -> int:
        """Generate a unique agent ID."""
        self._next_id += 1
        return self._next_id

    def _spawn_agents(self) -> None:
        """Spawn initial cars and pedestrians up to limits."""
        self._spawn_cars()
        self._spawn_pedestrians()

    def _spawn_cars(self) -> None:
        """Spawn cars up to max_cars at random car spawn points."""
        current_cars = sum(
            1 for a in self.schedule.agents if isinstance(a, CarAgent)
        )
        while current_cars < self.max_cars and self.car_spawns:
            spawn = random.choice(self.car_spawns)
            car = CarAgent(self._get_next_id(), self, spawn)
            self.schedule.add(car)
            current_cars += 1

    def _spawn_pedestrians(self) -> None:
        """Spawn pedestrians up to max_peds at random ped spawn points."""
        current_peds = sum(
            1 for a in self.schedule.agents if isinstance(a, PedestrianAgent)
        )
        while current_peds < self.max_peds and self.ped_spawns:
            spawn = random.choice(self.ped_spawns)
            ped = PedestrianAgent(self._get_next_id(), self, spawn)
            self.schedule.add(ped)
            current_peds += 1

    def get_cell(self, x: int, y: int) -> GridCell | None:
        """Get a grid cell by coordinates, or None if out of bounds."""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.grid[y][x]
        return None

    def get_traffic_light_at(self, x: int, y: int) -> TrafficLight | None:
        """Get traffic light at the given position, if any."""
        return self._light_map.get((x, y))

    def step(self) -> None:
        """Advance the simulation by one tick."""
        self.tick += 1

        # Update traffic lights
        for light in self.traffic_lights:
            light.update()

        # Step all agents
        self.schedule.step()

        # Respawn agents if below limits
        self._spawn_cars()
        self._spawn_pedestrians()

    def get_state_snapshot(self) -> dict:
        """Return full simulation state for API serialization."""
        agents_data = []
        for agent in self.schedule.agents:
            if hasattr(agent, "to_dict"):
                agents_data.append(agent.to_dict())

        lights_data = [tl.to_dict() for tl in self.traffic_lights]

        return {
            "tick": self.tick,
            "agents": agents_data,
            "traffic_lights": lights_data,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "grid": [
                [cell.raw_char for cell in row]
                for row in self.grid
            ],
        }

    def __repr__(self) -> str:
        return (
            f"CityModel(grid={self.grid_width}x{self.grid_height}, "
            f"lights={len(self.traffic_lights)}, "
            f"buildings={len(self.buildings)}, "
            f"agents={len(self.schedule.agents)}, "
            f"tick={self.tick})"
        )
