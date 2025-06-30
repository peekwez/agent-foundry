#!/bin/bash
set -e
sudo systemctl stop docker-registry || true
sudo cp docker-registry.service /etc/systemd/system/docker-registry.service
sudo systemctl enable docker-registry
sudo systemctl start docker-registry
sudo systemctl status docker-registry
