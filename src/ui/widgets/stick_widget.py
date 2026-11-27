"""
Interactive Stick Widget (Custom QPainter)
Provides guided testing stages with clean, stable instructional prompts:
- Stage 0: Свободный режим (Free Test)
- Stage 1: Проверка центра и дрейфа (Center & Drift)
- Stage 2: Обводка по окружности (Circularity 360°)
- Stage 3: Удержание в целевых кружках (Hold Targets for Noise measurement)
- Stage 4: Тест резкого отпускания (Snapback)
"""

import math
from typing import Dict, List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath

from ...analysis.sticks import StickAnalyzer
from ...i18n import tr


class StickCanvas(QWidget):
    """Square aspect-locked QPainter canvas rendering 2D stick deflection, gates, targets, and trails."""

    def __init__(self, analyzer: StickAnalyzer, target_zones: List[Dict], parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.target_zones = target_zones

        self.show_targets: bool = False
        self.active_target_idx: Optional[int] = None
        self.show_circularity: bool = False

        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        p.fillRect(QRectF(0.0, 0.0, w, h), QColor("#111827"))

        cx = w / 2.0
        cy = h / 2.0
        # World coordinate range [-1.25 .. +1.25] -> span = 2.5
        scale = max(20.0, min(w, h) / 2.5)

        def to_px(x: float, y: float) -> QPointF:
            return QPointF(cx + x * scale, cy - y * scale)

        # 1. Subtle background coordinate grid
        grid_pen = QPen(QColor(148, 163, 184, 35), 1.0, Qt.DotLine)
        p.setPen(grid_pen)
        for v in (-1.0, -0.5, 0.5, 1.0):
            p.drawLine(to_px(v, -1.18), to_px(v, 1.18))
            p.drawLine(to_px(-1.18, v), to_px(1.18, v))

        # Center axes
        p.setPen(QPen(QColor("#1F2937"), 1.2))
        p.drawLine(to_px(-1.15, 0.0), to_px(1.15, 0.0))
        p.drawLine(to_px(0.0, -1.15), to_px(0.0, 1.15))

        # 2. Reference Unit Circle (Radius 1.0) & Deadzone Circle (Radius 0.10)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#334155"), 1.5, Qt.DashLine))
        p.drawEllipse(QPointF(cx, cy), 1.0 * scale, 1.0 * scale)

        p.setPen(QPen(QColor("#475569"), 1.0, Qt.DotLine))
        p.drawEllipse(QPointF(cx, cy), 0.10 * scale, 0.10 * scale)

        # 3. Target zones (Stage 3 only)
        if self.show_targets:
            for idx, zone in enumerate(self.target_zones):
                tc = to_px(zone["x"], zone["y"])
                tr_px = 0.16 * scale
                if self.active_target_idx == idx:
                    p.setBrush(QBrush(QColor(56, 189, 248, 60)))
                    p.setPen(QPen(QColor("#38BDF8"), 2.0))
                    p.drawEllipse(tc, tr_px, tr_px)
                else:
                    p.setBrush(Qt.NoBrush)
                    p.setPen(QPen(QColor(zone["color"]), 1.5, Qt.DashLine))
                    p.drawEllipse(tc, tr_px, tr_px)

        # 4. Persistent circularity track & boundary dots (Stage 2 only)
        if self.show_circularity and self.analyzer.boundary_points:
            pts = self.analyzer.boundary_points
            path = QPainterPath()
            started = False
            valid_pts: List[QPointF] = []
            for px_val, py_val in pts:
                if math.isnan(px_val) or math.isnan(py_val):
                    started = False
                    continue
                pt = to_px(px_val, py_val)
                valid_pts.append(pt)
                if not started:
                    path.moveTo(pt)
                    started = True
                else:
                    path.lineTo(pt)

            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor("#10B981"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(16, 185, 129, 180)))
            for pt in valid_pts:
                p.drawEllipse(pt, 2.0, 2.0)

        # 5. Short moving trajectory trail (last 30 points)
        if len(self.analyzer._history) >= 2:
            hist = list(self.analyzer._history)[-30:]
            trail_path = QPainterPath()
            first = to_px(hist[0][1], hist[0][2])
            trail_path.moveTo(first)
            for item in hist[1:]:
                trail_path.lineTo(to_px(item[1], item[2]))
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(56, 189, 248, 160), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(trail_path)

        # 6. Current Position Dot
        pos = to_px(self.analyzer.curr_x, self.analyzer.curr_y)
        p.setBrush(QBrush(QColor("#38BDF8")))
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.drawEllipse(pos, 6.0, 6.0)

        p.end()


