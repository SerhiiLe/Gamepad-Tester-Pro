"""
Report Viewer & Export Widget
Displays formatted diagnostic health summary and provides buttons to export PDF / TXT reports.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from ...reports.text_report import generate_text_report
from ...reports.pdf_report import generate_pdf_report, get_last_pdf_error


class ReportWidget(QWidget):
    """Visualizes live diagnostic report and manages file export."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header controls
        header = QHBoxLayout()
        lbl = QLabel("<b>Паспорт технического состояния и диагностический отчёт</b>")
        lbl.setStyleSheet("color: #38BDF8; font-size: 13px;")
        header.addWidget(lbl)

        btn_refresh = QPushButton("Обновить данные")
        btn_refresh.clicked.connect(self.refresh_report)
        header.addWidget(btn_refresh)

        btn_copy = QPushButton("Копировать в буфер")
        btn_copy.clicked.connect(self.copy_to_clipboard)
        header.addWidget(btn_copy)

        btn_pdf = QPushButton("📄 Экспорт в PDF")
        btn_pdf.setObjectName("btn_success")
        btn_pdf.clicked.connect(self.export_pdf)
        header.addWidget(btn_pdf)

        btn_txt = QPushButton("💾 Сохранить .txt")
        btn_txt.clicked.connect(self.export_txt)
        header.addWidget(btn_txt)

        layout.addLayout(header)

        # Text View
        self.txt_view = QTextEdit()
        self.txt_view.setReadOnly(True)
        layout.addWidget(self.txt_view)

    def _collect_data(self):
        dev = self.mw.current_device
        dev_info = {
            "name": dev.name if dev else "No Gamepad Selected",
            "vid": dev.vendor_id if dev else 0,
            "pid": dev.product_id if dev else 0,
            "event_path": dev.event_path if dev else "N/A",
            "layout": self.mw.current_profile_key
        }
        polling_data = self.mw.polling_analyzer.get_summary()
        buttons_data = self.mw.buttons_analyzer.get_summary()
        left_stick = self.mw.left_stick_analyzer.get_summary()
        right_stick = self.mw.right_stick_analyzer.get_summary()
        triggers_data = self.mw.triggers_analyzer.get_summary()

        return dev_info, polling_data, buttons_data, left_stick, right_stick, triggers_data

    def refresh_report(self):
        dev_info, pdata, bdata, ls, rs, trigs = self._collect_data()
        report_text = generate_text_report(dev_info, pdata, bdata, ls, rs, trigs)
        self.txt_view.setPlainText(report_text)

    def copy_to_clipboard(self):
        self.refresh_report()
        text = self.txt_view.toPlainText()
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Успех", "Отчёт скопирован в буфер обмена!")

    def export_txt(self):
        self.refresh_report()
        text = self.txt_view.toPlainText()
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить текстовый отчёт", "gamepad_report.txt", "Text Files (*.txt)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Успех", f"Отчёт сохранён в:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def export_pdf(self):
        self.refresh_report()
        dev_info, pdata, bdata, ls, rs, trigs = self._collect_data()
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить PDF отчёт", "gamepad_health_passport.pdf", "PDF Files (*.pdf)")
        if path:
            ok = generate_pdf_report(path, dev_info, pdata, bdata, ls, rs, trigs)
            if ok:
                QMessageBox.information(self, "Успех", f"PDF-паспорт успешно создан:\n{path}")
            else:
                err = get_last_pdf_error() or "Не удалось сгенерировать PDF (проверьте наличие reportlab и права на запись)."
                QMessageBox.critical(self, "Ошибка генерации PDF", f"Не удалось создать PDF-паспорт:\n\n{err}")

