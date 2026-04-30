"""Car Agent refactored for Clean Architecture."""

from src.domain.entities.base import BaseTrafficAgent
from src.application.services.navigation_service import NavigationService
from src.domain.entities.traffic_components import Road, Traffic_Light

class Car(BaseTrafficAgent):
    """
    Car agent that follows road graphs and respects traffic lights.
    """
    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model, destination)
        self.intended_next_move = None

    def calculate_path(self):
        """Calculates path using the NavigationService."""
        if not self.pos or not self.destination:
            return

        start_node = (self.pos[1], self.pos[0]) # (y, x)
        goal_node = (self.destination[1], self.destination[0]) # (y, x)
        
        path_nodes = NavigationService.get_path(self.model.road_graph, start_node, goal_node)
        
        if len(path_nodes) > 1:
            # Convert (y, x) back to (x, y)
            self.path = [(x, y) for y, x in path_nodes]
            self.path.pop(0) # Remove current pos
        else:
            self.path = []

    def move(self):
        # 1. Check Arrival
        if self.pos == self.destination:
            self.has_arrived = True
            self.model.total_parked_cars += 1
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # 2. Path Management
        if not self.path or self.intended_next_move:
            self.calculate_path()

        if not self.path:
            # Fallback if adjacent to destination
            dist = abs(self.pos[0] - self.destination[0]) + abs(self.pos[1] - self.destination[1])
            if dist == 1:
                next_move = self.destination
            else:
                self.is_moving = False
                return
        else:
            next_move = self.path[0]

        # 3. Collision & Traffic Rules
        is_blocked = NavigationService.is_cell_blocked(self.model, next_move, "Car", self)
        
        # Intersection Exception: Don't stop if already at an intersection/light
        if is_blocked:
            current_cell_agents = self.model.grid.get_cell_list_contents(self.pos)
            at_intersection = any(isinstance(a, Traffic_Light) or (isinstance(a, Road) and a.direction == "Intersection") for a in current_cell_agents)
            if at_intersection:
                is_blocked = False

        if not is_blocked:
            self.previous_pos = self.pos
            self.model.grid.move_agent(self, next_move)
            if self.path:
                self.path.pop(0)
            self.is_moving = True
            self.intended_next_move = None
            self._update_direction(next_move)
        else:
            self.is_moving = False
            self.intended_next_move = next_move
