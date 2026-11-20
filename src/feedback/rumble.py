"""
Feedback Control (Force Feedback & Vibration)
"""

from typing import Optional
from ..core.device import GamepadDevice


class RumbleController:
    """Manages rumble actuation on the selected controller."""

    def __init__(self, device: Optional[GamepadDevice] = None):
        self.device = device

    def set_device(self, device: Optional[GamepadDevice]):
        self.device = device

    def pulse_left(self, duration_ms: int = 1000, intensity_pct: int = 100) -> bool:
        """Pulses Left (Heavy / Low frequency) motor."""
        if not self.device:
            return False
        return self.device.send_rumble(strong_pct=intensity_pct, weak_pct=0, duration_ms=duration_ms)

    def pulse_right(self, duration_ms: int = 1000, intensity_pct: int = 100) -> bool:
        """Pulses Right (Light / High frequency) motor."""
        if not self.device:
            return False
        return self.device.send_rumble(strong_pct=0, weak_pct=intensity_pct, duration_ms=duration_ms)

    def pulse_both(self, duration_ms: int = 1000, left_pct: int = 100, right_pct: int = 100) -> bool:
        """Pulses both rumble motors."""
        if not self.device:
            return False
        return self.device.send_rumble(strong_pct=left_pct, weak_pct=right_pct, duration_ms=duration_ms)

    def stop(self) -> bool:
        """Immediately stops all vibration."""
        if not self.device:
            return False
        return self.device.send_rumble(strong_pct=0, weak_pct=0, duration_ms=10)

