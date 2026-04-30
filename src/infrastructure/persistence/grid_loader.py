"""Infrastructure service to load and parse city grids."""

import json
import os
from src.domain.entities.traffic_components import (
    Road, Traffic_Light, Water, Building, Vegetation, SideWalk, 
    Angel, Destination, Parking, Lot, Home, CarSpawn, PedestrianSpawn,
    PedestrianCrossing
)

class GridLoader:
    """Loads grid data from files and creates initial agents."""

    @staticmethod
    def load_map_dictionary(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Map dictionary not found: {path}")
        with open(path, "r") as f:
            return json.load(f)

    @staticmethod
    def parse_grid_file(model, file_path, data_dict):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Grid file not found: {file_path}")
            
        with open(file_path, "r") as f:
            lines = f.readlines()
            
        width = len(lines[0].strip())
        height = len(lines)
        
        # Temporary lists for model initialization
        temp_data = {
            "positions": [],
            "ped_positions": [],
            "destinations": [],
            "parking": [],
            "car_spawns": [],
            "ped_spawns": [],
            "traffic_lights": []
        }

        for r, row in enumerate(lines):
            for c, col in enumerate(row.strip()):
                pos = (c, height - r - 1)
                
                if col in ["v", "^", ">", "<", "I", "1", "2", "3", "4"]:
                    road_dir = data_dict.get(col, "Intersection")
                    agent = Road(f"r_{r * width + c}", model, road_dir)
                    if col in ["1", "2", "3", "4"]:
                        agent.is_bus_stop = True
                    model.grid.place_agent(agent, pos)
                    if col in ["v", "^", ">", "<", "1", "2", "3", "4"]:
                        temp_data["positions"].append(pos)
                        
                elif col in ["T", "t"]:
                    road_agent = Road(f"r_{r * width + c}", model, "Intersection")
                    model.grid.place_agent(road_agent, pos)
                    agent = Traffic_Light(f"tl_{r * width + c}", model, False if col == "T" else True, int(data_dict[col]))
                    model.grid.place_agent(agent, pos)
                    model.schedule.add(agent)
                    temp_data["traffic_lights"].append(agent)
                    
                elif col == "W":
                    model.grid.place_agent(Water(f"w_{r * width + c}", model), pos)
                elif col == "B":
                    model.grid.place_agent(Building(f"b_{r * width + c}", model), pos)
                elif col == "V":
                    model.grid.place_agent(Vegetation(f"v_{r * width + c}", model), pos)
                elif col == "S":
                    model.grid.place_agent(SideWalk(f"s_{r * width + c}", model), pos)
                    temp_data["ped_positions"].append(pos)
                elif col == "A":
                    model.grid.place_agent(Angel(f"a_{r * width + c}", model), pos)
                elif col == "D":
                    agent = Destination(f"d_{r * width + c}", model)
                    model.schedule.add(agent)
                    model.grid.place_agent(agent, pos)
                    temp_data["destinations"].append(pos)
                elif col == "P":
                    model.grid.place_agent(Parking(f"p_{r * width + c}", model), pos)
                    temp_data["parking"].append(pos)
                    temp_data["ped_positions"].append(pos)
                elif col == "L":
                    model.grid.place_agent(Lot(f"l_{r * width + c}", model), pos)
                    temp_data["ped_positions"].append(pos)
                elif col == "H":
                    model.grid.place_agent(Home(f"h_{r * width + c}", model), pos)
                elif col == "c":
                    model.grid.place_agent(CarSpawn(f"cs_{r * width + c}", model), pos)
                    temp_data["car_spawns"].append(pos)
                elif col == "p":
                    model.grid.place_agent(PedestrianSpawn(f"ps_{r * width + c}", model), pos)
                    temp_data["ped_spawns"].append(pos)
                elif col in ["X", "x"]:
                    road_agent = Road(f"r_{r * width + c}", model, "Intersection")
                    model.grid.place_agent(road_agent, pos)
                    agent = PedestrianCrossing(f"pc_{r * width + c}", model)
                    if col == "X": agent.vertical = True
                    else: agent.horizontal = True
                    model.grid.place_agent(agent, pos)
                    model.schedule.add(agent)
                    temp_data["ped_positions"].append(pos)

        return width, height, temp_data
