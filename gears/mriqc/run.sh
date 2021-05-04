#!/usr/bin/env bash

# the Dockerfile creates docker-env.sh to preserve
# a lot of env vars that mriqc needs to run correctly
# source it here to make sure we have them set correctly
# before running our real script
source /flywheel/v0/docker-env.sh
python3 /flywheel/v0/run.py