class StickWidget(QWidget):
    """Visualizes stick 2D deflection, guided testing stages, circularity, and noise."""

    stage_changed = Signal(int)

    TARGET_ZONES = [
        {"key": "zone_north", "x": 0.0,   "y": 0.65,  "color": "#38BDF8"},
        {"key": "zone_east",  "x": 0.65,  "y": 0.0,   "color": "#34D399"},
        {"key": "zone_south", "x": 0.0,   "y": -0.65, "color": "#FBBF24"},
        {"key": "zone_west",  "x": -0.65, "y": 0.0,   "color": "#F472B6"},
    ]

    def __init__(self, analyzer: StickAnalyzer, title: str = "Левый стик (LS)", title_key: str = "stick_left_name", parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.title_str = title
        self.title_key = title_key

        self.current_stage = 0
        self.target_zone_idx = 0
        self.target_hold_timer_frames = 0
        self.target_settling_frames = 0
        self.target_hold_required_frames = 45

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.box = QGroupBox(tr(self.title_key) if self.title_key else title)
        self.box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        l_box = QVBoxLayout(self.box)
        l_box.setContentsMargins(6, 6, 6, 6)
        l_box.setSpacing(4)

        # Header: Mode selector + Reset button
        header_layout = QHBoxLayout()
        self.combo_stages = QComboBox()
        self._populate_stages()
        self.combo_stages.currentIndexChanged.connect(self._on_stage_changed)
        header_layout.addWidget(self.combo_stages, stretch=1)

        self.btn_reset = QPushButton(tr("btn_reset"))
        self.btn_reset.setMinimumWidth(70)
        self.btn_reset.clicked.connect(self.reset_data)
        header_layout.addWidget(self.btn_reset)
        l_box.addLayout(header_layout)

        # Instructions / Hints Banner (Purely instructional text, without jumping numbers)
        self.banner = QFrame()
        self.banner.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 4px;")
        l_banner = QHBoxLayout(self.banner)
        l_banner.setContentsMargins(4, 3, 4, 3)
        self.lbl_hint = QLabel(tr("hint_free"))
        self.lbl_hint.setStyleSheet("font-size: 10px; color: #F8FAFC;")
        l_banner.addWidget(self.lbl_hint)
        l_box.addWidget(self.banner)

        # Custom QPainter Canvas
        self.canvas = StickCanvas(self.analyzer, self.TARGET_ZONES)
        l_box.addWidget(self.canvas, stretch=1)

        # Bottom Metrics Bar (Permanent location for live coordinate values)
        self.lbl_metrics = QLabel("X: 0.000 | Y: 0.000")
        self.lbl_metrics.setStyleSheet("font-size: 10px; color: #94A3B8; font-family: monospace;")
        l_box.addWidget(self.lbl_metrics)

        layout.addWidget(self.box)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)
        self.timer.start(16)

    def _populate_stages(self):
        curr = self.combo_stages.currentIndex() if self.combo_stages.count() > 0 else 0
        self.combo_stages.blockSignals(True)
        self.combo_stages.clear()
        self.combo_stages.addItems([
            tr("stage_free"),
            tr("stage_center"),
            tr("stage_circle"),
            tr("stage_targets"),
            tr("stage_snapback")
        ])
        if 0 <= curr < self.combo_stages.count():
            self.combo_stages.setCurrentIndex(curr)
        self.combo_stages.blockSignals(False)

    def retranslate_ui(self):
        """Retranslates all text elements to the active language."""
        if self.title_key:
            self.box.setTitle(tr(self.title_key))
        self._populate_stages()
        self.btn_reset.setText(tr("btn_reset"))
        self._update_hint_text()

    def set_stage(self, idx: int):
        """Sets active stage synchronized from peer stick widget without recursion."""
        if self.current_stage == idx:
            return
        if 0 <= idx < self.combo_stages.count():
            self.combo_stages.blockSignals(True)
            self.combo_stages.setCurrentIndex(idx)
            self.combo_stages.blockSignals(False)
            self._on_stage_changed(idx, emit_signal=False)

    def _on_stage_changed(self, idx: int, emit_signal: bool = True):
        self.current_stage = idx
        self.analyzer.active_stage = idx
        self.analyzer.is_inside_target = False
        self.analyzer._tracking_release = False
        self.analyzer.clear_target_samples()
        self.target_hold_timer_frames = 0
        self.target_settling_frames = 0
        self.target_zone_idx = 0

        show_targets = (idx == 3)
        self.canvas.show_targets = show_targets
        self.canvas.active_target_idx = 0 if show_targets else None

        is_circ = (idx == 2)
        self.canvas.show_circularity = is_circ
        if is_circ:
            self.analyzer.clear_circularity_track()

        self.canvas.update()
        self._update_hint_text()
        if emit_signal:
            self.stage_changed.emit(idx)

    def _update_hint_text(self):
        idx = self.current_stage
        if idx == 0:
            self.lbl_hint.setText(tr("hint_free"))
        elif idx == 1:
            if self.analyzer.center_tested:
                self.lbl_hint.setText(tr("hint_center_done", drift=self.analyzer.center_drift_pct))
            else:
                self.lbl_hint.setText(tr("hint_center"))
        elif idx == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            if cov >= 95.0:
                self.lbl_hint.setText(tr("hint_circle_done", circ=self.analyzer.circularity_error_pct))
            else:
                self.lbl_hint.setText(tr("hint_circle"))
        elif idx == 3:
            if self.target_zone_idx >= len(self.TARGET_ZONES):
                self.lbl_hint.setText(tr("hint_targets_done", noise=self.analyzer.peak_jitter_pct))
            else:
                zone_key = self.TARGET_ZONES[self.target_zone_idx]["key"]
                self.lbl_hint.setText(tr("hint_targets_move", zone=tr(zone_key)))
        elif idx == 4:
            if self.analyzer.total_flicks_x < 6:
                self.lbl_hint.setText(tr("hint_snapback_x"))
            elif self.analyzer.total_flicks_y < 6:
                self.lbl_hint.setText(tr("hint_snapback_y"))
            else:
                self.lbl_hint.setText(tr("hint_snapback_done", x_rate=int(self.analyzer.snapback_rate_x_pct), y_rate=int(self.analyzer.snapback_rate_y_pct)))

    def reset_data(self):
        self.analyzer.reset()
        self.target_hold_timer_frames = 0
        self.target_settling_frames = 0
        self.target_zone_idx = 0
        self._on_stage_changed(self.current_stage, emit_signal=False)

    def update_view(self):
        x, y = self.analyzer.curr_x, self.analyzer.curr_y

        # Permanent metrics line at the bottom
        if self.current_stage == 0:
            if self.analyzer.adc_bits > 0:
                self.lbl_metrics.setText(
                    f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | {tr('metric_adc')}: <b>~{self.analyzer.adc_bits:.0f} {tr('metric_bit')}</b> ({tr('metric_step')}: {self.analyzer.adc_step})"
                )
            else:
                self.lbl_metrics.setText(
                    f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | {tr('metric_adc')}: <i>{tr('metric_adc_hint')}</i>"
                )
        elif self.current_stage == 1:
            drift = self.analyzer.center_drift_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | {tr('metric_center')}: <b>{drift:.1f}%</b>")
        elif self.current_stage == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            circ = self.analyzer.circularity_error_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | {tr('metric_coverage')}: <b>{cov:.0f}%</b> | {tr('metric_error')}: <b>{circ:.1f}%</b>")
        elif self.current_stage == 3:
            noise = self.analyzer.peak_jitter_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | {tr('metric_noise')}: <b>{noise:.2f}%</b>")
        elif self.current_stage == 4:
            flicks = self.analyzer.total_flicks
            peak = self.analyzer.peak_snapback_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | {tr('metric_flicks')}: <b>{flicks}/12</b> | {tr('metric_peak')}: <b>{peak:.1f}%</b>")

        # Stable instructional transitions
        if self.current_stage == 1:
            if self.analyzer.center_tested:
                self.lbl_hint.setText(tr("hint_center_done", drift=self.analyzer.center_drift_pct))
            else:
                self.lbl_hint.setText(tr("hint_center"))

        elif self.current_stage == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            if cov >= 95.0:
                self.lbl_hint.setText(tr("hint_circle_done", circ=self.analyzer.circularity_error_pct))
            else:
                self.lbl_hint.setText(tr("hint_circle"))

        elif self.current_stage == 3:
            if self.target_zone_idx < len(self.TARGET_ZONES):
                zone = self.TARGET_ZONES[self.target_zone_idx]
                self.canvas.active_target_idx = self.target_zone_idx
                dist = math.hypot(x - zone["x"], y - zone["y"])

                zone_title = tr(zone["key"])
                if dist < 0.16:
                    self.target_settling_frames += 1
                    if self.target_settling_frames > 10:
                        self.analyzer.is_inside_target = True
                        self.target_hold_timer_frames += 1
                        self.lbl_hint.setText(tr("hint_targets_measuring", zone=zone_title))
                    else:
                        self.lbl_hint.setText(tr("hint_targets_settling", zone=zone_title))

                    if self.target_hold_timer_frames >= self.target_hold_required_frames:
                        self.target_hold_timer_frames = 0
                        self.target_settling_frames = 0
                        self.target_zone_idx += 1
                        self.analyzer.is_inside_target = False
                        self.analyzer.clear_target_samples()
                        if self.target_zone_idx < len(self.TARGET_ZONES):
                            self.canvas.active_target_idx = self.target_zone_idx
                            next_name = tr(self.TARGET_ZONES[self.target_zone_idx]["key"])
                            self.lbl_hint.setText(tr("hint_targets_move", zone=next_name))
                        else:
                            self.canvas.active_target_idx = None
                            self.lbl_hint.setText(tr("hint_targets_done", noise=self.analyzer.peak_jitter_pct))
                else:
                    self.analyzer.is_inside_target = False
                    self.analyzer.clear_target_samples()
                    self.target_settling_frames = 0
                    self.target_hold_timer_frames = max(0, self.target_hold_timer_frames - 2)
                    self.lbl_hint.setText(tr("hint_targets_move", zone=zone_title))
            else:
                self.analyzer.is_inside_target = False
                self.canvas.active_target_idx = None
                self.lbl_hint.setText(tr("hint_targets_done", noise=self.analyzer.peak_jitter_pct))

        elif self.current_stage == 4:
            if self.analyzer.total_flicks_x < 6:
                self.lbl_hint.setText(tr("hint_snapback_x"))
            elif self.analyzer.total_flicks_y < 6:
                self.lbl_hint.setText(tr("hint_snapback_y"))
            else:
                self.lbl_hint.setText(tr("hint_snapback_done", x_rate=int(self.analyzer.snapback_rate_x_pct), y_rate=int(self.analyzer.snapback_rate_y_pct)))

        self.canvas.update()
