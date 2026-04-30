"""Mesa CityModel refactored for Clean Architecture."""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import json
import os

from src.domain.entities import Car, Pedestrian, Bus, Traffic_Light
from src.shared.config import GRID_FILE_PATH, BUS_ROUTES_FILE_PATH
from src.infrastructure.persistence.grid_loader import GridLoader
from src.application.services.graph_service import GraphService
from src.application.services.spawning_service import SpawningService


class CityModel(Model):
    """
    Core simulation model orchestrating agents and environment.
    """

    def __init__(
        self,
        grid_file: str | None = None,
        target_cars: int = 30,
        target_peds: int = 30,
        target_buses: int = 4,
    ) -> None:
        super().__init__()
        self.grid_file = grid_file or GRID_FILE_PATH

        # Load environment configuration
        map_dict_path = os.path.join(
            os.path.dirname(GRID_FILE_PATH), "mapDictionary.json"
        )
        dataDictionary = GridLoader.load_map_dictionary(map_dict_path)

        # Build graphs
        self.list_of_edges, self.road_graph, self.ped_graph = GraphService.build_graphs(
            self.grid_file
        )

        # Initialize grid and schedule
        with open(self.grid_file) as f:
            lines = f.readlines()
        self.width = len(lines[0].strip())
        self.height = len(lines)
        self.grid = MultiGrid(self.width, self.height, torus=False)
        self.schedule = RandomActivation(self)

        # Load grid agents and metadata
        _, _, temp_data = GridLoader.parse_grid_file(
            self, self.grid_file, dataDictionary
        )

        # Map metadata to model properties
        self.positions_temp = temp_data["positions"]
        self.pedPos_temp = temp_data["ped_positions"]
        self.destinys_temp = temp_data["destinations"]
        self.parking_temp = temp_data["parking"]
        self.car_spawns_temp = temp_data["car_spawns"]
        self.ped_spawns_temp = temp_data["ped_spawns"]
        self.traffic_lights = temp_data["traffic_lights"]

        # Bus Route Initialization
        self.bus_routes = self._load_bus_routes()

        # Simulation Settings
        self.target_cars = target_cars
        self.target_peds = target_peds
        self.target_buses = target_buses
        self.max_cars, self.max_peds, self.max_buses = 100, 250, 16

        # Statistics & Metrics
        self.total_arrived_cars = 0
        self.total_arrived_peds = 0
        self.metrics = {
            "total_passengers": 0,
            "total_frustrated": 0,
            "crashes": 0,
            "completed_trips": 0,
            "avg_bus_occupancy": 0,
        }

        self.regenerate_agents = False
        self.running = True
        self.replenish_agents()

    def _load_bus_routes(self):
        routes_path = os.path.join(
            os.path.dirname(GRID_FILE_PATH), os.path.basename(BUS_ROUTES_FILE_PATH)
        )
        with open(routes_path, "r") as rf:
            raw_routes = json.load(rf)
        return {
            rid: [tuple(coord) for coord in stops]
            for rid, stops in raw_routes.items()
            if not rid.startswith("_")
        }

    def step(self):
        """Advance the simulation by one step."""
        if not self.running:
            return

        if self.schedule.steps % 15 == 0:
            for agent in self.traffic_lights:
                agent.state = not agent.state

        if self.regenerate_agents:
            self.replenish_agents()

        self.schedule.step()
        self._calculate_crashes()

        # Auto-stop if no active agents left and not in regenerating mode
        if not self.regenerate_agents:
            active_agents = [a for a in self.schedule.agents if type(a).__name__ in ["Car", "Pedestrian"]]
            if not active_agents:
                self.running = False

    def _calculate_crashes(self):
        """Monitors vehicle collisions."""
        for contents, pos in self.grid.coord_iter():
            if len(contents) > 1:
                # Count moving VEHICLES (Car or Bus)
                moving_vehicles = [a for a in contents if getattr(a, "is_moving", False) and type(a).__name__ in ["Car", "Bus"]]
                
                if len(moving_vehicles) > 1:
                    self.metrics["crashes"] += 1

    def replenish_agents(self):
        """Orchestrate agent spawning via SpawningService."""
        SpawningService.replenish_cars(self)
        SpawningService.replenish_pedestrians(self)
        SpawningService.replenish_buses(self)

    def _bus_spawn_pos(self, route_id: str) -> tuple[int, int]:
        """Finds a valid bus spawn point adjacent to the first stop, prioritizing directional roads."""
        route = self.bus_routes.get(route_id)
        if not route:
            return (0, 0)
        stop_pos = route[0]
        neighbors = self.grid.get_neighborhood(
            stop_pos, moore=False, include_center=False
        )

        candidates = []
        for n in neighbors:
            # Graph keys are (y, x)
            if (n[1], n[0]) in self.road_graph:
                cell_agents = self.grid.get_cell_list_contents(n)
                is_road = any(type(a).__name__ == "Road" for a in cell_agents)
                is_directional = any(
                    type(a).__name__ == "Road"
                    and a.direction in ["Up", "Down", "Left", "Right"]
                    for a in cell_agents
                )

                # Scoring: 2 for directional roads, 1 for other roads (intersections), 0 for other nodes
                score = 2 if is_directional else (1 if is_road else 0)
                candidates.append((score, n))

        if candidates:
            # Sort by score descending
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]

        return stop_pos

    def get_config(self) -> dict:
        return {
            "target_cars": self.target_cars,
            "target_peds": self.target_peds,
            "target_buses": self.target_buses,
            "max_cars": self.max_cars,
            "max_peds": self.max_peds,
            "max_buses": self.max_buses,
            "regenerate_agents": self.regenerate_agents,
        }

    def set_config(self, config: dict):
        for key in ["target_cars", "target_peds", "target_buses"]:
            if key in config:
                setattr(
                    self,
                    key,
                    min(int(config[key]), getattr(self, f"max_{key.split('_')[1]}")),
                )
        if "regenerate_agents" in config:
            self.regenerate_agents = bool(config["regenerate_agents"])
        self.replenish_agents()

    def get_state_snapshot(self) -> dict:
        """Returns a snapshot of the simulation state for the frontend."""
        agents_data = []
        lights_data = []

        for agent in self.schedule.agents:
            if isinstance(agent, Car):
                agents_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "type": "CarAgent",
                        "has_arrived": agent.has_arrived,
                        "parked": agent.has_arrived,
                        "waiting": not agent.is_moving,
                        "destination": {
                            "x": agent.destination[0],
                            "y": agent.destination[1],
                        }
                        if agent.destination
                        else None,
                    }
                )
            elif isinstance(agent, Pedestrian):
                agents_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "type": "PedestrianAgent",
                        "has_arrived": agent.has_arrived,
                        "crossing": False,
                        "waiting": not agent.is_moving,
                        "is_boarding": getattr(agent, "is_boarding", False),
                        "despawned": agent.has_arrived,
                    }
                )
            elif isinstance(agent, Bus):
                agents_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "type": "BusAgent",
                        "waiting": not agent.is_moving,
                        "passenger_count": len(agent.passengers),
                        "route_id": agent.route_id,
                        "route_index": agent.current_stop_index,
                    }
                )
            elif isinstance(agent, Traffic_Light):
                lights_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "direction": "N",
                        "state": "green" if agent.state else "red",
                        "timer": agent.timeToChange,
                    }
                )

        with open(self.grid_file) as f:
            grid_lines = [list(line.strip()) for line in f.readlines()]
            grid_lines.reverse()

        active_buses = [a for a in self.schedule.agents if isinstance(a, Bus)]
        avg_occ = (
            sum(len(b.passengers) for b in active_buses) / len(active_buses)
            if active_buses
            else 0
        )
        self.metrics["avg_bus_occupancy"] = round(avg_occ, 1)

        return {
            "tick": self.schedule.steps,
            "running": self.running,
            "agents": agents_data,
            "traffic_lights": lights_data,
            "grid_width": self.width,
            "grid_height": self.height,
            "grid": grid_lines,
            "stats": {
                "active_cars": len(
                    [a for a in self.schedule.agents if isinstance(a, Car)]
                ),
                "active_peds": len(
                    [a for a in self.schedule.agents if isinstance(a, Pedestrian)]
                ),
                "active_buses": len(active_buses),
                "arrived_cars": self.total_arrived_cars,
                "arrived_peds": self.total_arrived_peds,
                "total_passengers": self.metrics["total_passengers"],
                "active_passengers": sum(len(b.passengers) for b in active_buses),
                "total_frustrated": self.metrics["total_frustrated"],
                "crashes": self.metrics["crashes"],
                "completed_trips": self.metrics["completed_trips"],
                "bus_occupancy": self.metrics["avg_bus_occupancy"],
            },
        }
