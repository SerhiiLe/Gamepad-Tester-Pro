"""
Stick Motion & Snapback Oscilloscope Widget (PyQtGraph)
Plots stick deflection vs time across a rolling ~100 ms window (100 points)
to visually capture real-time stick trail, release dynamics, and snapback.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg

from ...analysis.sticks import StickAnalyzer
from ...i18n import tr


class StickOscilloscopeWidget(QWidget):
    """Real-time oscilloscope displaying rolling stick movement waveform (~100 ms) and snapback."""

    def __init__(self, analyzer: StickAnalyzer, title: str = "Левый стик (LS)", title_key: str = "stick_left_name", parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.title_str = title
        self.title_key = title_key
        self._last_peak = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        t_name = tr(self.title_key) if self.title_key else title
        self.box = QGroupBox(tr("snapback_box_title", title=t_name))
        self.box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        l_box = QVBoxLayout(self.box)
        l_box.setContentsMargins(6, 6, 6, 6)
        l_box.setSpacing(4)

        # Header with status and clear button
        header = QHBoxLayout()
        self.lbl_peak = QLabel(tr("snapback_peak_label", peak=0.0))
        self.lbl_peak.setStyleSheet("font-size: 11px; color: #94A3B8;")
        header.addWidget(self.lbl_peak)

        self.btn_clear = QPushButton(tr("btn_reset"))
        self.btn_clear.setMinimumWidth(80)
        self.btn_clear.clicked.connect(self.clear_plot)
        header.addWidget(self.btn_clear, alignment=Qt.AlignRight)
        l_box.addLayout(header)

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#111827')
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setYRange(-1.15, 1.15)
        self.plot.setXRange(0, 100)
        self.plot.setLabel('left', tr("snapback_axis_y"), units='')
        self.plot.setLabel('bottom', tr("snapback_axis_x"))

        # Center line (Zero)
        self.plot.plot([0, 100], [0, 0], pen=pg.mkPen('#64748B', width=1.5))
        # Snapback tolerance (+- 0.05 / 5%)
        self.plot.plot([0, 100], [0.05, 0.05], pen=pg.mkPen('#EF4444', width=1, style=Qt.DashLine))
        self.plot.plot([0, 100], [-0.05, -0.05], pen=pg.mkPen('#EF4444', width=1, style=Qt.DashLine))

        # Real-time curves: X (cyan) and Y (emerald green)
        self.curve_x = self.plot.plot([], [], pen=pg.mkPen('#38BDF8', width=2), name="X")
        self.curve_y = self.plot.plot([], [], pen=pg.mkPen('#34D399', width=1.8), name="Y")
        l_box.addWidget(self.plot)

        layout.addWidget(self.box)

        self._last_event_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(25)

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        t_name = tr(self.title_key) if self.title_key else self.title_str
        self.box.setTitle(tr("snapback_box_title", title=t_name))
        self.btn_clear.setText(tr("btn_reset"))
        self.plot.setLabel('left', tr("snapback_axis_y"))
        self.plot.setLabel('bottom', tr("snapback_axis_x"))
        self.lbl_peak.setText(tr("snapback_peak_label", peak=self._last_peak))

    def clear_plot(self):
        self.curve_x.setData([], [])
        self.curve_y.setData([], [])
        self._last_peak = 0.0
        self.lbl_peak.setText(tr("snapback_peak_label", peak=0.0))
        self.lbl_peak.setStyleSheet("font-size: 11px; color: #94A3B8;")
        self._last_event_count = 0

    def update_plot(self):
        # Real-time rolling trail over the last 100 points (~100 ms at 1000 Hz)
        if len(self.analyzer._history) >= 2:
            hist = list(self.analyzer._history)[-100:]
            xs = [p[1] for p in hist]
            ys = [p[2] for p in hist]
            idx = list(range(len(xs)))
            self.curve_x.setData(idx, xs)
            self.curve_y.setData(idx, ys)

        # Check latest snapback event
        events = self.analyzer.snapback_events
        if events:
            latest = events[-1]
            pct = latest.overshoot_peak * 100.0
            self._last_peak = pct
            color = "#EF4444" if pct > 5.0 else "#10B981"
            self.lbl_peak.setText(f"{tr('snapback_peak_label', peak=pct)} ({latest.axis_name})")
            self.lbl_peak.setStyleSheet(f"font-size: 11px; color: {color};")
        else:
            self._last_peak = 0.0
            self.lbl_peak.setText(tr("snapback_peak_label", peak=0.0))
            self.lbl_peak.setStyleSheet("font-size: 11px; color: #94A3B8;")
