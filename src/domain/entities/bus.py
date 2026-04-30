"""Bus Agent refactored for Clean Architecture."""

from src.domain.entities.base import BaseTrafficAgent
from src.application.services.navigation_service import NavigationService
from src.domain.entities.traffic_components import Road, Traffic_Light, SideWalk

class Bus(BaseTrafficAgent):
    """
    Bus agent that follows routes and transports pedestrians.
    """
    def __init__(self, unique_id, model, route_id):
        super().__init__(unique_id, model)
        self.route_id = str(route_id)
        self.route = self.model.bus_routes.get(self.route_id, [])
        self.current_stop_index = 0
        self.passengers = []
        self.wait_timer = 0
        self.STOP_WAIT_TIME = 3
        self.intended_next_move = None

    def calculate_path(self, target_pos=None):
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

        possible_goals.sort(key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest))

        for goal_node in possible_goals:
            path_nodes = NavigationService.get_path(self.model.road_graph, start_node, goal_node)
            if len(path_nodes) > 1:
                self.path = [(x, y) for y, x in path_nodes]
                self.path.pop(0)
                return

        # Fallback
        self.path = []

    def move(self):
        # 1. Stop arrival logic
        if self.route:
            target_stop = self.route[self.current_stop_index]
            neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
            
            if target_stop in neighbors:
                cell_agents = self.model.grid.get_cell_list_contents(target_stop)
                from src.domain.entities.pedestrian import Pedestrian
                pedestrians_waiting = any(isinstance(a, Pedestrian) and a.waiting_for_bus for a in cell_agents)
                dropoff_needed = any(abs(p.destination[0] - self.pos[0]) + abs(p.destination[1] - self.pos[1]) < 5 for p in self.passengers)
                
                if pedestrians_waiting or dropoff_needed:
                    if self.wait_timer < self.STOP_WAIT_TIME:
                        self.handle_passengers(target_stop)
                        self.wait_timer += 1
                        self.is_moving = False
                        self.path = []
                        return
                    else:
                        self.wait_timer = 0
                        self.current_stop_index = (self.current_stop_index + 1) % len(self.route)
                        self.path = [] 
                else:
                    self.current_stop_index = (self.current_stop_index + 1) % len(self.route)
                    self.path = []

        # 2. Path Management
        if (not self.path or self.intended_next_move) and self.route:
            self.calculate_path()

        if not self.path:
            self.is_moving = False
            return
            
        next_move = self.path[0]

        # 3. Collision & Traffic Rules
        is_blocked = NavigationService.is_cell_blocked(self.model, next_move, "Bus", self)
        
        # Bus Stop Exception: Allow pedestrians at stop cells
        if is_blocked:
            cell_contents = self.model.grid.get_cell_list_contents(next_move)
            is_target_stop = any(getattr(obj, "is_bus_stop", False) for obj in cell_contents)
            if is_target_stop:
                # If only pedestrians are blocking, it's fine
                only_peds = all(type(a).__name__ == "Pedestrian" or isinstance(a, Road) for a in cell_contents)
                if only_peds:
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

    def handle_passengers(self, stop_pos, frustrated_only=False):
        # Drop off
        arrived = []
        for p in self.passengers:
            is_near = abs(p.destination[0] - self.pos[0]) + abs(p.destination[1] - self.pos[1]) < 5
            is_frustrated = getattr(p, "bus_ride_ticks", 0) >= 200
            if (not frustrated_only and is_near) or is_frustrated:
                arrived.append(p)
        
        for p in arrived:
            self.passengers.remove(p)
            neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
            actual_sidewalks = [n for n in neighbors if any(isinstance(a, SideWalk) or getattr(a, "is_bus_stop", False) for a in self.model.grid.get_cell_list_contents(n))]
            spawn_pos = actual_sidewalks[0] if actual_sidewalks else neighbors[0]
            self.model.grid.place_agent(p, spawn_pos)
            p.on_bus = False
            p.waiting_for_bus = False
            p.target_bus_stop = None
            p.path = []

        # Pick up
        if not frustrated_only:
            cell_agents = self.model.grid.get_cell_list_contents(stop_pos)
            from src.domain.entities.pedestrian import Pedestrian
            for a in cell_agents:
                if isinstance(a, Pedestrian) and a.waiting_for_bus:
                    if len(self.passengers) < 10:
                        self.passengers.append(a)
                        self.model.metrics["total_passengers"] += 1
                        a.on_bus = True
                        a.waiting_for_bus = False
                        a.is_boarding = True
                        a.boarding_ticks = 0
                        self.model.grid.move_agent(a, self.pos)
