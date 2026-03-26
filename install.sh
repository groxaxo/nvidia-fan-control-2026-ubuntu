#!/usr/bin/env bash
set -euo pipefail

rainbow_banner() {
  local -a colors=(31 33 35 36 32 34 91 95)
  local i=0
  while IFS= read -r line; do
    local c=${colors[i % ${#colors[@]}]}
    printf "\e[${c}m%s\e[0m\n" "$line"
    i=$((i+1))
  done
}

rainbow_banner <<'RB'
  ██████╗ ██████╗ ██████╗ ███████╗██████╗  ██████╗ ███████╗
  ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔════╝
  ██████╔╝██████╔╝██████╔╝█████╗  ██████╔╝██║   ██║███████╗
  ██╔═══╝ ██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗██║   ██║╚════██║
  ██║     ██║     ██║     ███████╗██║  ██║╚██████╔╝███████║
  ╚═╝     ╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝

  🌈 NVIDIA Fan Control — TRIPPY INSTALLER 🌈
  This will copy the NVML-powered daemon to /usr/local/bin
  and enable a systemd service so your fans stay adaptive on boot.
RB

echo
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

echo
rainbow_banner <<'RB'
  ✅ Installed and started: nvidia-fan-control.service
  🔎 Check status: sudo systemctl status nvidia-fan-control.service
  📜 View logs: sudo journalctl -u nvidia-fan-control.service -f
RB

echo "Installer finished. Stay trippy."
