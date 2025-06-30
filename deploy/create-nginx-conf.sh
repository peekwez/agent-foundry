#!/bin/bash
set -e
base=agent-foundry.canadacentral.cloudapp.azure.com

function add_nginx_site {
    local site_name=$1
    local port=$2
    sudo tee /etc/nginx/sites-available/$site_name <<EOF
server {
   listen 80;
   server_name $site_name;
   location / {
       proxy_pass http://localhost:$port;
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
   }
}
EOF
sudo ln -s /etc/nginx/sites-available/$site_name /etc/nginx/sites-enabled/
}

add_nginx_site "docker.$base" 8888
add_nginx_site "store.$base" 9000
add_nginx_site "langfuse.$base" 3000
add_nginx_site "api.$base" 5000
add_nginx_site "mcp.$base" 8000
sudo systemctl restart nginx
