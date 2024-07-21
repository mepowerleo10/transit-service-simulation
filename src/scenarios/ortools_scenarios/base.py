from timeit import default_timer as timer
import traceback
from typing import List

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from models import Trip
from ..base import SECONDS_PER_MINUTE, BaseScenario


class GoogleORToolsScenario(BaseScenario):
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

    def write_route_results(
        self,
        solution: pywrapcp.SolutionCollector,
        routing,
        manager,
        elapsed_time: 0.0,
    ):
        route_points = []
        try:
            # f.write(f"Objective: {solution.ObjectiveValue()} s\n")
            objective = self.config.reservation_cuttoff

            index = routing.Start(0)
            route_distance = 0.0
            while not routing.IsEnd(index):
                route_points.append(str(manager.IndexToNode(index)))
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
            route_points.append(str(manager.IndexToNode(index)))
            route_time = route_distance / (self.shuttle_speed * SECONDS_PER_MINUTE)

            self.write_results(
                objective,
                route_points,
                route_time,
                elapsed_time,
            )
        except Exception:
            self.write_results(
                error_messages=["Failed to find solution\n", traceback.format_exc()]
            )

    def write_distance_matrix(self):
        distance_matrix_file = self.scenario_directory / "distance_matrix.out"
        with open(distance_matrix_file, "w+") as f:
            np.savetxt(f, self.service_region.stops_distance_matrix)

    def pick_routing_stops_distance_matrix(self, trips: List[Trip]):
        trip_location_indices = [trip.location_index for trip in trips]
        locations = [self.service_region.fixed_stop_index] + trip_location_indices
        rows = self.service_region.stops_distance_matrix[locations]
        return rows[:, locations].astype(int)
