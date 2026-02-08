#!/bin/bash

# Exit on error
set -e

if [ "$(id -u)" -ne 0 ]; then
   echo "This script must be run as root"
   exit 1
fi

echo "Starting Debian Site Factory Setup..."

# 1. Install Dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y nginx python3 python3-pip python3-venv

# 2. Setup Directory Structure
echo "Setting up directories..."
# We assume the script is run from the repo root
REPO_DIR=$(pwd)
INSTALL_DIR="/opt/site-factory"
SITES_DIR="/var/www/sites"

mkdir -p "$SITES_DIR"
# Ensure www-data exists (installed by nginx) or use current user if testing
chown -R www-data:www-data "$SITES_DIR" || true
chmod -R 755 "$SITES_DIR"

# Copy application files
echo "Deploying application to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
# Copy manager directory
cp -r "$REPO_DIR/manager" "$INSTALL_DIR/"
# Ensure SITES_DIR in app.py points to /var/www/sites?
# Actually, the app.py uses `../sites` relative to itself.
# If app is in /opt/site-factory/manager, ../sites is /opt/site-factory/sites.
# But we want /var/www/sites.
# We should symlink /opt/site-factory/sites to /var/www/sites.
ln -sf "$SITES_DIR" "$INSTALL_DIR/sites"

# 3. Setup Python Environment
echo "Setting up Python virtual environment..."
cd "$INSTALL_DIR/manager"
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn

# 4. Configure Nginx
echo "Configuring Nginx..."
cp "$REPO_DIR/nginx/site-factory.conf" /etc/nginx/sites-available/site-factory
# Remove default if exists
rm -f /etc/nginx/sites-enabled/default
# Link new config
ln -sf /etc/nginx/sites-available/site-factory /etc/nginx/sites-enabled/

# Test Nginx config
nginx -t

# 5. Create Systemd Service
echo "Creating systemd service..."
cat > /etc/systemd/system/site-factory.service <<EOF
[Unit]
Description=Debian Site Factory Manager
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=$INSTALL_DIR/manager
Environment="PATH=$INSTALL_DIR/manager/venv/bin"
ExecStart=$INSTALL_DIR/manager/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
EOF

# 6. Start Services
echo "Starting services..."
systemctl daemon-reload
systemctl enable site-factory
systemctl restart site-factory
systemctl restart nginx

echo "Setup Complete!"
echo "Visit http://$(hostname -I | awk '{print $1}') to see the dashboard."
