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
        btn_reset.setMinimumWidth(150)
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
        self.plot.setLabel('bottom', 'Индекс пакета опроса (история шины)')
        self.plot.setXRange(0, 300, padding=0.01)
        self.plot.setYRange(0, 8)

        # Reference target line (e.g. 1.0 ms for 1000 Hz, 4.0 ms for 250 Hz, 8.0 ms for 125 Hz)
        self.target_line = self.plot.plot([0, 300], [4.0, 4.0], pen=pg.mkPen('#10B981', width=1.5, style=Qt.DashLine))

        self.curve = self.plot.plot([], [], pen=pg.mkPen('#0284C7', width=1.5))
        layout.addWidget(self.plot)

        self.lbl_note = QLabel("ℹ️ <b>Стабильность шины:</b> Вращайте стики по кругу для замера частоты. Для проводных геймпадов отсечение одинаковых пакетов драйвером Linux является штатным (не потеря кадров). Осциллограф отображает выровненный интервал шины и реальный аппаратный джиттер.")
        self.lbl_note.setStyleSheet("font-size: 11px; color: #94A3B8;")
        self.lbl_note.setWordWrap(True)
        layout.addWidget(self.lbl_note)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_view)
        self.timer.start(50)

    def reset_data(self):
        self.analyzer.reset()
        self.curve.setData([], [])
        self.plot.setXRange(0, 300, padding=0.01)

    def update_view(self):
        hz = self.analyzer.current_hz if self.analyzer.current_hz > 0 else float(self.analyzer.nominal_hz)
        self.lbl_hz.setText(f"<b>{hz:.1f} Гц</b>")

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
        self.target_line.setData([0, 300], [target_ms, target_ms])

        conn_type = "Беспроводной" if self.analyzer.is_wireless else "Проводной USB"
        drops_tag = f"Потерь: <b>{self.analyzer.dropped_packets_count}</b>" if self.analyzer.is_wireless else "Потери исключены"

        self.lbl_stats.setText(
            f"Шина: <b>{target_ms:.2f} мс</b> | "
            f"Джиттер: <b>{self.analyzer.jitter_stddev_ms:.3f} мс</b> | "
            f"Канал: <b>{conn_type}</b> | "
            f"Отсечено дублей: {self.analyzer.dedup_packets_count} | {drops_tag}"
        )

        # Plot last 300 normalized deltas (unfolded from deduplication multiples)
        plot_source = self.analyzer._norm_deltas_ms if self.analyzer._norm_deltas_ms else self.analyzer._deltas_ms
        if plot_source:
            deltas = list(plot_source)[-300:]
            self.curve.setData(list(range(len(deltas))), deltas)

            # Proportional vertical range around nominal target
            if target_ms <= 1.5:
                y_max = 3.0   # 1000 Hz (1 ms centered)
            elif target_ms <= 3.0:
                y_max = 5.0   # 500 Hz (2 ms centered)
            elif target_ms <= 6.0:
                y_max = 8.0   # 250 Hz / 200 Hz (4-5 ms centered)
            else:
                y_max = 16.0  # 125 Hz (8 ms centered)

            max_d = max(deltas)
            self.plot.setYRange(0, max(y_max, max_d * 1.25))
            self.plot.setXRange(0, 300, padding=0.01)
