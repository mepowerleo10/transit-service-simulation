import datetime
from enum import Enum
from typing import List

import numpy as np
from scipy.spatial import distance_matrix


class Stop:
    def __init__(self, x: float, y: float, fixed=False) -> None:
        self.x = x
        self.y = y
        self.fixed = fixed


class TripDirection(Enum):
    INBOUND = 1
    OUTBOUND = 2


class ReservationStatus(Enum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2


class Trip:
    def __init__(
        self,
        reserved_at: datetime.datetime,
        direction: TripDirection,
        reservation_status=ReservationStatus.PENDING,
    ) -> None:
        self.reserved_at = reserved_at
        self.direction = direction
        self.reservation_status = reservation_status


class ServiceRegion:
    def __init__(self, num_of_zones_per_row: int, zone_length: float) -> None:
        self.num_of_zones_per_row = num_of_zones_per_row
        self.zone_length = zone_length

        self.stops_coords: np.ndarray = None
        self.stops_grid: np.ndarray = None
        self.stops_distance_matrix: np.ndarray = None

        self.build_stops_grid()
        self.generate_distance_matrix()

    @property
    def num_of_zones(self):
        return self.num_of_zones_per_row * self.num_of_zones_per_row

    @property
    def zone_size(self):
        return self.zone_length * self.zone_length

    @property
    def grid_size(self):
        return self.num_of_zones * self.zone_size

    def build_stops_grid(self):
        x = self.generate_points()
        y = self.generate_points()

        # Create a grid of coordinates
        X, Y = np.meshgrid(x, y, indexing="xy")
        x_coords = X.flatten()
        y_coords = Y.flatten()

        self.stops_coords = (x_coords, y_coords)
        self.stops_grid = np.column_stack((x_coords, y_coords))

    def generate_points(self):
        return (
            np.arange(self.num_of_zones_per_row) * self.zone_length
            + self.zone_length / 2
        )

    def generate_distance_matrix(self):
        self.stops_distance_matrix = distance_matrix(self.stops_grid, self.stops_grid)
