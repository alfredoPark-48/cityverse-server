"""Car Agent with A* Pathfinding and Vehicle-like behavior."""

from mesa import Agent
from src.application.services.graph_service import a_star_search
from src.domain.entities.traffic_components import Road, Destination, Traffic_Light, PedestrianCrossing, Angel, Parking, CarSpawn

class Car(Agent):
    """
    Agent that moves using A* pathfinding on a road graph.
    """
    def __init__(self, unique_id, model, destiny):
        super().__init__(unique_id, model)
        self.destiny = destiny
        self.path = []
        self.moving = False
        self.inDestiny = False
        self.previous_pos = None
        self.intended_next_move = None
        self.direction = "None"

    def calculate_path(self):
        """Calculates a path to the destination using A*."""
        current_x, current_y = self.pos
        x_dest, y_dest = self.destiny
        
        start_node = (current_y, current_x)
        goal_node = (y_dest, x_dest)
        
        # 1. Ensure goal is in graph
        if goal_node not in self.model.road_graph:
            nodes = list(self.model.road_graph.keys())
            if nodes:
                goal_node = min(nodes, key=lambda n: abs(n[0] - goal_node[0]) + abs(n[1] - goal_node[1]))
        
        # 2. Try A*
        _, path = a_star_search(self.model.road_graph, start_node, goal_node)
        
        # 3. If A* failed to find a path to the goal, find the closest reachable node
        if len(path) <= 1:
            # BFS to find reachable set
            reachable = {start_node}
            queue = [start_node]
            while queue:
                curr = queue.pop(0)
                for _, neighbor in self.model.road_graph.get(curr, []):
                    if neighbor not in reachable:
                        reachable.add(neighbor)
                        queue.append(neighbor)
            
            # Find closest reachable node to original goal
            if reachable:
                best_goal = min(reachable, key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest))
                if best_goal != start_node:
                    _, path = a_star_search(self.model.road_graph, start_node, best_goal)

        if len(path) > 1:
            # Convert (y, x) back to (x, y) for Mesa grid
            self.path = [(x, y) for y, x in path]
            self.path.pop(0) # Remove current position
        else:
            self.path = []

    def move(self):
        # 1. Arrival Logic (Immediate Despawn)
        if self.pos == self.destiny:
            self.model.total_parked_cars += 1
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # 2. Path Management
        if not self.path or self.intended_next_move:
            self.calculate_path()

        # 3. Determine Next Move
        if self.path:
            next_move = self.path[0]
        else:
            # Fallback: if adjacent to destiny, move there even if not in graph
            dist = abs(self.pos[0] - self.destiny[0]) + abs(self.pos[1] - self.destiny[1])
            if dist == 1:
                next_move = self.destiny
            else:
                return

        # 4. Collision Detection & Traffic Rules
        cell_contents = self.model.grid.get_cell_list_contents(next_move)
        blockers = [a for a in cell_contents if not isinstance(a, Road)]
        
        can_move = True
        for b in blockers:
            if isinstance(b, Traffic_Light):
                if not b.state: # Red light
                    # Stay if we're not already in an intersection
                    if not self._is_at_intersection():
                        can_move = False
                        break
            elif isinstance(b, PedestrianCrossing):
                if b.state not in [None, "Car"]:
                    can_move = False
                    break
            elif isinstance(b, Car):
                # Vehicle ahead
                can_move = False
                break
            elif isinstance(b, (Angel, Parking, CarSpawn)):
                pass # Non-blocking
            elif type(b).__name__ == "Pedestrian":
                # Stop if blocked by a pedestrian
                can_move = False
                break
            else:
                can_move = False # Buildings, obstacles
                break

        if can_move:
            self.previous_pos = self.pos
            self.model.grid.move_agent(self, next_move)
            if self.path:
                self.path.pop(0)
            self.moving = True
            self.intended_next_move = None
            self._update_direction(next_move)
        else:
            self.moving = False
            self.intended_next_move = next_move # Wait for this cell to clear

    def _is_at_intersection(self):
        """Checks if the current cell is an intersection or has a traffic light."""
        current_cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for a in current_cell_agents:
            if isinstance(a, Road) and a.direction == "Intersection":
                return True
            if isinstance(a, Traffic_Light):
                return True
        return False

    def _update_direction(self, next_pos):
        """Updates the direction string for visuals."""
        curr_x, curr_y = self.pos
        next_x, next_y = next_pos
        if next_x > curr_x: self.direction = "Right"
        elif next_x < curr_x: self.direction = "Left"
        elif next_y > curr_y: self.direction = "Up"
        elif next_y < curr_y: self.direction = "Down"

    def step(self):
        self.move()
