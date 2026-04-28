"""Data Transfer Objects for API responses."""

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class PositionDTO(BaseModel):
    """Position in the grid."""
    x: int
    y: int


class CarStateDTO(BaseModel):
    """Car agent state for API response."""
    id: int
    x: int
    y: int
    type: str = "CarAgent"
    has_arrived: bool
    parked: bool
    waiting: bool
    destination: Optional[PositionDTO] = None


class PedStateDTO(BaseModel):
    """Pedestrian agent state for API response."""
    id: int
    x: int
    y: int
    type: str = "PedestrianAgent"
    has_arrived: bool
    crossing: bool
    waiting: bool
    despawned: bool
    destination: Optional[PositionDTO] = None


class LightStateDTO(BaseModel):
    """Traffic light state for API response."""
    id: int
    x: int
    y: int
    direction: str
    state: str
    timer: int


class SimulationStateDTO(BaseModel):
    """Full simulation state snapshot."""
    tick: int
    agents: list[dict]
    traffic_lights: list[dict]
    grid_width: int
    grid_height: int


class StatsDTO(BaseModel):
    """Simulation statistics."""
    tick: int
    active_cars: int
    active_pedestrians: int
    parked_cars: int
    waiting_cars: int
    waiting_pedestrians: int
    total_traffic_lights: int


class ConfigDTO(BaseModel):
    """Simulation configuration."""
    grid_width: int
    grid_height: int
    max_cars: int
    max_pedestrians: int
    car_spawn_count: int
    ped_spawn_count: int
    building_count: int
    traffic_light_count: int
