"""Application configuration constants."""

import os

GRID_FILE_PATH: str = os.getenv("GRID_FILE", "data/2022_base.txt")
TICKS_PER_SECOND: int = int(os.getenv("TICKS_PER_SECOND", "10"))
MAX_CARS: int = int(os.getenv("MAX_CARS", "10"))
MAX_PEDESTRIANS: int = int(os.getenv("MAX_PEDESTRIANS", "15"))
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
