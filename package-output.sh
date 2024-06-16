#!/bin/bash

OUTPUTS_DIR=./outputs
for name in $@; do
  /usr/bin/tar -rvf outputs.tar $OUTPUTS_DIR/$name
done