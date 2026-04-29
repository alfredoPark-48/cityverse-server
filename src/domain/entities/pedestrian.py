"""Pedestrian Agent with A* Pathfinding and Bus Interaction."""

from mesa import Agent
from src.application.services.graph_service import a_star_search
from src.domain.entities.traffic_components import (
    SideWalk,
    Destination,
    Traffic_Light,
    PedestrianCrossing,
    Building,
    Vegetation,
    Water,
    Parking,
    Lot,
    Home,
    Road,
)


class Pedestrian(Agent):
    """
    Agent that moves on sidewalks and crossings using A* pathfinding.
    Can take a bus if it's more efficient than walking.
    """

    def __init__(self, unique_id, model, destiny):
        super().__init__(unique_id, model)
        self.destiny = destiny
        self.path = []
        self.indestiny = False
        self.moving = False
        
        # Bus related states
        self.on_bus = False
        self.waiting_for_bus = False
        self.target_bus_stop = None
        self.efficiency_checked = False
        self.bus_wait_ticks = 0
        self.bus_ride_ticks = 0
        self.is_boarding = False
        self.boarding_ticks = 0
        self.gave_up_on_bus = False

    def check_bus_efficiency(self):
        """Determines if taking a bus is better than walking by checking each route."""
        current_pos = self.pos
        walk_dist = abs(current_pos[0] - self.destiny[0]) + abs(current_pos[1] - self.destiny[1])
        
        if self.gave_up_on_bus or walk_dist < 15:
            return False

        best_stop = None
        min_total_walk = walk_dist

        # Check each route independently to ensure it actually goes near the destination
        for rid, stops in self.model.bus_routes.items():
            if not stops:
                continue
                
            # Find nearest stop on THIS route to current pos
            n_start = min(stops, key=lambda s: abs(s[0] - current_pos[0]) + abs(s[1] - current_pos[1]))
            d_start = abs(n_start[0] - current_pos[0]) + abs(n_start[1] - current_pos[1])
            
            # Find nearest stop on THIS route to destination
            n_end = min(stops, key=lambda s: abs(s[0] - self.destiny[0]) + abs(s[1] - self.destiny[1]))
            d_end = abs(n_end[0] - self.destiny[0]) + abs(n_end[1] - self.destiny[1])
            
            # Efficiency check: Is walking to/from THIS route's stops better than just walking?
            if d_start + d_end < walk_dist * 0.7:
                if d_start + d_end < min_total_walk:
                    min_total_walk = d_start + d_end
                    best_stop = n_start

        if best_stop:
            self.target_bus_stop = best_stop
            return True
        
        return False

    def calculate_path(self):
        """Calculates a path to the destination or nearest bus stop."""
        if not self.efficiency_checked:
            if self.check_bus_efficiency():
                self.waiting_for_bus = False # Will be True once we reach the stop
            self.efficiency_checked = True

        current_x, current_y = self.pos
        
        if self.target_bus_stop and not self.waiting_for_bus:
            x_dest, y_dest = self.target_bus_stop
        else:
            x_dest, y_dest = self.destiny

        start_node = (current_y, current_x)
        goal_node = (y_dest, x_dest)

        # 1. Ensure goal is in graph
        if goal_node not in self.model.ped_graph:
            nodes = list(self.model.ped_graph.keys())
            if nodes:
                goal_node = min(
                    nodes, key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest)
                )

        # 2. Try A*
        _, path = a_star_search(self.model.ped_graph, start_node, goal_node)

        # 3. Fallback
        if len(path) <= 1:
            reachable = {start_node}
            queue = [start_node]
            while queue:
                curr = queue.pop(0)
                for _, neighbor in self.model.ped_graph.get(curr, []):
                    if neighbor not in reachable:
                        reachable.add(neighbor)
                        queue.append(neighbor)

            if reachable:
                best_goal = min(
                    reachable, key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest)
                )
                if best_goal != start_node:
                    _, path = a_star_search(self.model.ped_graph, start_node, best_goal)

        if len(path) > 1:
            self.path = [(x, y) for y, x in path]
            self.path.pop(0)
        else:
            self.path = []

    def move(self):
        if self.on_bus:
            return # Handled by Bus agent

        # 0. Traffic Light Safety Check (Emergency Evasion)
        # If we are on a traffic light and it's GREEN (cars have right of way), move to a safe neighbor
        current_contents = self.model.grid.get_cell_list_contents(self.pos)
        light = next((a for a in current_contents if isinstance(a, Traffic_Light)), None)
        if light and light.state == True: # state=True is Green for cars
            neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
            # Find a valid sidewalk or safe neighbor
            safe_neighbor = next((n for n in neighbors if any(isinstance(a, (SideWalk, Building, Vegetation, Water, Parking)) for a in self.model.grid.get_cell_list_contents(n))), None)
            if safe_neighbor:
                self.model.grid.move_agent(self, safe_neighbor)
                self.path = [] # Trigger recalculation
                return

        # 1. Arrival Check
        if self.pos == self.destiny:
            self.indestiny = True
            self.model.metrics["completed_trips"] += 1
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # 2. Bus Stop Check
        if self.target_bus_stop and self.pos == self.target_bus_stop:
            self.waiting_for_bus = True
            self.bus_wait_ticks += 1
            
            # Give up after 150 ticks of waiting
            if self.bus_wait_ticks > 150:
                self.waiting_for_bus = False
                self.target_bus_stop = None
                self.gave_up_on_bus = True
                self.path = [] # Trigger recalculation to walk to destination
                self.bus_wait_ticks = 0
                # Don't return, let it calculate path and move this tick
            else:
                self.moving = False
                return

        # 3. Path Management
        if not self.path:
            self.calculate_path()

        # 4. Determine Next Move
        if self.path:
            next_move = self.path[0]
        else:
            dist = abs(self.pos[0] - self.destiny[0]) + abs(self.pos[1] - self.destiny[1])
            if dist == 1:
                next_move = self.destiny
            else:
                return

        # 5. Collision & Traffic Rules
        cell_contents = self.model.grid.get_cell_list_contents(next_move)
        can_move = True
        for a in cell_contents:
            if isinstance(a, Traffic_Light):
                if a.state: # Red for peds
                    can_move = False
                    break
            elif isinstance(a, (Building, Home, Lot, Vegetation, Water)):
                can_move = False
                break
            elif isinstance(a, PedestrianCrossing):
                if a.state == "Car":
                    can_move = False
                    break
            elif type(a).__name__ in ["Car", "Bus"]:
                # Ignore blockers if this is a bus stop (allow stacking/passing)
                is_bus_stop = any(getattr(obj, "is_bus_stop", False) for obj in cell_contents)
                if not is_bus_stop:
                    can_move = False
                    break

        if can_move:
            self.model.grid.move_agent(self, next_move)
            if self.path:
                self.path.pop(0)
            self.moving = True
        else:
            self.moving = False
            if self.random.random() < 0.1:
                self.path = []

    def step(self):
        # 0. Boarding Animation Logic
        if self.is_boarding:
            self.boarding_ticks += 1
            if self.boarding_ticks >= 3:
                if self.pos:
                    self.model.grid.remove_agent(self)
                # Keep in schedule but as a 'ghost' on the bus
            return

        if self.on_bus:
            self.bus_ride_ticks += 1
            return # Handled by Bus agent
            
        self.move()
