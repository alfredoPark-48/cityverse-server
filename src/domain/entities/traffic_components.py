"""Traffic components: static agents for the city grid."""

from mesa import Agent

class Traffic_Light(Agent):
    """Traffic light. Where the traffic lights are in the grid."""
    def __init__(self, unique_id, model, state=False, timeToChange=10):
        super().__init__(unique_id, model)
        self.state = state
        self.timeToChange = timeToChange
        self.vertical = False
        self.horizontal = False

    def step(self):
        pass

class PedestrianCrossing(Agent):
    """Pedestrian crossing agent. Determines where a pedestrian can cross the street"""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = None

    def step(self):
        # Checks if a pedestrian or car is over it.
        # Note: Need to import Car and Bus or do lazy imports/class name matching to avoid circular deps
        AgentOverIt = self.model.grid.get_neighbors(self.pos, moore=False, include_center=True, radius=0)
        
        has_car = any(type(a).__name__ in ["Car", "Bus"] for a in AgentOverIt)
        has_ped = any(type(a).__name__ == "Pedestrian" for a in AgentOverIt)
        
        if has_car:
            self.state = "Car"
        elif has_ped:
            self.state = "Pedestrian"
        else:
            self.state = None


class Destination(Agent):
    """Destination agent. Where each car should go."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Obstacle(Agent):
    """Obstacle agent. Just to add obstacles to the grid. Interpreted as a building in Unity."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Angel(Agent):
    """Angel agent (obstacle). Interpreted as a traffic circle in Unity."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Road(Agent):
    """Road agent. Determines where the cars can move, and in which direction."""
    def __init__(self, unique_id, model, direction="Left"):
        super().__init__(unique_id, model)
        self.direction = direction

    def step(self):
        pass


class SideWalk(Agent):
    """Sidewalk agent. Determines where the persons can walk."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass
