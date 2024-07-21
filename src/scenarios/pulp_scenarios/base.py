import traceback
from timeit import default_timer as timer
from typing import List

import pulp
from models import ReservationStatus, Trip

from ..base import SECONDS_PER_MINUTE, BaseScenario


class PulpScenario(BaseScenario):
    def get_generated_route(self, trips: List[Trip]):
        starting_time = timer()

        locations = self.pick_routing_stops_locations(trips)
        no_of_locations = len(locations)
        distance_matrix = self.service_region.stops_distance_matrix

        problem = pulp.LpProblem("problem", pulp.LpMinimize)

        routes = [(i, j) for i in locations for j in locations]
        best_route = pulp.LpVariable.dicts(
            "best_route", (locations, locations), 0, 1, pulp.LpInteger
        )
        problem += (
            pulp.lpSum(best_route[i][j] * distance_matrix[i][j] for (i, j) in routes),
            "sum_of_distances_travelled",
        )

        # Constraits of the problem
        for i in locations:
            problem += (
                pulp.lpSum(best_route[j][i] for j in locations) == 1,
                f"sum_arrival_{i}",
            )

        for j in locations:
            problem += (
                pulp.lpSum(best_route[j][i] for i in locations) == 1,
                f"sum_departure_{j}",
            )

        problem += (
            pulp.lpSum(best_route[i][i] for i in locations) == 0,
            f"sum_{i,i}",
        )

        best_routes_flow = pulp.LpVariable.dicts(
            "flow", (locations, locations), 0, None, pulp.LpInteger
        )
        for i in locations:
            for j in locations:
                problem += (
                    best_routes_flow[i][j] <= (no_of_locations - 1) * best_route[i][j]
                )

        for k in locations[1:]:
            problem += (
                pulp.lpSum(
                    [best_routes_flow[i][k] - best_routes_flow[k][i] for i in locations]
                )
                == 1,
                f"flow_balance_{k}",
            )

        problem.writeLP(self.scenario_directory / "TSP.lp")
        problem.solve()

        print("Status: ", pulp.LpStatus[problem.status])
        for v in problem.variables():
            if v.varValue > 0:
                print(v.name, "=", v.varValue)

        print(f"Total distance = {pulp.value(problem.objective)}")

        ordered_route_points = []
        if pulp.LpStatus[problem.status] == "Optimal":
            route_points = [
                (i, j)
                for i in locations
                for j in locations
                if pulp.value(best_route[i][j]) == 1
            ]

            # Order the route
            ordered_route_points = [route_points[0][0]]
            next_point = route_points[0][1]
            while next_point != ordered_route_points[0]:
                ordered_route_points.append(next_point)
                for k in route_points:
                    if k[0] == next_point:
                        next_point = k[1]
                        break

            ordered_route_points.append(ordered_route_points[0])  # To complete the loop

        # Calculate the total distance traveled
        total_distance = sum(
            distance_matrix[i][j]
            for i, j in zip(ordered_route_points[:-1], ordered_route_points[1:])
        )
        objective_distance = pulp.value(problem.objective)
        elapsed_time = timer() - starting_time

        indexed_route_points = []
        loc_to_trip_id_mapping = dict(
            [(trip.location_index, trip.id) for trip in self.trips]
        )
        for point in ordered_route_points[1:-1]:
            indexed_route_points.append(str(loc_to_trip_id_mapping[point]))

        fixed_stop_index = "0"  # self.service_region.fixed_stop_index
        indexed_route_points.insert(0, str(fixed_stop_index))
        indexed_route_points.append(str(fixed_stop_index))

        for trip in self.trips:
            trip.reservation_status = ReservationStatus.ACCEPTED

        return {
            "objective": objective_distance / (self.shuttle_speed * SECONDS_PER_MINUTE),
            "route_points": indexed_route_points,
            "route_time": total_distance / (self.shuttle_speed * SECONDS_PER_MINUTE),
            "elapsed_time": elapsed_time,
        }

    def pick_routing_stops_locations(self, trips: List[Trip]):
        trip_location_indices = [trip.location_index for trip in trips]
        locations = [self.service_region.fixed_stop_index] + trip_location_indices

        return locations

    def init(self):
        self.trips_density = int(self.service_region.num_of_zones * self.lambda_param * self.planning_horizon)
        self.generate_trips()

    def run(self):
        try:
            self.write_results(**self.get_generated_route(self.trips))
        except Exception:
            self.write_results(error_messages=traceback.format_exc())

        self.write_generated_trips()
