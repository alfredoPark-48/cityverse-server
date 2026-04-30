"""Graph service for building road and pedestrian networks."""

import heapq

def a_star_search(graph, start, goal):
    """Standard A* search implementation."""
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal:
            break

        for weight, next_node in graph.get(current, []):
            new_cost = cost_so_far[current] + weight
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(goal, next_node)
                heapq.heappush(frontier, (priority, next_node))
                came_from[next_node] = current

    path = []
    if goal in came_from:
        curr = goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
    return cost_so_far.get(goal, float("inf")), path


class GraphService:
    """Service to build and manage simulation graphs."""

    @staticmethod
    def build_graphs(grid_file_path):
        with open(grid_file_path, "r") as f:
            matrix_inverted = [list(line.strip()) for line in f]

        matrix = list(reversed(matrix_inverted))
        rows = len(matrix)
        cols = len(matrix[0])

        road_graph = {}
        ped_graph = {}
        road_edges = []

        road_chars = ["v", "^", ">", "<", "I", "T", "t", "X", "x", "D", "A", "P", "L", "c"]
        ped_chars = ["S", "X", "x", "D", "T", "t", "P", "p", "c", "1", "2", "3", "4"]

        for y in range(rows):
            for x in range(cols):
                c = matrix[y][x]
                source = (y, x)
                neighbors = [(x, y + 1, "^"), (x, y - 1, "v"), (x - 1, y, "<"), (x + 1, y, ">")]

                # Road Graph
                if c in road_chars:
                    if source not in road_graph: road_graph[source] = []
                    for nx, ny, move_dir in neighbors:
                        if not (0 <= nx < cols and 0 <= ny < rows): continue
                        nc = matrix[ny][nx]
                        if nc not in road_chars: continue

                        can_move = False
                        if c == "c" or (c in ["I", "T", "t", "X", "x", "A", "D", "P"]):
                            if nc in road_chars or nc == move_dir: can_move = True
                        elif c == move_dir:
                            if nc in ["I", "T", "t", "X", "x", "A", "D", "P", "c"] or nc == move_dir: can_move = True

                        if can_move:
                            target = (ny, nx)
                            road_graph[source].append((1.0, target))
                            road_edges.append((source, target, 1.0))

                # Pedestrian Graph
                if c in ped_chars:
                    if source not in ped_graph: ped_graph[source] = []
                    for nx, ny, _ in neighbors:
                        if not (0 <= nx < cols and 0 <= ny < rows): continue
                        if matrix[ny][nx] in ped_chars:
                            ped_graph[source].append((1.0, (ny, nx)))

        return road_edges, road_graph, ped_graph
