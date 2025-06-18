#!/bin/bash
set -e

BLACKBOARD_REPOSITORY=$HOME/Desktop/projects/mcp-blackboard
FOUNDRY_REPOSITRY=$HOME/Desktop/projects/agent-foundry

function link_local_data() {
    cd $BLACKBOARD_REPOSITORY && make link-data
    cd $FOUNDRY_REPOSITRY && make link-data
}


function start_blackboard() {
    cd $BLACKBOARD_REPOSITORY && make down || true
    cd $FOUNDRY_REPOSITRY && make up || true
}

function run_setup() {
    link_local_data
    sleep 5
    start_blackboard
    sleep 5

}

function run_task() {
    cd $AGENT_REPOSITORY && make task-run \
        TASK_FILE=$PWD/samples/mortgage/_task.yaml \
        ENV_FILE=$PWD/.env.azure
}

run_setup
