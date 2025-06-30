#!/bin/bash
set -e
base=agent-foundry.canadacentral.cloudapp.azure.com

sudo certbot --nginx \
    -d "docker.$base" \
    -d "mcp.$base" \
    -d "store.$base" \
    -d "api.$base" \
    -d "langfuse.$base" \
    --non-interactive \
    --agree-tos --email kwesi.p.apponsah@pwc.com
