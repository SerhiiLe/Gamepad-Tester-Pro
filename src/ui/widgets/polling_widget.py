"""
Polling Rate & Jitter Waveform Widget (Custom QPainter)
Displays current communication bus frequency (Hz), inter-packet interval delta (dt),
and standard deviation jitter (ms).
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer

from .plot_canvas import TimeSeriesCanvas
from ...analysis.polling import PollingAnalyzer
from ...i18n import tr, i18n


class PollingWidget(QWidget):
    """Visualizes polling rate and bus timing stability."""

    def __init__(self, analyzer: PollingAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.lbl_title = QLabel(tr("polling_title"))
        self.lbl_title.setStyleSheet("color: #38BDF8; font-size: 13px;")
        header.addWidget(self.lbl_title)

        self.btn_reset = QPushButton(tr("btn_reset_stats"))
        self.btn_reset.setMinimumWidth(150)
        self.btn_reset.clicked.connect(self.reset_data)
        header.addWidget(self.btn_reset, alignment=Qt.AlignRight)
        layout.addLayout(header)

        # Big Digital Readout Banner
        banner = QHBoxLayout()
        self.lbl_hz = QLabel("<b>0.0 Hz</b>")
        self.lbl_hz.setStyleSheet("font-size: 32px; color: #10B981; font-weight: bold;")
        banner.addWidget(self.lbl_hz)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 13px; color: #94A3B8;")
        banner.addWidget(self.lbl_stats, alignment=Qt.AlignRight)
        layout.addLayout(banner)

        # Custom QPainter TimeSeriesCanvas for packet deltas
        self.plot = TimeSeriesCanvas(
            y_min=0.0,
            y_max=8.0,
            x_min=0.0,
            x_max=300.0,
            auto_y=True,
            auto_x=False,
            min_y_span=8.0,
            show_legend=False,
            x_label=tr("axis_polling_idx"),
            y_label=tr("axis_polling_dt"),
        )
        self.plot.set_ref_lines([
            {"y": 4.0, "color": "#10B981", "width": 1.5, "dashed": True},
        ])
        layout.addWidget(self.plot, stretch=1)

        self.lbl_note = QLabel(tr("polling_note"))
        self.lbl_note.setStyleSheet("font-size: 11px; color: #94A3B8;")
        self.lbl_note.setWordWrap(True)
        layout.addWidget(self.lbl_note)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)
        self.timer.start(50)

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        self.lbl_title.setText(tr("polling_title"))
        self.btn_reset.setText(tr("btn_reset_stats"))
        self.plot.set_labels(x_label=tr("axis_polling_idx"), y_label=tr("axis_polling_dt"))
        self.lbl_note.setText(tr("polling_note"))
        self.update_view()

    def reset_data(self):
        self.analyzer.reset()
        self.plot.set_series([])

    def update_view(self):
        hz = self.analyzer.current_hz if self.analyzer.current_hz > 0 else float(self.analyzer.nominal_hz)
        hz_unit = "Hz" if (i18n and i18n.current_lang == "EN") else "Гц"
        self.lbl_hz.setText(f"<b>{hz:.1f} {hz_unit}</b>")

        target_ms = self.analyzer.base_interval_ms if self.analyzer.base_interval_ms > 0 else 4.0

        # Color based on common standard rates
        if hz >= 900:
            color = "#10B981"  # 1000 Hz (GP2040-CE / Overclocked)
        elif hz >= 450:
            color = "#06B6D4"  # 500 Hz
        elif hz >= 200:
            color = "#3B82F6"  # 250 Hz (Standard Xbox 360 / DualSense BT)
        else:
            color = "#F59E0B"  # 125 Hz (Standard USB HID)

        self.lbl_hz.setStyleSheet(f"font-size: 32px; color: {color}; font-weight: bold;")
        self.plot.set_ref_lines([
            {"y": target_ms, "color": "#10B981", "width": 1.5, "dashed": True},
        ])

        conn_type = tr("polling_conn_wireless") if self.analyzer.is_wireless else tr("polling_conn_wired")
        drops_tag = f"{tr('polling_drops')} <b>{self.analyzer.dropped_packets_count}</b>" if self.analyzer.is_wireless else tr("polling_drops_excluded")

        self.lbl_stats.setText(
            f"{tr('polling_bus')} <b>{target_ms:.2f} ms</b> | "
            f"{tr('polling_jitter')} <b>{self.analyzer.jitter_stddev_ms:.3f} ms</b> | "
            f"{tr('polling_channel')} <b>{conn_type}</b> | "
            f"{tr('polling_dedup')} {self.analyzer.dedup_packets_count} | {drops_tag}"
        )

        # Plot last 300 normalized deltas (unfolded from deduplication multiples)
        plot_source = self.analyzer._norm_deltas_ms if self.analyzer._norm_deltas_ms else self.analyzer._deltas_ms
        if plot_source:
            deltas = list(plot_source)[-300:]
            self.plot.set_series([
                {"name": "dt", "color": "#0284C7", "width": 1.6, "xs": list(range(len(deltas))), "ys": deltas},
            ])
