"""
Polling Rate & Jitter Waveform Widget (PyQtGraph)
Displays current communication bus frequency (Hz), inter-packet interval delta (dt),
and standard deviation jitter (ms).
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
import pyqtgraph as pg

from ...analysis.polling import PollingAnalyzer


class PollingWidget(QWidget):
    """Visualizes polling rate and bus timing stability."""

    def __init__(self, analyzer: PollingAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        header = QHBoxLayout()
        lbl = QLabel("<b>Частота опроса (Polling Rate) и стабильность шины</b>")
        lbl.setStyleSheet("color: #38BDF8; font-size: 13px;")
        header.addWidget(lbl)

        btn_reset = QPushButton("Сбросить статистику")
        btn_reset.setMinimumWidth(180)
        btn_reset.clicked.connect(self.reset_data)
        header.addWidget(btn_reset, alignment=Qt.AlignRight)
        layout.addLayout(header)

        # Big Digital Readout Banner
        banner = QHBoxLayout()
        self.lbl_hz = QLabel("<b>0.0 Гц</b>")
        self.lbl_hz.setStyleSheet("font-size: 32px; color: #10B981; font-weight: bold;")
        banner.addWidget(self.lbl_hz)

        self.lbl_stats = QLabel("Интервал dt: 0.00 мс | Джиттер (StdDev): 0.000 мс | Пакетов: 0")
        self.lbl_stats.setStyleSheet("font-size: 13px; color: #94A3B8;")
        banner.addWidget(self.lbl_stats, alignment=Qt.AlignRight)
        layout.addLayout(banner)

        # PyQtGraph Plot for packet deltas
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#111827')
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel('left', 'Интервал Δt между пакетами (мс)')
        self.plot.setLabel('bottom', 'Индекс пакета опроса')
        self.plot.setYRange(0, 16)

        # Reference target line (e.g. 1.0 ms for 1000 Hz, 4.0 ms for 250 Hz, 8.0 ms for 125 Hz)
        self.target_line = self.plot.plot([-100, 1000], [1.0, 1.0], pen=pg.mkPen('#10B981', width=1, style=Qt.DashLine))

        self.curve = self.plot.plot([], [], pen=pg.mkPen('#0284C7', width=1.5))
        layout.addWidget(self.plot)

        self.lbl_note = QLabel("ℹ️ <b>Стабильность опроса:</b> На графике отображается время (мс) между пакетами опроса контроллера. Ровная горизонтальная линия означает стабильную передачу без джиттера.")
        self.lbl_note.setStyleSheet("font-size: 11px; color: #94A3B8;")
        layout.addWidget(self.lbl_note)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)
        self.timer.start(50)

    def reset_data(self):
        self.analyzer.reset()
        self.curve.setData([], [])

    def update_view(self):
        hz = self.analyzer.current_hz
        self.lbl_hz.setText(f"<b>{hz:.1f} Гц</b>")

        # Color based on common standard rates
        if hz >= 900:
            color = "#10B981"  # 1000 Hz (GP2040-CE / Overclocked)
            target_ms = 1.0
        elif hz >= 450:
            color = "#06B6D4"  # 500 Hz
            target_ms = 2.0
        elif hz >= 200:
            color = "#3B82F6"  # 250 Hz (DualSense BT default)
            target_ms = 4.0
        else:
            color = "#F59E0B"  # 125 Hz (Standard Xbox / generic)
            target_ms = 8.0

        self.lbl_hz.setStyleSheet(f"font-size: 32px; color: {color}; font-weight: bold;")
        self.target_line.setData([-100, 1000], [target_ms, target_ms])

        self.lbl_stats.setText(
            f"Интервал dt: <b>{self.analyzer.avg_delta_ms:.2f} мс</b> | "
            f"Джиттер: <b>{self.analyzer.jitter_stddev_ms:.3f} мс</b> | "
            f"Пакетов: {self.analyzer.packet_count} (Пропусков: {self.analyzer.dropped_packets_count})"
        )

        # Plot last 150 deltas
        if self.analyzer._deltas_ms:
            deltas = list(self.analyzer._deltas_ms)[-150:]
            self.curve.setData(list(range(len(deltas))), deltas)
            # Dynamic Y range
            max_d = max(deltas)
            self.plot.setYRange(0, max(10, max_d * 1.3))
