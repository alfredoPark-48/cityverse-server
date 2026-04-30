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

class Building(Agent):
    """Building agent. Where buildings are in the grid. Agent can arrive to the building as destination. Agent can't pass through the building."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Vegetation(Agent):
    """Vegetation agent. Where vegetation is in the grid. Agent can't pass through the vegetation."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class Water(Agent):
    """Water agent. Where water is in the grid. Agent can't pass through the water."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Angel(Agent):
    """Traffic circle agent. Where traffic circles are in the grid. Agent can't pass through the traffic circle."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass


class Road(Agent):
    """Road agent. Determines where the cars can move, and in which direction."""
    def __init__(self, unique_id, model, direction="Left"):
        super().__init__(unique_id, model)
        self.direction = direction
        self.is_bus_stop = False

    def step(self):
        pass


class SideWalk(Agent):
    """Sidewalk agent. Determines where the persons can walk."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class Parking(Agent):
    """Parking agent. Areas where cars can park or drive through."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class Lot(Agent):
    """Lot agent. Open spaces in the city."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class Home(Agent):
    """Home agent. Where pedestrians can spawn or go to."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class CarSpawn(Agent):
    """Car spawn agent. Where cars can spawn."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class PedestrianSpawn(Agent):
    """Pedestrian spawn agent. Where pedestrians can spawn."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass
