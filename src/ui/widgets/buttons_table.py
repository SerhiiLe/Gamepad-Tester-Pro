"""
Buttons & Contact Chatter Table Widget
Displays button descriptor index, mapped name, state, press count,
and flags contact chatter violations (< 7 ms).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...analysis.buttons import ButtonsAnalyzer


class ButtonsTableWidget(QWidget):
    """Real-time table of buttons and contact chatter / debounce analysis."""

    def __init__(self, analyzer: ButtonsAnalyzer, parent=None):
        super().__init__(parent)
        self.analyzer = analyzer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        # Header
        header = QHBoxLayout()
        lbl = QLabel("<b>Тестирование кнопок, крестовины (D-Pad) и детектор дребезга контактов (&lt; 7 мс)</b>")
        lbl.setStyleSheet("color: #38BDF8; font-size: 13px;")
        header.addWidget(lbl)

        btn_clear = QPushButton("Сбросить счётчики")
        btn_clear.setMinimumWidth(180)
        btn_clear.clicked.connect(self.clear_data)
        header.addWidget(btn_clear, alignment=Qt.AlignRight)
        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Код (Hex / Dec)", "Назначение кнопки", "Состояние", "Нажатий", "Дребезг (<7мс)", "Мин. интервал"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table, stretch=2)

        # Chatter Event Log
        lbl_log = QLabel("<b>Журнал событий дребезга (Ложные / повторные срабатывания &lt; 7 мс):</b>")
        lbl_log.setStyleSheet("color: #EF4444; font-size: 12px; margin-top: 6px;")
        layout.addWidget(lbl_log)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(120)
        layout.addWidget(self.txt_log, stretch=1)

        # Timer to update table (20 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table)
        self.timer.start(50)

        self._last_logged_chatter_count = 0

    def clear_data(self):
        self.analyzer.reset()
        self.table.setRowCount(0)
        self.txt_log.clear()
        self._last_logged_chatter_count = 0

    def update_table(self):
        buttons = list(self.analyzer.buttons.values())
        if len(buttons) != self.table.rowCount():
            self.table.setRowCount(len(buttons))

        for row, btn in enumerate(buttons):
            # 0. Code
            code_str = f"0x{btn.code:03X} ({btn.code})"
            item_code = self.table.item(row, 0)
            if not item_code:
                item_code = QTableWidgetItem(code_str)
                self.table.setItem(row, 0, item_code)
            else:
                item_code.setText(code_str)

            # 1. Name / Mapping
            name_str = f"{btn.name} ({btn.description})" if btn.description else btn.name
            item_name = self.table.item(row, 1)
            if not item_name:
                item_name = QTableWidgetItem(name_str)
                self.table.setItem(row, 1, item_name)
            else:
                item_name.setText(name_str)

            # 2. State
            state_str = "НАЖАТА" if btn.is_pressed else "Отпущена"
            item_state = self.table.item(row, 2)
            if not item_state:
                item_state = QTableWidgetItem(state_str)
                self.table.setItem(row, 2, item_state)
            else:
                item_state.setText(state_str)
            item_state.setForeground(QColor("#10B981" if btn.is_pressed else "#94A3B8"))

            # 3. Press count
            item_cnt = self.table.item(row, 3)
            if not item_cnt:
                item_cnt = QTableWidgetItem(str(btn.press_count))
                self.table.setItem(row, 3, item_cnt)
            else:
                item_cnt.setText(str(btn.press_count))

            # 4. Chatter count (Flagged in RED if > 0)
            chatter_str = str(btn.chatter_count)
            item_chatter = self.table.item(row, 4)
            if not item_chatter:
                item_chatter = QTableWidgetItem(chatter_str)
                self.table.setItem(row, 4, item_chatter)
            else:
                item_chatter.setText(chatter_str)

            if btn.chatter_count > 0:
                item_chatter.setForeground(QColor("#EF4444"))
                item_chatter.setBackground(QColor(239, 68, 68, 40))
            else:
                item_chatter.setForeground(QColor("#10B981"))
                item_chatter.setBackground(QColor(0, 0, 0, 0))

            # 5. Min Interval
            min_int_str = f"{btn.min_press_interval_ms:.2f} мс" if btn.min_press_interval_ms != float('inf') else "—"
            item_int = self.table.item(row, 5)
            if not item_int:
                item_int = QTableWidgetItem(min_int_str)
                self.table.setItem(row, 5, item_int)
            else:
                item_int.setText(min_int_str)

        # Update log if new chatter events arrived
        if len(self.analyzer.all_chatter_events) > self._last_logged_chatter_count:
            new_events = self.analyzer.all_chatter_events[self._last_logged_chatter_count:]
            for ev in new_events:
                self.txt_log.append(f"⚠️ [ДРЕБЕЗГ] Кнопка '{ev.button_name}' (0x{ev.button_code:03X}): {ev.transition} с интервалом {ev.delta_ms:.2f} мс (< 7.0 мс)!")
            self._last_logged_chatter_count = len(self.analyzer.all_chatter_events)
