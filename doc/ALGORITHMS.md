# CityVerse: Data Structures & Algorithms

This document provides a technical breakdown of the core algorithms and data structures that power the CityVerse simulation. It is designed to be accessible to junior developers while providing the depth required for a technical interviewer to assess the system's engineering quality.

---

## 1. A* Pathfinding (The "Navigation Brain")

### What is it?
A* (A-star) is a graph traversal and pathfinding algorithm that is both efficient and optimal. It is an extension of Dijkstra's algorithm but uses a **Heuristic** to guide its search towards the goal.

- **Formula**: $f(n) = g(n) + h(n)$
    - $g(n)$: The actual cost from the start to the current node.
    - $h(n)$: The estimated cost from the current node to the goal (the heuristic).

### How we use it in CityVerse
Every moving agent (Car, Bus, Pedestrian) uses A* to calculate their route. We use the **Manhattan Distance** as our heuristic because the city is structured as a grid, where movement is restricted to cardinal directions (Up, Down, Left, Right).

### Why it's important
Without A*, agents would either move randomly or use less efficient algorithms like Dijkstra, which would waste CPU cycles exploring the entire city instead of the path to the destination.

🔗 [Learn more about A* on Wikipedia](https://en.wikipedia.org/wiki/A*_search_algorithm)

---

## 2. Breadth-First Search (The "Topological Guard")

### What is it?
BFS is an algorithm for traversing or searching tree or graph data structures. It starts at a node and explores all of its neighbors at the present depth level before moving on to nodes at the next depth level.

### How we use it in CityVerse (Fallback Logic)
We use BFS in our **Navigation Fallback Strategy**. Before running A*, we use BFS to find the "Reachable Set" from the agent's current position. 
- If the target destination is not in the reachable set (e.g., a road that doesn't connect to a building), we use the BFS results to find the **absolute closest reachable node** to the target.

### Why it's important
It prevents "Infinite Loops" and "Stuck Agents." It ensures that even if the city map has a topological error (like an isolated road), the simulation remains robust and agents continue to move.

🔗 [Learn more about BFS on Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)

---

## 3. Directed Graph (The "City Topology")

### What is it?
A graph is a collection of nodes (vertices) and edges. A **Directed Graph** means the edges have a direction (e.g., you can go from A to B, but not necessarily from B to A).

### How we use it in CityVerse
The `GraphService` parses the `city.txt` file and builds an **Adjacency List** representation of the city.
- **Road Graph**: Captures one-way constraints (arrows like `^`, `v`, `<`, `>`).
- **Pedestrian Graph**: Captures bidirectional sidewalks and crosswalks.

### Why it's important
It allows us to model realistic traffic rules. Cars can't go the wrong way on a one-way street because the edge simply doesn't exist in the graph.

🔗 [Learn more about Directed Graphs](https://en.wikipedia.org/wiki/Directed_graph)

---

## 4. Priority Queue / Min-Heap (The "Efficiency Engine")

### What is it?
A Priority Queue is an abstract data type where each element has a "priority." In a Min-Heap implementation, the element with the lowest priority (lowest cost in our case) is always at the front.

### How we use it in CityVerse
A* relies on a Priority Queue to always explore the "most promising" node next. We use Python's `heapq` module to maintain this queue with $O(\log n)$ insertion and $O(1)$ retrieval.

### Why it's important
It is the difference between an algorithm that runs in milliseconds and one that lags the entire simulation. It ensures we always process the most efficient next step first.

🔗 [Learn more about Heaps](https://en.wikipedia.org/wiki/Heap_(data_structure))

---

## 5. Manhattan Distance (The "Heuristic")

### What is it?
The Manhattan Distance is the sum of the absolute differences of their Cartesian coordinates. It is the distance between two points measured along axes at right angles.

### How we use it in CityVerse
In our grid, agents can't move diagonally. Therefore, the Manhattan Distance ($|x_1 - x_2| + |y_1 - y_2|$) is the **perfectly admissible heuristic**, meaning it never overestimates the cost and guarantees that A* will find the shortest path.

### Why it's important
An admissible heuristic is the mathematical requirement for A* to be "optimal." It ensures our agents always take the literal shortest path possible.

🔗 [Learn more about Taxicab Geometry (Manhattan Distance)](https://en.wikipedia.org/wiki/Taxicab_geometry)
