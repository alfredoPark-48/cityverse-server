"""Application service to manage agent replenishment."""

import uuid
from src.domain.entities import Car, Pedestrian, Bus

class SpawningService:
    """Handles agent creation and replenishment logic."""

    @staticmethod
    def replenish_cars(model):
        active_cars = [a for a in model.schedule.agents if isinstance(a, Car)]
        if len(active_cars) < model.target_cars:
            spawn_pool = model.car_spawns_temp if model.car_spawns_temp else model.positions_temp
            for _ in range(model.target_cars - len(active_cars)):
                destpos = model.random.choice(model.parking_temp) if model.parking_temp else None
                a = Car(str(uuid.uuid4()), model, destpos)
                pos = model.random.choice(spawn_pool)
                
                # Check for space
                attempts = 5
                while any(isinstance(ag, Car) for ag in model.grid.get_cell_list_contents(pos)) and attempts > 0:
                    pos = model.random.choice(spawn_pool)
                    attempts -= 1
                
                model.schedule.add(a)
                model.grid.place_agent(a, pos)

    @staticmethod
    def replenish_pedestrians(model):
        active_peds = [a for a in model.schedule.agents if isinstance(a, Pedestrian)]
        if len(active_peds) < model.target_peds:
            spawn_pool = model.ped_spawns_temp if model.ped_spawns_temp else model.pedPos_temp
            for _ in range(model.target_peds - len(active_peds)):
                destpos = model.random.choice(model.destinys_temp)
                a = Pedestrian(str(uuid.uuid4()), model, destpos)
                pos = model.random.choice(spawn_pool)
                
                # Check for space (minor optimization to avoid immediate overlaps)
                attempts = 3
                while any(type(ag).__name__ == "Pedestrian" for ag in model.grid.get_cell_list_contents(pos)) and attempts > 0:
                    pos = model.random.choice(spawn_pool)
                    attempts -= 1
                
                model.schedule.add(a)
                model.grid.place_agent(a, pos)

    @staticmethod
    def replenish_buses(model):
        active_buses = [a for a in model.schedule.agents if isinstance(a, Bus)]
        
        # 1. Ensure coverage
        active_route_ids = [getattr(b, "route_id", None) for b in active_buses]
        for rid in model.bus_routes:
            if rid not in active_route_ids and model.bus_routes[rid]:
                b = Bus(str(uuid.uuid4()), model, rid)
                pos = model._bus_spawn_pos(rid)
                model.schedule.add(b)
                model.grid.place_agent(b, pos)
                active_buses.append(b)

        # 2. Scale
        while len(active_buses) < model.target_buses:
            route_counts = {rid: 0 for rid in model.bus_routes}
            for b in active_buses:
                route_counts[b.route_id] += 1
            target_rid = min(route_counts, key=route_counts.get)
            b = Bus(str(uuid.uuid4()), model, target_rid)
            pos = model._bus_spawn_pos(target_rid)
            model.schedule.add(b)
            model.grid.place_agent(b, pos)
            active_buses.append(b)
