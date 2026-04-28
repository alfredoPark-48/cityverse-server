# CityVerse Traffic Simulation

Agent-based traffic simulation for a smart city environment, built with Mesa and FastAPI.

## Clean Architecture Structure

The project follows a clean architecture approach, separated into the following layers:

- `src/domain/entities`: Contains all core simulation agents (Cars, Buses, Pedestrians, Traffic Lights, etc.)
- `src/application/services`: Contains algorithmic services (e.g., Graph Dijkstra Pathfinding).
- `src/infrastructure/models`: Contains the Mesa `CityModel` which orchestrates the simulation.
- `src/infrastructure/api`: Contains the FastAPI server for serving the simulation state to the frontend.

## Agent Documentation

This simulation uses a variety of agents to represent the dynamic and static components of the city.

### Moving Agents

1. **Car**
   - **Role**: Simulates standard vehicle traffic.
   - **Behavior**: Cars spawn at predefined road edges (`positions_temp`) and pick a random destination building (`Destination`). They use Dijkstra's Algorithm (`Graph.py` logic) to compute the shortest path to their destination. At intersections, they dynamically choose the next edge to travel.
   - **Traffic Rules**: Cars will stop for red `Traffic_Light`s, yield to `Pedestrian`s at `PedestrianCrossing`s, and stop if there is another vehicle directly in front of them to prevent collisions.

2. **Bus**
   - **Role**: Simulates public transit.
   - **Behavior**: Buses follow a hardcoded, predefined loop route `[(1,9),(6,8),(22,11)]`. They move strictly from coordinate to coordinate.
   - **Traffic Rules**: Like cars, they respect traffic lights, pedestrian crossings, and vehicle collisions.

3. **Pedestrian**
   - **Role**: Simulates foot traffic.
   - **Behavior**: Pedestrians spawn on `SideWalk`s and wander randomly. They prioritize moving to adjacent sidewalks, crosswalks, and destinations. They keep a `visited` list to avoid walking back and forth immediately.
   - **Traffic Rules**: Pedestrians will stop at `PedestrianCrossing`s if a car is currently occupying it, and they will wait at `Traffic_Light`s until it is safe to cross. They disappear upon reaching a `Destination`.

### Static Agents (Traffic Components)

1. **Traffic_Light (S, s)**
   - **Role**: Controls traffic flow at intersections.
   - **Behavior**: Toggles between Green (True) and Red (False) every 15 simulation steps. Cars and buses check the state of the traffic light before proceeding into the intersection.

2. **PedestrianCrossing (Z, z)**
   - **Role**: Safe zones for pedestrians to cross roads.
   - **Behavior**: Detects whether a `Car`, `Bus`, or `Pedestrian` is currently over it. If a car is over it, pedestrians wait. If a pedestrian is over it, cars wait.

3. **Destination (D)**
   - **Role**: The end goal for cars and pedestrians.
   - **Behavior**: When a car or pedestrian enters a destination cell, they have "arrived" and are removed from the active simulation schedule.

4. **Road (v, ^, <, >, +)**
   - **Role**: Dictates the valid paths and directions for vehicles.
   - **Behavior**: Provides directional metadata to cars. `+` represents an intersection where cars will consult their calculated Dijkstra path.

5. **Obstacle (#)**
   - **Role**: Impassable buildings or walls.
   - **Behavior**: Purely static. Agents cannot pathfind through them.

6. **Angel (A)**
   - **Role**: A roundabout obstacle.
   - **Behavior**: Purely static, placed to force traffic to flow around a central point.

7. **SideWalk (B)**
   - **Role**: Safe walking paths for pedestrians.
   - **Behavior**: Purely static. Pedestrians prioritize these tiles.

## Running the Simulation

1. Ensure Docker and Docker Compose are installed.
2. Run `docker compose up --build`
3. Navigate to `http://localhost:8000` to view the live simulation dashboard.
