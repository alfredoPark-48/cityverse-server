# CityVerse Architecture

This document describes the architectural patterns and design principles used in the CityVerse Server.

## 1. Clean Architecture Layers

### Domain Layer (`src/domain`)
The heart of the application. Contains business entities and core rules.
- **Entities**: `Car`, `Pedestrian`, `Bus`. These encapsulate state and high-level behaviors.
- **Value Objects**: Shared data structures like positions and directions.
- **Base Classes**: `BaseTrafficAgent` provides a template for all moving agents.

### Application Layer (`src/application`)
Orchestrates the flow of data to and from the domain.
- **Services**: `NavigationService` (pathfinding), `SpawningService` (population management), `GraphService` (network topology).
- **Orchestration**: `SimulationService` acts as the primary API for external layers (Infrastructure).

### Infrastructure Layer (`src/infrastructure`)
Handles technical details and external integrations.
- **Mesa Model**: `CityModel` implements the actual simulation loop using the Mesa framework.
- **Persistence**: `GridLoader` handles file I/O for grid maps and map dictionaries.
- **API**: (In progress) Flask/SocketIO endpoints for frontend communication.

## 2. Design Principles (SOLID)

- **Single Responsibility (SRP)**: Each service has a specific role. `GridLoader` only parses files; `NavigationService` only handles movement logic.
- **Open/Closed (OCP)**: New agent types can be added by inheriting from `BaseTrafficAgent` without modifying the core simulation loop.
- **Liskov Substitution (LSP)**: All traffic agents can be handled interchangeably by the simulation schedule.
- **Interface Segregation (ISP)**: Services are modular and only expose necessary methods.
- **Dependency Inversion (DIP)**: High-level application logic depends on abstractions (Base classes and Service interfaces) rather than concrete Mesa implementations where possible.

## 3. Design Patterns

- **Strategy Pattern**: Pathfinding algorithms are encapsulated in `NavigationService`, allowing for easy swapping (e.g., from A* to BFS).
- **Template Method**: `BaseTrafficAgent.step()` defines the skeleton of an agent's turn, while subclasses implement specific `move()` and `calculate_path()` logic.
- **Factory/Loader**: `GridLoader` acts as a factory for initializing the city grid from static files.
