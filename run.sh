#!/bin/bash

OUTPUT_DIR=./output
function cleanup() {
  if [[ -d $OUTPUT_DIR ]]; then
    if [[ -f $OUTPUT_DIR/.success ]]; then
      mv $OUTPUT_DIR $OUTPUT_DIR-$(cat $OUTPUT_DIR/.run_at)
    else
      rm -r $OUTPUT_DIR
    fi
  fi

  mkdir $OUTPUT_DIR
  date +%F_%H:%M:%S >$OUTPUT_DIR/.run_at
}

cleanup && python ./src/main.py
