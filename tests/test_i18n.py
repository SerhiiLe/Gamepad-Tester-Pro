"""
Unit and Integration Tests for Bilingual Localization (i18n / l10n)
Verifies:
1. System locale detection rules (ru_*, ua_*, uk_* -> RU, others -> EN).
2. Key parity between RU and EN dictionaries.
3. Live UI switching and retranslation in PyQt.
4. Text and PDF report generation in both RU and EN (1-page A4 verification).
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from src.i18n import i18n, tr, detect_system_language
from src.i18n.ru import TRANSLATIONS as RU_DICT
from src.i18n.en import TRANSLATIONS as EN_DICT
from src.ui.main_window import MainWindow
from src.reports.text_report import generate_text_report
from src.reports.pdf_report import generate_pdf_report


class TestLocalization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_key_parity(self):
        """Verifies that RU and EN dictionaries contain exactly the same keys."""
        ru_keys = set(RU_DICT.keys())
        en_keys = set(EN_DICT.keys())
        diff = ru_keys ^ en_keys
        self.assertEqual(diff, set(), f"Keys mismatch between RU and EN: {diff}")
        self.assertGreater(len(ru_keys), 150)

    def test_locale_detection(self):
        """Verifies OS locale detection logic."""
        cases = [
            ("ru_RU.UTF-8", "RU"),
            ("ru_UA.UTF-8", "RU"),
            ("ua_UA.UTF-8", "RU"),
            ("uk_UA.UTF-8", "RU"),
            ("en_US.UTF-8", "EN"),
            ("en_GB.UTF-8", "EN"),
            ("de_DE.UTF-8", "EN"),
            ("fr_FR.UTF-8", "EN"),
            ("es_ES.UTF-8", "EN"),
            ("C", "EN"),
        ]
        for locale_val, expected in cases:
            with patch.dict(os.environ, {"LANG": locale_val, "LC_ALL": "", "LC_MESSAGES": ""}):
                with patch("locale.getdefaultlocale", return_value=(locale_val, "UTF-8")):
                    detected = detect_system_language()
                    self.assertEqual(detected, expected, f"Failed for locale '{locale_val}': expected {expected}, got {detected}")

    def test_i18n_manager_switching(self):
        """Verifies setting language updates translations and callbacks."""
        i18n.set_language("EN")
        self.assertEqual(i18n.current_lang, "EN")
        self.assertIn("Comprehensive", tr("app_title"))
        self.assertEqual(tr("btn_reset"), "Reset")

        i18n.set_language("RU")
        self.assertEqual(i18n.current_lang, "RU")
        self.assertIn("Комплексная", tr("app_title"))
        self.assertEqual(tr("btn_reset"), "Сброс")

    def test_main_window_live_retranslation(self):
        """Verifies dynamic UI switching in MainWindow."""
        win = MainWindow()

        # Switch to EN
        win.combo_lang.setCurrentText("EN")
        self.assertEqual(i18n.current_lang, "EN")
        self.assertIn("Sticks & Triggers", win.tabs.tabText(0))
        self.assertIn("Buttons & Chatter", win.tabs.tabText(1))
        self.assertIn("Polling Rate", win.tabs.tabText(2))
        self.assertIn("Rumble & LEDs", win.tabs.tabText(3))
        self.assertIn("Passport / Report", win.tabs.tabText(4))
        self.assertIn("Controller:", win.lbl_controller.text())
        self.assertEqual(win.btn_rescan.text(), "↻ Rescan Devices")
        self.assertEqual(win.w_stick_left.btn_reset.text(), "Reset")
        self.assertEqual(win.w_triggers.box.title(), "Triggers")
        self.assertEqual(win.w_polling.btn_reset.text(), "Reset Statistics")

        # Switch to RU
        win.combo_lang.setCurrentText("RU")
        self.assertEqual(i18n.current_lang, "RU")
        self.assertIn("Стики и курки", win.tabs.tabText(0))
        self.assertIn("Кнопки и дребезг", win.tabs.tabText(1))
        self.assertIn("Частота опроса", win.tabs.tabText(2))
        self.assertIn("Вибрация и подсветка", win.tabs.tabText(3))
        self.assertIn("Паспорт / Отчёт", win.tabs.tabText(4))
        self.assertIn("Контроллер:", win.lbl_controller.text())
        self.assertEqual(win.btn_rescan.text(), "↻ Поиск устройств")
        self.assertEqual(win.w_stick_left.btn_reset.text(), "Сброс")
        self.assertEqual(win.w_triggers.box.title(), "Курки")
        self.assertEqual(win.w_polling.btn_reset.text(), "Сбросить статистику")

        win.close()

    def test_reports_bilingual_generation(self):
        """Verifies text and PDF generation in both Russian and English."""
        dev_info = {
            "name": "Microsoft X-Box 360 pad",
            "vid": 0x045E,
            "pid": 0x028E,
            "event_path": "/dev/input/event14",
            "layout": "xbox",
            "has_ff": True,
            "has_touchpad": False,
            "has_motion": False,
        }
        polling_data = {
            "status": "PASS",
            "current_hz": 250,
            "nominal_target_hz": 250,
            "avg_interval_ms": 4.0,
            "min_interval_ms": 3.8,
            "max_interval_ms": 4.2,
            "jitter_stddev_ms": 0.05,
            "is_wireless": False,
            "dropped_packets": 0,
            "total_packets": 500,
            "dedup_packets": 120,
        }
        buttons_data = {
            "status": "PASS",
            "total_buttons_tested": 10,
            "total_chatter_events": 0,
            "faulty_buttons": [],
        }
        left_stick = {
            "status": "PASS",
            "adc_bits": 10,
            "gate_shape": "circular",
            "circularity_error_pct": 5.2,
            "max_reach": 1.0,
            "peak_jitter_pct": 0.4,
            "motion_jitter_pct": 0.5,
            "snapback_rate_x_pct": 0.0,
            "snapback_rate_y_pct": 0.0,
            "snapback_flicks_x": 0,
            "total_flicks_x": 5,
            "snapback_flicks_y": 0,
            "total_flicks_y": 5,
            "max_snapback_x_pct": 2.1,
            "max_snapback_y_pct": 1.8,
        }
        right_stick = dict(left_stick)
        triggers_data = {
            "LT": {"raw_max": 255, "current_val_pct": 0.0, "adc_bits": 8},
            "RT": {"raw_max": 255, "current_val_pct": 0.0, "adc_bits": 8},
        }

        # 1. Text report RU
        txt_ru = generate_text_report(dev_info, polling_data, buttons_data, left_stick, right_stick, triggers_data, lang="RU")
        self.assertIn("ПАСПОРТ ТЕХНИЧЕСКОГО СОСТОЯНИЯ ГЕЙМПАДА", txt_ru)
        self.assertIn("Оригинальная аппаратная архитектура Xbox", txt_ru)

        # 2. Text report EN
        txt_en = generate_text_report(dev_info, polling_data, buttons_data, left_stick, right_stick, triggers_data, lang="EN")
        self.assertIn("GAMEPAD TECHNICAL CONDITION PASSPORT", txt_en)
        self.assertIn("Genuine Xbox Hardware Architecture", txt_en)

        # 3. PDF report RU and EN
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_ru_path = os.path.join(tmpdir, "report_ru.pdf")
            pdf_en_path = os.path.join(tmpdir, "report_en.pdf")

            ok_ru = generate_pdf_report(pdf_ru_path, dev_info, polling_data, buttons_data, left_stick, right_stick, triggers_data, lang="RU")
            self.assertTrue(ok_ru)
            self.assertTrue(os.path.exists(pdf_ru_path))

            ok_en = generate_pdf_report(pdf_en_path, dev_info, polling_data, buttons_data, left_stick, right_stick, triggers_data, lang="EN")
            self.assertTrue(ok_en)
            self.assertTrue(os.path.exists(pdf_en_path))

            # Verify page counts (strictly 1 page!)
            import shutil, subprocess
            if shutil.which("pdfinfo"):
                for p, label in [(pdf_ru_path, "RU"), (pdf_en_path, "EN")]:
                    out = subprocess.check_output(["pdfinfo", p], text=True)
                    for line in out.splitlines():
                        if line.startswith("Pages:"):
                            cnt = int(line.split(":")[1].strip())
                            self.assertEqual(cnt, 1, f"{label} PDF has {cnt} pages instead of 1!")


if __name__ == "__main__":
    unittest.main()
