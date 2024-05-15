from math import floor
import numpy as np
from typing import List
from models import ServiceRegion, Trip, TripDirection


class AbstractScenario:
    def __init__(
        self,
        num_of_zones_per_row: int,
        zone_length: float,
        lambda_param: float,
        planning_horizon: float,
    ) -> None:
        self.num_of_zones_per_row = num_of_zones_per_row
        self.zone_length = zone_length
        self.lambda_param = lambda_param
        self.planning_horizon = planning_horizon

        # Initialize a list of trips as empty in the beginning
        self.trips: List[Trip] = list()

        # Create a service region
        self.service_region = ServiceRegion(self.num_of_zones_per_row, self.zone_length)
        

    def run(self): ...

    def save(self): ...

    def plot(self): ...

    def initialize_random_trips(self, trips_density: int):
        # Pick random stops from all other stops, excluding the fixed stop. Theses will be used to generate a list of trips
        random_rows_index = np.random.choice(
            self.service_region.none_fixed_stops.shape[0], trips_density
        )
        random_stops = self.service_region.none_fixed_stops[random_rows_index]
        for stop in random_stops:
            reservation_time = np.random.randint(0, floor(self.planning_horizon * 60))
            direction_of_travel = (
                TripDirection.INBOUND
                if np.random.random() < 0.5
                else TripDirection.OUTBOUND
            )
            trip = Trip(
                reserved_at=reservation_time,
                direction=direction_of_travel,
                location=tuple(stop),
            )
            self.trips.append(trip)


class ScenarioZero(AbstractScenario):
    """
    Scenario 0: no short notice riders are accepted
    """

    def __init__(
        self,
        num_of_zones_per_row: int,
        zone_length: float,
        lambda_param: float,
        planning_horizon: float,
    ) -> None:
        super().__init__(
            num_of_zones_per_row, zone_length, lambda_param, planning_horizon
        )

        trips_density = int(
            self.service_region.num_of_zones * self.lambda_param * self.planning_horizon
        )
        self.initialize_random_trips(trips_density)
        
