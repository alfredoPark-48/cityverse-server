"""Grid repository – loads and parses city_grid.txt into domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.domain.entities.building import Building
from src.domain.entities.traffic_light import TrafficLight
from src.domain.value_objects.direction import Direction
from src.domain.value_objects.grid_cell import GridCell
from src.domain.value_objects.position import Position
from src.shared.constants import (
    CHAR_TO_CELL_TYPE,
    CellType,
    ROAD_DIRECTION_CHARS,
    TRAFFIC_LIGHT_DIRECTION,
)


@dataclass
class GridData:
    """Parsed grid data returned by the repository."""

    width: int
    height: int
    grid: list[list[GridCell]]
    traffic_lights: list[TrafficLight]
    buildings: list[Building]
    roundabout_cells: list[Position]
    car_spawns: list[Position]
    ped_spawns: list[Position]


class GridRepository:
    """Loads and parses a city grid text file."""

    def load(self, filepath: str) -> GridData:
        """Parse a grid file and return structured GridData."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Grid file not found: {filepath}")

        raw_lines = path.read_text().strip().splitlines()
        if not raw_lines:
            raise ValueError("Grid file is empty")

        height = len(raw_lines)
        width = len(raw_lines[0])

        grid: list[list[GridCell]] = []
        traffic_lights: list[TrafficLight] = []
        building_positions: list[Position] = []
        roundabout_cells: list[Position] = []
        car_spawns: list[Position] = []
        ped_spawns: list[Position] = []

        light_id = 0

        for y, line in enumerate(raw_lines):
            if len(line) != width:
                raise ValueError(
                    f"Row {y} has {len(line)} chars, expected {width}"
                )

            row: list[GridCell] = []
            for x, char in enumerate(line):
                pos = Position(x, y)
                cell_type = CHAR_TO_CELL_TYPE.get(char)

                if cell_type is None:
                    raise ValueError(
                        f"Unknown character '{char}' at ({x}, {y})"
                    )

                cell = GridCell(position=pos, cell_type=cell_type, raw_char=char)
                row.append(cell)

                # Collect special positions
                if cell_type == CellType.TRAFFIC_LIGHT:
                    direction_str = TRAFFIC_LIGHT_DIRECTION[char]
                    traffic_lights.append(
                        TrafficLight(
                            light_id=light_id,
                            position=pos,
                            direction=Direction(direction_str),
                        )
                    )
                    light_id += 1

                elif cell_type == CellType.BUILDING:
                    building_positions.append(pos)

                elif cell_type == CellType.ROUNDABOUT:
                    roundabout_cells.append(pos)

            grid.append(row)

        # Detect road cells near the edge as car spawn points
        # The grid perimeter is typically sidewalk, so look within 2 cells
        edge_margin = 2
        for y in range(height):
            for x in range(width):
                cell = grid[y][x]
                near_edge = (
                    x < edge_margin
                    or x >= width - edge_margin
                    or y < edge_margin
                    or y >= height - edge_margin
                )
                if near_edge and cell.cell_type == CellType.ROAD and cell.raw_char in ROAD_DIRECTION_CHARS:
                    car_spawns.append(cell.position)

        # Detect edge sidewalk cells as pedestrian spawn points
        for y in range(height):
            for x in range(width):
                cell = grid[y][x]
                if cell.cell_type == CellType.SIDEWALK:
                    if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                        ped_spawns.append(cell.position)

        # Group adjacent building cells into Building entities
        buildings = self._group_buildings(building_positions, grid, width, height)

        return GridData(
            width=width,
            height=height,
            grid=grid,
            traffic_lights=traffic_lights,
            buildings=buildings,
            roundabout_cells=roundabout_cells,
            car_spawns=car_spawns,
            ped_spawns=ped_spawns,
        )

    def _group_buildings(
        self,
        positions: list[Position],
        grid: list[list[GridCell]],
        width: int,
        height: int,
    ) -> list[Building]:
        """Group adjacent building cells into Building entities using flood fill."""
        visited: set[Position] = set()
        buildings: list[Building] = []
        building_id = 0

        pos_set = set(positions)

        for pos in positions:
            if pos in visited:
                continue

            # Flood-fill to find connected building cells
            cluster: list[Position] = []
            stack = [pos]
            while stack:
                current = stack.pop()
                if current in visited or current not in pos_set:
                    continue
                visited.add(current)
                cluster.append(current)

                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = current.x + dx, current.y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        neighbor = Position(nx, ny)
                        if neighbor not in visited and neighbor in pos_set:
                            stack.append(neighbor)

            # Find entrance: first adjacent road/sidewalk cell
            entrance = self._find_entrance(cluster, grid, width, height)

            buildings.append(
                Building(
                    building_id=building_id,
                    positions=cluster,
                    entrance=entrance,
                )
            )
            building_id += 1

        return buildings

    @staticmethod
    def _find_entrance(
        cluster: list[Position],
        grid: list[list[GridCell]],
        width: int,
        height: int,
    ) -> Position | None:
        """Find the first adjacent road or sidewalk cell as the building entrance."""
        for pos in cluster:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = pos.x + dx, pos.y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbor = grid[ny][nx]
                    if neighbor.cell_type in {CellType.ROAD, CellType.SIDEWALK, CellType.PARKING}:
                        return Position(nx, ny)
        return None
