"""Navigation service for agent pathfinding."""

from src.application.services.graph_service import a_star_search

class NavigationService:
    """Provides pathfinding and movement utilities for agents."""

    @staticmethod
    def get_path(graph, start_node, goal_node):
        """Calculates a path using A* and falls back to closest reachable if needed."""
        # Convert (x, y) to (y, x) if graph uses (y, x)
        # Note: Current implementation uses (y, x) for graph keys
        
        # 1. Ensure goal is in graph
        if goal_node not in graph:
            nodes = list(graph.keys())
            if nodes:
                goal_node = min(nodes, key=lambda n: abs(n[0] - goal_node[0]) + abs(n[1] - goal_node[1]))
        
        # 2. Try A*
        _, path = a_star_search(graph, start_node, goal_node)
        
        # 3. Fallback: BFS to find reachable set if A* failed
        if len(path) <= 1:
            reachable = {start_node}
            queue = [start_node]
            while queue:
                curr = queue.pop(0)
                for _, neighbor in graph.get(curr, []):
                    if neighbor not in reachable:
                        reachable.add(neighbor)
                        queue.append(neighbor)
            
            if reachable:
                best_goal = min(reachable, key=lambda n: abs(n[0] - goal_node[0]) + abs(n[1] - goal_node[1]))
                if best_goal != start_node:
                    _, path = a_star_search(graph, start_node, best_goal)

        return path

    @staticmethod
    def is_cell_blocked(model, pos, agent_type, self_agent=None):
        """Checks if a cell is blocked by other agents or traffic rules."""
        from src.domain.entities.traffic_components import Road, Traffic_Light, PedestrianCrossing, Angel, Parking, CarSpawn
        
        cell_contents = model.grid.get_cell_list_contents(pos)
        blockers = [a for a in cell_contents if a != self_agent and not isinstance(a, Road)]
        
        for b in blockers:
            if isinstance(b, Traffic_Light):
                if not b.state: # Red light
                    # Can't enter if it's red, unless we're already "inside" (intersection logic)
                    return True
            elif isinstance(b, PedestrianCrossing):
                if b.state not in [None, agent_type]:
                    return True
            elif type(b).__name__ in ["Car", "Bus", "Pedestrian"]:
                return True
            elif isinstance(b, (Angel, Parking, CarSpawn)):
                continue
            else:
                return True # Buildings, etc.
        
        return False
