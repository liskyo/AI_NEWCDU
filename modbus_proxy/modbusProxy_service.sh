#!/bin/bash

# Define the base directory relative to the location of this script
TARGET_DIR=/home/user/service/modbus_proxy
SERVICE_NAME="modbusProxy.service"
VENV_PATH="$TARGET_DIR/venv"
SCRIPT_PATH="$TARGET_DIR/proxyServer.py"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_NAME"

# Change to the target directory
cd "$TARGET_DIR" || { echo "Failed to change directory to $TARGET_DIR"; exit 1; }

sudo apt install python3.10-venv

python3 -m venv $VENV_PATH

source $VENV_PATH/bin/activate

pip install -r requirements.txt

cat <<EOL | sudo tee $SYSTEMD_PATH
[Unit]
Description=ModbusProxy Service
After=network.target

[Service]
User=user
Group=user
WorkingDirectory=$TARGET_DIR
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/python3 $SCRIPT_PATH

# Restart options
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 設定檔案權限
sudo chmod 644 $SYSTEMD_PATH

# 重新載入 systemd 管理設定檔
sudo systemctl daemon-reload

# 啟動 service
sudo systemctl start $SERVICE_NAME

# 設定 service 開機自動啟動
sudo systemctl enable $SERVICE_NAME

# 顯示 service 狀態
sudo systemctl status $SERVICE_NAME

# 退出 virtual environment
deactivate
