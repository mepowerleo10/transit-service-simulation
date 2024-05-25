import datetime
from math import floor
import traceback
from typing import List

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from models import ReservationStatus, ServiceRegion, Trip, TripDirection

from env import OUTPUT_DIR, SECONDS_PER_MINUTE, RESERVATION_CUTOFF, SHUTTLE_SPEED


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
        self.cut_off_time = RESERVATION_CUTOFF * SECONDS_PER_MINUTE  # 50 minutes
        self.shuttle_speed = SHUTTLE_SPEED
        self.max_distance = floor(self.cut_off_time * self.shuttle_speed)

    def run(self): ...

    def generate_scenario_name(self):
        now = datetime.datetime.now()
        return f"{self.__class__.__name__}/{now.strftime("%d_%m_%Y__%H_%M_%S.%f")}"

    def get_generated_route(self, trips: List[Trip]):
        routing_stops_distance_matrix = self.pick_routing_stops_distance_matrix(trips)
        manager = pywrapcp.RoutingIndexManager(
            len(trips),
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

        # Allow to drop nodes.
        penalty = 1000
        for node in range(1, len(trips)):
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        search_parameters.log_search = True

        solution = routing.SolveWithParameters(search_parameters)

        return manager, routing, solution

    def get_dropped_nodes(self, routing, manager, solution) -> List[int]:
        """Returns a list of IDs for the dropped nodes"""

        dropped_nodes = []
        for node in range(routing.Size()):
            if routing.IsStart(node) or routing.IsEnd(node):
                continue
            index = manager.IndexToNode(node)
            if solution.Value(routing.NextVar(index)) == index:
                dropped_nodes.append(manager.IndexToNode(index))

        return dropped_nodes

    def write_generated_trips(self):
        output_lines = (
            "ID, DIRECTION, LOCATION_INDEX, RESERVED_AT, RESERVATION_STATUS\n"
        )
        for trip in self.trips:
            output_lines += f"{trip.as_csv_line()}\n"

        trips_file = self.scenario_directory / "trips.csv"
        with open(trips_file, mode="w+") as f:
            f.write(output_lines)

    def write_results(
        self,
        solution: pywrapcp.SolutionCollector,
        routing,
        manager,
        dropped_nodes,
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

                f.writelines(["\nDropped Nodes: ", str(dropped_nodes)])

            except Exception:
                f.write("Failed to find solution\n")
                f.writelines(traceback.format_exc())

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
        trip_location_indices = [trip.location_index for trip in trips]
        locations = [self.service_region.fixed_stop_index] + trip_location_indices
        rows = self.service_region.stops_distance_matrix[locations]
        return rows[:, locations].astype(int)


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

    def run(self):
        """trips_within_time = [
            trip for trip in self.trips if trip.reserved_at <= RESERVATION_CUTOFF
        ]  # ignore all trips above the cutoff time"""

        trips_within_time = {}
        for index, trip in enumerate(self.trips):
            if trip.reserved_at <= RESERVATION_CUTOFF:
                trips_within_time[index] = trip

        manager, routing, solution = self.get_generated_route(
            list(trips_within_time.values())
        )
        dropped_nodes = self.get_dropped_nodes(routing, manager, solution)

        if solution:
            for index, trip in enumerate(self.trips):
                status = ReservationStatus.REJECTED
                if (
                    index in list(trips_within_time.keys())
                    and index + 1 not in dropped_nodes # dropped nodes contains the fixed_stop, offset the index by one forward
                ):
                    status = ReservationStatus.ACCEPTED

                trip.reservation_status = status

        self.write_generated_trips()
        self.write_results(solution, routing, manager, dropped_nodes)


class ScenarioOne(AbstractScenario):
    """
    Scenario 1: notice riders are considered
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

    def run(self):
        trips_within_time = [
            trip for trip in self.trips if trip.reserved_at <= RESERVATION_CUTOFF
        ]  # ignore all trips above the cutoff time

        manager, routing, solution = self.get_generated_route(trips_within_time)
        dropped_nodes = self.get_dropped_nodes(routing, manager, solution)

        if solution:
            for trip in self.trips:
                trip_within_time_ids = [t.id for t in trips_within_time]
                trip.reservation_status = (
                    ReservationStatus.ACCEPTED
                    if trip.id in trip_within_time_ids
                    else ReservationStatus.REJECTED
                )

        self.write_generated_trips()
        self.write_results(solution, routing, manager, dropped_nodes)
