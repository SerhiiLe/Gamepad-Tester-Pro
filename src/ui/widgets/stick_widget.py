"""
Interactive Stick Widget (PyQtGraph)
Provides guided testing stages with clean, stable instructional prompts:
- Stage 0: Свободный режим (Free Test)
- Stage 1: Проверка центра и дрейфа (Center & Drift)
- Stage 2: Обводка по окружности (Circularity 360°)
- Stage 3: Удержание в целевых кружках (Hold Targets for Noise measurement)
- Stage 4: Тест резкого отпускания (Snapback)
"""

import math
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg

from ...analysis.sticks import StickAnalyzer
from ...i18n import tr


class StickWidget(QWidget):
    """Visualizes stick 2D deflection, guided testing stages, circularity, and noise."""

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

        # PyQtGraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setXRange(-1.25, 1.25)
        self.plot_widget.setYRange(-1.25, 1.25)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setBackground('#111827')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.hideAxis('left')

        # Reference Unit Circle (Radius 1.0)
        theta = np.linspace(0, 2 * np.pi, 150)
        self.circle_item = self.plot_widget.plot(np.cos(theta), np.sin(theta), pen=pg.mkPen('#334155', width=1.5, style=Qt.DashLine))

        # Deadzone Circle (Radius 0.10)
        self.plot_widget.plot(0.10 * np.cos(theta), 0.10 * np.sin(theta), pen=pg.mkPen('#475569', width=1, style=Qt.DotLine))

        # Center axes
        self.plot_widget.plot([-1.15, 1.15], [0, 0], pen=pg.mkPen('#1F2937', width=1))
        self.plot_widget.plot([0, 0], [-1.15, 1.15], pen=pg.mkPen('#1F2937', width=1))

        # Target zones for Stage 3
        self.target_circles_plots = []
        for zone in self.TARGET_ZONES:
            tx = zone["x"] + 0.16 * np.cos(theta)
            ty = zone["y"] + 0.16 * np.sin(theta)
            curve = self.plot_widget.plot(tx, ty, pen=pg.mkPen(zone["color"], width=1.5, style=Qt.DashLine))
            curve.setVisible(False)
            self.target_circles_plots.append(curve)

        self.active_target_scatter = pg.ScatterPlotItem(size=32, brush=pg.mkBrush(56, 189, 248, 60), pen=pg.mkPen('#38BDF8', width=2))
        self.plot_widget.addItem(self.active_target_scatter)
        self.active_target_scatter.setVisible(False)

        # Boundary Points Scatter (Circularity samples)
        self.scatter_boundary = pg.ScatterPlotItem(size=4, brush=pg.mkBrush(16, 185, 129, 180), pen=None)
        self.plot_widget.addItem(self.scatter_boundary)
        self.scatter_boundary.setVisible(False)

        # Circularity Track Curve (Continuous perimeter line for Stage 2)
        self.circularity_track_curve = self.plot_widget.plot([], [], pen=pg.mkPen('#10B981', width=2.5), connect='finite')
        self.circularity_track_curve.setVisible(False)

        # Trajectory trail (Short moving history trail for all modes)
        self.trail_curve = self.plot_widget.plot([], [], pen=pg.mkPen(56, 189, 248, 160, width=1.5))

        # Current Position Dot
        self.pos_dot = self.plot_widget.plot([0], [0], pen=None, symbol='o', symbolSize=12, symbolBrush='#38BDF8', symbolPen=pg.mkPen('#FFFFFF', width=1.5))

        l_box.addWidget(self.plot_widget, stretch=1)

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

    def _on_stage_changed(self, idx: int):
        self.current_stage = idx
        self.analyzer.active_stage = idx
        self.analyzer.is_inside_target = False
        self.analyzer._tracking_release = False
        self.analyzer.clear_target_samples()
        self.target_hold_timer_frames = 0
        self.target_settling_frames = 0
        self.target_zone_idx = 0

        show_targets = (idx == 3)
        for p in self.target_circles_plots:
            p.setVisible(show_targets)
        self.active_target_scatter.setVisible(show_targets)

        # Stage 2 Circularity track visibility: strictly visible only in Stage 2!
        is_circ = (idx == 2)
        self.circularity_track_curve.setVisible(is_circ)
        self.scatter_boundary.setVisible(is_circ)
        if not is_circ:
            self.circularity_track_curve.setData([], [])
            self.scatter_boundary.clear()
        else:
            self.analyzer.clear_circularity_track()
            self.circularity_track_curve.setData([], [])
            self.scatter_boundary.clear()

        self._update_hint_text()

    def _update_hint_text(self):
        idx = self.current_stage
        if idx == 0:
            self.lbl_hint.setText(tr("hint_free"))
        elif idx == 1:
            self.lbl_hint.setText(tr("hint_center"))
        elif idx == 2:
            self.lbl_hint.setText(tr("hint_circle"))
        elif idx == 3:
            zone_key = self.TARGET_ZONES[self.target_zone_idx]["key"] if self.target_zone_idx < len(self.TARGET_ZONES) else "zone_north"
            self.lbl_hint.setText(f"🎯 {tr(zone_key)}")
        elif idx == 4:
            if self.analyzer.total_flicks_x < 5:
                self.lbl_hint.setText(tr("hint_snapback_x", done=self.analyzer.total_flicks_x, total=5))
            elif self.analyzer.total_flicks_y < 5:
                self.lbl_hint.setText(tr("hint_snapback_y", done=self.analyzer.total_flicks_y, total=5))
            else:
                self.lbl_hint.setText(tr("hint_snapback_done", x_rate=int(self.analyzer.snapback_rate_x_pct), y_rate=int(self.analyzer.snapback_rate_y_pct)))

    def reset_data(self):
        self.analyzer.reset()
        self.circularity_track_curve.setData([], [])
        self.scatter_boundary.clear()
        self.trail_curve.setData([], [])
        self.target_hold_timer_frames = 0
        self.target_settling_frames = 0
        self.target_zone_idx = 0
        self._on_stage_changed(self.current_stage)

    def update_view(self):
        x, y = self.analyzer.curr_x, self.analyzer.curr_y
        self.pos_dot.setData([x], [y])

        # Trajectory trail (Short moving history trail for all modes)
        if len(self.analyzer._history) >= 2:
            hist = list(self.analyzer._history)[-30:]
            tx = [p[1] for p in hist]
            ty = [p[2] for p in hist]
            self.trail_curve.setData(tx, ty)

        # Persistent circularity track & boundary dots (Stage 2 only)
        if self.current_stage == 2:
            pts = self.analyzer.boundary_points
            if pts:
                bx = [p[0] for p in pts]
                by = [p[1] for p in pts]
                self.circularity_track_curve.setData(bx, by)
                valid_bx = [p[0] for p in pts if not math.isnan(p[0])]
                valid_by = [p[1] for p in pts if not math.isnan(p[1])]
                self.scatter_boundary.setData(valid_bx, valid_by)

        # Permanent metrics line at the bottom
        if self.current_stage == 0:
            if self.analyzer.adc_bits > 0:
                self.lbl_metrics.setText(
                    f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | ADC: <b>~{self.analyzer.adc_bits:.0f} bit</b> (step: {self.analyzer.adc_step})"
                )
            else:
                self.lbl_metrics.setText(
                    f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | ADC: <i>...</i>"
                )
        elif self.current_stage == 1:
            drift = self.analyzer.center_drift_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Center: <b>{drift:.1f}%</b>")
        elif self.current_stage == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            circ = self.analyzer.circularity_error_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Cov: <b>{cov:.0f}%</b> | Err: <b>{circ:.1f}%</b>")
        elif self.current_stage == 3:
            noise = self.analyzer.peak_jitter_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Noise: <b>{noise:.2f}%</b>")
        elif self.current_stage == 4:
            flicks = self.analyzer.total_flicks
            peak = self.analyzer.peak_snapback_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Flicks: <b>{flicks}/10</b> | Peak: <b>{peak:.1f}%</b>")

        # Stable instructional transitions
        if self.current_stage == 1:
            if self.analyzer.center_tested:
                self.lbl_hint.setText("✅ " + tr("stage_center"))
            else:
                self.lbl_hint.setText(tr("hint_center"))

        elif self.current_stage == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            if cov >= 95.0:
                self.lbl_hint.setText("✅ " + tr("stage_circle"))
            else:
                self.lbl_hint.setText(tr("hint_circle"))

        elif self.current_stage == 3:
            if self.target_zone_idx < len(self.TARGET_ZONES):
                zone = self.TARGET_ZONES[self.target_zone_idx]
                self.active_target_scatter.setData([zone["x"]], [zone["y"]])
                dist = math.hypot(x - zone["x"], y - zone["y"])

                zone_title = tr(zone["key"])
                if dist < 0.16:
                    self.target_settling_frames += 1
                    if self.target_settling_frames > 10:
                        self.analyzer.is_inside_target = True
                        self.target_hold_timer_frames += 1
                        self.lbl_hint.setText(f"🎯 {zone_title}")
                    else:
                        self.lbl_hint.setText(f"⏳ {zone_title}")

                    if self.target_hold_timer_frames >= self.target_hold_required_frames:
                        self.target_hold_timer_frames = 0
                        self.target_settling_frames = 0
                        self.target_zone_idx += 1
                        self.analyzer.is_inside_target = False
                        self.analyzer.clear_target_samples()
                        if self.target_zone_idx < len(self.TARGET_ZONES):
                            next_name = tr(self.TARGET_ZONES[self.target_zone_idx]["key"])
                            self.lbl_hint.setText(f"🎯 {next_name}")
                        else:
                            self.active_target_scatter.setVisible(False)
                            self.lbl_hint.setText("🎉 OK")
                else:
                    self.analyzer.is_inside_target = False
                    self.analyzer.clear_target_samples()
                    self.target_settling_frames = 0
                    self.target_hold_timer_frames = max(0, self.target_hold_timer_frames - 2)
                    self.lbl_hint.setText(f"🎯 {zone_title}")
            else:
                self.analyzer.is_inside_target = False
                self.active_target_scatter.setVisible(False)
                self.lbl_hint.setText("🎉 OK")

        elif self.current_stage == 4:
            if self.analyzer.total_flicks_x < 5:
                self.lbl_hint.setText(tr("hint_snapback_x", done=self.analyzer.total_flicks_x, total=5))
            elif self.analyzer.total_flicks_y < 5:
                self.lbl_hint.setText(tr("hint_snapback_y", done=self.analyzer.total_flicks_y, total=5))
            else:
                self.lbl_hint.setText(tr("hint_snapback_done", x_rate=int(self.analyzer.snapback_rate_x_pct), y_rate=int(self.analyzer.snapback_rate_y_pct)))
