from scenarios import ScenarioZero
import env


def main():
    for i in range(env.NUM_OF_SIMULATIONS):
        scenario = ScenarioZero(
            num_of_zones_per_row=env.NUMBER_OF_ZONES_PER_ROW,
            zone_length=env.ZONE_LENGTH,
            lambda_param=env.LAMBDA_PARAM,
            planning_horizon=env.PLANNING_HORIZON,
        )

        print(f"Running {scenario.scenario_name} ...")
        scenario.run()
        print(
            f"{scenario.scenario_name} Complete. Results stored at {scenario.scenario_directory.as_posix()}."
        )
        print(
            "----------------------------------------------------------------------------------\n"
        )


if __name__ == "__main__":
    main()
