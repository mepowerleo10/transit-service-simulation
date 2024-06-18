from dataclasses import dataclass
import datetime
from enum import Enum
from math import floor
from pathlib import Path
from typing import Type

import numpy as np
from scipy.spatial import distance_matrix


@dataclass
class Config:
    scenario: Type
    reservation_cuttoff: int
    output_dir: Path
    number_of_zones_per_row: int
    zone_length: int
    zone_width: int
    lambda_param: float
    planning_horizon: float
    number_of_simulations: int
    shuttle_speed: float
    min_reservation_time: int
    max_reservation_time: int


class TripDirection(Enum):
    INBOUND = 1
    OUTBOUND = 2


class ReservationStatus(Enum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2

    def __str__(self) -> str:
        return self.name


@dataclass
class Trip:
    id: int
    reserved_at: datetime.datetime
    direction: TripDirection
    location_index: int
    reservation_status = ReservationStatus.PENDING

    def __str__(self) -> str:
        return f"""
        id: {self.id}, direction: {self.direction.name}, location_index: {self.location_index}, reserved_at: {self.reserved_at}, reservation_status: {self.reservation_status.name}
        """

    def as_csv_line(self) -> str:
        return f"""{self.id}, {self.direction.name}, {self.location_index}, {self.reserved_at}, {self.reservation_status.name}"""


class ServiceRegion:
    def __init__(
        self, num_of_zones_per_row: int, zone_length: float, zone_width: float
    ) -> None:
        self.num_of_zones_per_row = num_of_zones_per_row
        self.zone_length = zone_length
        self.zone_width = zone_width

        self.stops_coords: np.ndarray = None
        self.stops_grid: np.ndarray = None
        self.stops_distance_matrix: np.ndarray = None

        self.build_stops_grid()
        self.generate_distance_matrix()

        # Set a random fixed stop in the service region
        # 1. Get the number of rows in the array
        # 2. Pick a random row index
        num_rows = self.stops_grid.shape[0]
        self.fixed_stop_index = np.random.choice(num_rows)
        self.fixed_stop: np.ndarray = self.stops_grid[self.fixed_stop_index]

        # Pick all other stops ignoring the fixed stop as none_fixed_stops
        mask = ~np.all(self.stops_grid == self.fixed_stop, axis=1)
        self.none_fixed_stops = self.stops_grid[mask]

    @property
    def num_of_zones(self):
        return self.num_of_zones_per_row * self.num_of_zones_per_row

    @property
    def zone_size(self):
        return self.zone_length * self.zone_width

    @property
    def grid_size(self):
        return self.num_of_zones * self.zone_size

    def build_stops_grid(self):
        x = self.generate_points(self.zone_length)
        y = self.generate_points(self.zone_width)

        # Create a grid of coordinates
        X, Y = np.meshgrid(x, y, indexing="xy")
        x_coords = X.flatten()
        y_coords = Y.flatten()

        self.stops_coords = (x_coords, y_coords)
        self.stops_grid = np.column_stack(self.stops_coords)

    def generate_points(self, zone_size: float):
        return np.arange(self.num_of_zones_per_row) * zone_size + zone_size / 2

    def generate_distance_matrix(self):
        self.stops_distance_matrix = distance_matrix(self.stops_grid, self.stops_grid)
