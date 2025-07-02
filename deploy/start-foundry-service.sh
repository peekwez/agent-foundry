#!/bin/bash
set -e
sudo systemctl stop agent-foundry || true
sudo cp agent-foundry.service /etc/systemd/system/agent-foundry.service
sudo systemctl enable agent-foundry
sudo systemctl start agent-foundry
sudo systemctl status agent-foundry
