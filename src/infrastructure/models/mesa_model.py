"""Mesa CityModel – the core simulation model (Legacy Logic)."""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import json
import os
import uuid

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
from src.shared.config import GRID_FILE_PATH, BUS_ROUTES_FILE_PATH


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
        self.target_buses = 4

        # Cumulative stats
        self.total_parked_cars = 0
        self.total_parked_peds = 0

        # ── Bus Route Data ────────────────────────────────────────────────────
        # Routes are defined explicitly in bus_routes.json as ordered lists of
        # [x, y] stop coordinates (Mesa grid space). The file is the single
        # source of truth; no runtime sorting is ever performed.
        routes_path = os.path.join(os.path.dirname(GRID_FILE_PATH), os.path.basename(BUS_ROUTES_FILE_PATH))
        if not os.path.exists(routes_path):
            raise FileNotFoundError(f"Bus routes file not found: {routes_path}")
        with open(routes_path, "r") as rf:
            raw_routes = json.load(rf)

        # Strip the optional comment key and normalise values to tuples
        self.bus_routes: dict[str, list[tuple[int, int]]] = {
            rid: [tuple(coord) for coord in stops]
            for rid, stops in raw_routes.items()
            if not rid.startswith("_")  # ignore _comment and similar meta-keys
        }
        
        # Capacity limits
        self.max_cars = 100
        self.max_peds = 250
        self.max_buses = 16

        self.positions_temp = []
        self.pedPos_temp = []
        self.destinys_temp = []
        self.parking_temp = []
        self.car_spawns_temp = []
        self.ped_spawns_temp = []

        # Advanced Metrics Engine
        self.metrics = {
            "total_passengers": 0,
            "frustrated_pedestrians": 0,
            "near_misses": 0,
            "completed_trips": 0,
            "avg_bus_occupancy": 0
        }

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
                        if col in ["v", "^", ">", "<", "I", "1", "2", "3", "4"]:
                            road_dir = dataDictionary.get(col, "Intersection")
                            agent = Road(f"r_{r * self.width + c}", self, road_dir)
                            if col in ["1", "2", "3", "4"]:
                                # Mark the cell so passengers know this is a stop;
                                # stop ORDER comes from bus_routes.json, not the grid scan.
                                agent.is_bus_stop = True
                            self.grid.place_agent(agent, (c, self.height - r - 1))
                            if col in ["v", "^", ">", "<", "1", "2", "3", "4"]:
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

        # ── Validate that every stop from the JSON exists on the grid ────────
        # This catches mismatches between bus_routes.json and city.txt early,
        # giving a clear error instead of a silent pathfinding failure at runtime.
        for rid, stops in self.bus_routes.items():
            for stop in stops:
                sx, sy = stop
                if not (0 <= sx < self.width and 0 <= sy < self.height):
                    raise ValueError(
                        f"Route {rid} stop {stop} is outside the grid "
                        f"({self.width}×{self.height}). Check bus_routes.json."
                    )
                cell_agents = self.grid.get_cell_list_contents(stop)
                if not any(getattr(a, "is_bus_stop", False) for a in cell_agents):
                    raise ValueError(
                        f"Route {rid} stop {stop} does not match a bus-stop cell "
                        f"in the grid. Verify bus_routes.json against city.txt."
                    )

        # --- Initial Spawning ---
        self.replenish_agents()


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
        ped_chars = ["S", "X", "x", "D", "T", "t", "P", "p", "c", "1", "2", "3", "4"]

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
                        # Standard Directional Logic
                        if c == "c" or (c in ["I", "T", "t", "X", "x", "A", "D", "P"]):
                            if (
                                nc in road_chars 
                                or nc == move_dir 
                            ):
                                can_move = True
                        # Arrows Logic
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
        """Advance the simulation by one step."""
        if self.schedule.steps % 15 == 0:
            for agent in self.traffic_lights:
                agent.state = not agent.state
        self.schedule.step()

    def replenish_agents(self):
        """Maintain the population by spawning new agents at dedicated spawns."""
        active_cars = [a for a in self.schedule.agents if isinstance(a, Car)]
        active_peds = [a for a in self.schedule.agents if isinstance(a, Pedestrian)]
        
        # Replenish Cars
        if len(active_cars) < self.target_cars and self.positions_temp:
            spawn_pool = self.car_spawns_temp if self.car_spawns_temp else self.positions_temp
            for _ in range(self.target_cars - len(active_cars)):
                destpos = self.random.choice(self.parking_temp) if self.parking_temp else None
                new_id = str(uuid.uuid4())
                a = Car(new_id, self, destpos)
                
                pos = self.random.choice(spawn_pool)
                attempts = 5
                while any(isinstance(ag, Car) for ag in self.grid.get_cell_list_contents(pos)) and attempts > 0:
                    pos = self.random.choice(spawn_pool)
                    attempts -= 1
                    
                self.schedule.add(a)
                self.grid.place_agent(a, pos)

        # Replenish Pedestrians (Strict Quota: Active + Finished <= Target)
        if len(active_peds) < self.target_peds and self.destinys_temp:
            spawn_pool = self.ped_spawns_temp if self.ped_spawns_temp else self.pedPos_temp
            for _ in range(self.target_peds - len(active_peds)):
                destpos = self.random.choice(self.destinys_temp)
                new_id = str(uuid.uuid4())
                a = Pedestrian(new_id, self, destpos)
                
                
                pos = self.random.choice(spawn_pool)
                self.schedule.add(a)
                self.grid.place_agent(a, pos)

        # Replenish Buses
        active_buses = [a for a in self.schedule.agents if isinstance(a, Bus)]

        # 1. Ensure minimum coverage: every route must have at least one bus
        active_route_ids = [getattr(b, "route_id", None) for b in active_buses]
        for rid in self.bus_routes:
            if rid not in active_route_ids and self.bus_routes[rid]:
                new_id = str(uuid.uuid4())
                b = Bus(new_id, self, rid)
                pos = self._bus_spawn_pos(rid)
                self.schedule.add(b)
                self.grid.place_agent(b, pos)
                active_buses.append(b)

        # 2. Scale up if target_buses > 4: distribute extra buses round-robin
        while len(active_buses) < self.target_buses:
            route_counts = {rid: 0 for rid in self.bus_routes}
            for b in active_buses:
                route_counts[b.route_id] += 1
            target_rid = min(route_counts, key=route_counts.get)

            new_id = str(uuid.uuid4())
            b = Bus(new_id, self, target_rid)
            pos = self._bus_spawn_pos(target_rid)
            self.schedule.add(b)
            self.grid.place_agent(b, pos)
            active_buses.append(b)

    def _bus_spawn_pos(self, route_id: str) -> tuple[int, int]:
        """
        Finds a valid road cell to spawn a bus near its first stop.
        Filters out non-driving cells like Lots, Parking, and Destinations.
        """
        route = self.bus_routes.get(route_id)
        if not route:
            return (0, 0)
        
        stop_pos = route[0]
        next_stop = route[1] if len(route) > 1 else route[0]
        
        # Get all cardinal neighbors of the stop
        neighbors = self.grid.get_neighborhood(stop_pos, moore=False, include_center=False)
        
        # We only want neighbors that are:
        # 1. In the road graph
        # 2. NOT 'L', 'P', 'D', 'A', 'c' (Lots, Parking, etc. - these are in road_graph for peds)
        valid_candidates = []
        
        # Need to check the grid character to be sure
        for n in neighbors:
            if (n[1], n[0]) not in self.road_graph:
                continue
            
            # Check cell contents for Road objects to verify direction/type
            cell_agents = self.grid.get_cell_list_contents(n)
            is_driving_road = False
            for a in cell_agents:
                # Road agents have their direction set from the dataDictionary
                # We want to avoid things like "Lot", "Parking", etc.
                if type(a).__name__ == "Road":
                    # Directions like "Right", "Left", "Up", "Down", "Intersection" are valid
                    if a.direction in ["Right", "Left", "Up", "Down", "Intersection"]:
                        is_driving_road = True
                        break
            
            if is_driving_road:
                valid_candidates.append(n)
        
        if not valid_candidates:
            # Fallback to any road neighbor if no "pure" road neighbors found
            valid_candidates = [n for n in neighbors if (n[1], n[0]) in self.road_graph]
        
        if not valid_candidates:
            return stop_pos

        # Rank candidates by reachability to the NEXT stop
        from src.application.services.graph_service import a_star_search
        for cand in valid_candidates:
            start_node = (cand[1], cand[0])
            # Find a goal neighbor for the next stop
            next_goals = []
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                g = (next_stop[1] + dy, next_stop[0] + dx)
                if g in self.road_graph:
                    next_goals.append(g)
            
            for gn in next_goals:
                _, path = a_star_search(self.road_graph, start_node, gn)
                if len(path) > 1:
                    return cand
                    
        return valid_candidates[0]

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
                        "is_boarding": getattr(agent, "is_boarding", False),
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
                        "passenger_count": len(agent.passengers),
                        "route_id": agent.route_id,
                        "route_index": agent.current_stop_index,
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

        # Calculate live stats
        active_buses = [a for a in self.schedule.agents if isinstance(a, Bus)]
        avg_occ = sum(len(b.passengers) for b in active_buses) / len(active_buses) if active_buses else 0
        self.metrics["avg_bus_occupancy"] = round(avg_occ, 1)

        return {
            "tick": self.schedule.steps,
            "agents": agents_data,
            "traffic_lights": lights_data,
            "grid_width": self.width,
            "grid_height": self.height,
            "grid": grid_lines,
            "stats": {
                "active_cars": len([a for a in self.schedule.agents if isinstance(a, Car)]),
                "active_peds": len([a for a in self.schedule.agents if isinstance(a, Pedestrian)]),
                "active_buses": len(active_buses),
                "parked_cars": self.total_parked_cars,
                "parked_peds": self.total_parked_peds,
                "total_passengers": self.metrics["total_passengers"],
                "frustrated_peds": self.metrics["frustrated_pedestrians"],
                "near_misses": self.metrics["near_misses"],
                "completed_trips": self.metrics["completed_trips"],
                "bus_occupancy": self.metrics["avg_bus_occupancy"]
            }
        }
