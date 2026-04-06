#!/bin/bash
#
# Burgerreich-watch v3 — Pi4 bare-metal setup
# Run as root: sudo bash deploy/setup-pi.sh
#
set -euo pipefail

APP_DIR="/opt/burgerreich"
APP_USER="pi"

echo "=== Burgerreich-watch v3 — Pi4 Setup ==="

# 1. Install system deps
echo "[1/6] Installing system packages..."
apt-get update
apt-get install -y python3 python3-venv python3-pip nginx

# 2. Copy project
echo "[2/6] Setting up project directory..."
mkdir -p "$APP_DIR"
cp -r . "$APP_DIR/"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# 3. Python venv + deps
echo "[3/6] Creating Python venv and installing deps..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/collectors/requirements.txt"

# 4. Nginx
echo "[4/6] Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/burgerreich
ln -sf /etc/nginx/sites-available/burgerreich /etc/nginx/sites-enabled/burgerreich
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# 5. Systemd timer
echo "[5/6] Installing systemd timer..."
cp "$APP_DIR/deploy/burgerreich-collect.service" /etc/systemd/system/
cp "$APP_DIR/deploy/burgerreich-collect.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now burgerreich-collect.timer

# 6. Initial run
echo "[6/6] Running initial collection..."
touch /var/log/burgerreich.log
chown "$APP_USER:$APP_USER" /var/log/burgerreich.log
sudo -u "$APP_USER" bash -c "cd $APP_DIR && ./venv/bin/python run_all.py"

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=== DONE ==="
echo "Dashboard:  http://${IP}"
echo "Logs:       tail -f /var/log/burgerreich.log"
echo "Timer:      systemctl status burgerreich-collect.timer"
echo "Manual run: cd $APP_DIR && ./venv/bin/python run_all.py"
echo ""
