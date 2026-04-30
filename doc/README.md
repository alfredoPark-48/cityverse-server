# CityVerse Server Documentation

## Context: Project-Multiagentes Legacy
This project is an evolution of the [Project-Multiagentes](https://github.com/ivalani/Project-Multiagentes), which was originally developed as a university project for urban mobility simulation.

### Key Improvements in CityVerse
CityVerse adds significant features, revamps the architecture, and fixes numerous bugs from the legacy version:

1. **Architecture Revamp**:
   - Transitioned from a monolithic script to a **Clean Architecture** (Domain, Application, Infrastructure layers).
   - Implementation of **SOLID principles** to ensure maintainability and scalability.
   - Separation of concerns: Mesa-specific logic is now isolated in the Infrastructure layer.

2. **Agent Logic Enhancements**:
   - **Unified Navigation**: Pathfinding is now centralized in a `NavigationService`, reducing duplication between Car, Bus, and Pedestrian agents.
   - **Robust Collision System**: Improved rules for traffic lights, pedestrian crossings, and inter-agent collisions.
   - **Bus Logic**: Real routes parsed from JSON, proper boarding/alighting mechanics, and capacity management.

3. **Performance & Stability**:
   - Optimized graph building and A* search.
   - Fixed "ghost agents" and memory leaks by implementing proper agent lifecycle management (arrive-and-despawn).
   - Improved grid parsing and validation.

4. **Modern Interface**:
   - Added a high-fidelity frontend (Web) that communicates via a standardized API.
   - Real-time statistics and simulation control.

## Project Structure (New)
- `src/domain`: Core business logic, entities, and value objects.
- `src/application`: Use cases and services that orchestrate domain logic.
- `src/infrastructure`: External tools (Mesa, Flask/SocketIO), data persistence, and API.
- `src/shared`: Constants and utility functions.
- `data/`: Simulation configuration, grid maps, and route definitions.
- `frontend/`: Modern web-based visualization.
