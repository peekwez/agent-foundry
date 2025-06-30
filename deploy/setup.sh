#!/bin/bash
set -e

/bin/sh -c ./install-docker.sh
/bin/sh -c ./start-docker-registry.sh
/bin/sh -c ./create-certbot-cert.sh
/bin/sh -c ./create-nginx-conf.sh
