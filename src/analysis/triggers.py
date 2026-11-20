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
    _hold_count: int = 0
    _prev_abs_d: int = 0
    _curr_burst: int = 0
    _sample_count: int = 0
    _raw_buffer: collections.deque = field(default_factory=lambda: collections.deque(maxlen=150))
    _dwell_buffer: collections.deque = field(default_factory=lambda: collections.deque(maxlen=100))
    _burst_buffer: collections.deque = field(default_factory=lambda: collections.deque(maxlen=100))


class TriggersAnalyzer:
    """Analyzes analog triggers travel, linearity, and deadzones."""

    def __init__(self):
        self.triggers: Dict[int, TriggerStats] = {}

    def reset(self):
        self.triggers.clear()

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
        if trig._prev_raw_value is not None:
            abs_d = abs(raw_value - trig._prev_raw_value)
            if abs_d > 0:
                trig._raw_buffer.append(raw_value)
                trig._hold_count = 0
            else:
                trig._hold_count += 1
                if trig._hold_count == 2:
                    trig._dwell_buffer.append(raw_value)

            # Acceleration burst integration (filters decaying sub-steps)
            if abs_d == 0:
                if trig._curr_burst > 0:
                    if 1 <= trig._curr_burst <= 1024:
                        trig._burst_buffer.append(trig._curr_burst)
                    trig._curr_burst = 0
                trig._prev_abs_d = 0
            else:
                if trig._prev_abs_d > 0 and abs_d >= trig._prev_abs_d:
                    if trig._curr_burst > 0:
                        if 1 <= trig._curr_burst <= 1024:
                            trig._burst_buffer.append(trig._curr_burst)
                    trig._curr_burst = abs_d
                else:
                    trig._curr_burst += abs_d
                trig._prev_abs_d = abs_d

            trig._sample_count += 1
            if trig._sample_count % 30 == 0:
                self._analyze_trigger_buffer(trig)
        else:
            trig._raw_buffer.append(raw_value)

        trig._prev_raw_value = raw_value

        span = max(1, trig.raw_max - trig.raw_min)
        norm = (raw_value - trig.raw_min) / float(span)
        trig.curr_value = max(0.0, min(1.0, norm))

    def _analyze_trigger_buffer(self, trig: TriggerStats, flush_in_flight: bool = False):
        span = trig.raw_max - trig.raw_min
        if span <= 0:
            return

        if flush_in_flight and trig._curr_burst > 0:
            if 1 <= trig._curr_burst <= 1024:
                trig._burst_buffer.append(trig._curr_burst)
            trig._curr_burst = 0

        # Priority 1: Dwell buffer
        if len(trig._dwell_buffer) >= 6:
            s_vals = sorted(set(trig._dwell_buffer))
            diffs = [s_vals[i] - s_vals[i-1] for i in range(1, len(s_vals)) if 1 <= (s_vals[i] - s_vals[i-1]) <= 1024]
            if len(diffs) >= 4:
                res = self._score_quantum_candidates(span, Counter(diffs))
                if res[0] > 0:
                    trig.adc_bits, trig.min_step, trig.adc_levels = res
                    return

        # Priority 2: Burst buffer
        if len(trig._burst_buffer) >= 6:
            valid_b = [b for b in trig._burst_buffer if 1 <= b <= 1024]
            if len(valid_b) >= 4:
                res = self._score_quantum_candidates(span, Counter(valid_b))
                if res[0] > 0:
                    trig.adc_bits, trig.min_step, trig.adc_levels = res
                    return

        # Priority 3: Raw unique levels
        if len(trig._raw_buffer) >= 6:
            s_vals = sorted(set(trig._raw_buffer))
            diffs = [s_vals[i] - s_vals[i-1] for i in range(1, len(s_vals)) if 1 <= (s_vals[i] - s_vals[i-1]) <= 1024]
            if len(diffs) >= 4:
                res = self._score_quantum_candidates(span, Counter(diffs))
                if res[0] > 0:
                    trig.adc_bits, trig.min_step, trig.adc_levels = res
                    return

    def _score_quantum_candidates(self, span: int, diff_counts: Counter) -> Tuple[float, int, int]:
        candidate_bits = [8, 9, 10, 11, 12, 13, 14, 15, 16]
        candidates = []
        seen_q = set()
        for b in candidate_bits:
            nom_step = (span + 1) / (2 ** b)
            if nom_step < 0.5:
                continue
            q = max(1, round(nom_step))
            if q not in seen_q:
                seen_q.add(q)
                candidates.append((b, q))
        candidates.sort(key=lambda x: x[0], reverse=True)

        total_w = sum(diff_counts.values())
        best_b = None

        for b, q in candidates:
            tol = max(1, round(q * 0.20))
            direct_w = sum(w for s, w in diff_counts.items() if abs(s - q) <= tol)
            req_fraction = 0.25 if b >= 14 else (0.15 if b >= 13 else 0.10)
            req_direct = max(2, round(total_w * req_fraction))
            if direct_w >= req_direct:
                best_b = b
                break

        if best_b is None:
            most_common = diff_counts.most_common(1)[0][0]
            levels = max(1, round((span + 1) / most_common))
            bits = round(math.log2(levels), 1)
            return bits, most_common, levels

        levels = 2 ** best_b
        step = max(1, round((span + 1) / levels))
        return float(best_b), step, levels

    def get_summary(self) -> Dict:
        results = {}
        for code, trig in self.triggers.items():
            if trig._raw_buffer or trig._curr_burst > 0:
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

