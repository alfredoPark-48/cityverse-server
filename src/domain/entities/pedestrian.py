"""Pedestrian Agent refactored for Clean Architecture."""

from src.domain.entities.base import BaseTrafficAgent
from src.application.services.navigation_service import NavigationService
from src.domain.entities.traffic_components import SideWalk, Traffic_Light, PedestrianCrossing, Building, Vegetation, Water, Parking, Lot, Home
from src.shared.config import BUS_WAIT_PENALTY, BUS_TRAVEL_COST_PER_STOP, MIN_WALK_DISTANCE_FOR_BUS

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
        """
        Calculates if taking a bus is more efficient than walking.
        
        The decision is based on a cost model:
        Cost = WalkingToStop + WaitPenalty + (StopsNeeded * TravelCostPerStop) + WalkingFromStop
        """
        if not self.pos or self.gave_up_on_bus:
            return False
            
        # 1. Base walking distance (Manhattan)
        total_walk_dist = abs(self.pos[0] - self.destination[0]) + abs(self.pos[1] - self.destination[1])
        
        # Short distances are always faster on foot
        if total_walk_dist < MIN_WALK_DISTANCE_FOR_BUS:
            return False

        # Cost weights
        WALK_COST_WEIGHT = 1.0
        
        best_stop = None
        min_total_cost = total_walk_dist * WALK_COST_WEIGHT

        # 2. Evaluate all available bus routes
        for rid, stops in self.model.bus_routes.items():
            if len(stops) < 2:
                continue
            
            # Find nearest stop to current position
            idx_start, d_start = self._find_nearest_stop(self.pos, stops)
            # Find nearest stop to destination
            idx_end, d_end = self._find_nearest_stop(self.destination, stops)

            if idx_start != -1 and idx_end != -1:
                # Calculate stops needed on a circular route
                stops_needed = (idx_end - idx_start) % len(stops)
                
                # If stops_needed is 0, it means the nearest stop to start and end is the same
                if stops_needed == 0:
                    continue

                # Calculate estimated trip cost
                bus_trip_cost = (d_start * WALK_COST_WEIGHT) + \
                                BUS_WAIT_PENALTY + \
                                (stops_needed * BUS_TRAVEL_COST_PER_STOP) + \
                                (d_end * WALK_COST_WEIGHT)
                
                # 3. Decision: Is bus cheaper than current best?
                if bus_trip_cost < min_total_cost:
                    min_total_cost = bus_trip_cost
                    best_stop = stops[idx_start]

        if best_stop:
            self.target_bus_stop = best_stop
            return True
        return False

    def _find_nearest_stop(self, target_pos, stops):
        """Helper to find the index and distance of the nearest stop to a position."""
        best_idx = -1
        min_dist = float('inf')
        for i, stop in enumerate(stops):
            d = abs(stop[0] - target_pos[0]) + abs(stop[1] - target_pos[1])
            if d < min_dist:
                min_dist = d
                best_idx = i
        return best_idx, min_dist

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

        # 0. Backtracking Logic: If caught on a green light (car-phase), retreat to safety
        current_cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for a in current_cell_agents:
            if type(a).__name__ == "Traffic_Light" and getattr(a, "state", False):
                if self.previous_pos:
                    self.model.grid.move_agent(self, self.previous_pos)
                    self.path = []
                    self.is_moving = False
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
                self.model.metrics["frustrated_pedestrians"] += 1
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
            self.wait_ticks = 0
            self._update_direction(next_move)
        else:
            self.is_moving = False
            self.wait_ticks += 1
            if self.wait_ticks > 40:
                if self.wait_ticks % 20 == 0:
                    self.model.metrics["frustrated_pedestrians"] += 1
            
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
