# CityVerse: Architectural Blueprint

This document outlines the design decisions and architectural patterns used in the CityVerse Server.

## 1. Clean Architecture Layers

CityVerse follows a 3-tier architecture to ensure a clear separation of concerns between core logic, application orchestration, and infrastructure details.

### Domain Layer (`src/domain`)
- **Core Entities**: `Car`, `Pedestrian`, and `Bus` inherit from a unified `BaseTrafficAgent`.
- **State Management**: Agents maintain their own internal state (e.g., `on_bus`, `is_boarding`, `has_arrived`).

### Application Layer (`src/application`)
- **Services**: 
    - `NavigationService`: Centralizes pathfinding logic using A*.
    - `SpawningService`: Manages the lifecycle and replenishment of agents.
    - `GraphService`: Transforms grid data into a traversable directed graph.

### Infrastructure Layer (`src/infrastructure`)
- **Framework Integration**: Encapsulates the Mesa simulation engine.
- **Persistence**: Handles file I/O for the city grid (`city.txt`) and configuration.

---

## 2. Key Design Decisions

### Navigation Fallback Strategy
To ensure system stability, the `NavigationService` implements a fallback mechanism. Before pathfinding, the system uses a Breadth-First Search (BFS) to identify the reachable subgraph. If a target is topologically isolated, the agent dynamically re-routes to the closest reachable node to its destination.

### Multimodal State Machine
The pedestrian lifecycle is managed via a state machine that handles transitions between walking and public transport. When a pedestrian boards a bus, they are removed from the spatial index to prevent collisions but remain in the schedule to track their internal metrics.

### Collision Reservation System
CityVerse uses a reservation-based logic during the movement phase. Agents check if their intended next move is already occupied or reserved by a higher-priority agent (e.g., a Bus), preventing overlapping in discrete grid space.

---

## 3. Design Principles
- **Single Responsibility (SRP)**: Each service (e.g., `GridLoader`) has a single, well-defined role.
- **Open/Closed (OCP)**: New agent types or transport modes can be added by extending the `BaseTrafficAgent` without modifying the core simulation loop.
- **Dependency Inversion (DIP)**: High-level application logic depends on service abstractions rather than the specific details of the Mesa framework.
