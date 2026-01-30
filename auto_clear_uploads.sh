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

# 2. Check venv
if [ ! -f "$VENV_PATH/bin/uvicorn" ]; then
  echo "❌ venv not found or uvicorn not installed"
  exit 1
fi

# 3. Create systemd service
cat <<EOF > $SERVICE_FILE
[Unit]
Description=Mapsim Chat Uploads Auto-Cleaner
After=network.target

[Service]
ExecStart=/root/Mapsim_chat/venv/bin/python3 /root/Mapsim_chat/auto_clear_uploads.py
Restart=always
User=root
WorkingDirectory=/root/
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target

EOF

# 4. Reload systemd
systemctl daemon-reload

# 5. Enable & start service
systemctl enable $APP_NAME
systemctl restart $APP_NAME

echo "✅ Service installed and started successfully!"
echo "📌 Check status: systemctl status $APP_NAME"
