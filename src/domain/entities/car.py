"""Car Agent."""

from mesa import Agent
from src.application.services.graph_service import shortestPath
from src.domain.entities.traffic_components import Road, Destination, Traffic_Light, PedestrianCrossing, Angel

class Car(Agent):
    """
    Agent that moves using pathfinding.
    """
    def __init__(self, unique_id, model, destiny):
        super().__init__(unique_id, model)
        self.direction = None
        self.destiny = destiny
        self.moving = False
        self.myDestiny = None
        self.lastNode = None
        self.lastMove = None
        self.lastlastMove = None
        self.inDestiny = False
        self.previous_pos = None

    def move(self):
        next_move = None
        current_x, current_y = self.pos
        
        # 1. Arrival Check (Neighborhood Aware)
        # Check if destiny is in a neighbor cell
        aroundMe = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=1)
        for neighbor in aroundMe:
            if isinstance(neighbor, Destination) and neighbor.pos == self.destiny:
                next_move = neighbor.pos
                if 0 <= next_move[0] < self.model.grid.width and 0 <= next_move[1] < self.model.grid.height:
                    self.model.grid.move_agent(self, next_move)
                    self.inDestiny = True
                    self.model.schedule.remove(self)
                return

        # 2. Simple Directional Movement
        if self.direction in ["Up", "Down", "Left", "Right"]:
            if self.direction == "Up":
                next_move = (current_x, current_y + 1)
            elif self.direction == "Down":
                next_move = (current_x, current_y - 1)
            elif self.direction == "Left":
                next_move = (current_x - 1, current_y)
            elif self.direction == "Right":
                next_move = (current_x + 1, current_y)
        
        # 3. Intersection Pathfinding
        elif self.direction == "Intersection":
            # Recalculate path if none exists
            if self.myDestiny is None or len(self.myDestiny) == 0:
                x_dest, y_dest = self.destiny
                res = shortestPath(self.model.list_of_edges, (current_y, current_x), (y_dest, x_dest))
                self.myDestiny = res[1]
                if len(self.myDestiny) > 1:
                    self.myDestiny.pop(0) # Remove current pos
                
            if self.myDestiny:
                target_y, target_x = self.myDestiny.pop(0)
                next_move = (target_x, target_y)
            else:
                # Random fallback if pathfinding fails completely
                aroundAgent = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=1)
                agentsFront = [agent for agent in aroundAgent if isinstance(agent, Road) and agent.pos != self.previous_pos]
                if agentsFront:
                    next_move = self.random.choice(agentsFront).pos
                else:
                    return

        if next_move is None:
            return

        # 4. Final Movement & Collision Detection
        if not (0 <= next_move[0] < self.model.grid.width and 0 <= next_move[1] < self.model.grid.height):
            self.moving = False
            return

        # Check for blockers (other cars, red lights, etc.)
        cell_contents = self.model.grid.get_cell_list_contents(next_move)
        blockers = [a for a in cell_contents if not isinstance(a, Road)]
        
        can_move = True
        if blockers:
            for b in blockers:
                if isinstance(b, Traffic_Light):
                    if not b.state: # Red light
                        can_move = False
                        break
                elif isinstance(b, PedestrianCrossing):
                    if b.state not in [None, "Car"]: # Pedestrians crossing
                        can_move = False
                        break
                elif hasattr(b, "moving"): # Another car
                    if not b.moving:
                        can_move = False
                        break
                    # MultiGrid allows stacking, but for realism we stop
                    can_move = False
                    break
                elif isinstance(b, (Destination, Angel)):
                    pass # We can enter these
                else:
                    can_move = False # Buildings, etc.
                    break

        if can_move:
            self.previous_pos = self.pos
            self.model.grid.move_agent(self, next_move)
            self.moving = True
            # Update lastNode for direction guessing if needed
            self.lastNode = next_move
        else:
            self.moving = False
            # If we were following a path, put the target back
            if self.direction == "Intersection" and self.myDestiny is not None:
                # next_move was (target_x, target_y)
                self.myDestiny.insert(0, (next_move[1], next_move[0]))
        
        self.lastlastMove = self.lastMove
        self.lastMove = next_move

    def step(self):
        currentIn = self.model.grid.get_neighbors(self.pos, moore=False, include_center=True, radius=0)
        roads = [agent for agent in currentIn if isinstance(agent, Road)]
        if roads:
            self.direction = roads[0].direction
        self.move()
