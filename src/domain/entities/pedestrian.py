"""Pedestrian Agent with A* Pathfinding."""

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
)


class Pedestrian(Agent):
    """
    Agent that moves on sidewalks and crossings using A* pathfinding.
    """

    def __init__(self, unique_id, model, destiny):
        super().__init__(unique_id, model)
        self.destiny = destiny
        self.path = []
        self.indestiny = False
        self.moving = False

    def calculate_path(self):
        """Calculates a path to the destination using A* on the pedestrian graph."""
        current_x, current_y = self.pos
        x_dest, y_dest = self.destiny

        start_node = (current_y, current_x)
        goal_node = (y_dest, x_dest)

        # 1. Ensure goal is in graph
        if goal_node not in self.model.ped_graph:
            nodes = list(self.model.ped_graph.keys())
            if nodes:
                # Find nearest walkable node to destination
                goal_node = min(
                    nodes, key=lambda n: abs(n[0] - y_dest) + abs(n[1] - x_dest)
                )

        # 2. Try A*
        _, path = a_star_search(self.model.ped_graph, start_node, goal_node)

        # 3. Fallback: if goal is unreachable, find closest reachable node
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
            self.path.pop(0)  # Remove current pos
        else:
            self.path = []

    def move(self):
        # 1. Arrival Check
        if self.pos == self.destiny:
            self.indestiny = True
            self.model.total_parked_peds += 1
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # 1.5 No more proximity check - pedestrians must touch the destination cell.

        # 2. Path Management
        if not self.path:
            self.calculate_path()

        # 3. Determine Next Move
        if self.path:
            next_move = self.path[0]
        else:
            # Fallback: if adjacent to destiny
            dist = abs(self.pos[0] - self.destiny[0]) + abs(self.pos[1] - self.destiny[1])
            if dist == 1:
                next_move = self.destiny
            else:
                return

        # 3.5 Adjacency Arrival Check for "Building-like" destinations (Home, Lot)
        if next_move == self.destiny:
            cell_agents = self.model.grid.get_cell_list_contents(next_move)
            if any(isinstance(a, (Home, Lot)) for a in cell_agents):
                self.indestiny = True
                self.model.total_parked_peds += 1
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                return

        # 4. Collision & Traffic Rules
        cell_contents = self.model.grid.get_cell_list_contents(next_move)

        can_move = True
        for a in cell_contents:
            if isinstance(a, Traffic_Light):
                if a.state:  # Green for cars -> Red for pedestrians
                    can_move = False
                    break
            elif isinstance(a, Building):
                can_move = False
                break
            elif isinstance(a, Home):
                can_move = False
                break
            elif isinstance(a, Lot):
                can_move = False
                break
            elif isinstance(a, Vegetation):
                can_move = False
                break
            elif isinstance(a, Water):
                can_move = False
                break
            elif isinstance(a, PedestrianCrossing):
                if a.state == "Car":
                    can_move = False
                    break
            elif type(a).__name__ in ["Car", "Bus"]:
                # Wait for cars/buses if the cell is blocked
                can_move = False
                break
            # Note: Pedestrians ignore other pedestrians (they can stack)
            pass

        if can_move:
            self.model.grid.move_agent(self, next_move)
            if self.path:
                self.path.pop(0)
            self.moving = True
        else:
            self.moving = False
            # Re-calculate path occasionally if blocked for too long
            if self.random.random() < 0.1:
                self.path = []

    def step(self):
        self.move()
