from multiprocessing import Pool
import os
from scenarios import AbstractScenario, ScenarioOne, ScenarioZero
import env
from tqdm.contrib.concurrent import process_map

def run_scenario(scenario: AbstractScenario):
    print(f"Running {scenario.scenario_name} ...")
    scenario.run()
    print(
        f"{scenario.scenario_name} Complete. Results stored at {scenario.scenario_directory.as_posix()}."
    )
    print(
        "----------------------------------------------------------------------------------\n"
    )


def main():
    generated_scenarios = [
        ScenarioZero(
            num_of_zones_per_row=env.NUMBER_OF_ZONES_PER_ROW,
            zone_length=env.ZONE_LENGTH,
            lambda_param=env.LAMBDA_PARAM,
            planning_horizon=env.PLANNING_HORIZON,
        )
        for i in range(env.NUM_OF_SIMULATIONS)
    ]

    # generated_scenarios = generated_scenarios + [
    #     ScenarioOne(
    #         num_of_zones_per_row=env.NUMBER_OF_ZONES_PER_ROW,
    #         zone_length=env.ZONE_LENGTH,
    #         lambda_param=env.LAMBDA_PARAM,
    #         planning_horizon=env.PLANNING_HORIZON,
    #     )
    #     for i in range(env.NUM_OF_SIMULATIONS)
    # ]

    process_map(
        run_scenario,
        generated_scenarios
    )

    # with Pool(os.cpu_count()) as p:
    #     p.map(run_scenario, generated_scenarios, 200)


if __name__ == "__main__":
    main()
