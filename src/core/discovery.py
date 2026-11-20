"""
Gamepad Device Discovery Module
Discovers all connected gamepads using Linux evdev and hidraw with full capability probing.
"""

import os
import glob
import fcntl
import struct
from typing import List, Set, Dict

from .constants import (
    EV_KEY, EV_ABS, EV_FF,
    EVIOCGBIT_EV, EVIOCGBIT_KEY, EVIOCGBIT_ABS,
    EVIOCGNAME, HIDIOCGRAWNAME,
    BTN_JOYSTICK, BTN_GAMEPAD, ABS_X, ABS_Y
)
from .device import GamepadDevice


def _read_bitmask(fd: int, request: int, max_bytes: int = 64) -> Set[int]:
    """Reads capability bitmask via ioctl and returns set of active bit indexes."""
    try:
        buf = bytearray(max_bytes)
        fcntl.ioctl(fd, request, buf)
        active_bits = set()
        for byte_idx, byte_val in enumerate(buf):
            if byte_val:
                for bit in range(8):
                    if byte_val & (1 << bit):
                        active_bits.add(byte_idx * 8 + bit)
        return active_bits
    except Exception:
        return set()


def discover_gamepads() -> List[GamepadDevice]:
    """
    Scans /dev/input/event* and /dev/hidraw* to discover all connected gamepads.
    Filters out keyboards, mice, motion sensors, and touchpads.
    """
    devices: List[GamepadDevice] = []
    seen_events: Set[str] = set()

    # 1. Map hidraw devices by device name
    hidraw_map: Dict[str, str] = {}
    for h in sorted(glob.glob('/dev/hidraw*')):
        try:
            fd = os.open(h, os.O_RDWR | os.O_NONBLOCK)
            buf = bytearray(256)
            fcntl.ioctl(fd, HIDIOCGRAWNAME, buf)
            name = buf.decode('utf-8', errors='ignore').split('\x00')[0]
            os.close(fd)
            if name:
                hidraw_map[name] = h
        except Exception:
            pass

    # 2. Inspect all /dev/input/event* nodes
    for ev in sorted(glob.glob('/dev/input/event*')):
        try:
            fd = os.open(ev, os.O_RDONLY | os.O_NONBLOCK)
            buf = bytearray(256)
            fcntl.ioctl(fd, EVIOCGNAME, buf)
            name = buf.decode('utf-8', errors='ignore').split('\x00')[0]

            # Read EV capabilities
            ev_bits = _read_bitmask(fd, EVIOCGBIT_EV, 4)

            # A gamepad must report EV_KEY and usually EV_ABS
            has_key = EV_KEY in ev_bits
            has_abs = EV_ABS in ev_bits

            if not has_key:
                os.close(fd)
                continue

            # Read Key and ABS bits
            key_bits = _read_bitmask(fd, EVIOCGBIT_KEY, 64)
            abs_bits = _read_bitmask(fd, EVIOCGBIT_ABS, 8) if has_abs else set()
            os.close(fd)

            # Filter: must have gamepad or joystick buttons, or stick axes
            is_gamepad_btn = any(b in key_bits for b in range(BTN_GAMEPAD, BTN_GAMEPAD + 16))
            is_joystick_btn = any(b in key_bits for b in range(BTN_JOYSTICK, BTN_JOYSTICK + 16))
            has_sticks = (ABS_X in abs_bits and ABS_Y in abs_bits)

            # Ignore motion sensors, touchpad, or keyboards
            lower = name.lower()
            if "motion sensors" in lower or "touchpad" in lower or "keyboard" in lower:
                continue

            if is_gamepad_btn or is_joystick_btn or has_sticks:
                h_path = hidraw_map.get(name)
                dev = GamepadDevice(name, event_path=ev, hidraw_path=h_path,
                                    key_bits=key_bits, abs_bits=abs_bits)
                devices.append(dev)
                seen_events.add(ev)
        except Exception:
            pass

    return devices

