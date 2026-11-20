"""
Stick Anomalies & Metrics Table Widget
Displays side-by-side diagnostic metrics with separate tracking for axes X and Y,
enabling diagnosis of individual potentiometers, Hall sensors, and centering springs.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...analysis.sticks import StickAnalyzer


class StickAnomaliesWidget(QWidget):
    """Real-time comparative table of anomalous stick metrics with X/Y breakdown and rich tooltips."""

    ROW_DEFINITIONS = [
        (
            "Дрейф центра (Ось X)",
            "< 5.0%",
            "<b>Дрейф нуля по горизонтальной оси X:</b><br>"
            "Смещение стика влево/вправо в положении покоя.<br>"
            "<i>Допуск:</i> менее 5.0%.<br>"
            "<i>Замеряется в:</i> Этап 1 (Центр).<br>"
            "<b>Причина:</b> износ резистивного слоя потенциометра X (вытирание графитовой дорожки в районе нуля, окисление или люфт бегунка) либо сбитая калибровка нуля АЦП."
        ),
        (
            "Дрейф центра (Ось Y)",
            "< 5.0%",
            "<b>Дрейф нуля по вертикальной оси Y:</b><br>"
            "Смещение стика вверх/вниз в положении покоя.<br>"
            "<i>Допуск:</i> менее 5.0%.<br>"
            "<i>Замеряется в:</i> Этап 1 (Центр).<br>"
            "<b>Причина:</b> износ резистивного слоя потенциометра Y (вытирание графитовой дорожки в районе нуля, окисление или люфт бегунка) либо сбитая калибровка нуля АЦП."
        ),
        (
            "Ошибка круга (360°)",
            "< 8.0%",
            "<b>Ошибка окружности (Circularity Error):</b><br>"
            "Отклонение внешней границы хода стика от идеальной окружности (R=1.0).<br>"
            "<i>Допуск (с безелем):</i> менее 8.0% (типично 4–7%).<br>"
            "<i>Для гейта без безеля (квадратного):</i> норма составляет ~18–22% (так как по диагоналям X=1.0 и Y=1.0 дают радиус √2 ≈ 1.41).<br>"
            "<i>Замеряется в:</i> Этап 2 (Окружность).<br>"
            "Показывает геометрию физического ограничителя (безеля) корпуса и равномерность калибровки."
        ),
        (
            "Шум потенциометра X",
            "< 1.50%",
            "<b>Амплитуда шума и дрожания по оси X:</b><br>"
            "Флуктуации сигнала датчика Холла или износ резистивной дорожки X при удержании стика.<br>"
            "<i>Допуск:</i> менее 1.50%.<br>"
            "<i>Замеряется в:</i> Этап 3 (Попадите в кружки).<br>"
            "<b>Причина:</b> загрязнение, графитовая пыль, износ резистивного слоя или пульсации питания АЦП."
        ),
        (
            "Шум потенциометра Y",
            "< 1.50%",
            "<b>Амплитуда шума и дрожания по оси Y:</b><br>"
            "Флуктуации сигнала датчика Холла или износ резистивной дорожки Y при удержании стика.<br>"
            "<i>Допуск:</i> менее 1.50%.<br>"
            "<i>Замеряется в:</i> Этап 3 (Попадите в кружки).<br>"
            "<b>Причина:</b> загрязнение, графитовая пыль, износ резистивного слоя или пульсации питания АЦП."
        ),
        (
            "Snapback (Ось X)",
            "< 5.0%",
            "<b>Амплитуда отскока по горизонтали (Snapback X):</b><br>"
            "Пролёт нуля вправо/влево при резком отпускании горизонтального упора.<br>"
            "<i>Допуск:</i> менее 5.0%.<br>"
            "<i>Замеряется в:</i> Этап 4 (Snapback).<br>"
            "<b>Причина:</b> ослабление возвратных пружин, износ или люфт кулис механизма, потеря демпфирования."
        ),
        (
            "Snapback (Ось Y)",
            "< 5.0%",
            "<b>Амплитуда отскока по вертикали (Snapback Y):</b><br>"
            "Пролёт нуля вверх/вниз при резком отпускании вертикального упора.<br>"
            "<i>Допуск:</i> менее 5.0%.<br>"
            "<i>Замеряется в:</i> Этап 4 (Snapback).<br>"
            "<b>Причина:</b> ослабление возвратных пружин, износ или люфт кулис механизма, потеря демпфирования."
        ),
        (
            "Вероятность отскока",
            "< 10.0%",
            "<b>Вероятность отскока (Snapback Rate):</b><br>"
            "Доля резких сбросов стика, приведших к паразитному перелёту нуля (> 5.0%).<br>"
            "<i>Рекомендуемая серия:</i> 10 сбросов в разных направлениях.<br>"
            "<i>Допуск:</i> до 10.0% (норма: 0%). Значения выше 20.0% указывают на критический износ пружин или отсутствие демпфирования."
        ),
        (
            "Итоговый вердикт",
            "—",
            "<b>Комплексная оценка исправности узла:</b><br>"
            "Выносится по результатам всех этапов проверки."
        )
    ]

    def __init__(self, left_analyzer: StickAnalyzer, right_analyzer: StickAnalyzer, parent=None):
        super().__init__(parent)
        self.left_analyzer = left_analyzer
        self.right_analyzer = right_analyzer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        box = QGroupBox("Сводка аномалий и дефектов стиков (по осям X/Y)")
        box.setStyleSheet("QGroupBox { font-size: 11px; font-weight: bold; }")
        l_box = QVBoxLayout(box)
        l_box.setContentsMargins(6, 6, 6, 6)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Параметр проверки", "LS (Левый)", "RS (Правый)", "Допуск"])

        # Flexible width adaptation without rigid pixel lock
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setRowCount(len(self.ROW_DEFINITIONS))

        for r_idx, (p_name, tol, tooltip_text) in enumerate(self.ROW_DEFINITIONS):
            item_name = QTableWidgetItem(p_name)
            item_name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            item_name.setToolTip(tooltip_text)
            self.table.setItem(r_idx, 0, item_name)

            item_ls = QTableWidgetItem("Не тестир.")
            item_ls.setTextAlignment(Qt.AlignCenter)
            item_ls.setForeground(QColor("#64748B"))
            self.table.setItem(r_idx, 1, item_ls)

            item_rs = QTableWidgetItem("Не тестир.")
            item_rs.setTextAlignment(Qt.AlignCenter)
            item_rs.setForeground(QColor("#64748B"))
            self.table.setItem(r_idx, 2, item_rs)

            item_tol = QTableWidgetItem(tol)
            item_tol.setTextAlignment(Qt.AlignCenter)
            item_tol.setForeground(QColor("#94A3B8"))
            item_tol.setToolTip(f"Допустимая норма для '{p_name}': {tol}")
            self.table.setItem(r_idx, 3, item_tol)

        l_box.addWidget(self.table)
        layout.addWidget(box)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(100)

    def update_table(self):
        ls = self.left_analyzer
        rs = self.right_analyzer

        # 0. Center drift X
        if ls.center_tested:
            self._set_cell(0, 1, f"{ls.center_drift_x_pct:.1f}%", is_bad=(ls.center_drift_x_pct > 5.0), is_warn=(ls.center_drift_x_pct > 3.0))
        else:
            self._set_cell(0, 1, "Не тестир.", is_muted=True)

        if rs.center_tested:
            self._set_cell(0, 2, f"{rs.center_drift_x_pct:.1f}%", is_bad=(rs.center_drift_x_pct > 5.0), is_warn=(rs.center_drift_x_pct > 3.0))
        else:
            self._set_cell(0, 2, "Не тестир.", is_muted=True)

        # 1. Center drift Y
        if ls.center_tested:
            self._set_cell(1, 1, f"{ls.center_drift_y_pct:.1f}%", is_bad=(ls.center_drift_y_pct > 5.0), is_warn=(ls.center_drift_y_pct > 3.0))
        else:
            self._set_cell(1, 1, "Не тестир.", is_muted=True)

        if rs.center_tested:
            self._set_cell(1, 2, f"{rs.center_drift_y_pct:.1f}%", is_bad=(rs.center_drift_y_pct > 5.0), is_warn=(rs.center_drift_y_pct > 3.0))
        else:
            self._set_cell(1, 2, "Не тестир.", is_muted=True)

        # 2. Circularity error (Combined 360°)
        if ls.circularity_tested:
            is_bad = (ls.circularity_error_pct > 12.0)
            is_warn = (ls.circularity_error_pct > 8.0)
            self._set_cell(2, 1, f"{ls.circularity_error_pct:.1f}%", is_bad=is_bad, is_warn=is_warn)
        else:
            self._set_cell(2, 1, "Не тестир.", is_muted=True)

        if rs.circularity_tested:
            is_bad = (rs.circularity_error_pct > 12.0)
            is_warn = (rs.circularity_error_pct > 8.0)
            self._set_cell(2, 2, f"{rs.circularity_error_pct:.1f}%", is_bad=is_bad, is_warn=is_warn)
        else:
            self._set_cell(2, 2, "Не тестир.", is_muted=True)

        # 3. Noise X
        if ls.jitter_tested:
            self._set_cell(3, 1, f"{ls.peak_jitter_x_pct:.2f}%", is_bad=(ls.peak_jitter_x_pct > 2.0), is_warn=(ls.peak_jitter_x_pct > 1.2))
        else:
            self._set_cell(3, 1, "Не тестир.", is_muted=True)

        if rs.jitter_tested:
            self._set_cell(3, 2, f"{rs.peak_jitter_x_pct:.2f}%", is_bad=(rs.peak_jitter_x_pct > 2.0), is_warn=(rs.peak_jitter_x_pct > 1.2))
        else:
            self._set_cell(3, 2, "Не тестир.", is_muted=True)

        # 4. Noise Y
        if ls.jitter_tested:
            self._set_cell(4, 1, f"{ls.peak_jitter_y_pct:.2f}%", is_bad=(ls.peak_jitter_y_pct > 2.0), is_warn=(ls.peak_jitter_y_pct > 1.2))
        else:
            self._set_cell(4, 1, "Не тестир.", is_muted=True)

        if rs.jitter_tested:
            self._set_cell(4, 2, f"{rs.peak_jitter_y_pct:.2f}%", is_bad=(rs.peak_jitter_y_pct > 2.0), is_warn=(rs.peak_jitter_y_pct > 1.2))
        else:
            self._set_cell(4, 2, "Не тестир.", is_muted=True)

        # 5. Snapback X
        if ls.snapback_tested:
            self._set_cell(5, 1, f"{ls.peak_snapback_x_pct:.1f}%", is_bad=(ls.peak_snapback_x_pct > 8.0), is_warn=(ls.peak_snapback_x_pct > 5.0))
        else:
            self._set_cell(5, 1, "Не тестир.", is_muted=True)

        if rs.snapback_tested:
            self._set_cell(5, 2, f"{rs.peak_snapback_x_pct:.1f}%", is_bad=(rs.peak_snapback_x_pct > 8.0), is_warn=(rs.peak_snapback_x_pct > 5.0))
        else:
            self._set_cell(5, 2, "Не тестир.", is_muted=True)

        # 6. Snapback Y
        if ls.snapback_tested:
            self._set_cell(6, 1, f"{ls.peak_snapback_y_pct:.1f}%", is_bad=(ls.peak_snapback_y_pct > 8.0), is_warn=(ls.peak_snapback_y_pct > 5.0))
        else:
            self._set_cell(6, 1, "Не тестир.", is_muted=True)

        if rs.snapback_tested:
            self._set_cell(6, 2, f"{rs.peak_snapback_y_pct:.1f}%", is_bad=(rs.peak_snapback_y_pct > 8.0), is_warn=(rs.peak_snapback_y_pct > 5.0))
        else:
            self._set_cell(6, 2, "Не тестир.", is_muted=True)

        # 7. Snapback Rate (%)
        if ls.snapback_tested and ls.total_flicks > 0:
            rate_str = f"{ls.snapback_rate_pct:.0f}% (X:{ls.snapback_rate_x_pct:.0f}% Y:{ls.snapback_rate_y_pct:.0f}%)"
            self._set_cell(7, 1, rate_str, is_bad=(ls.snapback_rate_pct > 20.0), is_warn=(ls.snapback_rate_pct > 0.0))
        else:
            self._set_cell(7, 1, "Не тестир.", is_muted=True)

        if rs.snapback_tested and rs.total_flicks > 0:
            rate_str = f"{rs.snapback_rate_pct:.0f}% (X:{rs.snapback_rate_x_pct:.0f}% Y:{rs.snapback_rate_y_pct:.0f}%)"
            self._set_cell(7, 2, rate_str, is_bad=(rs.snapback_rate_pct > 20.0), is_warn=(rs.snapback_rate_pct > 0.0))
        else:
            self._set_cell(7, 2, "Не тестир.", is_muted=True)

        # 8. Overall Status Verdict
        any_ls = (ls.center_tested or ls.circularity_tested or ls.jitter_tested or ls.snapback_tested)
        any_rs = (rs.center_tested or rs.circularity_tested or rs.jitter_tested or rs.snapback_tested)

        if not any_ls:
            self._set_cell(8, 1, "Ожидание тестов", is_muted=True)
        else:
            ls_bad = (
                (ls.center_tested and (ls.center_drift_x_pct > 5.0 or ls.center_drift_y_pct > 5.0)) or
                (ls.circularity_tested and ls.circularity_error_pct > 12.0) or
                (ls.jitter_tested and (ls.peak_jitter_x_pct > 1.8 or ls.peak_jitter_y_pct > 1.8)) or
                (ls.snapback_tested and len(ls.snapback_events) > 0)
            )
            self._set_cell(8, 1, "⚠️ ДЕФЕКТ" if ls_bad else "✅ НОРМА", is_bad=ls_bad, is_bold=True)

        if not any_rs:
            self._set_cell(8, 2, "Ожидание тестов", is_muted=True)
        else:
            rs_bad = (
                (rs.center_tested and (rs.center_drift_x_pct > 5.0 or rs.center_drift_y_pct > 5.0)) or
                (rs.circularity_tested and rs.circularity_error_pct > 12.0) or
                (rs.jitter_tested and (rs.peak_jitter_x_pct > 1.8 or rs.peak_jitter_y_pct > 1.8)) or
                (rs.snapback_tested and len(rs.snapback_events) > 0)
            )
            self._set_cell(8, 2, "⚠️ ДЕФЕКТ" if rs_bad else "✅ НОРМА", is_bad=rs_bad, is_bold=True)

    def _set_cell(self, row: int, col: int, text: str, is_bad: bool = False, is_warn: bool = False, is_bold: bool = False, is_muted: bool = False):
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem(text)
            self.table.setItem(row, col, item)
        else:
            item.setText(text)

        item.setTextAlignment(Qt.AlignCenter)
        if is_muted:
            item.setForeground(QColor("#64748B"))
        elif is_bad:
            item.setForeground(QColor("#EF4444"))
        elif is_warn:
            item.setForeground(QColor("#F59E0B"))
        else:
            item.setForeground(QColor("#10B981"))
