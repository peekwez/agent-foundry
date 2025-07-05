#!/bin/bash
set -e

/bin/sh -c ./install-packages.sh
/bin/sh -c ./start-docker-registry.sh
/bin/sh -c ./create-certbot-cert.sh
/bin/sh -c ./create-nginx-conf.sh
/bin/sh -c ./create-nginx-conf-apps.sh
