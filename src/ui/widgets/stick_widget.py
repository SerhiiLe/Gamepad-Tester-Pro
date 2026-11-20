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


class StickWidget(QWidget):
    """Visualizes stick 2D deflection, guided testing stages, circularity, and noise."""

    TARGET_ZONES = [
        {"name": "Север (Вверх)",   "x": 0.0,   "y": 0.65,  "color": "#38BDF8"},
        {"name": "Восток (Вправо)", "x": 0.65,  "y": 0.0,   "color": "#34D399"},
        {"name": "Юг (Вниз)",       "x": 0.0,   "y": -0.65, "color": "#FBBF24"},
        {"name": "Запад (Влево)",   "x": -0.65, "y": 0.0,   "color": "#F472B6"},
    ]

    def __init__(self, analyzer: StickAnalyzer, title: str = "Левый стик (LS)", parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.title_str = title

        self.current_stage = 0
        self.target_zone_idx = 0
        self.target_hold_timer_frames = 0
        self.target_settling_frames = 0
        self.target_hold_required_frames = 45

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        box = QGroupBox(title)
        box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        l_box = QVBoxLayout(box)
        l_box.setContentsMargins(6, 6, 6, 6)
        l_box.setSpacing(4)

        # Header: Mode selector + Reset button
        header_layout = QHBoxLayout()
        self.combo_stages = QComboBox()
        self.combo_stages.addItems([
            "Свободный",
            "1: Центр",
            "2: Окружность",
            "3: В кружки (Шум)",
            "4: Snapback"
        ])
        self.combo_stages.currentIndexChanged.connect(self._on_stage_changed)
        header_layout.addWidget(self.combo_stages, stretch=1)

        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.setMinimumWidth(70)
        self.btn_reset.clicked.connect(self.reset_data)
        header_layout.addWidget(self.btn_reset)
        l_box.addLayout(header_layout)

        # Instructions / Hints Banner (Purely instructional text, without jumping numbers)
        self.banner = QFrame()
        self.banner.setStyleSheet("background-color: #1E293B; border: 1px solid #334155; border-radius: 4px;")
        l_banner = QHBoxLayout(self.banner)
        l_banner.setContentsMargins(4, 3, 4, 3)
        self.lbl_hint = QLabel("💡 Свободный ход (замеры отключены)")
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

        layout.addWidget(box)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)
        self.timer.start(16)

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
            # Hide and clear visual items so they don't appear in other modes
            self.circularity_track_curve.setData([], [])
            self.scatter_boundary.clear()
        else:
            # When entering Stage 2, start fresh circularity path
            self.analyzer.clear_circularity_track()
            self.circularity_track_curve.setData([], [])
            self.scatter_boundary.clear()

        # Clean static guidance prompts without fluctuating numbers
        if idx == 0:
            self.lbl_hint.setText("💡 Замер разрядности АЦП")
        elif idx == 1:
            self.lbl_hint.setText("🎯 Полностью отпустите стик для замера центра")
        elif idx == 2:
            self.lbl_hint.setText("🔄 Опишите полный круг по крайнему упору")
        elif idx == 3:
            zone_name = self.TARGET_ZONES[self.target_zone_idx]["name"]
            self.lbl_hint.setText(f"🎯 Направьте стик в кружок: {zone_name}")
        elif idx == 4:
            if self.analyzer.total_flicks_x < 5:
                self.lbl_hint.setText("⚡ 1. Отведите по горизонтали и отпустите")
            elif self.analyzer.total_flicks_y < 5:
                self.lbl_hint.setText("⚡ 2. Отведите по вертикали и отпустите")
            else:
                self.lbl_hint.setText("✅ 3. Тест завершён")

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
                    f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | АЦП: <b>~{self.analyzer.adc_bits:.0f} бит</b> (шаг: {self.analyzer.adc_step})"
                )
            else:
                self.lbl_metrics.setText(
                    f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | АЦП: <i>вращайте медленно...</i>"
                )
        elif self.current_stage == 1:
            drift = self.analyzer.center_drift_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Центр: <b>{drift:.1f}%</b>")
        elif self.current_stage == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            circ = self.analyzer.circularity_error_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Охват: <b>{cov:.0f}%</b> | Ошибка: <b>{circ:.1f}%</b>")
        elif self.current_stage == 3:
            noise = self.analyzer.peak_jitter_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Шум в точках: <b>{noise:.2f}%</b>")
        elif self.current_stage == 4:
            flicks = self.analyzer.total_flicks
            peak = self.analyzer.peak_snapback_pct
            self.lbl_metrics.setText(f"<b>X:</b>{x:+0.2f} <b>Y:</b>{y:+0.2f} | Сбросы: <b>{flicks}/10</b> | Пик: <b>{peak:.1f}%</b>")

        # Stable instructional transitions (No jumping numbers in hint banner)
        if self.current_stage == 1:
            if self.analyzer.center_tested:
                self.lbl_hint.setText("✅ Замер центра выполнен")
            else:
                self.lbl_hint.setText("🎯 Полностью отпустите стик для замера центра")

        elif self.current_stage == 2:
            cov = self.analyzer.get_circularity_coverage_pct()
            if cov >= 95.0:
                self.lbl_hint.setText("✅ Полный круг пройден!")
            else:
                self.lbl_hint.setText("🔄 Опишите полный круг по крайнему упору")

        elif self.current_stage == 3:
            if self.target_zone_idx < len(self.TARGET_ZONES):
                zone = self.TARGET_ZONES[self.target_zone_idx]
                self.active_target_scatter.setData([zone["x"]], [zone["y"]])
                dist = math.hypot(x - zone["x"], y - zone["y"])

                if dist < 0.16:
                    self.target_settling_frames += 1
                    if self.target_settling_frames > 10:
                        self.analyzer.is_inside_target = True
                        self.target_hold_timer_frames += 1
                        self.lbl_hint.setText(f"🎯 Идёт замер: {zone['name']}")
                    else:
                        self.lbl_hint.setText(f"⏳ Фиксация: {zone['name']}")

                    if self.target_hold_timer_frames >= self.target_hold_required_frames:
                        self.target_hold_timer_frames = 0
                        self.target_settling_frames = 0
                        self.target_zone_idx += 1
                        self.analyzer.is_inside_target = False
                        self.analyzer.clear_target_samples()
                        if self.target_zone_idx < len(self.TARGET_ZONES):
                            next_name = self.TARGET_ZONES[self.target_zone_idx]["name"]
                            self.lbl_hint.setText(f"🎯 Направьте стик в кружок: {next_name}")
                        else:
                            self.active_target_scatter.setVisible(False)
                            self.lbl_hint.setText("🎉 Все 4 зоны успешно пройдены!")
                else:
                    self.analyzer.is_inside_target = False
                    self.analyzer.clear_target_samples()
                    self.target_settling_frames = 0
                    self.target_hold_timer_frames = max(0, self.target_hold_timer_frames - 2)
                    self.lbl_hint.setText(f"🎯 Направьте стик в кружок: {zone['name']}")
            else:
                self.analyzer.is_inside_target = False
                self.active_target_scatter.setVisible(False)
                self.lbl_hint.setText("🎉 Все 4 зоны успешно пройдены!")

        elif self.current_stage == 4:
            if self.analyzer.total_flicks_x < 5:
                self.lbl_hint.setText("⚡ 1. Отведите по горизонтали и отпустите")
            elif self.analyzer.total_flicks_y < 5:
                self.lbl_hint.setText("⚡ 2. Отведите по вертикали и отпустите")
            else:
                self.lbl_hint.setText("✅ 3. Тест завершён")
