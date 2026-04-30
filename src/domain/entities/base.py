"""Base agent classes for CityVerse."""

from mesa import Agent
from abc import ABC, abstractmethod

class BaseTrafficAgent(Agent, ABC):
    """Base class for all traffic agents (Car, Pedestrian, Bus)."""
    
    def __init__(self, unique_id, model, destination=None):
        super().__init__(unique_id, model)
        self.destination = destination
        self.path = []
        self.is_moving = False
        self.has_arrived = False
        self.direction = "None"
        self.previous_pos = None
        self.wait_ticks = 0

    @abstractmethod
    def calculate_path(self):
        """Logic to calculate path to destination."""
        pass

    @abstractmethod
    def move(self):
        """Logic to move the agent."""
        pass

    def step(self):
        """Standard Mesa step."""
        if not self.has_arrived:
            self.move()

    def _update_direction(self, next_pos):
        """Updates the direction string for visuals."""
        if not self.pos or not next_pos:
            return
        curr_x, curr_y = self.pos
        next_x, next_y = next_pos
        if next_x > curr_x: self.direction = "Right"
        elif next_x < curr_x: self.direction = "Left"
        elif next_y > curr_y: self.direction = "Up"
        elif next_y < curr_y: self.direction = "Down"
