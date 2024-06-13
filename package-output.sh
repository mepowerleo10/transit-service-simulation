#!/bin/bash

for PATH in $@; do
  /usr/bin/tar -rvf outputs.tar $PATH
done