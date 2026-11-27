"""
Gamepad Gyroscope & Accelerometer (IMU) Analysis Module
Integrates 3-axis angular velocity into 3D orientation (unit quaternion & 3x3 rotation matrix),
computes Pitch / Yaw / Roll angles in degrees, tracks accelerometer linear shift (g),
and maintains a rolling time-series angle history for real-time plotting.
"""

import math
import collections
import threading
from typing import Deque, Dict, List, Optional, Tuple

from ..core.constants import (
    EV_SYN, EV_ABS,
    ABS_X, ABS_Y, ABS_Z,
    ABS_RX, ABS_RY, ABS_RZ
)


def _quat_mul(q1: Tuple[float, float, float, float],
              q2: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return (
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
    )


def _quat_norm(q: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z)
    if n < 1e-12:
        return (1.0, 0.0, 0.0, 0.0)
    return (w / n, x / n, y / n, z / n)


def _quat_to_mat3(q: Tuple[float, float, float, float]) -> Tuple[Tuple[float, float, float], ...]:
    w, x, y, z = q
    return (
        (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z),       2.0 * (x * z + w * y)),
        (2.0 * (x * y + w * z),       1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x)),
        (2.0 * (x * z - w * y),       2.0 * (y * z + w * x),       1.0 - 2.0 * (x * x + y * y)),
    )


def _mat3_to_euler_deg(R: Tuple[Tuple[float, float, float], ...]) -> Tuple[float, float, float]:
    """
    Extracts intrinsic Tait-Bryan angles (pitch_X, yaw_Y, roll_Z) in degrees
    within [-180, 180] from rotation matrix R = Rx(pitch) * Ry(yaw) * Rz(roll)
    or extrinsic ZYX order.
    """
    # Using R = Ry(yaw) * Rx(pitch) * Rz(roll) or standard graphics Y-up:
    # Check sin(pitch) = -R[1][2]
    sin_p = max(-1.0, min(1.0, -R[1][2]))
    pitch = math.asin(sin_p)
    cos_p = math.cos(pitch)
    if abs(cos_p) > 1e-5:
        yaw = math.atan2(R[0][2], R[2][2])
        roll = math.atan2(R[1][0], R[1][1])
    else:
        # Gimbal-lock fallback
        yaw = math.atan2(-R[2][0], R[0][0])
        roll = 0.0
    return (math.degrees(pitch), math.degrees(yaw), math.degrees(roll))


