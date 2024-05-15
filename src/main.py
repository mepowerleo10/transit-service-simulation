import matplotlib.pyplot as plt
import pandas as pd

from scenarios import ScenarioZero


def main():
    scenario = ScenarioZero(
        num_of_zones_per_row=10, zone_length=10, lambda_param=0.5, planning_horizon=0.3
    )

    region = scenario.service_region

    for trip in scenario.trips:
        print(trip)

    plt.scatter(region.stops_coords[0], region.stops_coords[1], c="r", marker="o")
    plt.grid(True)

    df = pd.DataFrame(region.stops_distance_matrix)
    print(df)


if __name__ == "__main__":
    main()
