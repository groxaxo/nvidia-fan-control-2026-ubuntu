#!/usr/bin/env bash
set -euo pipefail

cp ./nvidia-fan-control.py /usr/local/bin/nvidia-fan-control.py
chmod +x /usr/local/bin/nvidia-fan-control.py

cat > /etc/systemd/system/nvidia-fan-control.service <<'SERVICE'
[Unit]
Description=NVIDIA GPU Dynamic Fan Control
After=nvidia-persistenced.service
Wants=nvidia-persistenced.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /usr/local/bin/nvidia-fan-control.py --curve default --interval 5
Restart=always
RestartSec=10
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now nvidia-fan-control.service

echo "Installed nvidia-fan-control and started service."
