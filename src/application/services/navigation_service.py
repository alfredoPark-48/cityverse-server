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
        cell_contents = model.grid.get_cell_list_contents(pos)
        
        # Filter blockers, avoiding Road agents. 
        # Using string names for robust type checking across potential reloads.
        blockers = [a for a in cell_contents if a != self_agent and type(a).__name__ != "Road"]
        
        # Intersection logic: if we are already in an intersection or crossing, we shouldn't stop for red lights
        is_already_in_intersection = False
        if self_agent and getattr(self_agent, "pos", None):
            current_contents = model.grid.get_cell_list_contents(self_agent.pos)
            for a in current_contents:
                a_type = type(a).__name__
                # If we are on a light, a crossing, or a road segment explicitly marked as Intersection
                if a_type in ["Traffic_Light", "PedestrianCrossing"]:
                    is_already_in_intersection = True
                    break
                if a_type == "Road" and getattr(a, "direction", "") == "Intersection":
                    is_already_in_intersection = True
                    break

        for b in blockers:
            b_type = type(b).__name__
            if b_type == "Traffic_Light":
                light_state = getattr(b, "state", True)
                if agent_type == "Pedestrian":
                    # Pedestrians are blocked if the light is green for cars
                    if light_state:
                        return True
                else: # Car or Bus
                    # Vehicles are blocked if the light is red, unless already clearing the intersection
                    if not light_state:
                        if not is_already_in_intersection:
                            return True
            elif b_type == "PedestrianCrossing":
                if getattr(b, "state", None) not in [None, agent_type]:
                    return True
            elif b_type == "Pedestrian":
                # Pedestrians only block vehicles, not other pedestrians
                if agent_type != "Pedestrian":
                    return True
            elif b_type in ["Car", "Bus"]:
                return True
            elif b_type in ["Angel", "Parking", "CarSpawn", "SideWalk", "Home", "PedestrianSpawn", "Destination"]:
                continue
            else:
                return True # Buildings, etc.
        
        return False
