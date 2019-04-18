#!/usr/bin/env bash

set -e

cd /ants/build
cmake /ants/code/ANTs-2.3.1
make
mv bin /usr/lib/ants
mv /ants/code/ANTs-2.3.1/Scripts/* /usr/lib/ants/