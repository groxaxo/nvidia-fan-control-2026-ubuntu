#!/usr/bin/env bash
set -euo pipefail

# Configuration
GRADIENT_SPEED="medium"  # fast|medium|slow

# Map gradient speed to sleep delay per character
case "${GRADIENT_SPEED}" in
  fast) DELAY=0.002 ;; 
  slow) DELAY=0.020 ;; 
  *) DELAY=0.007 ;; # medium
esac

# Colors to cycle through (bright rainbow)
colors=(91 95 35 33 31 36 32 34)

per_char_gradient() {
  local text="$1"
  local delay="$2"
  local -i i=0
  local -i idx=0
  local len=${#text}

  while [ $i -lt $len ]; do
    ch="${text:i:1}"
    color=${colors[$((idx % ${#colors[@]}))]}
    printf "\e[${color}m%s\e[0m" "$ch"
    i=$((i+1))
    idx=$((idx+1))
    sleep "$delay"
  done
  printf "\n"
}

# Banner lines
banner=(
  " ███╗   ██╗ ██████╗ ██████╗ ███████╗   ███████╗██╗   ██╗"
  " ████╗  ██║██╔════╝██╔═══██╗██╔════╝   ██╔════╝██║   ██║"
  " ██╔██╗ ██║██║     ██║   ██║█████╗     █████╗  ██║   ██║"
  " ██║╚██╗██║██║     ██║   ██║██╔══╝     ██╔══╝  ██║   ██║"
  " ██║ ╚████║╚██████╗╚██████╔╝███████╗   ██║     ╚██████╔╝"
  " ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝   ╚═╝      ╚═════╝ "
)

# Print the banner with per-character gradient
for line in "${banner[@]}"; do
  per_char_gradient "$line" "$DELAY"
done

# Small explanatory blurb
printf "\n"
per_char_gradient "NVIDIA Fan Control — installed via neon installer" "$DELAY"
printf "\n"

# Spinner while copying files
spinner_chars=("|" "/" "-" "\\")

copy_and_enable() {
  cp ./nvidia-fan-control.py /usr/local/bin/nvidia-fan-control.py &
  PID=$!
  i=0
  while kill -0 "$PID" 2>/dev/null; do
    printf "\r[%s] Installing..." "${spinner_chars[$((i % 4))]}"
    i=$((i+1))
    sleep 0.12
  done
  wait "$PID"
  printf "\r[✓] File copied.             \n"

  # Write systemd service
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
}

copy_and_enable

printf "\n"
per_char_gradient "All set — fans will now be adaptive on boot." "$DELAY"
per_char_gradient "Check status: sudo systemctl status nvidia-fan-control.service" "$DELAY"

echo
