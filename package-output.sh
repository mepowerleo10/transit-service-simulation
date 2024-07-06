#!/bin/bash

OUTPUTS_DIR=./outputs
COMPRESSED_DIR=./outputs-compressed
mkdir $COMPRESSED_DIR
for name in $@; do
  /usr/bin/tar -cJvf $COMPRESSED_DIR/$name.xz $OUTPUTS_DIR/$name
done

/usr/bin/tar -rvf $COMPRESSED_DIR.tar $COMPRESSED_DIR