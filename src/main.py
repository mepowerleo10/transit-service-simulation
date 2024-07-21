from logging import getLogger
from pathlib import Path
from scenarios import (
    BaseScenario,
    ScenarioAllBelowCutoff,
    ScenarioOne,
    ScenarioZero,
    PulpScenario,
)
from tqdm.contrib.concurrent import process_map
from dotenv import dotenv_values

from models import Config

logger = getLogger(__name__)

scenarios_registry = {
    "Zero": ScenarioZero,
    "One": ScenarioOne,
    "AllBelowCutoff": ScenarioAllBelowCutoff,
    "Pulp": PulpScenario,
}


def read_env(env_file: Path):
    """Reads the environment file and returns a configuration object"""
    env = dotenv_values(env_file.as_posix())

    def value(key, type=None, default_value=None):
        return (
            type(env.get(key, default_value)) if type else env.get(key, default_value)
        )

    config = Config(
        scenario=scenarios_registry[value("SCENARIO")],
        reservation_cuttoff=value("RESERVATION_CUTOFF", int),
        output_dir=value("OUTPUT_DIR", Path),
        number_of_zones_per_row=value("NUMBER_OF_ZONES_PER_ROW", int),
        zone_length=value("ZONE_LENGTH", float),
        zone_width=value("ZONE_WIDTH", float),
        lambda_param=value("LAMBDA_PARAM", float),
        planning_horizon=value("PLANNING_HORIZON", float),
        number_of_simulations=value("NUM_OF_SIMULATIONS", int),
        shuttle_speed=value("SHUTTLE_SPEED", float),
        min_reservation_time=value("MIN_RESERVATION_TIME", int, 0),
        max_reservation_time=value("MAX_RESERVATION_TIME", int, 60),
    )

    return config


def run_scenario(scenario: BaseScenario):
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
    config = read_env(Path(".env"))

    args = {"config": config}

    generated_scenarios = [
        config.scenario(**args) for i in range(config.number_of_simulations)
    ]

    process_map(run_scenario, generated_scenarios)
    # run_scenario(generated_scenarios[0])

    with open(config.output_dir / ".success", "w+") as f:
        f.write("")

    # with Pool(os.cpu_count()) as p:
    #     p.map(run_scenario, generated_scenarios, 200)


if __name__ == "__main__":
    main()
