#!/bin/bash
set -e

base=agent-foundry.canadacentral.cloudapp.azure.com
config_file="/etc/nginx/sites-available/$base"

sudo unlink "/etc/nginx/sites-enabled/$base"|| true
sudo tee "$config_file" > /dev/null <<'EOF'
server {
    listen 80;
    server_name agent-foundry.canadacentral.cloudapp.azure.com;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name agent-foundry.canadacentral.cloudapp.azure.com;

    ssl_certificate /etc/letsencrypt/live/agent-foundry.canadacentral.cloudapp.azure.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agent-foundry.canadacentral.cloudapp.azure.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

}
EOF

sudo ln -s "$config_file" /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
