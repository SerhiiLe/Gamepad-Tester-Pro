"""
Touchpad & Gyroscope / IMU Diagnostic Widget
Provides:
  1. Touchpad visual surface (rounded rectangle with live finger circle(s), trail, click indicator)
  2. Gyroscope 3D wireframe sphere (circle with front-hemisphere Equator & Meridian arcs and intersection marker)
  3. Numeric rotation (Pitch/Yaw/Roll angles & angular rate) and displacement/accelerometer (g) readouts
  4. Real-time PyQtGraph 3-color time-series angle plot
"""

import math
from typing import Dict, List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from .plot_canvas import TimeSeriesCanvas
from ...analysis.touchpad import TouchpadAnalyzer
from ...analysis.motion import MotionAnalyzer
from ...core.device import GamepadDevice
from ...i18n import tr


# Distinct 3-axis colors shared across numeric readouts and time-series plot
COLOR_AXIS_X = "#38BDF8"  # Pitch (X) - Cyan
COLOR_AXIS_Y = "#10B981"  # Yaw   (Y) - Emerald
COLOR_AXIS_Z = "#F59E0B"  # Roll  (Z) - Amber


class TouchpadCanvas(QWidget):
    """Draws a rounded touchpad rectangle with live finger circles, trails, and click glow."""

    def __init__(self, analyzer: TouchpadAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.setMinimumSize(260, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 10.0

        # Maintain ~16:9 / 1.8:1 touchpad aspect ratio centered in available box
        avail_w = max(40.0, w - 2.0 * margin)
        avail_h = max(30.0, h - 2.0 * margin)
        aspect = 1.8
        if avail_w / avail_h > aspect:
            pad_h = avail_h
            pad_w = pad_h * aspect
        else:
            pad_w = avail_w
            pad_h = pad_w / aspect

        pad_x = (w - pad_w) / 2.0
        pad_y = (h - pad_h) / 2.0
        pad_rect = QRectF(pad_x, pad_y, pad_w, pad_h)

        slots_data, is_clicked, _, _ = self.analyzer.get_snapshot()

        # Touchpad surface & click border
        bg_color = QColor("#132A2E") if is_clicked else QColor("#0F172A")
        border_color = QColor("#10B981") if is_clicked else QColor("#334155")
        border_w = 2.5 if is_clicked else 1.8

        p.setBrush(QBrush(bg_color))
        p.setPen(QPen(border_color, border_w))
        p.drawRoundedRect(pad_rect, 12.0, 12.0)

        # Subtle center crosshair grid
        p.setPen(QPen(QColor(51, 65, 85, 110), 1.0, Qt.DashLine))
        p.drawLine(QPointF(pad_x + pad_w / 2.0, pad_y + 6),
                   QPointF(pad_x + pad_w / 2.0, pad_y + pad_h - 6))
        p.drawLine(QPointF(pad_x + 6, pad_y + pad_h / 2.0),
                   QPointF(pad_x + pad_w - 6, pad_y + pad_h / 2.0))

        finger_colors = [QColor("#38BDF8"), QColor("#10B981")]

        for slot_info in slots_data:
            idx = slot_info["slot"]
            col = finger_colors[idx % len(finger_colors)]
            trail = slot_info["trail"]

            # Draw recent finger trail
            if len(trail) >= 2:
                n = len(trail)
                for i in range(1, n):
                    alpha = int(30 + 150 * (i / float(n)))
                    trail_col = QColor(col.red(), col.green(), col.blue(), alpha)
                    p.setPen(QPen(trail_col, 2.0, Qt.SolidLine, Qt.RoundCap))
                    p0 = QPointF(pad_x + trail[i - 1][0] * pad_w, pad_y + trail[i - 1][1] * pad_h)
                    p1 = QPointF(pad_x + trail[i][0] * pad_w, pad_y + trail[i][1] * pad_h)
                    p.drawLine(p0, p1)

            # Draw active finger circle
            if slot_info["active"]:
                fx = pad_x + slot_info["norm_x"] * pad_w
                fy = pad_y + slot_info["norm_y"] * pad_h
                center = QPointF(fx, fy)

                # Outer halo
                halo_col = QColor(col.red(), col.green(), col.blue(), 65)
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(halo_col))
                p.drawEllipse(center, 18.0, 18.0)

                # Main circle
                p.setPen(QPen(QColor("#FFFFFF"), 2.0))
                p.setBrush(QBrush(col))
                p.drawEllipse(center, 10.0, 10.0)

                # Finger index label
                p.setPen(QPen(QColor("#0F172A")))
                p.setFont(QFont("Segoe UI", 8, QFont.Bold))
                p.drawText(QRectF(fx - 10, fy - 10, 20, 20), Qt.AlignCenter, str(idx + 1))

        p.end()


def _transform_pt(R: Tuple[Tuple[float, float, float], ...],
                  pt: Tuple[float, float, float]) -> Tuple[float, float, float]:
    x, y, z = pt
    return (
        R[0][0] * x + R[0][1] * y + R[0][2] * z,
        R[1][0] * x + R[1][1] * y + R[1][2] * z,
        R[2][0] * x + R[2][1] * y + R[2][2] * z,
    )


def extract_visible_arc_segments(
    R: Tuple[Tuple[float, float, float], ...],
    circle_pts: List[Tuple[float, float, float]]
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Projects 3D great-circle points through rotation matrix R and clips strictly
    to the front hemisphere (z >= 0). Back-hemisphere portions (z < 0) are omitted.
    """
    transformed = [_transform_pt(R, pt) for pt in circle_pts]
    segments: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
    n = len(transformed)
    for i in range(n):
        x0, y0, z0 = transformed[i]
        x1, y1, z1 = transformed[(i + 1) % n]

        if z0 >= 0.0 and z1 >= 0.0:
            segments.append(((x0, y0), (x1, y1)))
        elif z0 >= 0.0 and z1 < 0.0:
            t = z0 / (z0 - z1) if (z0 - z1) != 0 else 0.0
            xh = x0 + t * (x1 - x0)
            yh = y0 + t * (y1 - y0)
            segments.append(((x0, y0), (xh, yh)))
        elif z0 < 0.0 and z1 >= 0.0:
            t = z0 / (z0 - z1) if (z0 - z1) != 0 else 0.0
            xh = x0 + t * (x1 - x0)
            yh = y0 + t * (y1 - y0)
            segments.append(((xh, yh), (x1, y1)))
    return segments


class GyroWireframeCanvas(QWidget):
    """
    Wireframe sphere visualization for gyroscope orientation:
      - Outer circle silhouette
      - Front-hemisphere Equator arc (z >= 0 only)
      - Front-hemisphere Meridian arc (z >= 0 only)
      - Small circle & crosshair at the front intersection pole (0, 0, +1),
        hidden completely when rotated onto the back hemisphere (z <= 0).
    """

    def __init__(self, analyzer: MotionAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.setMinimumSize(210, 210)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Precompute unit great-circle samples (96 segments)
        steps = 96
        self._equator_pts = [
            (math.cos(2.0 * math.pi * i / steps), 0.0, math.sin(2.0 * math.pi * i / steps))
            for i in range(steps)
        ]
        self._meridian_pts = [
            (0.0, math.sin(2.0 * math.pi * i / steps), math.cos(2.0 * math.pi * i / steps))
            for i in range(steps)
        ]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        radius = max(40.0, min(w, h) / 2.0 - 16.0)

        snap = self.analyzer.get_snapshot()
        R = snap["rot_matrix"]

        # 1. Outer wireframe sphere silhouette
        p.setBrush(QBrush(QColor("#0B111E")))
        p.setPen(QPen(QColor("#475569"), 2.0))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

        # Subtle static reference rim ticks (N/S/E/W)
        p.setPen(QPen(QColor(71, 85, 105, 110), 1.0))
        tick = 5.0
        p.drawLine(QPointF(cx, cy - radius), QPointF(cx, cy - radius + tick))
        p.drawLine(QPointF(cx, cy + radius - tick), QPointF(cx, cy + radius))
        p.drawLine(QPointF(cx - radius, cy), QPointF(cx - radius + tick, cy))
        p.drawLine(QPointF(cx + radius - tick, cy), QPointF(cx + radius, cy))

        # 2. Equator front-hemisphere arc (z >= 0 only)
        eq_segs = extract_visible_arc_segments(R, self._equator_pts)
        p.setPen(QPen(QColor(COLOR_AXIS_X), 2.2, Qt.SolidLine, Qt.RoundCap))
        for (x0, y0), (x1, y1) in eq_segs:
            p.drawLine(
                QPointF(cx + x0 * radius, cy - y0 * radius),
                QPointF(cx + x1 * radius, cy - y1 * radius),
            )

        # 3. Meridian front-hemisphere arc (z >= 0 only)
        mer_segs = extract_visible_arc_segments(R, self._meridian_pts)
        p.setPen(QPen(QColor(COLOR_AXIS_Y), 2.2, Qt.SolidLine, Qt.RoundCap))
        for (x0, y0), (x1, y1) in mer_segs:
            p.drawLine(
                QPointF(cx + x0 * radius, cy - y0 * radius),
                QPointF(cx + x1 * radius, cy - y1 * radius),
            )

        # 4. Intersection pole (0, 0, +1): drawn ONLY on front side (z > 0)
        px, py, pz = _transform_pt(R, (0.0, 0.0, 1.0))
        if pz > 0.0:
            sx = cx + px * radius
            sy = cy - py * radius
            pole_pt = QPointF(sx, sy)

            # Small circle
            p.setBrush(QBrush(QColor("#0F172A")))
            p.setPen(QPen(QColor("#F8FAFC"), 2.0))
            p.drawEllipse(pole_pt, 7.0, 7.0)

            # Crosshair aligned with rotated local X/Y tangent axes
            ux, uy, _ = _transform_pt(R, (1.0, 0.0, 0.0))
            vx, vy, _ = _transform_pt(R, (0.0, 1.0, 0.0))
            arm = 11.0
            p.setPen(QPen(QColor("#F43F5E"), 2.0, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(sx - ux * arm, sy + uy * arm), QPointF(sx + ux * arm, sy - uy * arm))
            p.drawLine(QPointF(sx - vx * arm, sy + vy * arm), QPointF(sx + vx * arm, sy - vy * arm))

        p.end()


class TouchpadMotionWidget(QWidget):
    """Combined tab widget for Touchpad and Gyroscope / IMU diagnostics."""

    def __init__(
        self,
        touchpad_analyzer: TouchpadAnalyzer,
        motion_analyzer: MotionAnalyzer,
        parent=None
    ):
        super().__init__(parent)
        self.touchpad_analyzer = touchpad_analyzer
        self.motion_analyzer = motion_analyzer
        self.current_device: Optional[GamepadDevice] = None

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        # ======================================================================
        # Left Column: Touchpad
        # ======================================================================
        self.grp_touchpad = QGroupBox(tr("touchpad_group_title"))
        self.grp_touchpad.setStyleSheet("QGroupBox { font-size: 12px; font-weight: bold; }")
        l_tp = QVBoxLayout(self.grp_touchpad)
        l_tp.setContentsMargins(10, 14, 10, 10)
        l_tp.setSpacing(8)

        self.lbl_tp_status = QLabel()
        self.lbl_tp_status.setWordWrap(True)
        l_tp.addWidget(self.lbl_tp_status)

        self.tp_canvas = TouchpadCanvas(self.touchpad_analyzer)
        l_tp.addWidget(self.tp_canvas, stretch=1)

        # Touchpad numeric readouts + Reset button
        self.lbl_tp_coords = QLabel()
        self.lbl_tp_coords.setStyleSheet(
            "background-color: #0F172A; border: 1px solid #1E293B; border-radius: 5px; "
            "padding: 6px 10px; color: #CBD5E1; font-family: monospace; font-size: 11px;"
        )
        self.lbl_tp_coords.setWordWrap(True)
        l_tp.addWidget(self.lbl_tp_coords)

        tp_btn_row = QHBoxLayout()
        tp_btn_row.addStretch(1)
        self.btn_tp_reset = QPushButton(tr("btn_reset"))
        self.btn_tp_reset.setMinimumWidth(110)
        self.btn_tp_reset.clicked.connect(self._reset_touchpad)
        tp_btn_row.addWidget(self.btn_tp_reset)
        l_tp.addLayout(tp_btn_row)

        root.addWidget(self.grp_touchpad, stretch=4)

        # ======================================================================
        # Right Column: Gyroscope Wireframe + Numeric Values + Angle Time Plot
        # ======================================================================
        self.grp_gyro = QGroupBox(tr("gyro_group_title"))
        self.grp_gyro.setStyleSheet("QGroupBox { font-size: 12px; font-weight: bold; }")
        l_gyro = QVBoxLayout(self.grp_gyro)
        l_gyro.setContentsMargins(10, 14, 10, 10)
        l_gyro.setSpacing(8)

        self.lbl_gyro_status = QLabel()
        self.lbl_gyro_status.setWordWrap(True)
        l_gyro.addWidget(self.lbl_gyro_status)

        # Upper split: Wireframe Sphere (left) + Numeric Rotation/Shift Cards (right)
        top_gyro_row = QHBoxLayout()

        self.gyro_canvas = GyroWireframeCanvas(self.motion_analyzer)
        top_gyro_row.addWidget(self.gyro_canvas, stretch=3)

        # Numeric values & controls panel
        nums_col = QVBoxLayout()
        nums_col.setSpacing(8)

        # Card 1: Rotation (Angles & Angular Velocity)
        self.grp_rot = QGroupBox(tr("gyro_rot_title"))
        self.grp_rot.setStyleSheet("QGroupBox { font-size: 11px; color: #94A3B8; }")
        g_rot = QGridLayout(self.grp_rot)
        g_rot.setSpacing(4)

        self.lbl_pitch_name = QLabel("Pitch (X):")
        self.lbl_pitch_name.setStyleSheet(f"color: {COLOR_AXIS_X}; font-weight: bold;")
        self.lbl_pitch_val = QLabel("+0.0°  (0.0 °/s)")
        self.lbl_pitch_val.setStyleSheet("font-family: monospace; color: #E2E8F0;")

        self.lbl_yaw_name = QLabel("Yaw (Y):")
        self.lbl_yaw_name.setStyleSheet(f"color: {COLOR_AXIS_Y}; font-weight: bold;")
        self.lbl_yaw_val = QLabel("+0.0°  (0.0 °/s)")
        self.lbl_yaw_val.setStyleSheet("font-family: monospace; color: #E2E8F0;")

        self.lbl_roll_name = QLabel("Roll (Z):")
        self.lbl_roll_name.setStyleSheet(f"color: {COLOR_AXIS_Z}; font-weight: bold;")
        self.lbl_roll_val = QLabel("+0.0°  (0.0 °/s)")
        self.lbl_roll_val.setStyleSheet("font-family: monospace; color: #E2E8F0;")

        g_rot.addWidget(self.lbl_pitch_name, 0, 0)
        g_rot.addWidget(self.lbl_pitch_val, 0, 1)
        g_rot.addWidget(self.lbl_yaw_name, 1, 0)
        g_rot.addWidget(self.lbl_yaw_val, 1, 1)
        g_rot.addWidget(self.lbl_roll_name, 2, 0)
        g_rot.addWidget(self.lbl_roll_val, 2, 1)
        nums_col.addWidget(self.grp_rot)

        # Card 2: Shift / Accelerometer
        self.grp_shift = QGroupBox(tr("gyro_shift_title"))
        self.grp_shift.setStyleSheet("QGroupBox { font-size: 11px; color: #94A3B8; }")
        g_shift = QGridLayout(self.grp_shift)
        g_shift.setSpacing(4)

        self.lbl_ax_name = QLabel("ΔX (Accel):")
        self.lbl_ax_name.setStyleSheet(f"color: {COLOR_AXIS_X}; font-weight: bold;")
        self.lbl_ax_val = QLabel("+0.00 g  (+0.00 g)")
        self.lbl_ax_val.setStyleSheet("font-family: monospace; color: #E2E8F0;")

        self.lbl_ay_name = QLabel("ΔY (Accel):")
        self.lbl_ay_name.setStyleSheet(f"color: {COLOR_AXIS_Y}; font-weight: bold;")
        self.lbl_ay_val = QLabel("+0.00 g  (+0.00 g)")
        self.lbl_ay_val.setStyleSheet("font-family: monospace; color: #E2E8F0;")

        self.lbl_az_name = QLabel("ΔZ (Accel):")
        self.lbl_az_name.setStyleSheet(f"color: {COLOR_AXIS_Z}; font-weight: bold;")
        self.lbl_az_val = QLabel("+0.00 g  (+0.00 g)")
        self.lbl_az_val.setStyleSheet("font-family: monospace; color: #E2E8F0;")

        g_shift.addWidget(self.lbl_ax_name, 0, 0)
        g_shift.addWidget(self.lbl_ax_val, 0, 1)
        g_shift.addWidget(self.lbl_ay_name, 1, 0)
        g_shift.addWidget(self.lbl_ay_val, 1, 1)
        g_shift.addWidget(self.lbl_az_name, 2, 0)
        g_shift.addWidget(self.lbl_az_val, 2, 1)
        nums_col.addWidget(self.grp_shift)

        # Action buttons
        gyro_btns = QHBoxLayout()
        self.btn_recenter = QPushButton(tr("btn_gyro_recenter"))
        self.btn_recenter.clicked.connect(self._recenter_gyro)
        gyro_btns.addWidget(self.btn_recenter)

        self.btn_gyro_reset = QPushButton(tr("btn_reset"))
        self.btn_gyro_reset.clicked.connect(self._reset_gyro)
        gyro_btns.addWidget(self.btn_gyro_reset)
        nums_col.addLayout(gyro_btns)
        nums_col.addStretch(1)

        top_gyro_row.addLayout(nums_col, stretch=4)
        l_gyro.addLayout(top_gyro_row, stretch=5)

        # Lower section: Rolling Time-Series Plot of Angles (3 colors)
        self.plot = TimeSeriesCanvas(
            y_min=-185.0,
            y_max=185.0,
            x_min=0.0,
            x_max=10.0,
            auto_y=False,
            auto_x=True,
            show_legend=True,
            x_label=tr("gyro_plot_axis_x"),
            y_label=tr("gyro_plot_axis_y"),
        )
        self.plot.set_ref_lines([
            {"y": 0.0, "color": "#475569", "width": 1.0, "dashed": True},
        ])

        l_gyro.addWidget(self.plot, stretch=4)
        root.addWidget(self.grp_gyro, stretch=6)

        # 30 FPS UI refresh timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(33)

        self._update_support_banners()
        self._on_tick()

    def set_current_device(self, device: Optional[GamepadDevice]):
        """Updates hardware availability banners when active controller changes."""
        self.current_device = device
        self._update_support_banners()

    def _update_support_banners(self):
        has_tp = bool(self.current_device and getattr(self.current_device, 'has_touchpad', False))
        has_imu = bool(self.current_device and getattr(self.current_device, 'has_motion', False))

        self.btn_tp_reset.setEnabled(has_tp)
        self.btn_recenter.setEnabled(has_imu)
        self.btn_gyro_reset.setEnabled(has_imu)

        if not self.current_device:
            self._set_banner(self.lbl_tp_status, tr("tp_no_device"), "neutral")
            self._set_banner(self.lbl_gyro_status, tr("gyro_no_device"), "neutral")
        else:
            if has_tp:
                self.lbl_tp_status.setVisible(False)
            else:
                self._set_banner(self.lbl_tp_status, tr("tp_unsupported"), "warn")

            if has_imu:
                self.lbl_gyro_status.setVisible(False)
            else:
                self._set_banner(self.lbl_gyro_status, tr("gyro_unsupported"), "warn")

    def _set_banner(self, lbl: QLabel, text: str, kind: str):
        if kind == "warn":
            style = "background-color: #2D1515; border: 1px solid #7F1D1D; border-radius: 6px; padding: 6px 10px; color: #FCA5A5; font-size: 11px;"
        else:
            style = "background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 6px 10px; color: #94A3B8; font-size: 11px;"
        lbl.setText(text)
        lbl.setStyleSheet(style)
        lbl.setVisible(True)

    def _reset_touchpad(self):
        self.touchpad_analyzer.clear_trails()
        self._on_tick()

    def _recenter_gyro(self):
        self.motion_analyzer.recenter(calibrate_bias=True)
        self._on_tick()

    def _reset_gyro(self):
        self.motion_analyzer.reset()
        self.plot.set_series([])
        self._on_tick()

    def retranslate_ui(self):
        """Retranslates all texts to active language."""
        self.grp_touchpad.setTitle(tr("touchpad_group_title"))
        self.btn_tp_reset.setText(tr("btn_reset"))
        self.grp_gyro.setTitle(tr("gyro_group_title"))
        self.grp_rot.setTitle(tr("gyro_rot_title"))
        self.grp_shift.setTitle(tr("gyro_shift_title"))
        self.btn_recenter.setText(tr("btn_gyro_recenter"))
        self.btn_gyro_reset.setText(tr("btn_reset"))
        self.plot.set_labels(x_label=tr("gyro_plot_axis_x"), y_label=tr("gyro_plot_axis_y"))
        self._update_support_banners()
        self._on_tick()

    def _on_tick(self):
        """Updates Touchpad canvas, Gyro wireframe, numeric cards, and time-series plot."""
        # 1. Touchpad update
        self.tp_canvas.update()
        slots_data, is_clicked, click_cnt, touch_cnt = self.touchpad_analyzer.get_snapshot()
        s0 = slots_data[0] if len(slots_data) > 0 else {"active": False, "raw_x": 0, "raw_y": 0}
        s1 = slots_data[1] if len(slots_data) > 1 else {"active": False, "raw_x": 0, "raw_y": 0}

        click_state = tr("state_pressed") if is_clicked else tr("state_released")
        f1_txt = f"({s0['raw_x']}, {s0['raw_y']})" if s0["active"] else "—"
        f2_txt = f"({s1['raw_x']}, {s1['raw_y']})" if s1["active"] else "—"
        self.lbl_tp_coords.setText(
            tr("tp_coords_fmt", f1=f1_txt, f2=f2_txt, click=click_state, clicks=click_cnt, touches=touch_cnt)
        )

        # 2. Gyroscope wireframe & numeric cards
        self.gyro_canvas.update()
        snap = self.motion_analyzer.get_snapshot()
        unit_dps = tr("unit_deg_s")

        self.lbl_pitch_val.setText(f"{snap['pitch_deg']:+6.1f}°  ({snap['gx_dps']:+5.1f} {unit_dps})")
        self.lbl_yaw_val.setText(f"{snap['yaw_deg']:+6.1f}°  ({snap['gy_dps']:+5.1f} {unit_dps})")
        self.lbl_roll_val.setText(f"{snap['roll_deg']:+6.1f}°  ({snap['gz_dps']:+5.1f} {unit_dps})")

        self.lbl_ax_val.setText(f"{snap['shift_x_g']:+5.2f} g  ({snap['ax_g']:+5.2f} g)")
        self.lbl_ay_val.setText(f"{snap['shift_y_g']:+5.2f} g  ({snap['ay_g']:+5.2f} g)")
        self.lbl_az_val.setText(f"{snap['shift_z_g']:+5.2f} g  ({snap['az_g']:+5.2f} g)")

        # 3. Time-series angle plot
        hist = snap["history"]
        if len(hist) >= 2:
            ts = [h[0] for h in hist]
            ps = [h[1] for h in hist]
            ys = [h[2] for h in hist]
            rs = [h[3] for h in hist]
            self.plot.set_series([
                {"name": "Pitch (X)", "color": COLOR_AXIS_X, "width": 2.0, "xs": ts, "ys": ps},
                {"name": "Yaw (Y)", "color": COLOR_AXIS_Y, "width": 2.0, "xs": ts, "ys": ys},
                {"name": "Roll (Z)", "color": COLOR_AXIS_Z, "width": 2.0, "xs": ts, "ys": rs},
            ])
