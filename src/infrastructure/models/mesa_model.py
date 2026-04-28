"""Mesa CityModel – the core simulation model (Legacy Logic)."""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
import json
import os

from src.domain.entities import (
    Car, Pedestrian, Bus, Traffic_Light, PedestrianCrossing,
    Destination, Obstacle, Angel, Road, SideWalk
)
from src.shared.config import GRID_FILE_PATH

class CityModel(Model):
    """
    Creates a new model with random agents using legacy Multiagentes logic.
    """
    def __init__(self, grid_file: str | None = None) -> None:
        super().__init__()
        
        map_dict_path = os.path.join(os.path.dirname(GRID_FILE_PATH), "mapDictionary.json")
        with open(map_dict_path, "r") as f:
            dataDictionary = json.load(f)
            
        self.grid_file = grid_file or GRID_FILE_PATH
        self.list_of_edges, self.road_graph, self.ped_graph = self.build_graphs()
        self.traffic_lights = []
        self.num_agents = 30
        self.running = True
        
        positions_temp = []
        pedPos_temp = []
        destinys_temp = []

        with open(self.grid_file) as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0].strip())
            self.height = len(lines)

            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)

            for r, row in enumerate(lines):
                for c, col in enumerate(row.strip()):
                    if col in ["v", "^", ">", "<", "+", "1", "2", "3", "4"]:
                        dir_map = {"1": "Up", "2": "Down", "3": "Left", "4": "Right"}
                        road_dir = dir_map.get(col, dataDictionary.get(col, "Intersection"))
                        agent = Road(f"r_{r*self.width+c}", self, road_dir)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        if col in ["v", "^", ">", "<"]:
                            positions_temp.append((c, self.height - r - 1))

                    elif col in ["S", "s"]:
                        # Place a Road under the Traffic Light for direction context
                        road_agent = Road(f"r_{r*self.width+c}", self, "Intersection")
                        self.grid.place_agent(road_agent, (c, self.height - r - 1))
                        
                        agent = Traffic_Light(f"tl_{r*self.width+c}", self, False if col == "S" else True, int(dataDictionary[col]))
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)
                        self.traffic_lights.append(agent)

                    elif col == "#":
                        agent = Obstacle(f"ob_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))

                    elif col == "A":
                        agent = Angel(f"ob_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))

                    elif col == "D":
                        agent = Destination(f"d_{r*self.width+c}", self)
                        self.schedule.add(agent)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        destinys_temp.append((c, self.height - r - 1))

                    elif col == "P":
                        # Place a Road under the Parking for direction context
                        road_agent = Road(f"r_{r*self.width+c}", self, "Intersection")
                        self.grid.place_agent(road_agent, (c, self.height - r - 1))
                        
                        agent = Parking(f"pk_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        pedPos_temp.append((c, self.height - r - 1))

                    elif col in ["B", "E"]:
                        agent = SideWalk(f"sw_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        pedPos_temp.append((c, self.height - r - 1))

                    elif col in ["Z", "z"]:
                        # Place a Road under the Pedestrian Crossing
                        road_agent = Road(f"r_{r*self.width+c}", self, "Intersection")
                        self.grid.place_agent(road_agent, (c, self.height - r - 1))
                        
                        agent = PedestrianCrossing(f"pc_{r*self.width+c}", self)
                        if col == "Z":
                            agent.vertical = True
                        else:
                            agent.horizontal = True
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)
                        pedPos_temp.append((c, self.height - r - 1))

        for i in range(self.num_agents):
            if destinys_temp and positions_temp:
                destpos = self.random.choice(destinys_temp)
                a = Car(i+1000, self, destpos)
                pos = self.random.choice(positions_temp)
                while any(isinstance(agent, Car) for agent in self.grid.get_cell_list_contents(pos)):
                    pos = self.random.choice(positions_temp)
                self.schedule.add(a)
                self.grid.place_agent(a, pos)

        for i in range(self.num_agents):
            if destinys_temp and pedPos_temp:
                destpos = self.random.choice(destinys_temp)
                a = Pedestrian(i+2000, self, destpos)
                pos = self.random.choice(pedPos_temp)
                self.schedule.add(a)
                self.grid.place_agent(a, pos)
                
        if positions_temp:
            b = Bus(3000, self)
            pos = self.random.choice(positions_temp)
            self.schedule.add(b)
            self.grid.place_agent(b, pos)

    def build_graphs(self):
        # Read the grid into a matrix
        with open(self.grid_file or GRID_FILE_PATH, 'r') as f:
            matrix_inverted = [list(line.strip()) for line in f]
        
        matrix = list(reversed(matrix_inverted))
        rows = len(matrix)
        cols = len(matrix[0])

        road_graph = {}
        ped_graph = {}
        road_edges = []
        
        road_chars = ["v", "^", ">", "<", "+", "S", "s", "Z", "z", "D", "A", "P", "1", "2", "3", "4"]
        ped_chars = ["B", "E", "Z", "z", "D", "S", "s", "P"]

        for y in range(rows):
            for x in range(cols):
                c = matrix[y][x]
                source = (y, x)
                
                # Potential neighbors
                neighbors = [
                    (x, y + 1, "^"), (x, y - 1, "v"),
                    (x - 1, y, "<"), (x + 1, y, ">")
                ]
                
                # --- Road Graph ---
                if c in road_chars:
                    if source not in road_graph: road_graph[source] = []
                    for nx, ny, move_dir in neighbors:
                        if not (0 <= nx < cols and 0 <= ny < rows): continue
                        nc = matrix[ny][nx]
                        if nc not in road_chars: continue
                        
                        dir_symbols = {"^": "1", "v": "2", "<": "3", ">": "4"}
                        can_move = False
                        if c in ["+", "S", "s", "Z", "z", "A", "D", "P", "1", "2", "3", "4"]:
                            if nc in ["+", "S", "s", "Z", "z", "A", "D", "P", "1", "2", "3", "4"] or nc == move_dir or nc == dir_symbols.get(move_dir):
                                can_move = True
                        elif c == move_dir or c == dir_symbols.get(move_dir):
                            if nc in ["+", "S", "s", "Z", "z", "A", "D", "P", "1", "2", "3", "4"] or nc == move_dir or nc == dir_symbols.get(move_dir):
                                can_move = True
                        
                        if can_move:
                            target = (ny, nx)
                            road_graph[source].append((1.0, target))
                            road_edges.append((source, target, 1.0))

                # --- Pedestrian Graph ---
                if c in ped_chars:
                    if source not in ped_graph: ped_graph[source] = []
                    for nx, ny, _ in neighbors:
                        if not (0 <= nx < cols and 0 <= ny < rows): continue
                        nc = matrix[ny][nx]
                        if nc in ped_chars:
                            target = (ny, nx)
                            ped_graph[source].append((1.0, target))

        return road_edges, road_graph, ped_graph

    def step(self):
        if self.schedule.steps % 15 == 0:
            for agent in self.traffic_lights:
                agent.state = not agent.state
        self.schedule.step()

    def get_state_snapshot(self) -> dict:
        agents_data = []
        lights_data = []

        for agent in self.schedule.agents:
            # We map legacy agent state to the frontend's expected schema
            if isinstance(agent, Car):
                agents_data.append({
                    "id": agent.unique_id,
                    "x": agent.pos[0] if agent.pos else -1,
                    "y": agent.pos[1] if agent.pos else -1,
                    "type": "CarAgent",
                    "has_arrived": agent.inDestiny,
                    "parked": agent.inDestiny,
                    "waiting": not agent.moving,
                    "destination": {"x": agent.destiny[0], "y": agent.destiny[1]} if agent.destiny else None
                })
            elif isinstance(agent, Pedestrian):
                agents_data.append({
                    "id": agent.unique_id,
                    "x": agent.pos[0] if agent.pos else -1,
                    "y": agent.pos[1] if agent.pos else -1,
                    "type": "PedestrianAgent",
                    "has_arrived": agent.indestiny,
                    "crossing": False, 
                    "waiting": False,
                    "despawned": agent.indestiny,
                    "destination": None
                })
            elif isinstance(agent, Bus):
                agents_data.append({
                    "id": agent.unique_id,
                    "x": agent.pos[0] if agent.pos else -1,
                    "y": agent.pos[1] if agent.pos else -1,
                    "type": "BusAgent",
                    "has_arrived": False,
                    "waiting": not agent.moving,
                    "route_index": 0,
                    "destination": None
                })
            elif isinstance(agent, Traffic_Light):
                lights_data.append({
                    "id": agent.unique_id,
                    "x": agent.pos[0] if agent.pos else -1,
                    "y": agent.pos[1] if agent.pos else -1,
                    "direction": "N", # Frontend doesn't care
                    "state": "green" if agent.state else "red",
                    "timer": agent.timeToChange
                })

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
            "grid": grid_lines
        }
