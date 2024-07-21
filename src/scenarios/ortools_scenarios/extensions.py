from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from models import ReservationStatus
from . import GoogleORToolsScenario


class ScenarioZero(GoogleORToolsScenario):
    """
    Scenario 0: no short notice riders are accepted
    """

    def init(self):
        super().init()
        self.trips_density = int(
            self.service_region.num_of_zones * self.lambda_param * self.planning_horizon
        )
        self.generate_trips()

    def run(self):
        """trips_within_time = [
            trip for trip in self.trips if trip.reserved_at <= RESERVATION_CUTOFF
        ]  # ignore all trips above the cutoff time"""

        trips_within_time = {}
        for index, trip in enumerate(self.trips):
            if trip.reserved_at < self.config.reservation_cuttoff:
                trips_within_time[index] = trip

        manager, routing, solution, elapsed_time = self.get_generated_route(
            list(trips_within_time.values())
        )
        dropped_nodes = self.get_dropped_nodes(routing, manager, solution)

        if solution:
            for index, trip in enumerate(self.trips):
                status = ReservationStatus.REJECTED
                if (
                    index in list(trips_within_time.keys())
                    and index + 1
                    not in dropped_nodes  # dropped nodes contains the fixed_stop, offset the index by one forward
                ):
                    status = ReservationStatus.ACCEPTED

                trip.reservation_status = status

        self.write_generated_trips()
        self.write_route_results(solution, routing, manager, elapsed_time)
        # self.write_distance_matrix()


class ScenarioAllBelowCutoff(ScenarioZero):
    """Accepts all scenarios below zero"""

    def init(self):
        super().init()
        self.search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        self.search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        self.search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        self.search_parameters.time_limit.seconds = 5
        self.search_parameters.log_search = False
        self.search_parameters.use_full_propagation = False

    def run(self):
        self.max_distance = 1_000_000_000
        self.allow_dropping = False
        super().run()


class ScenarioOne(GoogleORToolsScenario):
    """
    Scenario 1: Short notice riders are considered
    """

    def init(self):
        self.trips_density = int(
            self.service_region.num_of_zones * self.lambda_param * self.planning_horizon
        )
        self.generate_trips()

    def run(self):
        all_trips_generated = dict(
            [(index, trip) for index, trip in enumerate(self.trips)]
        )

        manager, routing, solution, elapsed_time = self.get_generated_route(
            list(all_trips_generated.values())
        )
        dropped_nodes = self.get_dropped_nodes(routing, manager, solution)

        if solution:
            for index, trip in enumerate(self.trips):
                status = ReservationStatus.REJECTED
                if (
                    index + 1 not in dropped_nodes
                ):  # dropped nodes contain the fixed_stop, offset the index by one forward
                    status = ReservationStatus.ACCEPTED

                trip.reservation_status = status

        self.write_generated_trips()
        self.write_route_results(solution, routing, manager, elapsed_time)
        # self.write_distance_matrix()
