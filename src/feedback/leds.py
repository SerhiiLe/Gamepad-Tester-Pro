"""
LED & Indication Controller
Manages DualSense / DS4 RGB lightbar and Xbox 360 Ring of Light patterns.
"""

import os
from typing import Optional, Tuple
from ..core.device import GamepadDevice


class LedController:
    """Controls controller LEDs and RGB illumination."""

    COLOR_PRESETS = {
        "Red": (255, 0, 0),
        "Green": (0, 255, 0),
        "Blue": (0, 0, 255),
        "Yellow": (255, 255, 0),
        "Cyan": (0, 255, 255),
        "Magenta": (255, 0, 255),
        "White": (255, 255, 255),
        "Off": (0, 0, 0),
    }

    XPAD_PATTERNS = {
        0: "All Off",
        1: "All Blink",
        2: "Player 1 (Top-Left)",
        3: "Player 2 (Top-Right)",
        4: "Player 3 (Bottom-Left)",
        5: "Player 4 (Bottom-Right)",
        10: "Rotating",
        11: "Fast Blink",
        12: "Slow Blink",
        13: "Alternating"
    }

    def __init__(self, device: Optional[GamepadDevice] = None):
        self.device = device

    def set_device(self, device: Optional[GamepadDevice]):
        self.device = device

    def set_rgb(self, r: int, g: int, b: int) -> bool:
        """Applies RGB color to DualSense / DS4 lightbar."""
        if not self.device:
            return False
        return self.device.set_dualsense_led(r, g, b)

    def set_xpad_pattern(self, pattern: int) -> Tuple[bool, str]:
        """Sets Xbox 360 LED pattern via sysfs."""
        if not self.device or not self.device.sysfs_led_path:
            return False, "sysfs LED path not found for this device"
        try:
            b_path = os.path.join(self.device.sysfs_led_path, 'brightness')
            if not os.path.isfile(b_path):
                b_path = self.device.sysfs_led_path
            with open(b_path, 'w') as f:
                f.write(f"{pattern}\n")
            return True, "OK"
        except (PermissionError, OSError) as e:
            return False, f"Permission error writing to sysfs ({e})"

