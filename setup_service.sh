#!/bin/bash
set -e

APP_NAME="Mapsim_chat"
APP_DIR="/root/Mapsim_chat"   # مسیر پروژه روی VPS
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
Description=Mapsim Chat FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=$VENV_PATH/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
StandardOutput=journal
StandardError=journal

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
