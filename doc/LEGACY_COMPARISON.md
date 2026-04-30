# Legacy Comparison: Evolution of the Codebase

This document contrasts the legacy implementation ([Project-Multiagentes](https://github.com/ivalani/Project-Multiagentes)) with the current **CityVerse** architecture. This evolution represents a transition to a more modular and robust system.

## 1. Architectural Structure

| Feature | Legacy Implementation | CityVerse (Refactored) |
| :--- | :--- | :--- |
| **Organization** | Monolithic `agent.py` (500+ lines). | Decoupled layers (Domain, Application, Infra). |
| **Agent Logic** | Mixed concerns: Movement, Pathfinding, and UI state. | Separation of Concerns: Movement via `NavigationService`. |
| **Scalability** | Hard to extend; adding a "Bus" required manual hacks. | Highly extensible via `BaseTrafficAgent` inheritance. |
| **Reliability** | Agents frequently got "stuck" on isolated nodes. | Robust BFS-fallback logic for topological safety. |

---

## 2. Code Snippets: The "Refactoring" in Action

### Handling Movement & Decisions

**Legacy (`agent.py`)**: Massive conditional chains that are hard to test and prone to regression.
```python
# Legacy: 100+ line move() method with nested conditionals
def move(self):
    if self.direction == "Up":
        next_move = (self.pos[0], self.pos[1] + 1)
    elif self.direction == "Down":
        # ... 20 more lines of direction logic ...
    
    whatIsFront = self.model.grid.get_neighbors(next_move, radius=0)
    if not whatIsFront:
        self.model.grid.move_agent(self, next_move)
    elif isinstance(whatIsFront[0], Traffic_Light):
        # ... logic for every possible agent type ...
```

**CityVerse (`car.py` + `NavigationService`)**: Clean, delegated logic.
```python
# Modern: Delegation to specialized services
def move(self):
    next_move = self.path[0]
    
    # Logic is encapsulated in a reusable service
    is_blocked = NavigationService.is_cell_blocked(self.model, next_move, "Car", self)

    if not is_blocked:
        self.model.grid.move_agent(self, next_move)
        self.path.pop(0)
```

---

## 3. Pathfinding Improvements

### Legacy: Manual Path Popping
The legacy code manually popped coordinates and performed coordinate transformations (x/y to y/x) inside the agent's `step()` function. This led to "off-by-one" errors and difficult debugging.

### CityVerse: Centralized Navigation
In CityVerse, pathfinding is a **Service**. Agents simply request a path, and the `NavigationService` handles the complexities of graph traversal, coordinate mapping, and error recovery.

---

## 4. Why A* is better than Dijkstra? (Engineering Advantages)

In the legacy code, pathfinding was often treated as a "Uniform Cost Search" (Dijkstra-like). In our refactor, we explicitly moved to **A***, which yields several critical advantages:

### Behavioral Shift: Intentionality vs. Exploration
- **Legacy Behavior**: Car agents frequently exhibited a "wandering" or "exploring" behavior. Because Dijkstra expands in all directions equally, agents often moved to neighboring road cells that weren't strictly on the optimal path to the goal, making them look like they were searching for the way.
- **CityVerse Behavior**: A* provides agents with **clear intentionality**. By using a heuristic (Manhattan Distance), agents calculate the most direct route and follow it strictly. This results in realistic traffic flow where vehicles move purposefully towards their destinations.

### Computational Efficiency
- **Search Space**: Dijkstra explores a circular area around the start node (evaluating up to $N^2$ nodes). A* explores a narrow "beam" towards the goal.
- **Impact**: This reduction in search space allows CityVerse to handle a significantly higher agent density (from 30 agents in legacy to 100+ in the current build) without dropping the simulation's Ticks-Per-Second (TPS).
