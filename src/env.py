from pathlib import Path


SECONDS_PER_MINUTE = 60
RESERVATION_CUTOFF = 50
OUTPUT_DIR = Path("output")

NUMBER_OF_ZONES_PER_ROW = 10
ZONE_LENGTH = 10
LAMBDA_PARAM = 0.5
PLANNING_HORIZON = 0.9

NUM_OF_SIMULATIONS = 10_000
SHUTTLE_SPEED = (
    0.20  # the shuttle moves with a constant speed of x units of distance/sec
)
