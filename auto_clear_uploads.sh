#!/bin/bash

APP_NAME="mapsim-auto-clear-uploads"
APP_DIR="/root/Mapsim_chat"
VENV_PATH="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

echo "🚀 Setting up $APP_NAME service..."

# 1. Root check
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root"
  exit 1
fi

# 2. Python check
if [ ! -x "$VENV_PATH/bin/python3" ]; then
  echo "❌ Python not found in venv"
  echo "Expected: $VENV_PATH/bin/python3"
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
EnvironmentFile=$APP_DIR/.env
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

# 5. Enable & start
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

echo "✅ Auto-clean service installed and started"
echo "📌 Logs: journalctl -u $APP_NAME -f"
