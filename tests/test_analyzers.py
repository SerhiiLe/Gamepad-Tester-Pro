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
        self.assertFalse(fb.lbl_ff_status.isHidden())
        self.assertIn("не выбран", fb.lbl_ff_status.text())

        # Case 2: Device without Force Feedback
        dev_no_ff = MockDev("Generic Gamepad", vid=0x1111, pid=0x2222, has_ff=False, flavor="generic")
        fb.set_current_device(dev_no_ff)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 0)
        self.assertFalse(fb.slider_left.isEnabled())
        self.assertFalse(fb.lbl_ff_status.isHidden())
        self.assertIn("не поддерживает", fb.lbl_ff_status.text())

        # Case 3: Sony DualSense with Force Feedback
        dev_sony = MockDev("Sony DualSense Controller", vid=0x054C, pid=0x0CE6, has_ff=True, flavor="dualsense")
        fb.set_current_device(dev_sony)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 1)
        self.assertTrue(fb.slider_left.isEnabled())
        self.assertTrue(fb.lbl_ff_status.isHidden())

        # Case 4: Microsoft Xbox 360 with Force Feedback
        dev_xbox = MockDev("Microsoft X-Box 360 pad", vid=0x045E, pid=0x028E, has_ff=True, flavor="xbox")
        fb.set_current_device(dev_xbox)
        fb.auto_select_tab()
        self.assertEqual(fb.led_tabs.currentIndex(), 2)
        self.assertTrue(fb.slider_left.isEnabled())
        self.assertTrue(fb.lbl_ff_status.isHidden())

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
        from PySide6.QtWidgets import QSizePolicy
        self.assertEqual(w_trig.bar_l.sizePolicy().verticalPolicy(), QSizePolicy.Expanding)
        self.assertEqual(w_trig.bar_r.sizePolicy().verticalPolicy(), QSizePolicy.Expanding)

    def test_buttons_diagram_widget(self):
        """Verifies ButtonsDiagramWidget 3-state verification, progress tracking, and subtab integration."""
        from src.ui.widgets.buttons_container import ButtonsViewWidget
        from src.ui.widgets.buttons_diagram_widget import (
            ButtonsDiagramWidget, STATE_UNTESTED, STATE_PRESSED, STATE_TESTED
        )
        import os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        btn_analyzer = ButtonsAnalyzer()
        ls_analyzer = StickAnalyzer("Left")
        rs_analyzer = StickAnalyzer("Right")
        trig_analyzer = TriggersAnalyzer()

        view = ButtonsViewWidget(
            buttons_analyzer=btn_analyzer,
            left_stick_analyzer=ls_analyzer,
            right_stick_analyzer=rs_analyzer,
            triggers_analyzer=trig_analyzer,
            profile_getter=lambda: "xbox"
        )

        diagram = view.w_diagram

        # 1. Initial state: 0 tested, empty outline (STATE_UNTESTED)
        self.assertEqual(len(diagram.tested_roles), 0)
        self.assertEqual(diagram.progress_bar.value(), 0)
        roles = diagram.canvas._resolve_roles("xbox")
        self.assertEqual(roles["action_south"]["state"], STATE_UNTESTED)
        self.assertEqual(roles["action_south"]["label"], "A")

        # 2. Press button A (BTN_SOUTH / 0x130): becomes STATE_PRESSED
        btn_analyzer.process_button_event(0x130, True, 100.0, name="A", desc="Action Bottom")
        roles = diagram.canvas._resolve_roles("xbox")
        self.assertEqual(roles["action_south"]["state"], STATE_PRESSED)
        self.assertIn("action_south", diagram.tested_roles)

        # 3. Release button A: becomes STATE_TESTED (muted fill)
        btn_analyzer.process_button_event(0x130, False, 100.1, name="A", desc="Action Bottom")
        roles = diagram.canvas._resolve_roles("xbox")
        self.assertEqual(roles["action_south"]["state"], STATE_TESTED)

        # 4. Trigger deflection: analog trigger LT (ABS_Z) > 12% becomes pressed & tested
        trig_analyzer.update_trigger(0x02, 128, name="LT")
        roles = diagram.canvas._resolve_roles("xbox")
        self.assertEqual(roles["trigger_l"]["state"], STATE_PRESSED)
        self.assertIn("trigger_l", diagram.tested_roles)

        # 5. Regression test: Pressing Start button must NOT duplicate / highlight Right Trigger (RT)
        btn_analyzer.process_button_event(0x13B, True, 100.2, name="Start / Menu", desc="Start")
        roles = diagram.canvas._resolve_roles("xbox")
        self.assertEqual(roles["start"]["state"], STATE_PRESSED)
        self.assertEqual(roles["trigger_r"]["state"], STATE_UNTESTED)
        self.assertNotIn("trigger_r", diagram.tested_roles)

        btn_analyzer.process_button_event(0x13B, False, 100.3, name="Start / Menu", desc="Start")
        roles = diagram.canvas._resolve_roles("xbox")
        self.assertEqual(roles["start"]["state"], STATE_TESTED)
        self.assertEqual(roles["trigger_r"]["state"], STATE_UNTESTED)

        # 6. Reset tested button clears progress
        diagram.reset_tested()
        self.assertEqual(len(diagram.tested_roles), 0)
        self.assertEqual(diagram.progress_bar.value(), 0)

        # 7. Retranslate UI runs cleanly
        view.retranslate_ui()

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
        """Verifies full support for HORI Pokken / Nintendo Switch Generic HID mode."""
        from src.core.device import GamepadDevice
        from src.core.profiles import detect_layout_flavor, get_button_info
        from src.core.constants import (
            BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z,
            BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL,
            ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RZ, EV_KEY, EV_ABS
        )
        from src.core.reader import RawInputEvent
        from src.ui.main_window import MainWindow

        # 1. Profile detection (HORI Pokken with real 4-axis topology: ABS_X, ABS_Y, ABS_Z, ABS_RX)
        key_bits = {BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z, BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL}
        abs_bits = {ABS_X, ABS_Y, ABS_Z, ABS_RX}
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

        # 3. MainWindow event handling with 4-axis HID device (ABS_Z = RS X, ABS_RX = RS Y, range 0..255)
        win = MainWindow()
        mock_dev = GamepadDevice("HORI CO.,LTD. POKKEN CONTROLLER", event_path=None, key_bits=key_bits, abs_bits=abs_bits)
        mock_dev.abs_info = {
            ABS_X: (0, 255),
            ABS_Y: (0, 255),
            ABS_Z: (0, 255),
            ABS_RX: (0, 255)
        }
        win.current_device = mock_dev
        win.current_profile_key = "switch"
        win._update_axis_mappings()

        # Verify dynamic axis resolution for 4-axis descriptor
        self.assertEqual(win._rs_x_axis, ABS_Z)
        self.assertEqual(win._rs_y_axis, ABS_RX)
        self.assertNotIn(win._trig_l_axis, (ABS_Z, ABS_RX))
        self.assertNotIn(win._trig_r_axis, (ABS_Z, ABS_RX))

        # Left stick full right (255)
        win._on_input_event(RawInputEvent(100.0, EV_ABS, ABS_X, 255))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_x, 1.0, places=2)

        # Left stick full up (0)
        win._on_input_event(RawInputEvent(100.1, EV_ABS, ABS_Y, 0))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_y, 1.0, places=2)

        # Right stick: ABS_Z (Right Stick X) full left (0)
        win._on_input_event(RawInputEvent(100.2, EV_ABS, ABS_Z, 0))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_x, -1.0, places=2)

        # Right stick: ABS_RX (Right Stick Y) full down (255)
        win._on_input_event(RawInputEvent(100.3, EV_ABS, ABS_RX, 255))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_y, -1.0, places=2)

        # Right stick: ABS_RX full up (0)
        win._on_input_event(RawInputEvent(100.35, EV_ABS, ABS_RX, 0))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_y, 1.0, places=2)

        # Digital triggers: pressing ZL (BTN_TL) sets left trigger to 100%
        win._on_input_event(RawInputEvent(100.4, EV_KEY, BTN_TL, 1))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 100.0)

        # Releasing ZL sets left trigger to 0%
        win._on_input_event(RawInputEvent(100.5, EV_KEY, BTN_TL, 0))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 0.0)

        # Also verify switch pad with ABS_RZ (Z/Rz topology)
        mock_rz_dev = GamepadDevice("Nintendo Switch Controller", event_path=None, key_bits=key_bits, abs_bits={ABS_X, ABS_Y, ABS_Z, ABS_RZ})
        mock_rz_dev.abs_info = {
            ABS_X: (0, 255),
            ABS_Y: (0, 255),
            ABS_Z: (0, 255),
            ABS_RZ: (0, 255)
        }
        win.current_device = mock_rz_dev
        win._update_axis_mappings()
        self.assertEqual(win._rs_x_axis, ABS_Z)
        self.assertEqual(win._rs_y_axis, ABS_RZ)

        win.close()

    def test_ps4_gp2040_controller(self):
        """Verifies full support for GP2040-CE in Sony PS4 mode (Razer Panthera emulation)."""
        from src.core.device import GamepadDevice
        from src.core.profiles import detect_layout_flavor, get_button_info
        from src.core.constants import (
            BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z,
            BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL,
            ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ, EV_KEY, EV_ABS
        )
        from src.core.reader import RawInputEvent
        from src.ui.main_window import MainWindow

        # 1. Profile detection by name and VID/PID
        key_bits = {BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z, BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL}
        abs_bits = {ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ}
        flavor = detect_layout_flavor("Open Stick Community GP2040-CE (PS4)", key_bits, abs_bits, 0x1532, 0x0401)
        self.assertEqual(flavor, "ps4")

        # 2. Button mappings: Square, Cross, Circle, Triangle, L1, R1, L2, R2, Share, Options, L3, R3, PS, Touchpad
        btn_sq, _ = get_button_info("ps4", BTN_SOUTH)
        btn_cr, _ = get_button_info("ps4", BTN_EAST)
        btn_ci, _ = get_button_info("ps4", BTN_C)
        btn_tr, _ = get_button_info("ps4", BTN_NORTH)
        btn_l1, _ = get_button_info("ps4", BTN_WEST)
        btn_r1, _ = get_button_info("ps4", BTN_Z)
        btn_l2, _ = get_button_info("ps4", BTN_TL)
        btn_r2, _ = get_button_info("ps4", BTN_TR)
        btn_sh, _ = get_button_info("ps4", BTN_TL2)
        btn_op, _ = get_button_info("ps4", BTN_TR2)
        btn_l3, _ = get_button_info("ps4", BTN_SELECT)
        btn_r3, _ = get_button_info("ps4", BTN_START)
        btn_ps, _ = get_button_info("ps4", BTN_MODE)
        btn_tp, _ = get_button_info("ps4", BTN_THUMBL)

        self.assertIn("Square", btn_sq)
        self.assertIn("Cross", btn_cr)
        self.assertIn("Circle", btn_ci)
        self.assertIn("Triangle", btn_tr)
        self.assertIn("L1", btn_l1)
        self.assertIn("R1", btn_r1)
        self.assertIn("L2", btn_l2)
        self.assertIn("R2", btn_r2)
        self.assertIn("Share", btn_sh)
        self.assertIn("Options", btn_op)
        self.assertIn("L3", btn_l3)
        self.assertIn("R3", btn_r3)
        self.assertIn("PS", btn_ps)
        self.assertIn("Touchpad", btn_tp)

        # 3. MainWindow event handling with 0..255 axes
        win = MainWindow()
        mock_dev = GamepadDevice("Open Stick Community GP2040-CE (PS4)", event_path=None, key_bits=key_bits, abs_bits=abs_bits)
        mock_dev.abs_info = {
            ABS_X: (0, 255),
            ABS_Y: (0, 255),
            ABS_Z: (0, 255),
            ABS_RX: (0, 255),
            ABS_RY: (0, 255),
            ABS_RZ: (0, 255),
        }
        win.current_device = mock_dev
        win.current_profile_key = "ps4"
        win._update_axis_mappings()

        # Left stick: ABS_X full right (255)
        win._on_input_event(RawInputEvent(100.0, EV_ABS, ABS_X, 255))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_x, 1.0, places=2)

        # Left stick: ABS_Y full up (0)
        win._on_input_event(RawInputEvent(100.1, EV_ABS, ABS_Y, 0))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_y, 1.0, places=2)

        # Right stick: ABS_Z (Right Stick X) full left (0)
        win._on_input_event(RawInputEvent(100.2, EV_ABS, ABS_Z, 0))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_x, -1.0, places=2)

        # Right stick: ABS_RZ (Right Stick Y) full down (255)
        win._on_input_event(RawInputEvent(100.3, EV_ABS, ABS_RZ, 255))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_y, -1.0, places=2)

        # Analog triggers: ABS_RX (L2) full press (255)
        win._on_input_event(RawInputEvent(100.4, EV_ABS, ABS_RX, 255))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 100.0, places=1)
        self.assertEqual(r_pct, 0.0)

        # Analog triggers: ABS_RY (R2) full press (255)
        win._on_input_event(RawInputEvent(100.5, EV_ABS, ABS_RY, 255))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 100.0, places=1)
        self.assertAlmostEqual(r_pct, 100.0, places=1)

        # Release triggers
        win._on_input_event(RawInputEvent(100.6, EV_ABS, ABS_RX, 0))
        win._on_input_event(RawInputEvent(100.7, EV_ABS, ABS_RY, 0))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 0.0, places=1)
        self.assertAlmostEqual(r_pct, 0.0, places=1)

        # Digital triggers: BTN_TL (L2) and BTN_TR (R2)
        win._on_input_event(RawInputEvent(100.8, EV_KEY, BTN_TL, 1))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 100.0)

        win._on_input_event(RawInputEvent(100.9, EV_KEY, BTN_TL, 0))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 0.0)

        win.close()

    def test_standard_linux_gamepad(self):
        """Verifies full support for Standard Linux Gamepads (Linux Gamepad Specification - gamepad.rst)."""
        from src.core.device import GamepadDevice
        from src.core.profiles import detect_layout_flavor, get_button_info
        from src.core.constants import (
            BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z,
            BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL, BTN_THUMBR,
            ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ, EV_KEY, EV_ABS
        )
        from src.core.reader import RawInputEvent
        from src.ui.main_window import MainWindow

        # 1. Profile detection by capabilities and bipolar stick topology
        key_bits = {BTN_SOUTH, BTN_EAST, BTN_C, BTN_NORTH, BTN_WEST, BTN_Z, BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_SELECT, BTN_START, BTN_MODE, BTN_THUMBL, BTN_THUMBR}
        abs_bits = {ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ}
        abs_info = {
            ABS_X: (-32767, 32767),
            ABS_Y: (-32767, 32767),
            ABS_Z: (0, 255),
            ABS_RX: (-32767, 32767),
            ABS_RY: (-32767, 32767),
            ABS_RZ: (0, 255),
        }
        flavor = detect_layout_flavor("RP2040 Gamepad rp2040", key_bits, abs_bits, vendor_id=0x2e8a, product_id=0x0013, abs_info=abs_info)
        self.assertEqual(flavor, "standard")

        # 2. Button mappings
        btn_a, _ = get_button_info("standard", BTN_SOUTH)
        btn_b, _ = get_button_info("standard", BTN_EAST)
        btn_x, _ = get_button_info("standard", BTN_NORTH)
        btn_y, _ = get_button_info("standard", BTN_WEST)
        btn_lb, _ = get_button_info("standard", BTN_TL)
        btn_rb, _ = get_button_info("standard", BTN_TR)
        btn_lt, _ = get_button_info("standard", BTN_TL2)
        btn_rt, _ = get_button_info("standard", BTN_TR2)
        btn_sel, _ = get_button_info("standard", BTN_SELECT)
        btn_sta, _ = get_button_info("standard", BTN_START)
        btn_gui, _ = get_button_info("standard", BTN_MODE)
        btn_ls, _ = get_button_info("standard", BTN_THUMBL)
        btn_rs, _ = get_button_info("standard", BTN_THUMBR)

        self.assertIn("A", btn_a)
        self.assertIn("B", btn_b)
        self.assertIn("X", btn_x)
        self.assertIn("Y", btn_y)
        self.assertIn("LB", btn_lb)
        self.assertIn("RB", btn_rb)
        self.assertIn("LT", btn_lt)
        self.assertIn("RT", btn_rt)
        self.assertIn("Select", btn_sel)
        self.assertIn("Start", btn_sta)
        self.assertIn("Guide", btn_gui)
        self.assertIn("L3", btn_ls)
        self.assertIn("R3", btn_rs)

        # 3. MainWindow event handling with -32767..32767 sticks and 0..255 triggers
        win = MainWindow()
        mock_dev = GamepadDevice("RP2040 Gamepad rp2040", event_path=None, key_bits=key_bits, abs_bits=abs_bits)
        mock_dev.abs_info = abs_info
        win.current_device = mock_dev
        win.current_profile_key = "standard"
        win._update_axis_mappings()

        # Left stick: ABS_X full right (32767)
        win._on_input_event(RawInputEvent(100.0, EV_ABS, ABS_X, 32767))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_x, 1.0, places=2)

        # Left stick: ABS_Y full up (-32767)
        win._on_input_event(RawInputEvent(100.1, EV_ABS, ABS_Y, -32767))
        self.assertAlmostEqual(win.left_stick_analyzer.curr_y, 1.0, places=2)

        # Right stick: ABS_RX (Right Stick X) full left (-32767)
        win._on_input_event(RawInputEvent(100.2, EV_ABS, ABS_RX, -32767))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_x, -1.0, places=2)

        # Right stick: ABS_RY (Right Stick Y) full down (32767)
        win._on_input_event(RawInputEvent(100.3, EV_ABS, ABS_RY, 32767))
        self.assertAlmostEqual(win.right_stick_analyzer.curr_y, -1.0, places=2)

        # Analog triggers: ABS_Z (LT) full press (255)
        win._on_input_event(RawInputEvent(100.4, EV_ABS, ABS_Z, 255))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 100.0, places=1)
        self.assertEqual(r_pct, 0.0)

        # Analog triggers: ABS_RZ (RT) full press (255)
        win._on_input_event(RawInputEvent(100.5, EV_ABS, ABS_RZ, 255))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 100.0, places=1)
        self.assertAlmostEqual(r_pct, 100.0, places=1)

        # Release triggers
        win._on_input_event(RawInputEvent(100.6, EV_ABS, ABS_Z, 0))
        win._on_input_event(RawInputEvent(100.7, EV_ABS, ABS_RZ, 0))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertAlmostEqual(l_pct, 0.0, places=1)
        self.assertAlmostEqual(r_pct, 0.0, places=1)

        # Digital triggers: BTN_TL2 (LT) and BTN_TR2 (RT)
        win._on_input_event(RawInputEvent(100.8, EV_KEY, BTN_TL2, 1))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 100.0)

        win._on_input_event(RawInputEvent(100.9, EV_KEY, BTN_TL2, 0))
        l_pct, r_pct = win.triggers_analyzer.get_normalized_values()
        self.assertEqual(l_pct, 0.0)

        win.close()

    def test_touchpad_and_motion_diagnostics(self):
        """Verifies TouchpadAnalyzer, MotionAnalyzer 3D wireframe clipping, and TouchpadMotionWidget."""
        import os
        import math
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        from src.analysis.touchpad import TouchpadAnalyzer
        from src.analysis.motion import MotionAnalyzer
        from src.ui.widgets.touchpad_motion_widget import (
            TouchpadMotionWidget, extract_visible_arc_segments, _transform_pt
        )
        from src.core.constants import (
            EV_KEY, EV_ABS, EV_SYN,
            ABS_X, ABS_Y, ABS_Z, ABS_RX, ABS_RY, ABS_RZ,
            ABS_MT_SLOT, ABS_MT_TRACKING_ID, ABS_MT_POSITION_X, ABS_MT_POSITION_Y,
            BTN_LEFT
        )

        # 1. TouchpadAnalyzer multitouch & physical click
        tp = TouchpadAnalyzer()
        tp.set_raw_ranges(0, 1919, 0, 1079)
        tp.process_event(EV_ABS, ABS_MT_SLOT, 0)
        tp.process_event(EV_ABS, ABS_MT_TRACKING_ID, 42)
        tp.process_event(EV_ABS, ABS_MT_POSITION_X, 960)
        tp.process_event(EV_ABS, ABS_MT_POSITION_Y, 540)
        tp.process_event(EV_KEY, BTN_LEFT, 1)

        slots, clicked, clicks, touches = tp.get_snapshot()
        self.assertTrue(slots[0]["active"])
        self.assertAlmostEqual(slots[0]["norm_x"], 0.5, places=2)
        self.assertAlmostEqual(slots[0]["norm_y"], 0.5, places=2)
        self.assertTrue(clicked)
        self.assertEqual(clicks, 1)
        self.assertEqual(touches, 1)

        tp.process_event(EV_ABS, ABS_MT_TRACKING_ID, -1)
        tp.process_event(EV_KEY, BTN_LEFT, 0)
        slots, clicked, _, _ = tp.get_snapshot()
        self.assertFalse(slots[0]["active"])
        self.assertFalse(clicked)

        # 2. MotionAnalyzer orientation, accelerometer shift & back-hemisphere clipping
        motion = MotionAnalyzer()
        motion.process_event(EV_ABS, ABS_Y, 8192, 0.0)  # 1.0g resting accel
        motion.process_event(EV_SYN, 0, 0, 0.0)
        motion.recenter(calibrate_bias=False)

        # Rotate Pitch +120 deg (past 90 deg -> front pole moves onto back hemisphere z < 0)
        raw_rate = int(120.0 * 1024)
        for i in range(1, 11):
            t = i * 0.1
            motion.process_event(EV_ABS, ABS_RX, raw_rate, t)
            motion.process_event(EV_ABS, ABS_Y, 4096, t)  # 0.5g -> shift -0.5g
            motion.process_event(EV_SYN, 0, 0, t)

        snap = motion.get_snapshot()
        self.assertAlmostEqual(snap["shift_y_g"], -0.5, places=2)
        self.assertGreater(len(snap["history"]), 5)

        R = snap["rot_matrix"]
        _, _, pz = _transform_pt(R, (0.0, 0.0, 1.0))
        self.assertLess(pz, 0.0)  # Pole is behind sphere -> hidden

        eq_pts = [(math.cos(2.0 * math.pi * i / 64), 0.0, math.sin(2.0 * math.pi * i / 64)) for i in range(64)]
        vis_segs = extract_visible_arc_segments(R, eq_pts)
        # Roughly half the great circle is visible (front hemisphere z >= 0)
        self.assertGreater(len(vis_segs), 20)
        self.assertLess(len(vis_segs), 40)

        # 3. TouchpadMotionWidget UI + availability banners + repaint
        class MockDev:
            def __init__(self, has_tp, has_imu):
                self.has_touchpad = has_tp
                self.has_motion = has_imu

        w = TouchpadMotionWidget(tp, motion)
        w.set_current_device(MockDev(False, False))
        self.assertFalse(w.lbl_tp_status.isHidden())
        self.assertFalse(w.lbl_gyro_status.isHidden())
        self.assertFalse(w.btn_recenter.isEnabled())

        w.set_current_device(MockDev(True, True))
        self.assertTrue(w.lbl_tp_status.isHidden())
        self.assertTrue(w.lbl_gyro_status.isHidden())
        self.assertTrue(w.btn_recenter.isEnabled())

        w.resize(900, 600)
        w.tp_canvas.repaint()
        w.gyro_canvas.repaint()
        w.plot.repaint()
        w._on_tick()
        w.retranslate_ui()
        w._recenter_gyro()
        snap_after = motion.get_snapshot()
        self.assertAlmostEqual(snap_after["pitch_deg"], 0.0, places=3)

        # 4. Also verify StickWidget, StickOscilloscopeWidget, and PollingWidget QPainter canvases
        from src.ui.widgets.stick_widget import StickWidget
        from src.ui.widgets.snapback_widget import StickOscilloscopeWidget
        from src.ui.widgets.polling_widget import PollingWidget
        from src.analysis.polling import PollingAnalyzer

        stick_an = StickAnalyzer("TestStick")
        stick_an.update_axis(0x00, 16000, 1.0, is_x=True)
        stick_an.update_axis(0x01, -16000, 1.01, is_x=False)
        sw = StickWidget(stick_an)
        sw._on_stage_changed(2)
        sw.update_view()
        sw.canvas.repaint()
        sw._on_stage_changed(3)
        sw.update_view()
        sw.canvas.repaint()

        osc = StickOscilloscopeWidget(stick_an)
        osc.update_plot()
        osc.plot.repaint()

        pa = PollingAnalyzer()
        for k in range(10):
            pa.record_packet(100.0 + k * 0.001)
        pw = PollingWidget(pa)
        pw.update_view()
        pw.plot.repaint()


if __name__ == "__main__":
    unittest.main()
