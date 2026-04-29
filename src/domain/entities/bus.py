"""Bus Agent with A* Pathfinding, Passenger logic, and Route management."""

from mesa import Agent
from src.application.services.graph_service import a_star_search
from src.domain.entities.traffic_components import Road, Traffic_Light, PedestrianCrossing

class Bus(Agent):
    """
    Bus agent that follows a specific route (1, 2, or 3) defined in the model.
    Picks up and drops off pedestrians at designated stops.
    """
    def __init__(self, unique_id, model, route_id):
        super().__init__(unique_id, model)
        self.route_id = str(route_id)
        self.route = self.model.bus_routes.get(self.route_id, [])
        self.current_stop_index = 0
        self.path = []
        self.moving = False
        self.previous_pos = None
        self.intended_next_move = None
        self.passengers = []
        self.wait_timer = 0
        self.STOP_WAIT_TIME = 3 # Ticks to wait at each stop

    def calculate_path(self, target_pos):
        """Calculates a path to the target stop using A*.

        Goal selection strategy
        -----------------------
        Each bus stop cell is a non-road tile (chars 1-4). The bus must stop
        adjacent to it on a real road cell. We rank the stop's road neighbours
        and probe A* through each in order, taking the first that yields a
        valid path. This prevents the bus from picking a road cell that is
        physically close but topologically disconnected from the route.
        """
        current_x, current_y = self.pos
        x_dest, y_dest = target_pos

        start_node = (current_y, current_x)

        # Collect road cells that are direct cardinal neighbours of the stop
        possible_goals = []
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n = (y_dest + dy, x_dest + dx)
            if n in self.model.road_graph:
                possible_goals.append(n)

        # Sort by proximity to the stop itself (stable, adjacent order)
        possible_goals.sort(key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest))

        # Try each candidate; use the first one A* can actually reach.
        for goal_node in possible_goals:
            _, path = a_star_search(self.model.road_graph, start_node, goal_node)
            if len(path) > 1:
                self.path = [(x, y) for y, x in path]
                self.path.pop(0)  # Remove current position
                return

        # Fallback: no cardinal road cell reachable - aim for absolute nearest road node.
        if not self.path:
            nodes = list(self.model.road_graph.keys())
            goal_node = min(nodes, key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest))
            _, path = a_star_search(self.model.road_graph, start_node, goal_node)
            if len(path) > 1:
                self.path = [(x, y) for y, x in path]
                self.path.pop(0)
            else:
                self.path = []

    def move(self):
        # -1. Simulation Termination Check: Stop if no active peds and bus is empty
        from src.domain.entities.pedestrian import Pedestrian
        active_peds = [a for a in self.model.schedule.agents if isinstance(a, Pedestrian) and not a.on_bus]
        if not active_peds and not self.passengers:
            self.moving = False
            return

        # 0. Emergency Egress: If we are beside ANY stop and have frustrated passengers, let them off
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        any_stop = next((n for n in neighbors if any(getattr(obj, "is_bus_stop", False) for obj in self.model.grid.get_cell_list_contents(n))), None)
        has_frustrated = any(p.bus_ride_ticks >= 200 for p in self.passengers)
        
        if any_stop and has_frustrated:
            # Check if this IS our target stop
            target_stop = self.route[self.current_stop_index] if self.route else None
            is_target = (any_stop == target_stop)
            
            # Let them off. If not target, ONLY frustrated ones get off
            self.handle_passengers(any_stop, frustrated_only=not is_target)
            
            # If it was our target, we handle the wait state as normal
            if is_target:
                self.moving = False
                self.wait_timer += 1
                self.path = []
                return

        # 1. Stop arrival logic: Stop if we are ADJACENT to our target stop
        if self.route:
            target_stop = self.route[self.current_stop_index]
            # Use Von Neumann (4-neighbor) to ensure we stop exactly BESIDE, not diagonally early
            neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
            
            # If our target stop is one of our neighbors, we have "arrived" beside it
            if target_stop in neighbors:
                # Check if anyone needs to board or drop off
                cell_agents = self.model.grid.get_cell_list_contents(target_stop)
                pedestrians_waiting = any(type(a).__name__ == "Pedestrian" and getattr(a, "waiting_for_bus", False) for a in cell_agents)
                dropoff_needed = any(abs(p.destiny[0] - self.pos[0]) + abs(p.destiny[1] - self.pos[1]) < 5 for p in self.passengers)
                
                if pedestrians_waiting or dropoff_needed:
                    if self.wait_timer < self.STOP_WAIT_TIME:
                        self.handle_passengers(target_stop)
                        self.wait_timer += 1
                        self.moving = False
                        # Force clear path so we recalculate after waiting
                        self.path = []
                        return
                    else:
                        self.wait_timer = 0
                        self.current_stop_index = (self.current_stop_index + 1) % len(self.route)
                        self.path = [] 
                else:
                    # No one needs the stop, but if we are at the end of our path to it, move to next
                    if not self.path or self.pos == self.path[-1]:
                        self.current_stop_index = (self.current_stop_index + 1) % len(self.route)
                        self.path = []

        # 2. Path Management
        if (not self.path or self.intended_next_move) and self.route:
            self.calculate_path(self.route[self.current_stop_index])

        # 3. Determine Next Move
        if self.path:
            next_move = self.path[0]
        else:
            return

        # 4. Anti-Jamming & Collision Logic
        cell_contents = self.model.grid.get_cell_list_contents(next_move)
        
        # Special check: If next_move is a Bus Stop, and it's already occupied by another Bus
        is_target_stop = any(getattr(obj, "is_bus_stop", False) for obj in cell_contents)
        if is_target_stop:
            other_buses = [a for a in cell_contents if type(a).__name__ == "Bus"]
            if other_buses:
                # Stop is occupied! Wait on the road to avoid jamming the pull-over
                self.moving = False
                self.intended_next_move = next_move
                return

        blockers = [a for a in cell_contents if not isinstance(a, Road)]
        
        can_move = True
        for b in blockers:
            if isinstance(b, Traffic_Light):
                if not b.state: # Red light
                    if not self._is_at_intersection():
                        can_move = False
                        break
            elif isinstance(b, PedestrianCrossing):
                if b.state not in [None, "Car"]:
                    can_move = False
                    break
            elif type(b).__name__ in ["Car", "Bus"]:
                # Standard vehicle blocking
                can_move = False
                break
            elif type(b).__name__ == "Pedestrian":
                # Don't let pedestrians block the bus at a STOP cell
                if not is_target_stop:
                    can_move = False
                    break
            else:
                can_move = False
                break
        
        if can_move:
            self.previous_pos = self.pos
            self.model.grid.move_agent(self, next_move)
            if self.path:
                self.path.pop(0)
            self.moving = True
            self.intended_next_move = None
        else:
            self.moving = False
            self.intended_next_move = next_move

    def handle_passengers(self, stop_pos, frustrated_only=False):
        """Pick up waiting pedestrians from the adjacent stop and drop off those whose destination is near."""
        # 1. Drop off
        arrived_passengers = []
        for p in self.passengers:
            dist_to_dest = abs(p.destiny[0] - self.pos[0]) + abs(p.destiny[1] - self.pos[1])
            # Normal drop off: near destination
            is_near = dist_to_dest < 5
            # Timeout drop off: ride time exceeded 200 ticks
            is_frustrated = p.bus_ride_ticks >= 200
            
            if (not frustrated_only and is_near) or is_frustrated: 
                arrived_passengers.append(p)
                if is_frustrated:
                    p.gave_up_on_bus = True
                    self.model.metrics["frustrated_pedestrians"] += 1
                else:
                    self.model.metrics["completed_trips"] += 1
        
        for p in arrived_passengers:
            self.passengers.remove(p)
            # Use Von Neumann (4-neighbor) to place them strictly beside the road
            neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
            from src.domain.entities.traffic_components import SideWalk
            actual_sidewalks = [n for n in neighbors if any(isinstance(a, SideWalk) or getattr(a, "is_bus_stop", False) for a in self.model.grid.get_cell_list_contents(n))]
            
            spawn_pos = actual_sidewalks[0] if actual_sidewalks else neighbors[0]
            self.model.grid.place_agent(p, spawn_pos)
            p.on_bus = False
            p.waiting_for_bus = False
            p.target_bus_stop = None
            p.path = []

        # 2. Pick up (Only if this is an official stop for this bus and not just an emergency egress stop)
        if not frustrated_only:
            cell_agents = self.model.grid.get_cell_list_contents(stop_pos)
            for a in cell_agents:
                if type(a).__name__ == "Pedestrian" and getattr(a, "waiting_for_bus", False):
                    if len(self.passengers) < 10: # Capacity
                        self.passengers.append(a)
                        self.model.metrics["total_passengers"] += 1
                        a.on_bus = True
                        a.waiting_for_bus = False
                        a.bus_wait_ticks = 0
                        a.is_boarding = True
                        a.boarding_ticks = 0
                        # Move to bus position to show them "entering"
                        self.model.grid.move_agent(a, self.pos)

    def _is_at_intersection(self):
        current_cell_agents = self.model.grid.get_cell_list_contents(self.pos)
        for a in current_cell_agents:
            if isinstance(a, Road) and a.direction == "Intersection":
                return True
            if isinstance(a, Traffic_Light):
                return True
        return False

    def step(self):
        self.move()
