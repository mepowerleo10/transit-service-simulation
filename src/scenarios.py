import datetime
from math import floor
from pathlib import Path
from typing import List

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from models import ServiceRegion, Trip, TripDirection

from env import OUTPUT_DIR, SECONDS_PER_MINUTE


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

        self.scenario_name = self.generate_scenario_name()
        self.scenario_directory = OUTPUT_DIR / self.scenario_name
        self.scenario_directory.mkdir(parents=True, exist_ok=True)

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
        self.trips_density = 0
        self.cut_off_time = 50 * SECONDS_PER_MINUTE  # 50 minutes
        self.shuttle_speed = (
            0.5  # the shuttle moves with a constant speed of x units of distance/sec
        )
        self.max_distance = floor(self.cut_off_time * self.shuttle_speed)

    def generate_scenario_name(self):
        now = datetime.datetime.now()
        return f"{self.__class__.__name__}__{now.strftime("%d_%m_%Y__%H_%M_%S.%f")}"

    def run(self): ...

    def save(self): ...

    def write_generated_trips(self):
        output_lines = "ID, DIRECTION, LOCATION_INDEX, RESERVED_AT, RESERVATION_STATUS"
        for trip in self.trips:
            output_lines += f"{trip.as_csv_line()}\n"

        trips_file = self.scenario_directory / "trips.csv"
        with open(trips_file, mode="w+") as f:
            f.write(output_lines)

    def write_results(
        self, solution: pywrapcp.SolutionCollector, routing, manager, picked_trips
    ):
        """Writes the solution to the filesystem."""

        results_file = self.scenario_directory / "results.txt"
        with open(results_file, mode="w+") as f:
            try:
                f.write(f"Objective: {solution.ObjectiveValue()} s\n")

                index = routing.Start(0)
                plan_output = "Route for Shuttle:\n"
                route_distance = 0.0
                while not routing.IsEnd(index):
                    plan_output += f" {manager.IndexToNode(index)} ->"
                    previous_index = index
                    index = solution.Value(routing.NextVar(index))
                    route_distance += routing.GetArcCostForVehicle(
                        previous_index, index, 0
                    )
                plan_output += f" {manager.IndexToNode(index)}\n"
                plan_output += f"Route time: {route_distance}s\n\n"

                f.write(plan_output)
                f.write(str(picked_trips))
            except Exception as e:
                f.write("Failed to find solution")
                f.write(e)

    def generate_trips(self):
        # Pick random stops from all other stops, excluding the fixed stop.
        # These will be used to generate a list of trips
        random_stops_index = np.random.choice(
            self.service_region.none_fixed_stops.shape[0], self.trips_density
        )
        for num, stop_index in enumerate(random_stops_index):
            reservation_time = np.random.randint(0, 60)
            direction_of_travel = (
                TripDirection.INBOUND
                if np.random.random() < self.inbound_or_outbound_px
                else TripDirection.OUTBOUND
            )
            trip = Trip(
                id=num + 1,
                reserved_at=reservation_time,
                direction=direction_of_travel,
                location_index=stop_index,
            )
            self.trips.append(trip)

    def pick_routing_stops_distance_matrix(self, trips: List[Trip]):
        trip_ids = [trip.id for trip in trips]
        trip_location_indices = [trip.location_index for trip in trips]
        locations = [self.service_region.fixed_stop_index] + trip_location_indices
        rows = self.service_region.stops_distance_matrix[locations]
        return tuple(zip(trip_ids, trip_location_indices)), rows[:, locations].astype(
            int
        )


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

        self.trips_density = int(self.service_region.num_of_zones * self.lambda_param)
        self.generate_trips()

    def generate_route(self, trips):
        trip_locations, routing_stops_distance_matrix = (
            self.pick_routing_stops_distance_matrix(trips)
        )
        manager = pywrapcp.RoutingIndexManager(
            self.trips_density,
            self.num_of_shuttles,
            0,
        )
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            """Returns the travel distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return routing_stops_distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        dimension_name = "Distance"
        routing.AddDimension(
            transit_callback_index,
            0,  # no slack
            self.max_distance,  # maximum travel time
            True,  # start cumul at zero
            dimension_name,
        )
        distance_dimension: pywrapcp.RoutingDimension = routing.GetDimensionOrDie(
            dimension_name
        )
        distance_dimension.SetGlobalSpanCostCoefficient(50)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(search_parameters)
        return trip_locations, manager, routing, solution

    def run(self):
        trip_locations, manager, routing, solution = self.generate_route(self.trips)

        self.write_generated_trips()
        self.write_results(solution, routing, manager, trip_locations)
