"""Mesa CityModel – the core simulation model (Legacy Logic)."""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import json
import os

from src.domain.entities import (
    Car,
    Pedestrian,
    Bus,
    Traffic_Light,
    PedestrianCrossing,
    Destination,
    Building,
    Vegetation,
    Water,
    Angel,
    Road,
    SideWalk,
    Parking,
    Lot,
    Home,
    CarSpawn,
    PedestrianSpawn,
)
from src.shared.config import GRID_FILE_PATH


class CityModel(Model):
    """
    Creates a new model with random agents using legacy Multiagentes logic.
    """

    def __init__(self, grid_file: str | None = None) -> None:
        super().__init__()

        map_dict_path = os.path.join(
            os.path.dirname(GRID_FILE_PATH), "mapDictionary.json"
        )
        if not os.path.exists(map_dict_path):
            raise FileNotFoundError(f"Critical error: {map_dict_path} not found.")

        with open(map_dict_path, "r") as f:
            dataDictionary = json.load(f)

        self.grid_file = grid_file or GRID_FILE_PATH
        if not os.path.exists(self.grid_file):
            raise FileNotFoundError(f"Critical error: Grid file {self.grid_file} not found.")

        self.list_of_edges, self.road_graph, self.ped_graph = self.build_graphs()
        self.traffic_lights = []
        self.running = True

        # Dynamic Targets
        self.target_cars = 30
        self.target_peds = 30
        self.target_buses = 1
        
        # Cumulative stats
        self.total_parked_cars = 0
        self.total_parked_peds = 0
        
        # Capacity limits (will be calculated after grid parsing)
        self.max_cars = 100
        self.max_peds = 100
        self.max_buses = 5

        self.positions_temp = []
        self.pedPos_temp = []
        self.destinys_temp = []
        self.parking_temp = []
        self.car_spawns_temp = []
        self.ped_spawns_temp = []

        try:
            with open(self.grid_file) as baseFile:
                lines = baseFile.readlines()
                if not lines:
                    raise ValueError("Grid file is empty.")
                    
                self.width = len(lines[0].strip())
                self.height = len(lines)

                self.grid = MultiGrid(self.width, self.height, torus=False)
                self.schedule = RandomActivation(self)

                for r, row in enumerate(lines):
                    for c, col in enumerate(row.strip()):
                        if col in ["v", "^", ">", "<", "I"]:
                            road_dir = dataDictionary.get(col, "Intersection")
                            agent = Road(f"r_{r * self.width + c}", self, road_dir)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            if col in ["v", "^", ">", "<"]:
                                self.positions_temp.append((c, self.height - r - 1))
                        elif col in ["T", "t"]:
                            # Place a Road under the Traffic Light for direction context
                            road_agent = Road(
                                f"r_{r * self.width + c}", self, "Intersection"
                            )
                            self.grid.place_agent(road_agent, (c, self.height - r - 1))

                            agent = Traffic_Light(
                                f"tl_{r * self.width + c}",
                                self,
                                False if col == "T" else True,
                                int(dataDictionary[col]),
                            )
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.schedule.add(agent)
                            self.traffic_lights.append(agent)

                        elif col == "W":
                            agent = Water(f"ob_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                        elif col == "B":
                            agent = Building(f"ob_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                        elif col == "V":
                            agent = Vegetation(f"ob_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                        elif col == "S":
                            agent = SideWalk(f"sw_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.pedPos_temp.append((c, self.height - r - 1))
                        elif col == "A":
                            agent = Angel(f"ob_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                        elif col == "D":
                            agent = Destination(f"d_{r * self.width + c}", self)
                            self.schedule.add(agent)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.destinys_temp.append((c, self.height - r - 1))
                        elif col == "P":
                            agent = Parking(f"pk_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.parking_temp.append((c, self.height - r - 1))
                            self.pedPos_temp.append((c, self.height - r - 1))
                        elif col == "L":
                            agent = Lot(f"lt_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.pedPos_temp.append((c, self.height - r - 1))
                        elif col == "H":
                            agent = Home(f"hm_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                        elif col == "c":
                            agent = CarSpawn(f"gs_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.car_spawns_temp.append((c, self.height - r - 1))
                        elif col == "p":
                            agent = PedestrianSpawn(f"ps_{r * self.width + c}", self)
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.ped_spawns_temp.append((c, self.height - r - 1))
                        elif col in ["X", "x"]:
                            road_agent = Road(f"r_{r * self.width + c}", self, "Intersection")
                            self.grid.place_agent(road_agent, (c, self.height - r - 1))
                            agent = PedestrianCrossing(f"pc_{r * self.width + c}", self)
                            if col == "X":
                                agent.vertical = True
                            else:
                                agent.horizontal = True
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            self.schedule.add(agent)
                            self.pedPos_temp.append((c, self.height - r - 1))

        except Exception as e:
            raise RuntimeError(f"Failed to parse grid file: {e}")

        # Calculate dynamic max capacities based on infrastructure density
        self.max_cars = max(10, len(self.positions_temp) // 2)
        self.max_peds = max(10, len(self.pedPos_temp) // 2)
        
        # --- Initial Spawning ---
        self.replenish_agents()

        if self.positions_temp:
            b = Bus(3000, self)
            pos = self.random.choice(self.positions_temp)
            self.schedule.add(b)
            self.grid.place_agent(b, pos)

    def build_graphs(self):
        # Read the grid into a matrix
        with open(self.grid_file or GRID_FILE_PATH, "r") as f:
            matrix_inverted = [list(line.strip()) for line in f]

        matrix = list(reversed(matrix_inverted))
        rows = len(matrix)
        cols = len(matrix[0])

        road_graph = {}
        ped_graph = {}
        road_edges = []

        road_chars = [
            "v",
            "^",
            ">",
            "<",
            "I",
            "T",
            "t",
            "X",
            "x",
            "D",
            "A",
            "P",
            "L",
            "c",
        ]
        ped_chars = ["S", "X", "x", "D", "T", "t", "P", "p", "c"]

        for y in range(rows):
            for x in range(cols):
                c = matrix[y][x]
                source = (y, x)

                # Potential neighbors
                neighbors = [
                    (x, y + 1, "^"),
                    (x, y - 1, "v"),
                    (x - 1, y, "<"),
                    (x + 1, y, ">"),
                ]

                # --- Road Graph ---
                if c in road_chars:
                    if source not in road_graph:
                        road_graph[source] = []
                    for nx, ny, move_dir in neighbors:
                        if not (0 <= nx < cols and 0 <= ny < rows):
                            continue
                        nc = matrix[ny][nx]
                        if nc not in road_chars:
                            continue

                        can_move = False
                        # Special case: Spawns (G) and Connector nodes can move to ANY adjacent road
                        if c == "c" or (c in ["I", "T", "t", "X", "x", "A", "D", "P"]):
                            if (
                                nc in road_chars 
                                or nc == move_dir 
                            ):
                                can_move = True
                        elif c == move_dir:
                            if (
                                nc
                                in [
                                    "I",
                                    "T",
                                    "t",
                                    "X",
                                    "x",
                                    "A",
                                    "D",
                                    "P",
                                    "c",
                                ]
                                or nc == move_dir
                            ):
                                can_move = True

                        if can_move:
                            target = (ny, nx)
                            road_graph[source].append((1.0, target))
                            road_edges.append((source, target, 1.0))

                # --- Pedestrian Graph ---
                if c in ped_chars:
                    if source not in ped_graph:
                        ped_graph[source] = []
                    for nx, ny, _ in neighbors:
                        if not (0 <= nx < cols and 0 <= ny < rows):
                            continue
                        nc = matrix[ny][nx]
                        if nc in ped_chars:
                            target = (ny, nx)
                            ped_graph[source].append((1.0, target))

        return road_edges, road_graph, ped_graph

    def step(self):
        """Replenish agents and step the model."""
        self.replenish_agents()
        if self.schedule.steps % 15 == 0:
            for agent in self.traffic_lights:
                agent.state = not agent.state
        self.schedule.step()

    def replenish_agents(self):
        """Maintain the population by spawning new agents at dedicated spawns."""
        active_cars = [a for a in self.schedule.agents if isinstance(a, Car)]
        active_peds = [a for a in self.schedule.agents if isinstance(a, Pedestrian)]
        active_buses = [a for a in self.schedule.agents if isinstance(a, Bus)]

        # Replenish Cars (Strict Quota: Active + Parked <= Target)
        total_cars_session = len(active_cars) + self.total_parked_cars
        if total_cars_session < self.target_cars and self.parking_temp:
            spawn_pool = self.car_spawns_temp if self.car_spawns_temp else self.positions_temp
            for _ in range(min(self.target_cars - total_cars_session, 5)): # Spawn in small batches
                destpos = self.random.choice(self.parking_temp)
                new_id = self.random.randint(10000, 19999)
                a = Car(new_id, self, destpos)
                
                pos = self.random.choice(spawn_pool)
                attempts = 5
                while any(isinstance(ag, Car) for ag in self.grid.get_cell_list_contents(pos)) and attempts > 0:
                    pos = self.random.choice(spawn_pool)
                    attempts -= 1
                    
                self.schedule.add(a)
                self.grid.place_agent(a, pos)

        # Replenish Pedestrians (Strict Quota: Active + Finished <= Target)
        total_peds_session = len(active_peds) + self.total_parked_peds
        if total_peds_session < self.target_peds and self.destinys_temp:
            spawn_pool = self.ped_spawns_temp if self.ped_spawns_temp else self.pedPos_temp
            for _ in range(min(self.target_peds - total_peds_session, 5)):
                destpos = self.random.choice(self.destinys_temp)
                new_id = self.random.randint(20000, 29999)
                a = Pedestrian(new_id, self, destpos)
                
                pos = self.random.choice(spawn_pool)
                self.schedule.add(a)
                self.grid.place_agent(a, pos)

        # Replenish Buses
        if len(active_buses) < self.target_buses and self.positions_temp:
            for _ in range(self.target_buses - len(active_buses)):
                new_id = self.random.randint(30000, 39999)
                b = Bus(new_id, self)
                pos = self.random.choice(self.positions_temp)
                self.schedule.add(b)
                self.grid.place_agent(b, pos)

    def get_config(self) -> dict:
        """Return the current simulation configuration."""
        return {
            "target_cars": self.target_cars,
            "target_peds": self.target_peds,
            "target_buses": self.target_buses,
            "max_cars": self.max_cars,
            "max_peds": self.max_peds,
            "max_buses": self.max_buses
        }

    def set_config(self, config: dict):
        """Update simulation targets, respecting safety caps."""
        if "target_cars" in config:
            self.target_cars = min(int(config["target_cars"]), self.max_cars)
        if "target_peds" in config:
            self.target_peds = min(int(config["target_peds"]), self.max_peds)
        if "target_buses" in config:
            self.target_buses = min(int(config["target_buses"]), self.max_buses)

    def get_state_snapshot(self) -> dict:
        agents_data = []
        lights_data = []

        for agent in self.schedule.agents:
            # We map legacy agent state to the frontend's expected schema
            if isinstance(agent, Car):
                agents_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "type": "CarAgent",
                        "has_arrived": agent.inDestiny,
                        "parked": agent.inDestiny,
                        "waiting": not agent.moving,
                        "destination": {"x": agent.destiny[0], "y": agent.destiny[1]}
                        if agent.destiny
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
                        "has_arrived": agent.indestiny,
                        "crossing": False,
                        "waiting": not agent.moving,
                        "despawned": agent.indestiny,
                        "destination": None,
                    }
                )
            elif isinstance(agent, Bus):
                agents_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "type": "BusAgent",
                        "has_arrived": False,
                        "waiting": not agent.moving,
                        "route_index": 0,
                        "destination": None,
                    }
                )
            elif isinstance(agent, Traffic_Light):
                lights_data.append(
                    {
                        "id": agent.unique_id,
                        "x": agent.pos[0] if agent.pos else -1,
                        "y": agent.pos[1] if agent.pos else -1,
                        "direction": "N",  # Frontend doesn't care
                        "state": "green" if agent.state else "red",
                        "timer": agent.timeToChange,
                    }
                )

        # Load grid for frontend overlay
        with open(self.grid_file) as f:
            grid_lines = [list(line.strip()) for line in f.readlines()]
            # Original project grid y is flipped
            grid_lines.reverse()

        return {
            "tick": self.schedule.steps,
            "agents": agents_data,
            "traffic_lights": lights_data,
            "grid_width": self.width,
            "grid_height": self.height,
            "grid": grid_lines,
            "total_parked_cars": self.total_parked_cars,
            "total_parked_peds": self.total_parked_peds,
        }
