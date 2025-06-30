#!/bin/bash
set -e
base=agent-foundry.canadacentral.cloudapp.azure.com
config_file="/etc/nginx/sites-available/$base"

sudo tee "$config_file" > /dev/null <<EOF
server {
   listen 80;
   server_name $base;
   return 301 https://\$host\$request_uri;
}

server {
   listen 443 ssl;
   server_name $base;

    ssl_certificate /etc/letsencrypt/live/$base/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$base/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location /docker/ {
        proxy_pass http://localhost:8888/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /store/ {
        proxy_pass http://localhost:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /langfuse/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /mcp/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -s "$config_file" /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
