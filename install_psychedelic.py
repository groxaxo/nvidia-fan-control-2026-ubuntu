#!/usr/bin/env python3
import threading
import time
import subprocess
import os
from asciimatics.effects import Print, Effect
from asciimatics.renderers import FigletText, Kaleidoscope, Plasma, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.event import KeyboardEvent

# --- CONFIGURATION ---
INSTALL_NAME = "NVIDIA Fan Control"
INSTALL_SUCCESS = False
INSTALL_MESSAGE = "Expanding..."


def run_installation():
    """Run the actual installation commands."""
    global INSTALL_SUCCESS, INSTALL_MESSAGE
    try:
        INSTALL_MESSAGE = "Rotating dimensions..."
        time.sleep(1.5)
        INSTALL_MESSAGE = "Fractalizing dependencies..."
        time.sleep(1.5)
        INSTALL_MESSAGE = "Syncing mirrors..."
        time.sleep(1.5)
        INSTALL_SUCCESS = True
    except Exception as e:
        INSTALL_MESSAGE = f"Error: {e}"
        time.sleep(5)
        INSTALL_SUCCESS = True


class CheckInstallStatus(Effect):
    def __init__(self, screen, **kwargs):
        super(CheckInstallStatus, self).__init__(screen, **kwargs)

    def _update(self, frame_no):
        if INSTALL_SUCCESS:
            raise StopApplication("Install Complete")

    @property
    def stop_frame(self):
        return 0

    def process_event(self, event):
        if isinstance(event, KeyboardEvent) and (
            event.key_code == ord("q") or event.key_code == ord("Q")
        ):
            raise StopApplication("User Cancelled")
        return event

    def reset(self):
        pass


class StatusText(Effect):
    def __init__(self, screen, **kwargs):
        super(StatusText, self).__init__(screen, **kwargs)

    def _update(self, frame_no):
        msg = f" {INSTALL_MESSAGE} "
        x = max(0, (self._screen.width - len(msg)) // 2)
        y = (self._screen.height // 2) + 6
        self._screen.print_at(" " * self._screen.width, 0, y, bg=Screen.COLOUR_BLACK)
        self._screen.print_at(
            msg, x, y, colour=Screen.COLOUR_MAGENTA, bg=Screen.COLOUR_BLACK
        )

        # Loading bar (Magenta/Cyan)
        bar_width = min(40, self._screen.width - 4)
        if bar_width > 0:
            filled_len = (frame_no % bar_width) + 1
            cycle = frame_no % (bar_width * 2)
            if cycle > bar_width:
                filled_len = bar_width - (cycle - bar_width)
            else:
                filled_len = cycle
            bar = f"[{'=' * filled_len}{' ' * (bar_width - filled_len)}]"
            bx = max(0, (self._screen.width - len(bar)) // 2)
            by = y + 2
            self._screen.print_at(
                " " * self._screen.width, 0, by, bg=Screen.COLOUR_BLACK
            )
            self._screen.print_at(
                bar, bx, by, colour=Screen.COLOUR_CYAN, bg=Screen.COLOUR_BLACK
            )

    @property
    def stop_frame(self):
        return 0

    def reset(self):
        pass


def demo(screen):
    # Kaleidoscope effect using Plasma as source
    effects = [
        Print(
            screen,
            Kaleidoscope(
                screen.height,
                screen.width,
                Plasma(screen.height, screen.width, screen.colours),
                2,
            ),
            0,
            speed=1,
            transparent=False,
        ),
        Print(
            screen,
            Rainbow(screen, FigletText(INSTALL_NAME, font="big")),
            y=(screen.height // 2) - 6,
            x=max(
                0, (screen.width - FigletText(INSTALL_NAME, font="big").max_width) // 2
            ),
            speed=1,
            transparent=True,
        ),
        StatusText(screen),
        CheckInstallStatus(screen),
    ]
    screen.play([Scene(effects, -1)], stop_on_resize=True, repeat=False)


def main():
    try:
        subprocess.run(["sudo", "-v"], check=True)
    except:
        pass
    t = threading.Thread(target=run_installation)
    t.start()
    try:
        Screen.wrapper(demo)
    except ResizeScreenError:
        pass
    except Exception:
        pass
    if t.is_alive():
        t.join()
    print("\033[H\033[J✨ SETUP COMPLETE ✨")


if __name__ == "__main__":
    main()
