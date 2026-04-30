import json
import os
from typing import List, Tuple, Dict
from src.shared.config import BUS_ROUTES_PATH

class BusRoute:
    """
    Represents a bus route as a sequence of coordinates.
    """
    def __init__(self, route_id: str, stops: List[Tuple[int, int]]):
        self.route_id = route_id
        self.stops = stops

    def __len__(self):
        return len(self.stops)

    def __getitem__(self, index):
        return self.stops[index]

def load_bus_routes() -> Dict[str, BusRoute]:
    """
    Loads bus routes from a JSON file and returns a dictionary of BusRoute objects.
    Falls back to hardcoded defaults if the file is missing or invalid.
    """
    # Hardcoded defaults for resilience
    default_data = {
        "1": [(5, 54), (17, 54), (26, 45), (12, 45)],
        "2": [(5, 42), (18, 42), (33, 42), (48, 42)],
        "3": [(5, 26), (17, 26), (34, 26), (49, 26)],
        "4": [(5, 13), (17, 13), (34, 13), (49, 13)]
    }
    
    default_routes = {rid: BusRoute(rid, stops) for rid, stops in default_data.items()}

    if not os.path.exists(BUS_ROUTES_PATH):
        return default_routes

    try:
        with open(BUS_ROUTES_PATH, "r") as f:
            data = json.load(f)
            return {
                rid: BusRoute(rid, [tuple(stop) for stop in stops])
                for rid, stops in data.items()
            }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Warning: Failed to load bus routes from {BUS_ROUTES_PATH}: {e}. Using defaults.")
        return default_routes

# Initial load of routes
DEFAULT_BUS_ROUTES = load_bus_routes()