class MotionAnalyzer:
    """
    Processes 6-axis IMU (3-axis Gyroscope + 3-axis Accelerometer) events.
    Thread-safe for background InputReader writes and 30-60 FPS Qt reads.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # Sensor scaling (counts per deg/s for gyro, counts per g for accel)
        # Linux hid-playstation defaults: gyro=1024 counts/(deg/s), accel=8192 counts/g
        self.gyro_res: Dict[int, float] = {ABS_RX: 1024.0, ABS_RY: 1024.0, ABS_RZ: 1024.0}
        self.accel_res: Dict[int, float] = {ABS_X: 8192.0, ABS_Y: 8192.0, ABS_Z: 8192.0}

        # Latest raw sensor readings
        self._raw_gx: int = 0
        self._raw_gy: int = 0
        self._raw_gz: int = 0
        self._raw_ax: int = 0
        self._raw_ay: int = 0
        self._raw_az: int = 0

        # Resting bias calibration (counts)
        self._bias_gx: float = 0.0
        self._bias_gy: float = 0.0
        self._bias_gz: float = 0.0

        # Calibrated angular velocity (deg/s)
        self.gx_dps: float = 0.0
        self.gy_dps: float = 0.0
        self.gz_dps: float = 0.0

        # Accelerometer (g) and relative shift from recenter baseline (g)
        self.ax_g: float = 0.0
        self.ay_g: float = 0.0
        self.az_g: float = 0.0
        self._base_ax_g: float = 0.0
        self._base_ay_g: float = 0.0
        self._base_az_g: float = 0.0
        self.shift_x_g: float = 0.0
        self.shift_y_g: float = 0.0
        self.shift_z_g: float = 0.0

        # 3D Orientation quaternion (w, x, y, z) & extracted angles (deg)
        self.quaternion: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
        self.pitch_deg: float = 0.0
        self.yaw_deg: float = 0.0
        self.roll_deg: float = 0.0

        # Timing & rolling history for plot: (t_rel_sec, pitch_deg, yaw_deg, roll_deg)
        self._start_ts: Optional[float] = None
        self._last_sync_ts: Optional[float] = None
        self._sample_idx: int = 0
        self.history: Deque[Tuple[float, float, float, float]] = collections.deque(maxlen=300)

    def reset(self):
        """Resets orientation, baseline, bias, and history."""
        with self._lock:
            self._raw_gx = self._raw_gy = self._raw_gz = 0
            self._raw_ax = self._raw_ay = self._raw_az = 0
            self._bias_gx = self._bias_gy = self._bias_gz = 0.0
            self.gx_dps = self.gy_dps = self.gz_dps = 0.0
            self.ax_g = self.ay_g = self.az_g = 0.0
            self._base_ax_g = self._base_ay_g = self._base_az_g = 0.0
            self.shift_x_g = self.shift_y_g = self.shift_z_g = 0.0
            self.quaternion = (1.0, 0.0, 0.0, 0.0)
            self.pitch_deg = self.yaw_deg = self.roll_deg = 0.0
            self._start_ts = None
            self._last_sync_ts = None
            self._sample_idx = 0
            self.history.clear()

    def recenter(self, calibrate_bias: bool = True):
        """
        Resets 3D orientation to neutral center (0°, 0°, 0°) and clears accelerometer shift.
        If calibrate_bias is True and gyro is roughly still, captures current gyro reading as bias.
        """
        with self._lock:
            self.quaternion = (1.0, 0.0, 0.0, 0.0)
            self.pitch_deg = 0.0
            self.yaw_deg = 0.0
            self.roll_deg = 0.0

            if calibrate_bias:
                # Only capture bias if angular velocity isn't violently spinning (> 25 deg/s)
                if (abs(self._raw_gx / self.gyro_res[ABS_RX]) < 25.0 and
                        abs(self._raw_gy / self.gyro_res[ABS_RY]) < 25.0 and
                        abs(self._raw_gz / self.gyro_res[ABS_RZ]) < 25.0):
                    self._bias_gx = float(self._raw_gx)
                    self._bias_gy = float(self._raw_gy)
                    self._bias_gz = float(self._raw_gz)
                self.gx_dps = self.gy_dps = self.gz_dps = 0.0

            self._base_ax_g = self.ax_g
            self._base_ay_g = self.ay_g
            self._base_az_g = self.az_g
            self.shift_x_g = 0.0
            self.shift_y_g = 0.0
            self.shift_z_g = 0.0

    def configure_axes(self, abs_info: Dict[int, Tuple[int, int, int]]):
        """Configures physical unit resolutions from Linux input_absinfo (min, max, res)."""
        with self._lock:
            for code in (ABS_RX, ABS_RY, ABS_RZ):
                if code in abs_info:
                    amin, amax, res = abs_info[code]
                    if res > 0:
                        self.gyro_res[code] = float(res)
                    elif amax >= 32767:
                        # Fallback for drivers reporting raw signed 16-bit full-scale ±2000 deg/s
                        self.gyro_res[code] = max(16.0, float(amax) / 2000.0)

            for code in (ABS_X, ABS_Y, ABS_Z):
                if code in abs_info:
                    amin, amax, res = abs_info[code]
                    if res > 0:
                        self.accel_res[code] = float(res)
                    elif amax >= 32767:
                        # Fallback for raw 16-bit ±4g
                        self.accel_res[code] = max(1000.0, float(amax) / 4.0)

    def process_event(self, ev_type: int, code: int, value: int, timestamp: float):
        """Processes raw Linux input event from Motion Sensors node."""
        with self._lock:
            if ev_type == EV_ABS:
                if code == ABS_RX:
                    self._raw_gx = value
                elif code == ABS_RY:
                    self._raw_gy = value
                elif code == ABS_RZ:
                    self._raw_gz = value
                elif code == ABS_X:
                    self._raw_ax = value
                elif code == ABS_Y:
                    self._raw_ay = value
                elif code == ABS_Z:
                    self._raw_az = value
            elif ev_type == EV_SYN and code == 0:
                self._commit_sample(timestamp)

    def _commit_sample(self, timestamp: float):
        """Updates velocities, accelerometer shift, 3D quaternion, and rolling angle history."""
        # Convert raw gyro to deg/s (subtract calibrated bias + small deadband < 0.3 deg/s)
        gx = (self._raw_gx - self._bias_gx) / self.gyro_res[ABS_RX]
        gy = (self._raw_gy - self._bias_gy) / self.gyro_res[ABS_RY]
        gz = (self._raw_gz - self._bias_gz) / self.gyro_res[ABS_RZ]

        self.gx_dps = 0.0 if abs(gx) < 0.25 else gx
        self.gy_dps = 0.0 if abs(gy) < 0.25 else gy
        self.gz_dps = 0.0 if abs(gz) < 0.25 else gz

        # Convert raw accel to g and compute relative shift
        self.ax_g = self._raw_ax / self.accel_res[ABS_X]
        self.ay_g = self._raw_ay / self.accel_res[ABS_Y]
        self.az_g = self._raw_az / self.accel_res[ABS_Z]
        self.shift_x_g = self.ax_g - self._base_ax_g
        self.shift_y_g = self.ay_g - self._base_ay_g
        self.shift_z_g = self.az_g - self._base_az_g

        if self._start_ts is None:
            self._start_ts = timestamp
        if self._last_sync_ts is None:
            self._last_sync_ts = timestamp
            self.history.append((0.0, self.pitch_deg, self.yaw_deg, self.roll_deg))
            return

        dt = timestamp - self._last_sync_ts
        self._last_sync_ts = timestamp

        if 0.0 < dt < 0.2:
            # Incremental axis-angle integration into unit quaternion
            wx = math.radians(self.gx_dps) * dt
            wy = math.radians(self.gy_dps) * dt
            wz = math.radians(self.gz_dps) * dt
            angle = math.sqrt(wx * wx + wy * wy + wz * wz)
            if angle > 1e-7:
                half = 0.5 * angle
                s = math.sin(half) / angle
                dq = (math.cos(half), wx * s, wy * s, wz * s)
                self.quaternion = _quat_norm(_quat_mul(self.quaternion, dq))

            R = _quat_to_mat3(self.quaternion)
            self.pitch_deg, self.yaw_deg, self.roll_deg = _mat3_to_euler_deg(R)

        t_rel = max(0.0, timestamp - self._start_ts)
        self.history.append((t_rel, self.pitch_deg, self.yaw_deg, self.roll_deg))

    def get_snapshot(self) -> Dict:
        """Returns a thread-safe snapshot of orientation matrix, angles, rates, shift, and history."""
        with self._lock:
            R = _quat_to_mat3(self.quaternion)
            return {
                "rot_matrix": R,
                "pitch_deg": self.pitch_deg,
                "yaw_deg": self.yaw_deg,
                "roll_deg": self.roll_deg,
                "gx_dps": self.gx_dps,
                "gy_dps": self.gy_dps,
                "gz_dps": self.gz_dps,
                "ax_g": self.ax_g,
                "ay_g": self.ay_g,
                "az_g": self.az_g,
                "shift_x_g": self.shift_x_g,
                "shift_y_g": self.shift_y_g,
                "shift_z_g": self.shift_z_g,
                "history": list(self.history),
            }
