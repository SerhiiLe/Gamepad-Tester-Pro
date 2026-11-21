"""
Gamepad Device Representation
Wraps Linux evdev and hidraw endpoints, sysfs metadata, LED and rumble control.
"""

import os
import glob
import time
import fcntl
import struct
import threading
from typing import Optional, Set, Tuple

from .constants import (
    EV_FF, FF_RUMBLE, EVIOCSFF, EVIOCGID,
    ABS_X, ABS_Y, ABS_RX, ABS_RY, ABS_Z, ABS_RZ, ABS_BRAKE, ABS_GAS
)
from .profiles import detect_layout_flavor


class GamepadDevice:
    """Represents a connected physical gamepad with event and hidraw interfaces."""

    def __init__(self, name: str, event_path: Optional[str] = None, hidraw_path: Optional[str] = None,
                 key_bits: Optional[Set[int]] = None, abs_bits: Optional[Set[int]] = None,
                 ev_bits: Optional[Set[int]] = None):
        self.name = name
        self.event_path = event_path
        self.hidraw_path = hidraw_path
        self.key_bits = key_bits or set()
        self.abs_bits = abs_bits or set()
        self.ev_bits = ev_bits or set()

        # Vendor and Product IDs
        self.bus, self.vendor_id, self.product_id, self.version = self._read_device_id()

        # ABS axis ranges (min, max)
        self.abs_info: Dict[int, Tuple[int, int]] = {}
        self._read_abs_info()

        # Profile / Layout flavor detection
        self.layout_flavor = detect_layout_flavor(self.name, self.key_bits, self.abs_bits)

        # Device flags
        lower_name = self.name.lower()
        self.is_dualsense = ("dualsense" in lower_name or (self.vendor_id == 0x054C and self.product_id in (0x0CE6, 0x0DF2)))
        self.is_ds4 = ("dualshock" in lower_name or "wireless controller" in lower_name or (self.vendor_id == 0x054C and self.product_id in (0x05C4, 0x09CC)))
        self.is_xbox = ("xbox" in lower_name or self.vendor_id == 0x045E or "x-box" in lower_name)
        self.is_gp2040 = ("gp2040" in lower_name or "rp2040" in lower_name or self.vendor_id == 0x2E8A)

        # Sysfs paths for LEDs and Battery
        self.sysfs_led_path = self._find_sysfs_led()
        self.sysfs_battery_path = self._find_sysfs_battery()

        # Connection type: Bluetooth or battery-powered wireless vs wired USB
        self.is_wireless: bool = (
            self.bus == 0x05 or
            bool(self.sysfs_battery_path) or
            ("wireless" in lower_name and "receiver" not in lower_name and "adapter" not in lower_name)
        )

        # Force feedback state
        self._ff_fd: Optional[int] = None
        self.active_effect_id: int = -1
        self._ff_timer: Optional[threading.Thread] = None
        self.has_ff: bool = (EV_FF in self.ev_bits) or self._check_ff_support()

        # Sibling devices (Touchpad & Motion Sensors)
        self.has_touchpad: bool = False
        self.has_motion: bool = False
        self._probe_siblings()

    def _check_ff_support(self) -> bool:
        """Checks if event device supports Force Feedback (EV_FF)."""
        if not self.event_path:
            return False
        try:
            fd = os.open(self.event_path, os.O_RDONLY | os.O_NONBLOCK)
            buf = bytearray(4)
            fcntl.ioctl(fd, 0x80044520, buf)  # EVIOCGBIT_EV
            os.close(fd)
            bits = set()
            for byte_idx, byte_val in enumerate(buf):
                for bit in range(8):
                    if byte_val & (1 << bit):
                        bits.add(byte_idx * 8 + bit)
            return EV_FF in bits
        except Exception:
            return False

    def _probe_siblings(self):
        """Scans /proc/bus/input/devices to detect if companion touchpad or motion sensors exist."""
        if not self.event_path:
            return
        try:
            with open('/proc/bus/input/devices', 'r') as f:
                content = f.read()
        except Exception:
            return

        ev_base = os.path.basename(self.event_path)
        entries = content.strip().split('\n\n')
        target_phys = None
        for entry in entries:
            lines = entry.splitlines()
            h_line = next((l for l in lines if l.startswith('H: Handlers=')), '')
            if 'Handlers=' in h_line and ev_base in h_line.split('Handlers=')[1].split():
                for l in lines:
                    if l.startswith('P: Phys='):
                        target_phys = l.split('=', 1)[1].strip()
                    elif l.startswith('B: FF='):
                        ff_val = l.split('=', 1)[1].strip()
                        if ff_val and ff_val != '0':
                            self.has_ff = True
                break

        if target_phys:
            phys_prefix = target_phys.split('/input')[0] if '/input' in target_phys else target_phys
            for entry in entries:
                lines = entry.splitlines()
                p_line = next((l for l in lines if l.startswith('P: Phys=')), '')
                n_line = next((l for l in lines if l.startswith('N: Name=')), '')
                entry_phys = p_line.split('=', 1)[1].strip() if p_line else ''
                entry_name = n_line.split('=', 1)[1].strip().strip('\"') if n_line else ''

                if entry_phys and (entry_phys == target_phys or (phys_prefix and entry_phys.startswith(phys_prefix))):
                    lower = entry_name.lower()
                    if 'touchpad' in lower:
                        self.has_touchpad = True
                    if 'motion' in lower or 'sensor' in lower or 'gyro' in lower or 'accelerometer' in lower:
                        self.has_motion = True

    def _read_abs_info(self):
        """Reads min and max ranges for all ABS axes via ioctl or evdev."""
        if not self.event_path:
            return
        try:
            fd = os.open(self.event_path, os.O_RDONLY | os.O_NONBLOCK)
            for code in self.abs_bits:
                buf = bytearray(24)  # struct input_absinfo is 6 x 32-bit ints = 24 bytes
                fcntl.ioctl(fd, 0x80184540 + code, buf)  # EVIOCGABS(code)
                val, amin, amax, fuzz, flat, res = struct.unpack('iiiiii', buf)
                self.abs_info[code] = (amin, amax)
            os.close(fd)
        except Exception:
            try:
                import evdev
                dev = evdev.InputDevice(self.event_path)
                for code, absinfo in dev.capabilities().get(evdev.ecodes.EV_ABS, []):
                    self.abs_info[code] = (absinfo.min, absinfo.max)
                dev.close()
            except Exception:
                pass

    def get_axis_range(self, code: int, default: Tuple[int, int] = (-32768, 32767)) -> Tuple[int, int]:
        return self.abs_info.get(code, default)

    def has_axis(self, code: int) -> bool:
        return code in self.abs_bits

    def _read_device_id(self) -> Tuple[int, int, int, int]:
        """Reads Bus, Vendor ID, Product ID, and Version from event node via ioctl."""
        if not self.event_path:
            return 0, 0, 0, 0
        try:
            fd = os.open(self.event_path, os.O_RDONLY | os.O_NONBLOCK)
            buf = bytearray(8)
            fcntl.ioctl(fd, EVIOCGID, buf)
            os.close(fd)
            bus, vid, pid, ver = struct.unpack('HHHH', buf)
            return bus, vid, pid, ver
        except Exception:
            return 0, 0, 0, 0

    def _find_sysfs_led(self) -> Optional[str]:
        """Locates sysfs LED control node (e.g. for xpad or playstation)."""
        if not self.event_path:
            return None
        try:
            ev_name = os.path.basename(self.event_path)
            dev_sys = os.path.realpath(f'/sys/class/input/{ev_name}/device')
            p = dev_sys
            for _ in range(5):
                if not p or p == '/':
                    break
                cand = os.path.join(p, 'leds')
                if os.path.isdir(cand):
                    leds = os.listdir(cand)
                    if leds:
                        return os.path.join(cand, leds[0])
                p = os.path.dirname(p)
        except Exception:
            pass
        return None

    def _find_sysfs_battery(self) -> Optional[str]:
        """Finds sysfs power_supply path if battery powered."""
        try:
            for p in glob.glob('/sys/class/power_supply/*'):
                lower = p.lower()
                if 'ps-controller' in lower or 'sony' in lower or 'dualsense' in lower or 'gamepad' in lower:
                    return p
        except Exception:
            pass
        return None

    def get_battery_info(self) -> Tuple[Optional[int], str]:
        """Returns (capacity_percent, status_string)."""
        if not self.sysfs_battery_path:
            return None, "Not available (USB wired or no battery sensor)"
        try:
            cap_file = os.path.join(self.sysfs_battery_path, 'capacity')
            stat_file = os.path.join(self.sysfs_battery_path, 'status')
            cap = None
            stat = "Unknown"
            if os.path.isfile(cap_file):
                with open(cap_file, 'r') as f:
                    cap = int(f.read().strip())
            if os.path.isfile(stat_file):
                with open(stat_file, 'r') as f:
                    stat = f.read().strip()
            return cap, stat
        except Exception as e:
            return None, f"Error: {e}"

    def send_rumble(self, strong_pct: int = 0, weak_pct: int = 0, duration_ms: int = 1000) -> bool:
        """
        Sends vibration effect to controller.
        strong_pct (0..100): Heavy / Low frequency motor (Left)
        weak_pct (0..100): Light / High frequency motor (Right)
        """
        # 1. DualShock 4 direct USB HID report fallback
        if self.is_ds4 and self.hidraw_path:
            try:
                motor_l = int((strong_pct / 100.0) * 255)
                motor_r = int((weak_pct / 100.0) * 255)
                self.send_ds4_raw(motor_l=motor_l, motor_r=motor_r)
                if duration_ms > 0:
                    def _stop_ds4():
                        time.sleep(duration_ms / 1000.0)
                        self.send_ds4_raw(motor_l=0, motor_r=0)
                    threading.Thread(target=_stop_ds4, daemon=True).start()
                return True
            except Exception:
                pass

        # 2. Standard Linux Force Feedback (EV_FF / ff_effect)
        if self.event_path:
            try:
                if self._ff_fd is None:
                    self._ff_fd = os.open(self.event_path, os.O_RDWR)

                if self._ff_timer and self._ff_timer.is_alive():
                    self._ff_timer.cancel()

                if strong_pct == 0 and weak_pct == 0:
                    if self.active_effect_id != -1:
                        stop_event = struct.pack('qqHHi', 0, 0, EV_FF, self.active_effect_id, 0)
                        os.write(self._ff_fd, stop_event)
                    return True

                strong_val = int((strong_pct / 100.0) * 65535)
                weak_val   = int((weak_pct / 100.0) * 65535)

                # 48-byte struct ff_effect on 64-bit Linux:
                effect_data = struct.pack(
                    'HhHHHHH2xHH28s',
                    FF_RUMBLE,
                    self.active_effect_id,
                    0, 0, 0,
                    duration_ms, 0,
                    strong_val, weak_val,
                    b'\x00' * 28
                )
                res = fcntl.ioctl(self._ff_fd, EVIOCSFF, effect_data)
                eff_id = struct.unpack('Hh', res[:4])[1]
                self.active_effect_id = eff_id

                play_event = struct.pack('qqHHi', 0, 0, EV_FF, self.active_effect_id, 1)
                os.write(self._ff_fd, play_event)

                if duration_ms > 0:
                    def _stop():
                        time.sleep(duration_ms / 1000.0)
                        if self._ff_fd is not None and self.active_effect_id != -1:
                            try:
                                stop_ev = struct.pack('qqHHi', 0, 0, EV_FF, self.active_effect_id, 0)
                                os.write(self._ff_fd, stop_ev)
                            except Exception:
                                pass
                    self._ff_timer = threading.Thread(target=_stop, daemon=True)
                    self._ff_timer.start()
                return True
            except Exception as e:
                print(f"[Device] FF rumble error on {self.event_path}: {e}")
                return False
        return False

    def send_ds4_raw(self, motor_l: int = 0, motor_r: int = 0, led_r: Optional[int] = None,
                     led_g: Optional[int] = None, led_b: Optional[int] = None) -> bool:
        """Sends USB Output Report 0x05 to Sony DualShock 4 via hidraw."""
        if not self.hidraw_path:
            return False
        try:
            fd = os.open(self.hidraw_path, os.O_RDWR)
            report = bytearray(32)
            report[0] = 0x05  # Output Report ID 5
            flags = 0x00
            if motor_l > 0 or motor_r > 0 or (led_r is None):
                flags |= 0x01  # Motor enable
            if led_r is not None:
                flags |= 0x02  # LED enable

            report[1] = flags
            report[4] = motor_r & 0xFF
            report[5] = motor_l & 0xFF
            if led_r is not None:
                report[6] = led_r & 0xFF
                report[7] = led_g & 0xFF
                report[8] = led_b & 0xFF
            os.write(fd, report)
            os.close(fd)
            return True
        except Exception:
            return False

    def set_dualsense_led(self, r: int, g: int, b: int) -> bool:
        """
        Sets RGB Lightbar for DualSense or DS4.
        Tries sysfs LED node first, then hidraw report.
        """
        # Try sysfs color nodes if present (hid-playstation kernel driver)
        if self.event_path:
            ev_name = os.path.basename(self.event_path)
            sys_path = os.path.realpath(f'/sys/class/input/{ev_name}/device')
            for rgb_pattern in [f'{sys_path}/leds/*::rgb', f'{sys_path}/../leds/*::rgb']:
                matches = glob.glob(rgb_pattern)
                if matches:
                    rgb_node = matches[0]
                    try:
                        with open(os.path.join(rgb_node, 'multi_intensity'), 'w') as f:
                            f.write(f"{r} {g} {b}\n")
                        return True
                    except Exception:
                        pass

        # Fallback to DS4 HID report
        if self.is_ds4 and self.hidraw_path:
            return self.send_ds4_raw(led_r=r, led_g=g, led_b=b)

        return False

    def close(self):
        """Clean up active force feedback effects and file descriptors."""
        if self._ff_fd is not None:
            if self.active_effect_id != -1:
                try:
                    os.write(self._ff_fd, struct.pack('qqHHi', 0, 0, EV_FF, self.active_effect_id, 0))
                except Exception:
                    pass
            try:
                os.close(self._ff_fd)
            except Exception:
                pass
            self._ff_fd = None

    def __del__(self):
        self.close()

    def __repr__(self) -> str:
        vid_pid = f"VID:0x{self.vendor_id:04X} PID:0x{self.product_id:04X}"
        return f"<GamepadDevice '{self.name}' ({vid_pid}) on {self.event_path or self.hidraw_path}>"

