"""
Report Viewer & Export Widget
Displays formatted diagnostic health summary and provides buttons to export PDF / TXT reports.
Supports bilingual Russian (RU) and English (EN) generation.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from ...reports.text_report import generate_text_report
from ...reports.pdf_report import generate_pdf_report, get_last_pdf_error
from ...i18n import tr, i18n


class ReportWidget(QWidget):
    """Visualizes live diagnostic report and manages file export."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.mw = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header controls
        header = QHBoxLayout()
        self.lbl_title = QLabel(tr("report_header_title"))
        self.lbl_title.setStyleSheet("color: #38BDF8; font-size: 13px;")
        self.lbl_title.setWordWrap(True)
        header.addWidget(self.lbl_title)

        self.btn_refresh = QPushButton(tr("btn_refresh_report"))
        self.btn_refresh.clicked.connect(self.refresh_report)
        header.addWidget(self.btn_refresh)

        self.btn_copy = QPushButton(tr("btn_copy_clipboard"))
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        header.addWidget(self.btn_copy)

        self.btn_pdf = QPushButton(tr("btn_export_pdf"))
        self.btn_pdf.setObjectName("btn_success")
        self.btn_pdf.clicked.connect(self.export_pdf)
        header.addWidget(self.btn_pdf)

        self.btn_txt = QPushButton(tr("btn_export_txt"))
        self.btn_txt.clicked.connect(self.export_txt)
        header.addWidget(self.btn_txt)

        layout.addLayout(header)

        # Text View
        self.txt_view = QTextEdit()
        self.txt_view.setReadOnly(True)
        layout.addWidget(self.txt_view)

    def retranslate_ui(self):
        """Retranslates all text elements to active language."""
        self.lbl_title.setText(tr("report_header_title"))
        self.btn_refresh.setText(tr("btn_refresh_report"))
        self.btn_copy.setText(tr("btn_copy_clipboard"))
        self.btn_pdf.setText(tr("btn_export_pdf"))
        self.btn_txt.setText(tr("btn_export_txt"))
        self.refresh_report()

    def _collect_data(self):
        dev = self.mw.current_device
        dev_info = {
            "name": dev.name if dev else "No Gamepad Selected",
            "vid": dev.vendor_id if dev else 0,
            "pid": dev.product_id if dev else 0,
            "event_path": dev.event_path if dev else "N/A",
            "layout": self.mw.current_profile_key,
            "has_ff": dev.has_ff if dev else False,
            "has_touchpad": dev.has_touchpad if dev else False,
            "has_motion": dev.has_motion if dev else False,
            "has_leds": bool(dev.sysfs_led_path) if dev else False,
            "has_battery": bool(dev.sysfs_battery_path) if dev else False,
        }
        polling_data = self.mw.polling_analyzer.get_summary()
        buttons_data = self.mw.buttons_analyzer.get_summary()
        left_stick = self.mw.left_stick_analyzer.get_summary()
        right_stick = self.mw.right_stick_analyzer.get_summary()
        triggers_data = self.mw.triggers_analyzer.get_summary()

        return dev_info, polling_data, buttons_data, left_stick, right_stick, triggers_data

    def refresh_report(self):
        dev_info, pdata, bdata, ls, rs, trigs = self._collect_data()
        report_text = generate_text_report(dev_info, pdata, bdata, ls, rs, trigs, lang=i18n.current_lang)
        self.txt_view.setPlainText(report_text)

    def copy_to_clipboard(self):
        self.refresh_report()
        text = self.txt_view.toPlainText()
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Report", tr("report_copied_notice"))

    def export_txt(self):
        self.refresh_report()
        text = self.txt_view.toPlainText()
        path, _ = QFileDialog.getSaveFileName(self, "Save Text Report", "gamepad_report.txt", "Text Files (*.txt)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Success", tr("txt_export_success", path=path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

    def export_pdf(self):
        self.refresh_report()
        dev_info, pdata, bdata, ls, rs, trigs = self._collect_data()
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF Report", "gamepad_health_passport.pdf", "PDF Files (*.pdf)")
        if path:
            ok = generate_pdf_report(path, dev_info, pdata, bdata, ls, rs, trigs, lang=i18n.current_lang)
            if ok:
                QMessageBox.information(self, "Success", tr("pdf_export_success", path=path))
            else:
                err = get_last_pdf_error() or "Cannot generate PDF (verify reportlab and file write permissions)."
                QMessageBox.critical(self, "PDF Generation Error", tr("pdf_export_error", err=err))
