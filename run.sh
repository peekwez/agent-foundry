#!/bin/bash
set -e
make task-run \
    TASK_FILE=$PWD/samples/mortgage/_task-new.yaml \
    ENV_FILE=$PWD/.env.agent
