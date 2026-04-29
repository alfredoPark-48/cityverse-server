"""Domain constants and enumerations."""

from enum import Enum


class CellType(str, Enum):
    """Types of cells in the city grid."""

    ROAD = "road"
    SIDEWALK = "sidewalk"
    CROSSWALK = "crosswalk"
    BUILDING = "building"
    TRAFFIC_LIGHT = "traffic_light"
    PARKING = "parking"
    VEGETATION = "vegetation"
    WATER = "water"
    ANGEL = "angel"
    PED_SPAWN = "ped_spawn"
    CAR_SPAWN = "car_spawn"


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
    "I": CellType.ROAD,  # Intersection
    "B": CellType.BUILDING,
    "L": CellType.BUILDING,
    "S": CellType.SIDEWALK,
    "P": CellType.PARKING,
    "T": CellType.TRAFFIC_LIGHT,  # Long
    "t": CellType.TRAFFIC_LIGHT,  # Short
    "V": CellType.VEGETATION,  # Vegetation
    "W": CellType.WATER,
    "D": CellType.DESTINATION,  # Destination
    "A": CellType.ANGEL,  # Angel
    "X": CellType.CROSSWALK,
    "x": CellType.CROSSWALK,
    "p": CellType.PED_SPAWN,
    "c": CellType.CAR_SPAWN,
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
