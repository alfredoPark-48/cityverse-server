"""Bus Agent."""

from mesa import Agent
from src.domain.entities.traffic_components import Road, Traffic_Light, PedestrianCrossing

class Bus(Agent):
    """
    Bus agent that follows roads but picks directions randomly at intersections.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.direction = None
        self.lastDirection = None
        self.moving = False
        self.previous_pos = None
        self.intended_next_move = None

    def move(self):
        next_move = None
        
        # If we have an intended move (e.g. from a previous step where we were blocked), reuse it
        if self.intended_next_move:
            next_move = self.intended_next_move
        else:
            if self.direction == "Up":
                next_move = (self.pos[0], self.pos[1] + 1)
            elif self.direction == "Down":
                next_move = (self.pos[0], self.pos[1] - 1)
            elif self.direction == "Left":
                next_move = (self.pos[0] - 1, self.pos[1])
            elif self.direction == "Right":
                next_move = (self.pos[0] + 1, self.pos[1])
            elif self.direction == "Intersection":
                aroundAgent = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=1)
                # Avoid U-turns
                agentsRoad = [agent for agent in aroundAgent if isinstance(agent, Road) and agent.pos != self.previous_pos]
                if agentsRoad:
                    next_move = self.random.choice(agentsRoad).pos
                else:
                    return
            else:
                return

        # Check if next_move is out of bounds
        if not next_move or not (0 <= next_move[0] < self.model.grid.width and 0 <= next_move[1] < self.model.grid.height):
            self.moving = False
            self.intended_next_move = None
            return

        # Check for blockers
        whatIsFront = self.model.grid.get_cell_list_contents(next_move)
        blockers = [agent for agent in whatIsFront if not isinstance(agent, Road)]

        can_move = True
        if blockers:
            for b in blockers:
                if isinstance(b, Traffic_Light):
                    if not b.state: # Red light
                        can_move = False
                        break
                elif isinstance(b, PedestrianCrossing):
                    if b.state not in [None, "Car"]:
                        can_move = False
                        break
                elif hasattr(b, "moving"):
                    # Other vehicles
                    can_move = False
                    break
                else:
                    # Buildings, etc.
                    can_move = False
                    break

        if can_move:
            old_pos = self.pos
            self.model.grid.move_agent(self, next_move)
            self.moving = True
            self.previous_pos = old_pos
            self.intended_next_move = None # Clear after successful move
        else:
            self.moving = False
            self.intended_next_move = next_move # Remember choice to avoid shuffling

    def step(self):
        currentIn = self.model.grid.get_cell_list_contents(self.pos)
        roads = [agent for agent in currentIn if isinstance(agent, Road)]
        if roads:
            self.lastDirection = self.direction
            # Prioritize Intersection mode
            if any(r.direction == "Intersection" for r in roads):
                self.direction = "Intersection"
            else:
                self.direction = roads[0].direction
        self.move()
