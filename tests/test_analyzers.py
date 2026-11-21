"""
Unit and Integration Tests for Gamepad Tester Analytics & Reports
"""

import os
import time
import unittest
from src.analysis.buttons import ButtonsAnalyzer
from src.analysis.sticks import StickAnalyzer
from src.analysis.polling import PollingAnalyzer
from src.analysis.triggers import TriggersAnalyzer
from src.reports.text_report import generate_text_report
from src.reports.pdf_report import generate_pdf_report


class TestGamepadAnalyzers(unittest.TestCase):

    def test_button_debounce_chatter_detection(self):
        analyzer = ButtonsAnalyzer()
        t = 1000.0

        # Normal press and release (interval > 50 ms)
        analyzer.process_button_event(0x130, True, t, name="Cross")
        t += 0.080
        analyzer.process_button_event(0x130, False, t, name="Cross")

        summary1 = analyzer.get_summary()
        self.assertEqual(summary1["total_chatter_events"], 0)
        self.assertEqual(summary1["status"], "PASS")

        # Contact chatter: bounce within 3 ms (< 7 ms threshold)
        t += 0.003
        analyzer.process_button_event(0x130, True, t, name="Cross")

        summary2 = analyzer.get_summary()
        self.assertEqual(summary2["total_chatter_events"], 1)
        self.assertEqual(summary2["status"], "FAIL_CHATTER")
        self.assertIn("Cross", summary2["faulty_buttons"])

    def test_stick_circularity_and_snapback(self):
        import math
        stick = StickAnalyzer("Left Stick")
        t = 100.0

        # In Stage 0 (Free mode), no snapback events should be registered
        stick.active_stage = 0
        stick.update_axis(0x00, 32767, t, is_x=True)
        t += 0.020
        stick.update_axis(0x00, -6553, t, is_x=True)
        self.assertEqual(len(stick.snapback_events), 0)

        # In Stage 2 (Circularity 360°), full perimeter track is recorded
        stick.active_stage = 2

        # 1. Simulate Lead-in (pushing from center to rim)
        for r_in in [0.2, 0.4, 0.6, 0.8]:
            stick.update_axis(0x00, int(r_in * 32767), t, is_x=True)
            t += 0.010

        # 2. Simulate full 360° rotation along circular rim (r = 1.0)
        for angle_deg in range(0, 360, 5):
            rad = math.radians(angle_deg)
            raw_x = int(math.cos(rad) * 32767)
            raw_y = int(-math.sin(rad) * 32767)
            t += 0.010
            stick.update_axis(0x00, raw_x, t, is_x=True)
            stick.update_axis(0x01, raw_y, t, is_x=False)

        # 3. Simulate Lead-out (releasing back towards center)
        for r_out in [0.8, 0.6, 0.4, 0.2]:
            stick.update_axis(0x00, int(r_out * 32767), t, is_x=True)
            t += 0.010

        self.assertTrue(stick.circularity_tested)
        self.assertGreaterEqual(stick.get_circularity_coverage_pct(), 95.0)
        self.assertGreater(len(stick.boundary_points), 50)
        # Lead-in and lead-out must be excluded; error on pure circle must be < 2.0%
        self.assertLess(stick.circularity_error_pct, 2.0)
        self.assertIn("Круглый", stick.gate_shape_detected)

        # Release stick to center before next stage
        t += 0.050
        stick.update_axis(0x00, 0, t, is_x=True)
        stick.update_axis(0x01, 0, t, is_x=False)

        # In Stage 4 (Snapback test mode), snapback is captured
        stick.active_stage = 4
        # Hold stick at +1.0
        for _ in range(5):
            stick.update_axis(0x00, 32767, t, is_x=True)  # +1.0
            t += 0.010
        # Release with overshoot to -0.20
        stick.update_axis(0x00, -6553, t, is_x=True)  # snapback to -0.20
        t += 0.070
        stick.update_axis(0x00, 0, t, is_x=True)  # finish 65 ms window

        summary = stick.get_summary()
        self.assertEqual(stick.total_flicks, 1)
        self.assertEqual(stick.snapback_flicks, 1)
        self.assertEqual(stick.snapback_rate_pct, 100.0)
        self.assertGreater(summary["max_snapback_overshoot_pct"], 10.0)
        self.assertEqual(summary["status"], "FAIL_SNAPBACK")

    def test_square_gate_detection(self):
        import math
        stick = StickAnalyzer("Right Stick")
        stick.active_stage = 2
        t = 200.0
        # Simulate square gate: X and Y independent in [-1, 1], reaching corners at ~1.41
        for angle_deg in range(0, 360, 5):
            rad = math.radians(angle_deg)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)
            scale = 1.0 / max(abs(cos_a), abs(sin_a))
            raw_x = int(cos_a * scale * 32767)
            raw_y = int(-sin_a * scale * 32767)
            t += 0.010
            stick.update_axis(0x00, raw_x, t, is_x=True)
            stick.update_axis(0x01, raw_y, t, is_x=False)

        self.assertTrue(stick.circularity_tested)
        self.assertIn("Квадратный", stick.gate_shape_detected)
        self.assertGreater(stick.max_radial_reach, 1.30)
        summary = stick.get_summary()
        self.assertIn("Квадратный", summary["gate_shape"])

    def test_polling_rate_analysis(self):
        polling = PollingAnalyzer()
        t = 1000.0
        # 100 packets at 1000 Hz (1 ms delta)
        for _ in range(100):
            polling.record_packet(t)
            t += 0.001

        summary = polling.get_summary()
        self.assertGreater(summary["current_hz"], 900)
        self.assertAlmostEqual(summary["avg_interval_ms"], 1.0, delta=0.1)

    def test_reports_generation(self):
        dev_info = {"name": "DualSense Wireless Controller", "vid": 0x054C, "pid": 0x0CE6, "event_path": "/dev/input/event10", "layout": "dualsense"}
        pdata = {"current_hz": 1000.0, "nominal_target_hz": 1000, "avg_interval_ms": 1.0, "min_interval_ms": 0.95, "max_interval_ms": 1.05, "jitter_stddev_ms": 0.03, "total_packets": 500, "dropped_packets": 0, "status": "PASS"}
        bdata = {"total_buttons_tested": 12, "total_chatter_events": 0, "faulty_buttons": [], "status": "PASS"}
        ls = {"name": "Left Stick", "circularity_error_pct": 7.4, "max_reach": 1.01, "peak_jitter_pct": 0.35, "motion_jitter_pct": 0.2, "adc_bits": 10.0, "adc_step": 64, "adc_levels": 1024, "snapback_count": 0, "max_snapback_overshoot_pct": 0.0, "status": "PASS"}
        rs = {"name": "Right Stick", "circularity_error_pct": 8.1, "max_reach": 1.0, "peak_jitter_pct": 0.40, "motion_jitter_pct": 0.22, "adc_bits": 10.0, "adc_step": 64, "adc_levels": 1024, "snapback_count": 0, "max_snapback_overshoot_pct": 0.0, "status": "PASS"}
        trigs = {"L2": {"code": 0x02, "current_val_pct": 0.0, "raw_max": 255, "min_step": 1, "adc_levels": 256, "adc_bits": 8.0}, "R2": {"code": 0x05, "current_val_pct": 0.0, "raw_max": 255, "min_step": 1, "adc_levels": 256, "adc_bits": 8.0}}

        # Text report
        text = generate_text_report(dev_info, pdata, bdata, ls, rs, trigs)
        self.assertIn("ПАСПОРТ ТЕХНИЧЕСКОГО СОСТОЯНИЯ", text)
        self.assertIn("ПРЕДПОЛАГАЕМЫЕ ХАРАКТЕРИСТИКИ И ПОДЛИННОСТЬ", text)
        self.assertIn("Разрядность АЦП стиков:     ~10 бит", text)
        self.assertIn("Разрядность АЦП триггеров:  ~8 бит", text)
        self.assertIn("Sony DualSense", text)

        # PDF report
        test_pdf_path = "/tmp/test_gamepad_report.pdf"
        ok = generate_pdf_report(test_pdf_path, dev_info, pdata, bdata, ls, rs, trigs)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(test_pdf_path))
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)

    def test_hardware_profile_authenticity(self):
        from src.analysis.authenticity import analyze_authenticity

        ls = {"adc_bits": 12.0}
        rs = {"adc_bits": 12.0}
        trigs = {"L2": {"adc_bits": 8.0}, "R2": {"adc_bits": 8.0}}

        # 1. Genuine Xbox 360
        dev_x360 = {"name": "Microsoft X-Box 360 pad", "vid": 0x045E, "pid": 0x028E, "has_ff": True}
        res_x360 = analyze_authenticity(dev_x360, ls, rs, trigs)
        self.assertIn("12 бит", res_x360.stick_adc_str)
        self.assertIn("8 бит", res_x360.trigger_adc_str)
        self.assertIn("Оригинальная аппаратная архитектура", res_x360.verdict)
        self.assertFalse(res_x360.is_replica)

        # 2. Fake / Replica DualShock 4 (claims DS4 but missing Touchpad & Motion sensors)
        dev_fake_ds4 = {"name": "Wireless Controller", "vid": 0x054C, "pid": 0x05C4, "layout": "ds4", "has_touchpad": False, "has_motion": False}
        res_fake_ds4 = analyze_authenticity(dev_fake_ds4, ls, rs, trigs)
        self.assertIn("Имитация / Реплика", res_fake_ds4.verdict)
        self.assertIn("ОТСУТСТВУЕТ", res_fake_ds4.actual_spec)
        self.assertTrue(res_fake_ds4.is_replica)

        # 3. Genuine DualShock 4 (Touchpad and Motion sensors both present)
        dev_real_ds4 = {"name": "Wireless Controller", "vid": 0x054C, "pid": 0x05C4, "layout": "ds4", "has_touchpad": True, "has_motion": True, "has_ff": True}
        res_real_ds4 = analyze_authenticity(dev_real_ds4, ls, rs, trigs)
        self.assertIn("Оригинал / Полная", res_real_ds4.verdict)
        self.assertFalse(res_real_ds4.is_replica)

    def test_adc_resolution_estimation(self):
        # 1. Stick 10-bit test (increments of 64 on span 65535)
        stick = StickAnalyzer("Test Stick")
        t = 50.0
        val = 0
        for _ in range(20):
            val += 64
            t += 0.008
            stick.update_axis(0x00, val, t, is_x=True)
            stick.update_axis(0x01, val, t, is_x=False)

        summary = stick.get_summary()
        self.assertEqual(summary["adc_step_x"], 64)
        self.assertEqual(summary["adc_step_y"], 64)
        self.assertEqual(summary["adc_levels_x"], 1024)
        self.assertEqual(summary["adc_bits_x"], 10.0)
        self.assertEqual(summary["adc_bits"], 10.0)

        # 2. Stick 12-bit test with interpolation/smoothing (steps of 16 smoothed into sub-steps of 2)
        stick12 = StickAnalyzer("12-bit Filtered Stick")
        t = 100.0
        y = 0.0
        curr = 0
        for _ in range(40):
            curr += 16
            for _ in range(5):
                y = 0.35 * curr + 0.65 * y
                t += 0.002
                stick12.update_axis(0x00, round(y), t, is_x=True)
                stick12.update_axis(0x01, round(y), t, is_x=False)

        summary12 = stick12.get_summary()
        self.assertEqual(summary12["adc_bits_x"], 12.0)
        self.assertEqual(summary12["adc_bits_y"], 12.0)
        self.assertEqual(summary12["adc_bits"], 12.0)
        self.assertEqual(summary12["adc_step"], 16)

        # 3. Stick stops moving: sensor/wiper noise toggles (+/- 1 or +/- 2)
        # Must retain 12-bit and NEVER jump to 15-bit!
        noise_vals = [0, 1, -1, 2, -2, 1, 0, -1]
        for i in range(80):
            t += 0.002
            stopped_val = round(y) + noise_vals[i % len(noise_vals)]
            stick12.update_axis(0x00, stopped_val, t, is_x=True)
            stick12.update_axis(0x01, stopped_val, t, is_x=False)

        summary_stopped = stick12.get_summary()
        self.assertEqual(summary_stopped["adc_bits_x"], 12.0)
        self.assertEqual(summary_stopped["adc_bits_y"], 12.0)
        self.assertEqual(summary_stopped["adc_bits"], 12.0)
        self.assertEqual(summary_stopped["adc_step"], 16)

        # 4. Trigger 8-bit test (increments of 1 on span 255)
        from src.analysis.triggers import TriggersAnalyzer
        triggers = TriggersAnalyzer()
        t_val = 0
        for _ in range(15):
            t_val += 1
            triggers.update_trigger(0x02, t_val, "LT")

        t_summary = triggers.get_summary()
        self.assertIn("LT", t_summary)
        self.assertEqual(t_summary["LT"]["min_step"], 1)
        self.assertEqual(t_summary["LT"]["adc_levels"], 256)
        self.assertEqual(t_summary["LT"]["adc_bits"], 8.0)

    def test_oscilloscope_rolling_waveform(self):
        stick = StickAnalyzer("Waveform Stick")
        t = 1.0
        # Feed 150 points across movement
        for i in range(150):
            t += 0.001
            stick.update_axis(0x00, int(i * 200), t, is_x=True)
            stick.update_axis(0x01, int(i * 150), t, is_x=False)

        # Bottom oscilloscope displays rolling window of last 100 points
        hist = list(stick._history)[-100:]
        self.assertEqual(len(hist), 100)
        xs = [p[1] for p in hist]
        ys = [p[2] for p in hist]
        self.assertEqual(len(xs), 100)
        self.assertEqual(len(ys), 100)
        # Verify span of the 100 entries (50 packets * 1 ms = ~49 ms)
        span_ms = (hist[-1][0] - hist[0][0]) * 1000.0
        self.assertAlmostEqual(span_ms, 49.0, delta=2.0)

    def test_feedback_widget_and_support(self):
        """Verifies Force Feedback support status detection and automatic LED subtab selection."""
        import os
        from PySide6.QtWidgets import QApplication
        from src.ui.widgets.feedback_widget import FeedbackWidget
        from src.feedback.rumble import RumbleController
        from src.feedback.leds import LedController

        class MockDev:
            def __init__(self, name="Mock", vid=0x045E, pid=0x028E, has_ff=True, flavor="xbox"):
                self.name = name
                self.vendor_id = vid
                self.product_id = pid
                self.has_ff = has_ff
                self.layout_flavor = flavor
                self.is_dualsense = ("dualsense" in name.lower() or (vid == 0x054C and pid == 0x0CE6))
                self.is_ds4 = ("dualshock" in name.lower() or (vid == 0x054C and pid == 0x05C4))
                self.is_xbox = ("xbox" in name.lower() or vid == 0x045E)
                self.sysfs_led_path = "/sys/class/leds/xpad0" if self.is_xbox else None

        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication.instance() or QApplication([])

        fb = FeedbackWidget(RumbleController(), LedController())

        # Case 1: No device
        fb.set_current_device(None)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 0)
        self.assertFalse(fb.slider_left.isEnabled())
        self.assertIn("не выбран", fb.lbl_ff_status.text())

        # Case 2: Device without Force Feedback
        dev_no_ff = MockDev("Generic Gamepad", vid=0x1111, pid=0x2222, has_ff=False, flavor="generic")
        fb.set_current_device(dev_no_ff)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 0)
        self.assertFalse(fb.slider_left.isEnabled())
        self.assertIn("не поддерживает", fb.lbl_ff_status.text())

        # Case 3: Sony DualSense with Force Feedback
        dev_sony = MockDev("Sony DualSense Controller", vid=0x054C, pid=0x0CE6, has_ff=True, flavor="dualsense")
        fb.set_current_device(dev_sony)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 1)
        self.assertTrue(fb.slider_left.isEnabled())
        self.assertIn("поддерживается", fb.lbl_ff_status.text())

        # Case 4: Microsoft Xbox 360 with Force Feedback
        dev_xbox = MockDev("Microsoft X-Box 360 pad", vid=0x045E, pid=0x028E, has_ff=True, flavor="xbox")
        fb.set_current_device(dev_xbox)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 2)
        self.assertTrue(fb.slider_left.isEnabled())
        self.assertIn("поддерживается", fb.lbl_ff_status.text())

    def test_trigger_analyzer_and_widget(self):
        """Verifies trigger values normalization and TriggerWidget UI updates."""
        from src.ui.widgets.trigger_widget import TriggerWidget
        trig_analyzer = TriggersAnalyzer()
        w_trig = TriggerWidget(trig_analyzer)

        # Initially 0
        l_pct, r_pct = trig_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 0.0)
        self.assertEqual(r_pct, 0.0)

        # Update left trigger (e.g. ABS_Z, raw range 0..255) to 50%
        trig_analyzer.update_trigger(0x02, 128, name="LT (Левый триггер)")
        # Update right trigger (e.g. ABS_RZ, raw range 0..255) to 100%
        trig_analyzer.update_trigger(0x05, 255, name="RT (Правый триггер)")

        l_pct, r_pct = trig_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 50.19, delta=1.0)
        self.assertAlmostEqual(r_pct, 100.0, delta=1.0)

        # update_values() should run cleanly without AttributeError
        w_trig.update_values()
        self.assertEqual(w_trig.bar_l.value(), int(l_pct))
        self.assertEqual(w_trig.bar_r.value(), int(r_pct))
        self.assertIn("%", w_trig.lbl_l_val.text())
        self.assertIn("%", w_trig.lbl_r_val.text())

    def test_stick_stage_synchronization(self):
        """Verifies synchronized stage switching across sticks while keeping hints and resets separate."""
        from src.ui.main_window import MainWindow
        win = MainWindow()

        # Both initially in Stage 0 (Free Run)
        self.assertEqual(win.w_stick_left.current_stage, 0)
        self.assertEqual(win.w_stick_right.current_stage, 0)
        self.assertEqual(win.w_stick_left.combo_stages.currentIndex(), 0)
        self.assertEqual(win.w_stick_right.combo_stages.currentIndex(), 0)

        # 1. Changing left stick stage to 2 (Circularity) syncs right stick
        win.w_stick_left.combo_stages.setCurrentIndex(2)
        self.assertEqual(win.w_stick_left.current_stage, 2)
        self.assertEqual(win.w_stick_right.current_stage, 2)
        self.assertEqual(win.w_stick_right.combo_stages.currentIndex(), 2)
        self.assertEqual(win.left_stick_analyzer.active_stage, 2)
        self.assertEqual(win.right_stick_analyzer.active_stage, 2)

        # 2. Changing right stick stage to 1 (Center) syncs left stick
        win.w_stick_right.combo_stages.setCurrentIndex(1)
        self.assertEqual(win.w_stick_left.current_stage, 1)
        self.assertEqual(win.w_stick_right.current_stage, 1)
        self.assertEqual(win.w_stick_left.combo_stages.currentIndex(), 1)
        self.assertEqual(win.left_stick_analyzer.active_stage, 1)
        self.assertEqual(win.right_stick_analyzer.active_stage, 1)

        # 3. Independent resets: resetting left stick data does not affect right stick
        win.right_stick_analyzer.adc_bits = 12.0
        win.w_stick_left.btn_reset.click()
        # Stage remains 1 on both
        self.assertEqual(win.w_stick_left.current_stage, 1)
        self.assertEqual(win.w_stick_right.current_stage, 1)
        # Right stick analyzer data is not wiped by left stick reset
        self.assertEqual(win.right_stick_analyzer.adc_bits, 12.0)

        win.close()

    def test_stick_widget_hints_and_completion(self):
        """Verifies compact hints, 6-flick snapback thresholds (12 total), and '✅ Тест пройден' banners."""
        from src.i18n import i18n
        from src.ui.main_window import MainWindow

        i18n.set_language("RU")
        win = MainWindow()
        sw = win.w_stick_left

        # Stage 0: Free run
        sw._on_stage_changed(0)
        self.assertIn("Свободный ход", sw.lbl_hint.text())

        # Stage 1: Center
        sw._on_stage_changed(1)
        self.assertIn("Отпустите стик в центр", sw.lbl_hint.text())
        sw.analyzer.center_tested = True
        sw.analyzer.center_drift_pct = 2.4
        sw.update_view()
        self.assertIn("✅ Тест пройден (дрейф: 2.4%)", sw.lbl_hint.text())

        # Stage 2: Circularity
        sw._on_stage_changed(2)
        self.assertIn("Опишите полный круг", sw.lbl_hint.text())
        sw.analyzer.circularity_error_pct = 4.8
        # Simulate 95% coverage
        sw.analyzer._outer_envelope = {i: 1.0 for i in range(72)}
        sw.update_view()
        self.assertIn("✅ Тест пройден (ошибка: 4.8%)", sw.lbl_hint.text())

        # Stage 3: Targets / Noise
        sw._on_stage_changed(3)
        self.assertIn("Направьте в кружок", sw.lbl_hint.text())
        sw.target_zone_idx = len(sw.TARGET_ZONES)
        sw.analyzer.peak_jitter_pct = 0.35
        sw.update_view()
        self.assertIn("✅ Тест пройден (шум: 0.35%)", sw.lbl_hint.text())

        # Stage 4: Snapback (6 per axis, total 12)
        sw._on_stage_changed(4)
        sw.analyzer.total_flicks_x = 0
        sw.analyzer.total_flicks_y = 0
        sw.update_view()
        self.assertEqual(sw.lbl_hint.text(), "⚡ 1. Отведите по горизонтали и отпустите")
        self.assertIn("/12", sw.lbl_metrics.text())

        sw.analyzer.total_flicks_x = 6
        sw.analyzer.total_flicks_y = 0
        sw.update_view()
        self.assertEqual(sw.lbl_hint.text(), "⚡ 2. Отведите по вертикали и отпустите")

        sw.analyzer.total_flicks_y = 6
        sw.analyzer.snapback_rate_x_pct = 0.0
        sw.analyzer.snapback_rate_y_pct = 0.0
        sw.update_view()
        self.assertIn("✅ Тест пройден (Snapback: X 0%, Y 0%)", sw.lbl_hint.text())

        # Test EN language switching
        i18n.set_language("EN")
        sw.retranslate_ui()
        self.assertIn("✅ Test passed (Snapback: X 0%, Y 0%)", sw.lbl_hint.text())

        # Reset language to RU
        i18n.set_language("RU")
        win.close()

    def test_switch_gp2040_controller(self):
        """Verifies full support for GP2040-CE in HORI Pokken Nintendo Switch mode."""
        from src.core.device import GamepadDevice
        from src.core.profiles import detect_layout_flavor, get_button_info
        from src.core.constants import (
            BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z,
            BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL,
            ABS_X, ABS_Y, ABS_Z, ABS_RZ, EV_KEY, EV_ABS
        )
        from src.core.reader import RawInputEvent
        from src.ui.main_window import MainWindow

        # 1. Profile detection
        key_bits = {BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z, BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL}
        abs_bits = {ABS_X, ABS_Y, ABS_Z, ABS_RZ}
        flavor = detect_layout_flavor("HORI CO.,LTD. POKKEN CONTROLLER", key_bits, abs_bits)
        self.assertEqual(flavor, "switch")

        # 2. Button mappings: A, B, X, Y, L, R, ZL, ZR
        btn_y, _ = get_button_info("switch", BTN_SOUTH)
        btn_b, _ = get_button_info("switch", BTN_EAST)
        btn_a, _ = get_button_info("switch", BTN_C)
        btn_x, _ = get_button_info("switch", BTN_NORTH)
        btn_l, _ = get_button_info("switch", BTN_WEST)
        btn_r, _ = get_button_info("switch", BTN_Z)
        btn_zl, _ = get_button_info("switch", BTN_TL)
        btn_zr, _ = get_button_info("switch", BTN_TR)

        self.assertIn("Y", btn_y)
        self.assertIn("B", btn_b)
        self.assertIn("A", btn_a)
        self.assertIn("X", btn_x)
        self.assertIn("L", btn_l)
        self.assertIn("R", btn_r)
        self.assertIn("ZL", btn_zl)
        self.assertIn("ZR", btn_zr)

        # 3. MainWindow event handling with 0..255 axes
        win = MainWindow()
        mock_dev = GamepadDevice("HORI CO.,LTD. POKKEN CONTROLLER", event_path=None, key_bits=key_bits, abs_bits=abs_bits)
        mock_dev.abs_info = {
            ABS_X: (0, 255),
            ABS_Y: (0, 255),
            ABS_Z: (0, 255),
            ABS_RZ: (0, 255)
        }
        win.current_device = mock_dev
        win.current_profile_key = "switch"

        # Apply raw ranges from device
        win.left_stick_analyzer.set_raw_ranges(0, 255, 0, 255)
        win.right_stick_analyzer.set_raw_ranges(0, 255, 0, 255)

        # Left stick full right (255)
        win._on_input_event(RawInputEvent(100.0, EV_ABS, ABS_X, 255))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_x, 1.0, places=2)

        # Left stick full up (0)
        win._on_input_event(RawInputEvent(100.1, EV_ABS, ABS_Y, 0))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_y, 1.0, places=2)

        # Right stick: ABS_Z (Right Stick X) full left (0)
        win._on_input_event(RawInputEvent(100.2, EV_ABS, ABS_Z, 0))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_x, -1.0, places=2)

        # Right stick: ABS_RZ (Right Stick Y) full down (255)
        win._on_input_event(RawInputEvent(100.3, EV_ABS, ABS_RZ, 255))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_y, -1.0, places=2)

        # Digital triggers: pressing ZL (BTN_TL) sets left trigger to 100%
        win._on_input_event(RawInputEvent(100.4, EV_KEY, BTN_TL, 1))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 100.0)

        # Releasing ZL sets left trigger to 0%
        win._on_input_event(RawInputEvent(100.5, EV_KEY, BTN_TL, 0))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 0.0)

        win.close()


if __name__ == "__main__":
    unittest.main()
