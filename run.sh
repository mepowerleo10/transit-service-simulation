#!/bin/bash

OUTPUTS_DIR=./outputs
CURRENT_OUTPUT_DIR=$OUTPUTS_DIR/current
QUEUES_DIR=./queues
ACTIVE_QUEUE_DIR=$QUEUES_DIR/active
RUN_AT=$(date +%F_%H:%M:%S)

function cleanup() {
  if [[ -d $CURRENT_OUTPUT_DIR ]]; then
    if [[ -f $CURRENT_OUTPUT_DIR/.success ]]; then
      mv $CURRENT_OUTPUT_DIR $OUTPUTS_DIR/$(cat $CURRENT_OUTPUT_DIR/.run_at)
    else
      rm -r $CURRENT_OUTPUT_DIR
    fi
  fi

  mkdir $CURRENT_OUTPUT_DIR
  date +%F_%H:%M:%S >$CURRENT_OUTPUT_DIR/.run_at
}

if [[ ! -d $ACTIVE_QUEUE_DIR ]]; then
  echo "$ACTIVE_QUEUE_DIR directory not found, create it and add your environment file(s). exiting ..."
  exit 1
fi

for env_file in "$ACTIVE_QUEUE_DIR"/*.conf; do
  cp $env_file .env
  cleanup && cp .env $CURRENT_OUTPUT_DIR/.conf && python ./src/main.py
  rm .env
done

if [[ $? -eq 0 ]]; then
  cp -r $ACTIVE_QUEUE_DIR $QUEUES_DIR/$RUN_AT
  mkdir -p $ACTIVE_QUEUE_DIR
fi
