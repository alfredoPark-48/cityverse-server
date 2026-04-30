"""Bus Agent refactored for Clean Architecture."""

from src.domain.entities.base import BaseTrafficAgent
from src.application.services.navigation_service import NavigationService
from src.domain.entities.traffic_components import Road, Traffic_Light, SideWalk

class Bus(BaseTrafficAgent):
    """
    Bus agent that follows routes and transports pedestrians.
    """
    def __init__(self, unique_id, model, route_id, start_stop_index=0):
        super().__init__(unique_id, model)
        self.route_id = str(route_id)
        self.route = self.model.bus_routes.get(self.route_id, [])
        # Distribute starting positions based on the number of buses already on the route
        self.current_stop_index = start_stop_index % len(self.route) if self.route else 0
        self.passengers = []
        self.wait_timer = 0
        self.STOP_WAIT_TIME = 3
        self.intended_next_move = None

    def calculate_path(self, target_pos=None):
        """Calculates the A* path to the current target stop."""
        if not self.pos or not self.route:
            return

        target = target_pos or self.route[self.current_stop_index]
        start_node = (self.pos[1], self.pos[0])
        
        # Goal selection: Bus must stop ADJACENT to the stop character (1-4)
        x_dest, y_dest = target
        possible_goals = []
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            n = (y_dest + dy, x_dest + dx)
            if n in self.model.road_graph:
                possible_goals.append(n)

        # Sort goals by Manhattan distance to the visual stop center
        possible_goals.sort(key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest))

        for goal_node in possible_goals:
            path_nodes = NavigationService.get_path(self.model.road_graph, start_node, goal_node)
            if len(path_nodes) > 1:
                self.path = [(x, y) for y, x in path_nodes]
                self.path.pop(0)
                return

        self.path = []

    def move(self):
        """Main step logic for bus movement and stop behavior."""
        # 1. Handle Bus Stops (Always stop at route stops)
        if self._handle_stop_logic():
            return

        # 2. Path Management
        if (not self.path or self.intended_next_move) and self.route:
            self.calculate_path()

        if not self.path:
            self.is_moving = False
            return
            
        next_move = self.path[0]

        # 3. Collision & Traffic Rules
        if self._check_collisions(next_move):
            self.is_moving = False
            self.intended_next_move = next_move
            return

        # 4. Physical Movement
        self.previous_pos = self.pos
        self.model.grid.move_agent(self, next_move)
        if self.path:
            self.path.pop(0)
        self.is_moving = True
        self.intended_next_move = None
        self._update_direction(next_move)

    def _handle_stop_logic(self):
        """Manages the stopping behavior at designated bus stops."""
        if not self.route:
            return False

        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        current_target = self.route[self.current_stop_index]
        
        # Determine if we are adjacent to our target stop or ANY stop
        stop_pos = None
        if current_target in neighbors:
            stop_pos = current_target
        else:
            # Check for non-target stops where we might need to drop off frustrated passengers
            for n in neighbors:
                if any(getattr(a, "is_bus_stop", False) for a in self.model.grid.get_cell_list_contents(n)):
                    stop_pos = n
                    break
        
        if not stop_pos:
            return False

        # Activity check: Do we HAVE to stop here?
        # Mandatory stop at current target, or conditional stop for passengers
        from src.domain.entities.pedestrian import Pedestrian
        from src.shared.config import BUS_MAX_RIDE_TICKS
        
        cell_agents = self.model.grid.get_cell_list_contents(stop_pos)
        peds_waiting = any(isinstance(a, Pedestrian) and a.waiting_for_bus for a in cell_agents)
        dropoff_needed = any(abs(p.destination[0] - self.pos[0]) + abs(p.destination[1] - self.pos[1]) < 5 for p in self.passengers)
        is_frustrated = any(p.bus_ride_ticks >= BUS_MAX_RIDE_TICKS for p in self.passengers)

        should_stop = (stop_pos == current_target) or peds_waiting or dropoff_needed or is_frustrated

        if should_stop:
            if self.wait_timer < self.STOP_WAIT_TIME:
                self.handle_passengers(stop_pos)
                self.wait_timer += 1
                self.is_moving = False
                self.path = []
                return True
            else:
                # Finished waiting
                self.wait_timer = 0
                if stop_pos == current_target:
                    self.current_stop_index = (self.current_stop_index + 1) % len(self.route)
                self.path = []
                return False
        
        return False

    def _check_collisions(self, next_move):
        """Checks if the next cell is blocked, with special handling for stops."""
        is_blocked = NavigationService.is_cell_blocked(self.model, next_move, "Bus", self)
        
        if is_blocked:
            cell_contents = self.model.grid.get_cell_list_contents(next_move)
            # Allow moving onto a stop cell if it's only blocked by pedestrians
            if any(getattr(obj, "is_bus_stop", False) for obj in cell_contents):
                from src.domain.entities.pedestrian import Pedestrian
                if all(isinstance(a, (Pedestrian, Road)) for a in cell_contents):
                    return False
        return is_blocked

    def handle_passengers(self, stop_pos, frustrated_only=False):
        """Processes pick-ups and drop-offs at the current stop."""
        from src.shared.config import BUS_MAX_RIDE_TICKS
        from src.domain.entities.pedestrian import Pedestrian
        
        # 1. Drop off passengers
        arrived = []
        for p in self.passengers:
            is_at_dest = abs(p.destination[0] - self.pos[0]) + abs(p.destination[1] - self.pos[1]) < 5
            is_frustrated = p.bus_ride_ticks >= BUS_MAX_RIDE_TICKS
            
            if (not frustrated_only and is_at_dest) or is_frustrated:
                if is_frustrated:
                    p.gave_up_on_bus = True
                    self.model.metrics["total_frustrated"] += 1
                arrived.append(p)
        
        for p in arrived:
            self.passengers.remove(p)
            self._place_pedestrian_on_sidewalk(p)
            p.on_bus = False
            p.waiting_for_bus = False
            p.target_bus_stop = None
            p.path = []

        # 2. Pick up passengers
        if not frustrated_only:
            cell_agents = self.model.grid.get_cell_list_contents(stop_pos)
            for a in cell_agents:
                if isinstance(a, Pedestrian) and a.waiting_for_bus:
                    if len(self.passengers) < 10: # Bus capacity
                        self._board_pedestrian(a)

    def _place_pedestrian_on_sidewalk(self, pedestrian):
        """Safely places a departing passenger on an adjacent sidewalk."""
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        sidewalks = [n for n in neighbors if any(type(a).__name__ in ["SideWalk", "PedestrianCrossing"] or getattr(a, "is_bus_stop", False) for a in self.model.grid.get_cell_list_contents(n))]
        spawn_pos = sidewalks[0] if sidewalks else neighbors[0]
        self.model.grid.place_agent(pedestrian, spawn_pos)

    def _board_pedestrian(self, pedestrian):
        """Handles the boarding process for a passenger."""
        self.passengers.append(pedestrian)
        self.model.metrics["total_passengers"] += 1
        pedestrian.on_bus = True
        pedestrian.waiting_for_bus = False
        pedestrian.is_boarding = True
        pedestrian.boarding_ticks = 0
        pedestrian.bus_ride_ticks = 0
        self.model.grid.move_agent(pedestrian, self.pos)
