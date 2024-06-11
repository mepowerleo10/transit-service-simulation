from pathlib import Path


SECONDS_PER_MINUTE = 60
RESERVATION_CUTOFF = 50
OUTPUT_DIR = Path("output")

NUMBER_OF_ZONES_PER_ROW = 10
ZONE_LENGTH = 1
LAMBDA_PARAM = 0.1
PLANNING_HORIZON = 0.7

NUM_OF_SIMULATIONS = 1_000
SHUTTLE_SPEED = (
    0.015  # the shuttle moves with a constant speed of x units of distance/sec
)
