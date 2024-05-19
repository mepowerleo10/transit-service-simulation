import matplotlib.pyplot as plt
import pandas as pd

from scenarios import ScenarioZero


def main():
    scenario = ScenarioZero(
        num_of_zones_per_row=10, zone_length=10, lambda_param=0.5, planning_horizon=0.3
    )

    # scenario.run()
    # scenario.print()


if __name__ == "__main__":
    main()
