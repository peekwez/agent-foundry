#!/bin/bash
set -e

/bin/bash -c install-docker.sh || true
/bin/bash -c start-docker-registry.sh || true
/bin/bash -c create-nginx-conf.sh || true
/bin/bash -c create-certbot-cert.sh || true
