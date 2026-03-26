# NVIDIA Fan Control (Ubuntu)

NVML-based dynamic fan control for NVIDIA GPUs. Uses pynvml (nvidia-ml-py) so no X11 is required.

## Features
- Adaptive fan curves (default, quiet, performance)
- Systemd service for autostart
- No X server dependency

## Requirements
- Ubuntu with NVIDIA drivers installed (NVML support)
- python3, pip3
- Root privileges to control fans

## Quick install

1. Install prerequisites:

```bash
sudo apt update
sudo apt install -y python3 python3-pip
sudo pip3 install nvidia-ml-py
```

2. Copy files and enable service (from repo root):

```bash
sudo cp nvidia-fan-control.py /usr/local/bin/
sudo chmod +x /usr/local/bin/nvidia-fan-control.py
sudo cp nvidia-fan-control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nvidia-fan-control.service
```

3. Verify:

```bash
systemctl status nvidia-fan-control.service
journalctl -u nvidia-fan-control.service -f
nvidia-smi --query-gpu=index,name,temperature.gpu,fan.speed --format=csv
```

## Troubleshooting
- If `pynvml` is missing: `sudo pip3 install nvidia-ml-py`
- If you see `Insufficient Permissions`, ensure the service is running as root or run the script with `sudo`.
- Ensure `nvidia-persistenced` is running: `sudo systemctl enable --now nvidia-persistenced.service`.

## Usage
Run directly for testing:

```bash
sudo /usr/bin/python3 /usr/local/bin/nvidia-fan-control.py --curve quiet --interval 10
```

Stopping service:

```bash
sudo systemctl stop nvidia-fan-control.service
sudo systemctl disable nvidia-fan-control.service
```

