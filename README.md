# Sandbox For Evaluating and Designing Semi-Flex Transit Services

Simulating a Semi-Flex Transit service

## Requirements
- Python 3.12+
- Bash 5+

## Running
- If you don't have a virtual environment create one:
  `python -m venv .venv`
- Activate the virtual environment:
  `source .venv/bin/activate`
- Create an active queue folder if it does not exist:
  `mkdir -p ./queues/active`
- Copy `sample.conf` into your active queues directory make as many copies as possible for all different parameters you want to try. i.e.:
  `cat sample.conf > ./queues/active/{first,second,third}.conf`
- Run the simulation:
  `./run.sh`

## Scenarios for the Environment Configuration file
| Key            | Scenario                | Description                                                 |
| -------------- | ----------------------- | ----------------------------------------------------------- |
| Zero           | ScenarioZero            | Scenario 0: no short-notice riders are accepted             |
| One            | ScenarioOne             | Scenario 1: short-notice riders are considered case by case |
| AllBelowCutoff | ScenarioAllBelowCuttoff | All Trips below the Cutoff are automatically accepted       |



## Packaging the **Results**
- `./package-output.sh [FOLDER NAMES ...]`
