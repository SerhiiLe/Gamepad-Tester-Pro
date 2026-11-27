"""
Stick Motion & Snapback Oscilloscope Widget (Custom QPainter)
Plots stick deflection vs time across a rolling ~100 ms window (100 points)
to visually capture real-time stick trail, release dynamics, and snapback.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, QTimer

from .plot_canvas import TimeSeriesCanvas
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

        # Custom QPainter TimeSeriesCanvas
        self.plot = TimeSeriesCanvas(
            y_min=-1.15,
            y_max=1.15,
            x_min=0.0,
            x_max=100.0,
            auto_y=False,
            auto_x=False,
            show_legend=True,
            x_label=tr("snapback_axis_x"),
            y_label=tr("snapback_axis_y"),
        )
        self.plot.set_ref_lines([
            {"y": 0.0, "color": "#64748B", "width": 1.3, "dashed": False},
            {"y": 0.05, "color": "#EF4444", "width": 1.0, "dashed": True},
            {"y": -0.05, "color": "#EF4444", "width": 1.0, "dashed": True},
        ])
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
        self.plot.set_labels(x_label=tr("snapback_axis_x"), y_label=tr("snapback_axis_y"))
        self.lbl_peak.setText(tr("snapback_peak_label", peak=self._last_peak))

    def clear_plot(self):
        self.plot.set_series([])
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
            self.plot.set_series([
                {"name": "X", "color": "#38BDF8", "width": 2.0, "xs": idx, "ys": xs},
                {"name": "Y", "color": "#34D399", "width": 1.8, "xs": idx, "ys": ys},
            ])

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
