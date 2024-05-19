from math import floor
from typing import List

import numpy as np
import pandas as pd
from models import ServiceRegion, Trip, TripDirection
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


class AbstractScenario:
    def __init__(
        self,
        num_of_zones_per_row: int,
        zone_length: float,
        lambda_param: float,
        planning_horizon: float,
    ) -> None:
        """
        lambda_param: Demand density (number of passengers per hour per zone)
        """

        self.num_of_zones_per_row = num_of_zones_per_row
        self.zone_length = zone_length
        self.lambda_param = lambda_param
        self.planning_horizon = planning_horizon

        # Initialize a list of trips as empty in the beginning
        self.trips: List[Trip] = list()

        # Create a service region
        self.service_region = ServiceRegion(self.num_of_zones_per_row, self.zone_length)

        self.inbound_or_outbound_px = (
            0.5  # Probability that a trip is inbound or outbound
        )

        self.num_of_shuttles = 1

        self.manager: pywrapcp.RoutingIndexManager = None
        self.routing: pywrapcp.RoutingModel = None
        self.solution = None

    def run(self): ...

    def save(self): ...

    def print(self): ...

    def generate_trips(self, trips_density: int):
        # Pick random stops from all other stops, excluding the fixed stop. Theses will be used to generate a list of trips
        random_rows_index = np.random.choice(
            self.service_region.none_fixed_stops.shape[0], trips_density
        )
        random_stops = self.service_region.none_fixed_stops[random_rows_index]
        for stop in random_stops:
            reservation_time = np.random.randint(0, floor(self.planning_horizon * 60))
            direction_of_travel = (
                TripDirection.INBOUND
                if np.random.random() < self.inbound_or_outbound_px
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
        self.generate_trips(trips_density)

        self.manager = pywrapcp.RoutingIndexManager(
            self.num_of_zones_per_row,
            self.num_of_shuttles,
            self.service_region.fixed_stop_index,
        )
        self.routing = pywrapcp.RoutingModel(self.manager)

    def run(self):
        def time_callback(from_index, to_index):
            """Returns the travel time between the two nodes."""
            # Convert from routing variable Index to time matrix NodeIndex.
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return self.service_region.stops_distance_matrix[from_node][to_node]

        transit_callback_index = self.routing.RegisterTransitCallback(time_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        dimension_name = "Distance"
        self.routing.AddDimension(
            transit_callback_index,
            0, # no slack
            3000, # maximum travel time
            True, # start cumul at zero
            dimension_name,
        )
        distance_dimension: pywrapcp.RoutingDimension = self.routing.GetDimensionOrDie(dimension_name)
        distance_dimension.SetGlobalSpanCostCoefficient(50)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        self.solution = self.routing.SolveWithParameters(search_parameters)

    def print(self):
        df = pd.DataFrame(self.service_region.stops_distance_matrix)
        print(df)

        """Prints solution on console."""
        print(f"Objective: {self.solution.ObjectiveValue()} miles")
        index = self.routing.Start(0)
        plan_output = "Route for vehicle 0:\n"
        route_distance = 0
        while not self.routing.IsEnd(index):
            plan_output += f" {self.manager.IndexToNode(index)} ->"
            previous_index = index
            index = self.solution.Value(self.routing.NextVar(index))
            route_distance += self.routing.GetArcCostForVehicle(
                previous_index, index, 0
            )
        plan_output += f" {self.manager.IndexToNode(index)}\n"
        print(plan_output)
        plan_output += f"Route distance: {route_distance}miles\n"
