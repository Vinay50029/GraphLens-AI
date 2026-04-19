#!/bin/bash

# ==============================================================================
# Intelligent Research Assistant - EC2 Setup Script
# This script automates the installation of dependencies, Nginx, and Gunicorn
# for the Django backend on an Ubuntu 22.04 LTS instance.
# ==============================================================================

# Exit on error
set -e

echo "🚀 Starting setup for Intelligent Research Assistant Backend..."

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python, Pip, Nginx, and Git
sudo apt install -y python3-pip python3-venv nginx git

# 3. Create Project Directory (if not already in it)
# Assuming you cloned into ~/intelligent-research-assistant
PROJECT_ROOT="$HOME/intelligent-research-assistant"
BACKEND_DIR="$PROJECT_ROOT/research-assistant/backend"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Error: Project directory $PROJECT_ROOT not found."
    echo "Please clone your repository to $PROJECT_ROOT before running this script."
    exit 1
fi

cd "$BACKEND_DIR"

# 4. Set up Virtual Environment
echo "📦 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 5. Configure Gunicorn Systemd Service
echo "⚙️ Configuring Gunicorn service..."
GUNICORN_SERVICE="/etc/systemd/system/django.service"

sudo bash -c "cat > $GUNICORN_SERVICE" <<EOF
[Unit]
Description=Gunicorn instance to serve Intelligent Research Assistant Backend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:django.sock \
    core.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

# 6. Start Gunicorn
sudo systemctl start django
sudo systemctl enable django

# 7. Configure Nginx
echo "🌐 Configuring Nginx..."
NGINX_CONF="/etc/nginx/sites-available/django"

sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name _; # Change this to your domain later

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root $BACKEND_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$BACKEND_DIR/django.sock;
    }
}
EOF

# Enable Nginx site
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 8. Permissions
sudo chown -R ubuntu:www-data "$BACKEND_DIR"
sudo chmod -R 775 "$BACKEND_DIR"

echo "✅ Setup complete!"
echo "Next steps:"
echo "1. Create your .env file in $BACKEND_DIR"
echo "2. Run 'sudo systemctl restart django' after creating .env"
echo "3. (Optional) Run 'sudo certbot --nginx' for SSL if you have a domain."
