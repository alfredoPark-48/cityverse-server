"""Graph operations for pathfinding using A* algorithm."""

import heapq
from typing import List, Tuple, Dict, Any, Optional

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(graph: Dict[Tuple[int, int], List[Tuple[float, Tuple[int, int]]]], 
                  start: Tuple[int, int], 
                  goal: Tuple[int, int]) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Perform A* search on the graph.
    graph: Dict mapping node -> List of (cost, neighbor_node)
    """
    frontier = []
    heapq.heappush(frontier, (0, start))
    
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    cost_so_far: Dict[Tuple[int, int], float] = {start: 0.0}
    
    while frontier:
        current_priority, current = heapq.heappop(frontier)
        
        if current == goal:
            break
            
        for cost, neighbor in graph.get(current, []):
            new_cost = cost_so_far[current] + cost
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current
    
    if goal not in came_from:
        return 0.0, [start]
        
    # Reconstruct path
    path = []
    curr = goal
    while curr is not None:
        path.append(curr)
        curr = came_from[curr]
    path.reverse()
    
    return cost_so_far[goal], path

# For backward compatibility with the existing code
def shortestPath(edges: List[Tuple[Any, Any, float]], source: Tuple[int, int], sink: Tuple[int, int]) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Deprecated: Use a pre-built graph with a_star_search for better performance.
    Maintained for legacy support.
    """
    graph = {}
    for l, r, c in edges:
        if l not in graph:
            graph[l] = []
        graph[l].append((c, r))
    
    return a_star_search(graph, source, sink)
