"""Bus Agent."""

from mesa import Agent
from src.domain.entities.traffic_components import Road, Traffic_Light, PedestrianCrossing

class Bus(Agent):
    """
    Bus agent.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.route = [(1,9),(6,8),(22,11)]
        self.direction = None
        self.lastDirection = None
        self.moving = False
        self.previous_pos = None

    def move(self):
        if self.pos == self.route[0]:
            if self.direction != self.lastDirection:
                self.direction = self.lastDirection
            else:
                self.direction = self.direction
            temp = self.route[0]
            self.route.remove(self.route[0])
            self.route.append(temp)

        next_move = None
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
            return

        whatIsFront = self.model.grid.get_neighbors(next_move, moore=False, include_center=True, radius=0)
        agentsFront = [agent for agent in whatIsFront if not isinstance(agent, Road)]

        if agentsFront == []:
            old_pos = self.pos
            self.model.grid.move_agent(self, next_move)
            self.moving = True
            self.previous_pos = old_pos
            return
        elif isinstance(agentsFront[0], Traffic_Light) or isinstance(agentsFront[-1], Traffic_Light):
            agentsFront = [agent for agent in agentsFront if isinstance(agent, Traffic_Light)]
            if agentsFront and agentsFront[0].state == True:
                old_pos = self.pos
                self.model.grid.move_agent(self, next_move)
                self.moving = True
                self.previous_pos = old_pos
                return
            else:
                self.moving = False
                return
        elif isinstance(agentsFront[0], PedestrianCrossing) or isinstance(agentsFront[-1], PedestrianCrossing):
            agentsFront = [agent for agent in agentsFront if isinstance(agent, PedestrianCrossing)]
            if agentsFront and agentsFront[0].state == False:
                old_pos = self.pos
                self.model.grid.move_agent(self, next_move)
                self.moving = True
                self.previous_pos = old_pos
                return
            else:
                self.moving = False
                return
        elif hasattr(agentsFront[0], "moving"):
            if agentsFront[0].moving == True:
                old_pos = self.pos
                self.model.grid.move_agent(self, next_move)
                self.moving = True
                self.previous_pos = old_pos
                return
            else:
                self.moving = False
                return

    def step(self):
        currentIn = self.model.grid.get_neighbors(self.pos, moore=False, include_center=True, radius=0)
        RoadDirection = [agent for agent in currentIn if isinstance(agent, Road)]
        if RoadDirection != []:
            self.lastDirection = self.direction
            self.direction = RoadDirection[0].direction
        else:
            self.direction = self.direction
        self.move()
