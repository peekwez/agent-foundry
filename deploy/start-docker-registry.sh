#!/bin/bash
set -e
sudo cp docker-registry.service /etc/systemd/system/docker-registry.service
sudo systemctl enable docker-registry
sudo systemctl start docker-registry
