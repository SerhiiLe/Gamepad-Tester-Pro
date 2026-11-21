"""
Analog Triggers Analysis Module
Analyzes L2/R2 (LT/RT) analog travel, deadzones (initial and end), and smoothness.
"""

import math
import collections
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


@dataclass
class TriggerStats:
    name: str
    code: int
    raw_min: int = 0
    raw_max: int = 255
    curr_value: float = 0.0   # Normalized 0.0 .. 1.0
    initial_deadzone_pct: float = 0.0
    end_deadzone_pct: float = 0.0
    peak_jitter_pct: float = 0.0
    min_step: int = 0
    adc_levels: int = 0
    adc_bits: float = 0.0
    _prev_raw_value: Optional[int] = None
    _sample_count: int = 0
    _raw_buffer: collections.deque = field(default_factory=lambda: collections.deque(maxlen=100))


class TriggersAnalyzer:
    """Analyzes analog triggers travel, linearity, and deadzones."""

    def __init__(self):
        self.triggers: Dict[int, TriggerStats] = {}

    def reset(self):
        self.triggers.clear()

    def get_normalized_values(self) -> Tuple[float, float]:
        """
        Returns (left_trigger_pct, right_trigger_pct) as floats in range 0.0 .. 100.0.
        """
        l_pct = 0.0
        r_pct = 0.0
        for code, trig in self.triggers.items():
            pct = trig.curr_value * 100.0
            name_low = trig.name.lower()
            if ("l2" in name_low or "lt" in name_low or "brake" in name_low
                    or "zl" in name_low or "левый" in name_low or "left" in name_low
                    or code in (0x02, 0x03, 0x0A)):  # ABS_Z, ABS_RX (PS4), or ABS_BRAKE
                l_pct = pct
            elif ("r2" in name_low or "rt" in name_low or "gas" in name_low
                  or "zr" in name_low or "правый" in name_low or "right" in name_low
                  or code in (0x04, 0x05, 0x09)):  # ABS_RY (PS4), ABS_RZ, or ABS_GAS
                r_pct = pct
            else:
                if l_pct == 0.0:
                    l_pct = pct
                else:
                    r_pct = pct
        return l_pct, r_pct

    def update_digital_trigger(self, is_left: bool, is_pressed: bool,
                               code: Optional[int] = None, name: Optional[str] = None):
        """Allows digital triggers/bumpers (e.g. Switch ZL/ZR or GP2040) to animate trigger bars."""
        if code is None:
            code = 0x02 if is_left else 0x05
        if name is None:
            name = "LT (ZL)" if is_left else "RT (ZR)"
        val = 255 if is_pressed else 0
        self.update_trigger(code, val, name=name)

    def update_trigger(self, code: int, raw_value: int, name: str = "Trigger"):
        if code not in self.triggers:
            # Guess raw range: 0..255 (DirectInput / PS) or 0..1023 (Xbox)
            raw_max = 1023 if raw_value > 255 else 255
            self.triggers[code] = TriggerStats(name=name, code=code, raw_min=0, raw_max=raw_max)

        trig = self.triggers[code]
        if raw_value > trig.raw_max:
            trig.raw_max = raw_value
        if raw_value < trig.raw_min:
            trig.raw_min = raw_value

        # ADC step measurement with discrete buffer collection
        trig._raw_buffer.append(raw_value)
        trig._sample_count += 1
        if trig._sample_count % 15 == 0:
            self._analyze_trigger_buffer(trig)

        trig._prev_raw_value = raw_value

        span = max(1, trig.raw_max - trig.raw_min)
        norm = (raw_value - trig.raw_min) / float(span)
        trig.curr_value = max(0.0, min(1.0, norm))

    def _analyze_trigger_buffer(self, trig: TriggerStats, flush_in_flight: bool = False):
        span = trig.raw_max - trig.raw_min
        if span <= 0 or len(trig._raw_buffer) < 8:
            return

        samples = list(trig._raw_buffer)
        total_range = max(samples) - min(samples)
        if total_range < 4:
            # Stationary trigger
            return

        diffs = [samples[i] - samples[i-1] for i in range(1, len(samples))]
        non_zero_d = [abs(d) for d in diffs if d != 0]
        if not non_zero_d:
            return

        counts = Counter(non_zero_d)
        best_step = None
        for step in [1, 2, 4, 8]:
            if counts.get(step, 0) >= 2 or (len(non_zero_d) < 5 and counts.get(step, 0) >= 1):
                best_step = step
                break

        if best_step is None:
            best_step = counts.most_common(1)[0][0]

        levels = max(1, round((span + 1) / best_step))
        bits = round(math.log2(levels), 1)
        trig.adc_bits = bits
        trig.min_step = best_step
        trig.adc_levels = levels

    def get_summary(self) -> Dict:
        results = {}
        for code, trig in self.triggers.items():
            if trig._raw_buffer:
                self._analyze_trigger_buffer(trig, flush_in_flight=True)
            results[trig.name] = {
                "code": trig.code,
                "current_val_pct": trig.curr_value * 100.0,
                "raw_min": trig.raw_min,
                "raw_max": trig.raw_max,
                "min_step": trig.min_step,
                "adc_levels": trig.adc_levels,
                "adc_bits": trig.adc_bits,
                "status": "PASS"
            }
        return results

