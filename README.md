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
- Copy `env.dist` into your active queues directory make as many copies as possible for all different parameters you want to try. i.e.:
  `cp env.dist ./queues/active/simple.env`
- Run the simulation:
  `./run.sh`

## Packaging the Results
- `./package-output.sh [FOLDER NAMES ...]`
