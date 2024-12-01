#!/bin/bash

# Script to run and test on my MacBook development system

# RUN_ON_HOST:USING_PORT forms the URL where JavaScript posts are directed
export RUN_ON_HOST="192.168.1.20"
export USING_PORT="8080"

# mSec interval between updates to player browsers
export MINGO_UPDATE_INTERVAL="500"

export MINGO_DEBUG_MODE="True"

# Execute the code!
python mingo_web.py
