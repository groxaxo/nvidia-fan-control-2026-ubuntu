#!/usr/bin/env python3
"""
Dynamic NVIDIA GPU Fan Control Script
Adjusts fan speeds based on GPU temperature using NVML (no X11 required).
"""

import time
import signal
import logging
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional

try:
    import pynvml
except ImportError:
    print("ERROR: pynvml not found. Install with: pip install nvidia-ml-py", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class FanCurve:
    """Temperature to fan speed mapping."""

    points: List[Tuple[int, int]]  # (temperature, fan_speed)
    step_temp_c: Optional[int] = None
    step_speed_percent: Optional[int] = None

    def get_fan_speed(self, temp: int) -> int:
        """Get fan speed for given temperature using linear interpolation."""
        # Sort points by temperature
        sorted_points = sorted(self.points, key=lambda x: x[0])

        # Optional stepped mode: increase fixed fan% every fixed temperature delta.
        if self.step_temp_c and self.step_speed_percent:
            min_temp, min_speed = sorted_points[0]
            max_temp, max_speed = sorted_points[-1]

            if temp <= min_temp:
                return min_speed
            if temp >= max_temp:
                return max_speed

            step_count = (temp - min_temp) // self.step_temp_c
            stepped_speed = min_speed + (step_count * self.step_speed_percent)
            return max(min_speed, min(max_speed, stepped_speed))

        # Below first point
        if temp <= sorted_points[0][0]:
            return sorted_points[0][1]

        # Above last point
        if temp >= sorted_points[-1][0]:
            return sorted_points[-1][1]

        # Find between which points we are
        for i in range(len(sorted_points) - 1):
            low_temp, low_speed = sorted_points[i]
            high_temp, high_speed = sorted_points[i + 1]

            if low_temp <= temp <= high_temp:
                # Linear interpolation
                if high_temp == low_temp:
                    return low_speed
                ratio = (temp - low_temp) / (high_temp - low_temp)
                return int(low_speed + ratio * (high_speed - low_speed))

        return sorted_points[-1][1]


# Default curve: 30% at 40°C → 95% at 70°C with 10 intermediate levels.
DEFAULT_CURVE = FanCurve(
    [
        (40, 30),  # anchor: 30% at 40°C
        (43, 36),
        (45, 42),
        (48, 48),
        (51, 54),
        (54, 60),
        (56, 65),
        (59, 71),
        (62, 77),
        (65, 83),
        (67, 89),
        (70, 95),  # anchor: 95% at 70°C
    ]
)

# Quiet curve: 35°C=25%, 55°C=45%, 70°C=75%, 80°C=100%
QUIET_CURVE = FanCurve(
    [
        (35, 25),
        (55, 45),
        (70, 75),
        (80, 100),
    ]
)

# Performance curve: 30°C=40%, 50°C=60%, 65°C=85%, 75°C=100%
PERFORMANCE_CURVE = FanCurve(
    [
        (30, 40),
        (50, 60),
        (65, 85),
        (75, 100),
    ]
)


class GPUFanController:
    """Controls fans for all NVIDIA GPUs using NVML (no X11 required)."""

    def __init__(self, fan_curve: Optional[FanCurve] = None, update_interval: int = 5):
        self.fan_curve = fan_curve or DEFAULT_CURVE
        self.update_interval = update_interval
        self.running = False
        # List of (index, handle, name, num_fans, min_speed, max_speed)
        self.gpus: List[tuple] = []

    def discover_gpus(self):
        """Discover all GPUs and their fan capabilities via NVML."""
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        logger.info(f"Discovered {count} NVIDIA GPU(s) via NVML")

        for i in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            try:
                num_fans = pynvml.nvmlDeviceGetNumFans(handle)
                if num_fans == 0:
                    logger.warning(f"GPU {i} ({name}): no fans reported, skipping")
                    continue
                try:
                    min_spd, max_spd = pynvml.nvmlDeviceGetMinMaxFanSpeed(handle)
                except pynvml.NVMLError:
                    min_spd, max_spd = 0, 100
                self.gpus.append((i, handle, name, num_fans, min_spd, max_spd))
                logger.info(f"GPU {i}: {name} — {num_fans} fan(s), speed range {min_spd}%–{max_spd}%")
            except pynvml.NVMLError as exc:
                logger.warning(f"GPU {i} ({name}): fan control not available ({exc}), skipping")

    def enable_manual_control(self):
        """Switch all GPU fans to manual control mode."""
        for idx, handle, name, num_fans, _, _ in self.gpus:
            for fan in range(num_fans):
                try:
                    pynvml.nvmlDeviceSetFanControlPolicy(
                        handle, fan, pynvml.NVML_FAN_POLICY_MANUAL
                    )
                except pynvml.NVMLError as exc:
                    logger.error(f"GPU {idx} fan {fan}: failed to set manual control: {exc}")

    def restore_auto_control(self):
        """Restore automatic thermal fan control for all GPUs."""
        for idx, handle, name, num_fans, _, _ in self.gpus:
            for fan in range(num_fans):
                try:
                    pynvml.nvmlDeviceSetFanControlPolicy(
                        handle, fan, pynvml.NVML_FAN_POLICY_TEMPERATURE_CONTINOUS_SW
                    )
                    pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle, fan)
                except pynvml.NVMLError as exc:
                    logger.warning(f"GPU {idx} fan {fan}: failed to restore auto control: {exc}")
        logger.info("Automatic fan control restored")

    def set_fan_speed(self, idx: int, handle, fan: int, speed: int, min_spd: int, max_spd: int):
        """Set a single fan to the clamped target speed."""
        clamped = max(min_spd, min(max_spd, speed))
        try:
            pynvml.nvmlDeviceSetFanSpeed_v2(handle, fan, clamped)
        except pynvml.NVMLError as exc:
            logger.error(f"GPU {idx} fan {fan}: failed to set speed to {clamped}%: {exc}")

    def control_loop(self):
        """Main adaptive fan control loop."""
        self.enable_manual_control()
        logger.info("Adaptive fan control started")

        while self.running:
            for idx, handle, name, num_fans, min_spd, max_spd in self.gpus:
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                except pynvml.NVMLError as exc:
                    logger.error(f"GPU {idx}: failed to read temperature: {exc}")
                    continue

                target = self.fan_curve.get_fan_speed(temp)

                for fan in range(num_fans):
                    self.set_fan_speed(idx, handle, fan, target, min_spd, max_spd)

                clamped = max(min_spd, min(max_spd, target))
                logger.info(
                    f"GPU {idx} ({name}): {temp}°C → {clamped}% fan"
                    + (f" (curve={target}%, clamped to [{min_spd}–{max_spd}%])" if clamped != target else "")
                )

            time.sleep(self.update_interval)

    def run(self):
        """Initialise, run the control loop, and clean up on exit."""
        self.discover_gpus()

        if not self.gpus:
            logger.error("No GPUs with controllable fans found — exiting")
            pynvml.nvmlShutdown()
            return

        self.running = True

        def _stop(signum, frame):
            logger.info(f"Received signal {signum}, shutting down…")
            self.running = False

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

        try:
            self.control_loop()
        finally:
            self.restore_auto_control()
            pynvml.nvmlShutdown()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Dynamic NVIDIA GPU Fan Control")
    parser.add_argument(
        "--curve",
        choices=["default", "quiet", "performance"],
        default="default",
        help="Fan curve preset",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Update interval in seconds (default: 5)",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.curve == "quiet":
        curve = QUIET_CURVE
        logger.info("Using quiet fan curve")
    elif args.curve == "performance":
        curve = PERFORMANCE_CURVE
        logger.info("Using performance fan curve")
    else:
        curve = DEFAULT_CURVE
        logger.info("Using default fan curve")

    controller = GPUFanController(fan_curve=curve, update_interval=args.interval)
    controller.run()


if __name__ == "__main__":
    main()
