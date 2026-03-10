#!/bin/bash

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
   echo "This script must be run as root"
   exit 1
fi

echo "Starting Debian Site Factory setup..."

REPO_DIR=$(pwd)
INSTALL_DIR="/opt/site-factory"
SITES_DIR="/var/www/sites"
SERVICE_USER="www-data"
SERVICE_GROUP="www-data"
APP_ENV_FILE="/etc/site-factory.env"

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  echo "Expected service user '$SERVICE_USER' to exist after nginx installation."
  exit 1
fi

echo "Installing system dependencies..."
apt-get update
apt-get install -y nginx python3 python3-pip python3-venv

echo "Setting up directories..."
mkdir -p "$INSTALL_DIR" "$SITES_DIR"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$SITES_DIR"
chmod -R 755 "$SITES_DIR"

echo "Deploying application to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR/manager"
cp -r "$REPO_DIR/manager" "$INSTALL_DIR/"
cp "$REPO_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"
ln -sfn "$SITES_DIR" "$INSTALL_DIR/sites"
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

echo "Setting up Python virtual environment..."
cd "$INSTALL_DIR/manager"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"

echo "Writing environment file..."
SECRET_KEY=$(python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)
cat > "$APP_ENV_FILE" <<EOF
SITE_FACTORY_SECRET_KEY=$SECRET_KEY
SITE_FACTORY_SITES_DIR=$SITES_DIR
EOF
chmod 640 "$APP_ENV_FILE"
chown root:"$SERVICE_GROUP" "$APP_ENV_FILE"

echo "Configuring Nginx..."
cp "$REPO_DIR/nginx/site-factory.conf" /etc/nginx/sites-available/site-factory
rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/site-factory /etc/nginx/sites-enabled/site-factory
nginx -t

echo "Creating systemd service..."
cat > /etc/systemd/system/site-factory.service <<EOF
[Unit]
Description=Debian Site Factory Manager
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$INSTALL_DIR/manager
EnvironmentFile=$APP_ENV_FILE
Environment="PATH=$INSTALL_DIR/manager/venv/bin"
ExecStart=$INSTALL_DIR/manager/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Starting services..."
systemctl daemon-reload
systemctl enable site-factory
systemctl restart site-factory
systemctl restart nginx

echo "Setup complete."
echo "Visit http://$(hostname -I | awk '{print $1}') to see the dashboard."