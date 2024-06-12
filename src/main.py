from logging import getLogger
from scenarios import AbstractScenario, ScenarioAllBelowCuttof, ScenarioZero
import env
from tqdm.contrib.concurrent import process_map

logger = getLogger(__name__)


def run_scenario(scenario: AbstractScenario):
    try:
        print(f"Running {scenario.scenario_name} ...")
        scenario.run()
        print(
            f"{scenario.scenario_name} Complete. Results stored at {scenario.scenario_directory.as_posix()}."
        )
        print(
            "----------------------------------------------------------------------------------\n"
        )
    except Exception as e:
        logger.error(e)


def main():
    args = {
        "num_of_zones_per_row": env.NUMBER_OF_ZONES_PER_ROW,
        "zone_length": env.ZONE_LENGTH,
        "zone_width": env.ZONE_WIDTH,
        "lambda_param": env.LAMBDA_PARAM,
        "planning_horizon": env.PLANNING_HORIZON,
    }

    generated_scenarios = [ScenarioZero(**args) for i in range(env.NUM_OF_SIMULATIONS)]

    generated_scenarios += [
        ScenarioAllBelowCuttof(**args) for i in range(env.NUM_OF_SIMULATIONS)
    ]

    process_map(run_scenario, generated_scenarios)

    with open(env.OUTPUT_DIR / ".success", "w+") as f:
        f.write("")

    # with Pool(os.cpu_count()) as p:
    #     p.map(run_scenario, generated_scenarios, 200)


if __name__ == "__main__":
    main()
