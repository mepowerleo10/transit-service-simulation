#!/bin/bash

OUTPUT_DIR=./output
if [[ -d $OUTPUT_DIR ]]; then
  if [[ -f $OUTPUT_DIR/.success ]]; then
    mv $OUTPUT_DIR $OUTPUT_DIR-$(date +%F_%H:%M:%S)
  else
    rm -r $OUTPUT_DIR
  fi
fi

python ./src/main.py