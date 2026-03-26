# Ubuntu notes

- Ensure NVIDIA drivers are installed and support NVML.
- Enable nvidia-persistenced if not running:
  `sudo systemctl enable --now nvidia-persistenced.service`
- The service runs as root and uses NVML to control fans directly.
- To debug, check `journalctl -u nvidia-fan-control.service`.

