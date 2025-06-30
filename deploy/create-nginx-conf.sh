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

    location /store/ {
        proxy_pass http://localhost:9092/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /langfuse/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /mcp/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s "$config_file" /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
