import datetime
from math import floor
from timeit import default_timer as timer
import traceback
from typing import List

import numpy as np
import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from models import Config, ReservationStatus, ServiceRegion, Trip, TripDirection
import graph

SECONDS_PER_MINUTE = 60


class AbstractScenario:
    def __init__(
        self,
        config: Config,
    ) -> None:
        """
        lambda_param: Demand density (number of passengers per hour per zone)
        """

        self.config = config

        self.scenario_name = self.generate_scenario_name()
        self.scenario_directory = config.output_dir / "data" / self.scenario_name
        self.scenario_directory.mkdir(parents=True, exist_ok=True)

        self.num_of_zones_per_row = config.number_of_zones_per_row
        self.zone_length = config.zone_length
        self.zone_width = config.zone_width
        self.lambda_param = config.lambda_param
        self.planning_horizon = config.planning_horizon

        # Initialize a list of trips as empty in the beginning
        self.trips: List[Trip] = list()

        # Create a service region
        self.service_region = ServiceRegion(
            self.num_of_zones_per_row, self.zone_length, self.zone_width
        )

        self.inbound_or_outbound_px = (
            0.5  # Probability that a trip is inbound or outbound
        )

        self.num_of_shuttles = 1
        self.trips_density = 0
        self.cut_off_time = (
            config.reservation_cuttoff * SECONDS_PER_MINUTE
        )  # 50 minutes
        self.shuttle_speed = config.shuttle_speed
        self.max_distance = floor(self.cut_off_time * self.shuttle_speed)

        self.search_parameters = None
        self.allow_dropping = True

        self.init()

    def init(self):
        pass

    def run(self): ...

    def generate_scenario_name(self):
        now = datetime.datetime.now()
        return f"{now.strftime("%d_%m_%Y__%H_%M_%S.%f")}"

    def get_generated_route(self, trips: List[Trip]):
        starting_time = timer()

        routing_stops_distance_matrix = self.pick_routing_stops_distance_matrix(trips)
        manager = pywrapcp.RoutingIndexManager(
            len(trips) + 1,
            self.num_of_shuttles,
            0,  # the fixed stop index is always the first item in routing_stops_distance_matrix
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

        if self.allow_dropping:
            # Allow to drop nodes.
            penalty = 1000
            for node in range(1, len(trips)):
                routing.AddDisjunction([manager.NodeToIndex(node)], penalty)

        if not self.search_parameters:
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = 30
            search_parameters.log_search = True
        else:
            search_parameters = self.search_parameters

        solution = routing.SolveWithParameters(search_parameters)

        elapsed_time = timer() - starting_time

        return manager, routing, solution, elapsed_time

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
        elapsed_time: 0.0,
    ):
        """Writes the solution to the filesystem."""

        route_points = []
        results_file = self.scenario_directory / "results.txt"
        with open(results_file, mode="w+") as f:
            try:
                # f.write(f"Objective: {solution.ObjectiveValue()} s\n")
                f.write(f"Objective: <= {self.config.reservation_cuttoff} minutes\n")

                index = routing.Start(0)
                route_distance = 0.0
                while not routing.IsEnd(index):
                    route_points.append(str(manager.IndexToNode(index)))
                    previous_index = index
                    index = solution.Value(routing.NextVar(index))
                    route_distance += routing.GetArcCostForVehicle(
                        previous_index, index, 0
                    )
                route_points.append(str(manager.IndexToNode(index)))
                route_time = route_distance / (self.shuttle_speed * SECONDS_PER_MINUTE)

                f.writelines(
                    [
                        "Route for Shuttle:\n",
                        " -> ".join(route_points) + "\n",
                        f"Route time: {route_time:.2f} minutes\n\n"
                        f"Elapsed time: {elapsed_time} seconds\n",
                    ]
                )
            except Exception:
                f.write("Failed to find solution\n")
                f.writelines(traceback.format_exc())

        self.draw_graph(route_points)

    def write_distance_matrix(self):
        distance_matrix_file = self.scenario_directory / "distance_matrix.out"
        with open(distance_matrix_file, "w+") as f:
            np.savetxt(f, self.service_region.stops_distance_matrix)

    def draw_graph(self, route_points: List):
        route_points_iterator = iter(route_points)
        prev_point = int(next(route_points_iterator))

        fixed_stop_color, inbound_color, outbound_color = (
            "#8DB1E2",
            "#C4D6A0",
            "#FFC000",
        )
        fixed_stop_size, trips_node_size = (3000, 500)

        nodes = [prev_point]
        next_nodes = []
        colors = [fixed_stop_color]
        sizes = [fixed_stop_size]
        positions = [tuple(self.service_region.fixed_stop)]

        for curr_point in route_points_iterator:
            curr_point = int(curr_point)
            if curr_point == 0:
                continue

            trip = self.trips[curr_point - 1]
            direction = trip.direction
            prev_point = curr_point

            nodes.append(curr_point)
            next_nodes.append(curr_point)
            colors.append(
                outbound_color if direction == TripDirection.OUTBOUND else inbound_color
            )
            sizes.append(trips_node_size)
            positions.append(trip.location)
        next_nodes.append(0)

        nodes_df = pd.DataFrame(
            {
                "NODES": nodes,
                "NEXT_NODES": next_nodes,
                "POSITIONS": positions,
                "COLORS": colors,
                "SIZES": sizes,
            }
        )

        dropped_trips = filter(
            lambda x: x.reservation_status == ReservationStatus.REJECTED, self.trips
        )
        for trip in dropped_trips:
            nodes_df.loc[-1] = [
                int(trip.id),
                np.nan,
                tuple(trip.location),
                outbound_color
                if direction == TripDirection.OUTBOUND
                else inbound_color,
                trips_node_size,
            ]
            nodes_df.index += 1

        # graph.draw(pd.concat([accepted_nodes_df, dropped_nodes_df]), self.scenario_directory)
        graph.draw(nodes_df, self.scenario_directory)

    def generate_trips(self):
        # Pick random stops from all other stops, excluding the fixed stop.
        # These will be used to generate a list of trips
        random_stops_index = np.random.choice(
            self.service_region.none_fixed_stops.shape[0],
            self.trips_density,
            replace=False,
        )
        for num, stop_index in enumerate(random_stops_index):
            reservation_time = np.random.randint(
                self.config.min_reservation_time, self.config.max_reservation_time
            )
            stop_position = tuple(self.service_region.none_fixed_stops[stop_index])

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
                location=stop_position,
            )
            self.trips.append(trip)

    def pick_routing_stops_distance_matrix(self, trips: List[Trip]):
        trip_location_indices = [trip.location_index for trip in trips]
        locations = [self.service_region.fixed_stop_index] + trip_location_indices
        rows = self.service_region.stops_distance_matrix[locations]
        return rows[:, locations].astype(int)
