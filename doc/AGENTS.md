# CityVerse: Agent Behaviors & Logic

This document details the state machines and decision-making logic of the various agents within CityVerse. For details on the underlying data structures and pathfinding mathematics, see [Algorithms & Data Structures](./ALGORITHMS.md).

## 1. The Multi-Agent System (MAS)

CityVerse follows a **Decentralized Multi-Agent approach**. Each entity is an independent actor with local perception, responsible for its own navigation and collision avoidance.

### Base Class: `BaseTrafficAgent`
All moving agents inherit from this abstract base class to ensure consistent state management and visualization.
- **Attributes**: `pos`, `destination`, `path`, `is_moving`, `has_arrived`.
- **Life Cycle**: 
    1. `calculate_path()`: Invoked at spawn or if the path is blocked.
    2. `move()`: Executes the next step in the path if the cell is clear.
    3. `step()`: Orchestrates the above via the Mesa scheduler.

---

## 2. Agent Specifications

### Car Agent (`car.py`)
Cars represent the primary vehicular traffic.
- **Decision Logic**: Cars follow the **Road Graph**, which enforces one-way street constraints.
- **Traffic Awareness**:
    - **Traffic Lights**: Respects state changes. If a light is Red, the car stops *before* entering the cell.
    - **Intersections**: Implements a "Clearance" rule — if already inside an intersection, the car will finish its move even if the light changes, preventing gridlock.
    - **Vehicle Following**: Maintains a 1-cell safety buffer with the vehicle ahead.

### Pedestrian Agent (`pedestrian.py`)
Pedestrians are the most complex agents due to their multimodal nature.
- **State Machine**:
    - `WALKING`: Navigating sidewalks and crossings.
    - `WAITING`: Waiting at a bus stop after evaluating the public transport system is efficient.
    - `BOARDING`: A transient state where the agent is moved from the grid into the Bus's passenger list.
    - `ON_BUS`: State where movement is controlled by the Bus agent.
- **Smart Routing**: Upon spawning, pedestrians calculate the walk-distance to their goal. If a Bus route exists that reduces their travel time by >30%, they dynamically update their goal to the nearest Bus Stop.

### Bus Agent (`bus.py`)
Buses follow fixed loops and act as "Parent Agents" for passengers.
- **Route Management**: Follows ordered stops defined in `bus_routes.json`.
- **Passenger Handling**: 
    - At each stop, it checks for `Pedestrian` agents in the `WAITING` state.
    - It drops off passengers who have reached their destination or have exceeded their "Frustration Threshold" (ride time > 200 ticks).

---

## 3. Environment Layout

The city is parsed from `data/city.txt`. The mapping is as follows:

| Character | Entity | Role |
| :--- | :--- | :--- |
| `^`, `v`, `>`, `<` | Road | One-way directed traffic. |
| `I` | Intersection | Bi-directional road crossing. |
| `T`, `t` | Traffic Light | Timed signal (T=starts green, t=starts red). |
| `S` | Sidewalk | Pedestrian-only navigation nodes. |
| `1`, `2`, `3`, `4` | Bus Stop | Interaction points for the Bus system. |
| `D`, `P` | Arrive/Despawn | Buildings and Parking lots for trip completion. |
