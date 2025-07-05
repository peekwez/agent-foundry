#!/bin/bash
set -e
base=agent-foundry.canadacentral.cloudapp.azure.com

sudo certbot --nginx \
    -d "$base" \
    --non-interactive \
    --agree-tos --email kwesi.p.apponsah@pwc.com
sudo certbot renew --dry-run
