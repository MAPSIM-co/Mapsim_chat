#!/bin/bash
set -e

APP_NAME="Mapsim_chat_auto_clear_uploads"
APP_DIR="/root/Mapsim_chat"
VENV_PATH="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

echo "🚀 Setting up $APP_NAME service..."

# 1. Check root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root"
  exit 1
fi

# 2. Check python in venv
if [ ! -x "$VENV_PATH/bin/python3" ]; then
  echo "❌ python3 not found in venv"
  exit 1
fi

echo "✅ venv python detected"

# 3. Create systemd service
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Mapsim Chat Uploads Auto-Cleaner
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$VENV_PATH/bin/python3 $APP_DIR/auto_clear_uploads.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 4. Reload systemd
systemctl daemon-reload

# 5. Enable & start service
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

echo "✅ Auto-clean service installed and started!"
echo "📌 Check logs: journalctl -u $APP_NAME -f"
