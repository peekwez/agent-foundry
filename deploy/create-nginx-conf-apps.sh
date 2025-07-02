#!/bin/bash
set -e

# ----- CONFIG -----
DOMAIN="agent-foundry.canadacentral.cloudapp.azure.com"
LE_PATH="/etc/letsencrypt/live/$DOMAIN"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"

# Define apps as (name external_port internal_port)
APPS=(
 "langfuse 10443 3000"
 "store 11443 9093"
 "mcp 12443 8000"
 "api 13443 5000"
)

# ----- FUNCTION -----
generate_server_block() {
    local NAME="$1"
    local EXTERNAL_PORT="$2"
    local INTERNAL_PORT="$3"
    local CONFIG_FILE="$NGINX_SITES_AVAILABLE/$NAME"
    echo "Creating NGINX config for $NAME (public: $EXTERNAL_PORT → local: $INTERNAL_PORT)"

    # Start with basic configuration
    sudo tee "$CONFIG_FILE" > /dev/null <<EOF
server {
   listen $EXTERNAL_PORT ssl;
   server_name $DOMAIN;
   ssl_certificate $LE_PATH/fullchain.pem;
   ssl_certificate_key $LE_PATH/privkey.pem;
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_prefer_server_ciphers on;
   location / {
       proxy_pass http://localhost:$INTERNAL_PORT;
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
   }
EOF

    # Add WebSocket support for the API server only
    if [ "$NAME" == "api" ]; then
        sudo tee -a "$CONFIG_FILE" > /dev/null <<EOF
   location /ws/run-task/updates {
       proxy_pass http://localhost:$INTERNAL_PORT/ws/run-task/updates;
       proxy_http_version 1.1;
       proxy_set_header Upgrade \$http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
   }
EOF
    fi

    # Close the server block
    sudo tee -a "$CONFIG_FILE" > /dev/null <<EOF
}
EOF

    # Enable the site
    sudo unlink "$NGINX_SITES_ENABLED/$NAME" || true
    sudo ln -sf "$CONFIG_FILE" "$NGINX_SITES_ENABLED/$NAME"
}

# ----- MAIN -----
echo "🔧 Generating NGINX server blocks for domain: $DOMAIN"
for app in "${APPS[@]}"; do
 read NAME EXTERNAL_PORT INTERNAL_PORT <<< "$app"
 generate_server_block "$NAME" "$EXTERNAL_PORT" "$INTERNAL_PORT"
done
echo "✅ All server configs generated."
echo "🔎 Testing NGINX configuration..."
sudo nginx -t
echo "🔄 Reloading NGINX..."
sudo systemctl reload nginx
echo "🎉 Done! NGINX reloaded with new HTTPS server blocks."
