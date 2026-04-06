#!/bin/bash
#
# Burgerreich-watch v3 — Self-hosted setup
# Works on: Raspberry Pi (arm64), Ubuntu/Debian laptop, any Linux
# Run as root: sudo bash deploy/setup-pi.sh
#
set -euo pipefail

APP_DIR="/opt/burgerreich"

# Auto-detect user: prefer $SUDO_USER, fallback to 'pi', then first non-root user
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    APP_USER="$SUDO_USER"
elif id -u pi &>/dev/null; then
    APP_USER="pi"
else
    APP_USER=$(awk -F: '$3 >= 1000 && $3 < 65534 {print $1; exit}' /etc/passwd)
fi

echo "=== Burgerreich-watch v3 — Setup ==="
echo "    User: $APP_USER"
echo "    Dir:  $APP_DIR"
echo ""

# 1. Install system deps
echo "[1/6] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx > /dev/null

# 2. Copy project
echo "[2/6] Setting up project directory..."
mkdir -p "$APP_DIR"
rsync -a --exclude='.git' --exclude='venv' --exclude='__pycache__' . "$APP_DIR/"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# 3. Python venv + deps
echo "[3/6] Creating Python venv and installing deps..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/collectors/requirements.txt"

# 4. Nginx
echo "[4/6] Configuring nginx..."
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/burgerreich
ln -sf /etc/nginx/sites-available/burgerreich /etc/nginx/sites-enabled/burgerreich
rm -f /etc/nginx/sites-enabled/default
nginx -t 2>/dev/null && systemctl restart nginx

# 5. Systemd timer (update service with correct user)
echo "[5/6] Installing systemd timer (every 15 min)..."
sed "s/User=pi/User=$APP_USER/" "$APP_DIR/deploy/burgerreich-collect.service" > /etc/systemd/system/burgerreich-collect.service
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
echo "Dashboard:    http://${IP}"
echo "Logs:         tail -f /var/log/burgerreich.log"
echo "Timer:        systemctl status burgerreich-collect.timer"
echo "Manual run:   cd $APP_DIR && ./venv/bin/python run_all.py"
echo ""
echo "To change collection interval (e.g. every 5 minutes):"
echo "  sudo systemctl edit burgerreich-collect.timer"
echo "  Add: [Timer]"
echo "       OnUnitActiveSec=5min"
echo ""
