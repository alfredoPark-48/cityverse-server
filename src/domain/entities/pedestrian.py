"""Pedestrian Agent."""

from mesa import Agent
from src.domain.entities.traffic_components import PedestrianCrossing, SideWalk, Destination, Traffic_Light

class Pedestrian(Agent):
    """
    Pedestrian agent.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.visited = []
        self.indestiny = False

    def move(self):
        if self.pos == None:
            self.indestiny = True
            self.model.schedule.remove(self)
            return

        posibleSteps = self.model.grid.get_neighbors(self.pos, moore=False, include_center=False, radius=1)
        isPedestrianViable = [agent.pos for agent in posibleSteps if isinstance(agent, PedestrianCrossing) or isinstance(agent, SideWalk) or isinstance(agent, Destination) or isinstance(agent, Traffic_Light)]
        
        if not isPedestrianViable:
            return

        next_move = self.random.choice(isPedestrianViable)
        isPedestrianViable.remove(next_move)

        while next_move in self.visited and isPedestrianViable != []:
            next_move = self.random.choice(isPedestrianViable)
            isPedestrianViable.remove(next_move)

        self.visited.append(next_move)

        whatIsFront = self.model.grid.get_neighbors(next_move, moore=False, include_center=True, radius=0)
        notAPedestrian = [agent for agent in whatIsFront if type(agent).__name__ not in ["Pedestrian", "Car", "Bus"]]

        if not notAPedestrian:
            self.model.grid.move_agent(self, next_move)
            return

        if isinstance(notAPedestrian[0], Traffic_Light):
            if notAPedestrian[0].state == False:
                self.model.grid.move_agent(self, next_move)
                return
            else:
                if next_move in self.visited:
                    self.visited.remove(next_move)
                return
                
        elif isinstance(notAPedestrian[0], PedestrianCrossing):
            if notAPedestrian[0].state == None or notAPedestrian[0].state == "Pedestrian":
                self.model.grid.move_agent(self, next_move)
                return
            else:
                if next_move in self.visited:
                    self.visited.remove(next_move)
                return
                
        elif isinstance(notAPedestrian[0], Destination):
            self.indestiny = True
            self.model.schedule.remove(self)
            self.model.grid.move_agent(self, next_move)
            return
            
        else:
            self.model.grid.move_agent(self, next_move)
            return

    def step(self):
        self.move()
