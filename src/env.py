from pathlib import Path


SECONDS_PER_MINUTE = 60
RESERVATION_CUTOFF = 50
OUTPUT_DIR = Path("output")

NUMBER_OF_ZONES_PER_ROW = 10
ZONE_LENGTH = 2
ZONE_WIDTH = 0.5
LAMBDA_PARAM = 0.1
PLANNING_HORIZON = 0.7

NUM_OF_SIMULATIONS = 20
SHUTTLE_SPEED = (
    0.00556   # the shuttle moves with a constant speed of x units of distance/sec
)
