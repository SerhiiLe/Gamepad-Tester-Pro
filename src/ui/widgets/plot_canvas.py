"""
Lightweight Custom QPainter Chart Canvas
Replaces pyqtgraph PlotWidget for real-time time-series waveforms
(Stick Snapback oscilloscope, Polling Rate jitter, Gyroscope IMU angles).
"""

import math
from typing import Dict, List, Optional, Sequence, Tuple

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath


class TimeSeriesCanvas(QWidget):
    """High-speed custom QPainter 2D time-series oscilloscope / line chart."""

    def __init__(
        self,
        y_min: float = -1.0,
        y_max: float = 1.0,
        x_min: float = 0.0,
        x_max: float = 100.0,
        auto_y: bool = False,
        auto_x: bool = False,
        min_y_span: float = 0.0,
        show_legend: bool = False,
        x_label: str = "",
        y_label: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._y_min = y_min
        self._y_max = y_max
        self._x_min = x_min
        self._x_max = x_max
        self._auto_y = auto_y
        self._auto_x = auto_x
        self._min_y_span = min_y_span
        self._show_legend = show_legend
        self._x_label = x_label
        self._y_label = y_label

        self._ref_lines: List[Dict] = []
        self._series: List[Dict] = []

        self.setMinimumSize(180, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_labels(self, x_label: Optional[str] = None, y_label: Optional[str] = None):
        """Updates axis labels."""
        if x_label is not None:
            self._x_label = x_label
        if y_label is not None:
            self._y_label = y_label
        self.update()

    def set_y_range(self, y_min: float, y_max: float, auto: bool = False, min_span: float = 0.0):
        self._y_min = y_min
        self._y_max = y_max
        self._auto_y = auto
        self._min_y_span = min_span
        self.update()

    def set_x_range(self, x_min: float, x_max: float, auto: bool = False):
        self._x_min = x_min
        self._x_max = x_max
        self._auto_x = auto
        self.update()

    def set_ref_lines(self, lines: List[Dict]):
        """Sets horizontal reference lines: [{'y': float, 'color': str, 'width': float, 'dashed': bool}]."""
        self._ref_lines = list(lines)
        self.update()

    def set_series(self, series: List[Dict]):
        """Sets plotted curves: [{'name': str, 'color': str, 'width': float, 'xs': Seq, 'ys': Seq}]."""
        self._series = list(series)
        self.update()

    def clear_series(self):
        """Clears curve data while keeping axes and reference lines."""
        for s in self._series:
            s["xs"] = []
            s["ys"] = []
        self.update()

    def _compute_bounds(self) -> Tuple[float, float, float, float]:
        x_min, x_max = self._x_min, self._x_max
        y_min, y_max = self._y_min, self._y_max

        if self._auto_x:
            xs_all = [x for s in self._series for x in s.get("xs", []) if math.isfinite(x)]
            if len(xs_all) >= 2:
                x_min = min(xs_all)
                x_max = max(xs_all)
                if x_max - x_min < 1e-6:
                    x_max = x_min + 1.0

        if self._auto_y:
            ys_all = [y for s in self._series for y in s.get("ys", []) if math.isfinite(y)]
            for ref in self._ref_lines:
                if math.isfinite(ref["y"]):
                    ys_all.append(ref["y"])
            if ys_all:
                lo = min(0.0, min(ys_all))
                hi = max(ys_all)
                span = max(self._min_y_span, (hi - lo) * 1.12)
                y_min = lo
                y_max = lo + span

        if y_max - y_min < 1e-6:
            y_max = y_min + 1.0
        if x_max - x_min < 1e-6:
            x_max = x_min + 1.0
        return x_min, x_max, y_min, y_max

    @staticmethod
    def _fmt_tick(val: float, span: float) -> str:
        if span >= 20.0:
            return f"{val:.0f}"
        elif span >= 2.0:
            return f"{val:.1f}"
        return f"{val:.2f}"

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w = float(self.width())
        h = float(self.height())

        # Margins for Y ticks/label on left and X ticks/label at bottom
        m_left = 54.0 if self._y_label else 40.0
        m_right = 12.0
        m_top = 10.0
        m_bottom = 32.0 if self._x_label else 20.0

        plot_w = max(40.0, w - m_left - m_right)
        plot_h = max(30.0, h - m_top - m_bottom)
        plot_rect = QRectF(m_left, m_top, plot_w, plot_h)

        # Widget background & plot frame
        p.fillRect(QRectF(0.0, 0.0, w, h), QColor("#111827"))
        p.setPen(QPen(QColor("#1F2937"), 1.0))
        p.setBrush(QBrush(QColor("#111827")))
        p.drawRect(plot_rect)

        x_min, x_max, y_min, y_max = self._compute_bounds()
        x_span = x_max - x_min
        y_span = y_max - y_min

        def to_px(xv: float, yv: float) -> QPointF:
            px = m_left + ((xv - x_min) / x_span) * plot_w
            py = m_top + plot_h - ((yv - y_min) / y_span) * plot_h
            return QPointF(px, py)

        # 1. Grid lines and tick labels (5 ticks on Y, 5 ticks on X)
        tick_font = QFont("Segoe UI", 8)
        p.setFont(tick_font)
        grid_pen = QPen(QColor(148, 163, 184, 45), 1.0, Qt.DotLine)
        tick_pen = QPen(QColor("#94A3B8"))

        y_ticks = 4
        for i in range(y_ticks + 1):
            frac = i / float(y_ticks)
            yv = y_min + frac * y_span
            py = m_top + plot_h - frac * plot_h
            if 0 < i < y_ticks:
                p.setPen(grid_pen)
                p.drawLine(QPointF(m_left, py), QPointF(m_left + plot_w, py))
            p.setPen(tick_pen)
            lbl = self._fmt_tick(yv, y_span)
            p.drawText(QRectF(m_left - 42, py - 8, 38, 16), Qt.AlignRight | Qt.AlignVCenter, lbl)

        x_ticks = 4
        for i in range(x_ticks + 1):
            frac = i / float(x_ticks)
            xv = x_min + frac * x_span
            px = m_left + frac * plot_w
            if 0 < i < x_ticks:
                p.setPen(grid_pen)
                p.drawLine(QPointF(px, m_top), QPointF(px, m_top + plot_h))
            p.setPen(tick_pen)
            lbl = self._fmt_tick(xv, x_span)
            p.drawText(QRectF(px - 22, m_top + plot_h + 2, 44, 14), Qt.AlignCenter, lbl)

        # Axis titles
        title_font = QFont("Segoe UI", 8)
        p.setFont(title_font)
        p.setPen(QPen(QColor("#94A3B8")))
        if self._x_label:
            p.drawText(QRectF(m_left, h - 16, plot_w, 15), Qt.AlignCenter, self._x_label)

        if self._y_label:
            p.save()
            p.translate(12.0, m_top + plot_h / 2.0)
            p.rotate(-90.0)
            p.drawText(QRectF(-plot_h / 2.0, -10.0, plot_h, 16.0), Qt.AlignCenter, self._y_label)
            p.restore()

        # Clip interior for curves and reference lines
        p.save()
        p.setClipRect(plot_rect)

        # 2. Horizontal reference lines
        for ref in self._ref_lines:
            ry = ref["y"]
            if y_min <= ry <= y_max:
                py = m_top + plot_h - ((ry - y_min) / y_span) * plot_h
                style = Qt.DashLine if ref.get("dashed", False) else Qt.SolidLine
                p.setPen(QPen(QColor(ref.get("color", "#64748B")), ref.get("width", 1.0), style))
                p.drawLine(QPointF(m_left, py), QPointF(m_left + plot_w, py))

        # 3. Series curves
        for s in self._series:
            xs = s.get("xs", [])
            ys = s.get("ys", [])
            n = min(len(xs), len(ys))
            if n < 2:
                continue

            path = QPainterPath()
            started = False
            for i in range(n):
                xv = xs[i]
                yv = ys[i]
                if not (math.isfinite(xv) and math.isfinite(yv)):
                    started = False
                    continue
                pt = to_px(xv, yv)
                if not started:
                    path.moveTo(pt)
                    started = True
                else:
                    path.lineTo(pt)

            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(s.get("color", "#38BDF8")), s.get("width", 1.8), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(path)

        p.restore()

        # 4. Compact Legend inside top-right/top-left if enabled
        if self._show_legend and self._series:
            leg_x = m_left + 8.0
            leg_y = m_top + 6.0
            p.setFont(QFont("Segoe UI", 8, QFont.Bold))
            for s in self._series:
                name = s.get("name", "")
                if not name:
                    continue
                col = QColor(s.get("color", "#38BDF8"))
                p.setPen(QPen(col, 2.5))
                p.drawLine(QPointF(leg_x, leg_y + 6), QPointF(leg_x + 14, leg_y + 6))
                p.setPen(QPen(QColor("#CBD5E1")))
                p.drawText(QRectF(leg_x + 18, leg_y - 1, 70, 15), Qt.AlignLeft | Qt.AlignVCenter, name)
                leg_x += 78.0

        p.end()
