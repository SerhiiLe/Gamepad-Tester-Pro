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
        self.assertIn("Разрядность АЦП:        ~10 бит", text)
        self.assertIn("АЦП: ~8 бит", text)

        # PDF report
        test_pdf_path = "/tmp/test_gamepad_report.pdf"
        ok = generate_pdf_report(test_pdf_path, dev_info, pdata, bdata, ls, rs, trigs)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(test_pdf_path))
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)

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


if __name__ == "__main__":
    unittest.main()
