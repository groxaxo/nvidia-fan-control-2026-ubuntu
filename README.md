# ⚡️🌈 NVIDIA Fan Control — TRIPPY EDITION 🛸🍄

╔════════════════════════════════════════════════════════════════════════╗
║  🌀✨🌈 WELCOME, EARTHLING — meet the fan guardian that GROOVES with temps 🌈✨🌀  ║
╠════════════════════════════════════════════════════════════════════════╣
║  This daemon listens to each NVIDIA GPU's heartbeat (temperature), and    ║
║  gently nudges the fans to keep your rig cool, quiet, and very, very     ║
║  relaxed. No X server. Just NVML, pure vibes.                            ║
╚════════════════════════════════════════════════════════════════════════╝

                  .-"""-.
               .-"       "-.
             .'  .-"""-.  `.
            /   /  .-.  \   \
           ;   ;  (   )  ;   ;
           |   |   `-`   |   |
           ;   ;  .---.  ;   ;
            \   \(     )/   /
             `.  `-.-'  .'
               `-.___.-'

---

NVML-driven, systemd-enabled, and tuned with three curves:
- default — balanced cooling
- quiet — quieter, warmer
- performance — aggressive cooling

Quick install (summary):

```bash
sudo apt update
sudo apt install -y python3 python3-pip
sudo pip3 install nvidia-ml-py
sudo ./install.sh    # from the repo root
```

More details, usage, and troubleshooting below in this README.

