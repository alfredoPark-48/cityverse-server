"""Domain constants and enumerations."""

from enum import Enum


class CellType(str, Enum):
    """Types of cells in the city grid."""

    ROAD = "road"
    SIDEWALK = "sidewalk"
    CROSSWALK = "crosswalk"
    BUILDING = "building"
    TRAFFIC_LIGHT = "traffic_light"
    EMPTY = "empty"
    ROUNDABOUT = "roundabout"
    PARKING = "parking"
    GRASS = "grass"


class TrafficLightState(str, Enum):
    """States for a traffic light."""

    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


# Grid character → CellType mapping
CHAR_TO_CELL_TYPE: dict[str, CellType] = {
    "v": CellType.ROAD,
    "^": CellType.ROAD,
    ">": CellType.ROAD,
    "<": CellType.ROAD,
    "+": CellType.ROAD, # Intersection
    "B": CellType.SIDEWALK,
    "S": CellType.TRAFFIC_LIGHT, # Red
    "s": CellType.TRAFFIC_LIGHT, # Green
    "#": CellType.BUILDING, # Obstacle
    "D": CellType.BUILDING, # Destination
    "A": CellType.ROUNDABOUT, # Angel
    "Z": CellType.CROSSWALK,
    "z": CellType.CROSSWALK,
}

# Characters that represent directional roads
ROAD_DIRECTION_CHARS: set[str] = {"v", "^", ">", "<"}

# Traffic light direction characters → direction name (Legacy from city_grid, kept for compatibility if needed)
TRAFFIC_LIGHT_DIRECTION: dict[str, str] = {
    "D": "S",  # Down → South-facing
    "U": "N",  # Up → North-facing
    "R": "E",  # Right → East-facing
    "L": "W",  # Left → West-facing
}
