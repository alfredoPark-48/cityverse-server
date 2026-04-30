"""Pedestrian Agent refactored for Clean Architecture."""

from src.domain.entities.base import BaseTrafficAgent
from src.application.services.navigation_service import NavigationService
from src.domain.entities.traffic_components import SideWalk, Traffic_Light, PedestrianCrossing, Building, Vegetation, Water, Parking, Lot, Home

class Pedestrian(BaseTrafficAgent):
    """
    Pedestrian agent that walks on sidewalks and can take buses.
    """
    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model, destination)
        
        # Bus states
        self.on_bus = False
        self.waiting_for_bus = False
        self.target_bus_stop = None
        self.efficiency_checked = False
        self.bus_wait_ticks = 0
        self.is_boarding = False
        self.boarding_ticks = 0
        self.gave_up_on_bus = False

    def check_bus_efficiency(self):
        """Logic to decide if a bus is worth taking."""
        if not self.pos or self.gave_up_on_bus:
            return False
            
        walk_dist = abs(self.pos[0] - self.destination[0]) + abs(self.pos[1] - self.destination[1])
        if walk_dist < 15:
            return False

        best_stop = None
        min_total_walk = walk_dist

        for rid, stops in self.model.bus_routes.items():
            if not stops: continue
            
            n_start = min(stops, key=lambda s: abs(s[0] - self.pos[0]) + abs(s[1] - self.pos[1]))
            d_start = abs(n_start[0] - self.pos[0]) + abs(n_start[1] - self.pos[1])
            
            n_end = min(stops, key=lambda s: abs(s[0] - self.destination[0]) + abs(s[1] - self.destination[1]))
            d_end = abs(n_end[0] - self.destination[0]) + abs(n_end[1] - self.destination[1])
            
            if d_start + d_end < walk_dist * 0.7:
                if d_start + d_end < min_total_walk:
                    min_total_walk = d_start + d_end
                    best_stop = n_start

        if best_stop:
            self.target_bus_stop = best_stop
            return True
        return False

    def calculate_path(self):
        if not self.efficiency_checked:
            if self.check_bus_efficiency():
                self.waiting_for_bus = False
            self.efficiency_checked = True

        goal = self.target_bus_stop if (self.target_bus_stop and not self.waiting_for_bus) else self.destination
        
        start_node = (self.pos[1], self.pos[0])
        goal_node = (goal[1], goal[0])
        
        path_nodes = NavigationService.get_path(self.model.ped_graph, start_node, goal_node)
        
        if len(path_nodes) > 1:
            self.path = [(x, y) for y, x in path_nodes]
            self.path.pop(0)
        else:
            self.path = []

    def move(self):
        if self.on_bus or self.is_boarding:
            return

        # 1. Arrival Logic
        if self.pos == self.destination:
            self.has_arrived = True
            self.model.metrics["completed_trips"] += 1
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # 2. Bus Stop Logic
        if self.target_bus_stop and self.pos == self.target_bus_stop:
            self.waiting_for_bus = True
            self.bus_wait_ticks += 1
            if self.bus_wait_ticks > 150:
                self.waiting_for_bus = False
                self.target_bus_stop = None
                self.gave_up_on_bus = True
                self.path = []
                self.bus_wait_ticks = 0
            else:
                self.is_moving = False
                return

        # 3. Path Management
        if not self.path:
            self.calculate_path()

        if not self.path:
            dist = abs(self.pos[0] - self.destination[0]) + abs(self.pos[1] - self.destination[1])
            if dist == 1:
                next_move = self.destination
            else:
                self.is_moving = False
                return
        else:
            next_move = self.path[0]

        # 4. Collision & Traffic Rules
        is_blocked = NavigationService.is_cell_blocked(self.model, next_move, "Pedestrian", self)
        
        if not is_blocked:
            self.model.grid.move_agent(self, next_move)
            if self.path:
                self.path.pop(0)
            self.is_moving = True
            self._update_direction(next_move)
        else:
            self.is_moving = False
            # Randomly clear path to try a new route if stuck
            if self.random.random() < 0.1:
                self.path = []

    def step(self):
        if self.is_boarding:
            self.boarding_ticks += 1
            if self.boarding_ticks >= 3:
                if self.pos:
                    self.model.grid.remove_agent(self)
            return

        if self.on_bus:
            return
            
        super().step()
