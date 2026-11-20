"""
Analog Sticks Analysis Module
Analyzes analog sticks in real-time with stage-gated metric recording
and separate tracking for X and Y axes to diagnose individual potentiometers and springs:
- Center drift X & Y
- Resistor / sensor noise X & Y (using robust successive-difference method to isolate true ADC/wiper jitter from hand drift)
- Snapback overshoot X & Y
- Circularity 360° (with smooth perimeter tracking down to r >= 0.55 for all controller gates)
"""

import math
import collections
from collections import Counter
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field


@dataclass
class SnapbackEvent:
    """Represents a detected snapback (stick overshooting opposite half-plane on release)."""
    timestamp: float
    axis_name: str
    release_from: float       # Starting position (e.g. +1.0)
    overshoot_peak: float     # Max opposite deflection (e.g. -0.22)
    return_duration_ms: float
    waveform: List[Tuple[float, float]] = field(default_factory=list)


class StickAnalyzer:
    """
    Performs real-time physics and signal analysis for a single 2D stick (X, Y).
    Separates X and Y metrics to identify specific potentiometer/spring degradation.
    """

    def __init__(self, name: str = "Left Stick"):
        self.name = name

        # Active test stage (0: Free, 1: Center, 2: Circle, 3: Targets, 4: Snapback)
        self.active_stage: int = 0
        self.is_inside_target: bool = False

        # Completion flags
        self.center_tested: bool = False
        self.circularity_tested: bool = False
        self.jitter_tested: bool = False
        self.snapback_tested: bool = False

        # Raw coordinate ranges
        self.raw_min_x: int = -32768
        self.raw_max_x: int = 32767
        self.raw_min_y: int = -32768
        self.raw_max_y: int = 32767

        # Current normalized state (-1.0 .. +1.0)
        self.curr_x: float = 0.0
        self.curr_y: float = 0.0
        self.curr_raw_x: int = 0
        self.curr_raw_y: int = 0

        # Stage 1: Center drift per axis
        self.center_drift_pct: float = 0.0
        self.center_drift_x_pct: float = 0.0
        self.center_drift_y_pct: float = 0.0

        # Stage 2: Circularity & Outer Envelope
        self.boundary_points: List[Tuple[float, float]] = []
        self._outer_envelope: Dict[int, float] = {}              # bin_idx (0..71) -> max_r
        self._outer_points: Dict[int, Tuple[float, float]] = {}  # bin_idx -> (x, y)
        self.circularity_error_pct: float = 0.0
        self.max_radial_reach: float = 0.0
        self.gate_shape_detected: str = "Круглый (с безелем)"

        # Stage 3: Jitter in target zones per axis
        self._target_samples: List[Tuple[float, float]] = []
        self.held_jitter_x: float = 0.0
        self.held_jitter_y: float = 0.0
        self.peak_jitter_x_pct: float = 0.0
        self.peak_jitter_y_pct: float = 0.0
        self.peak_jitter_pct: float = 0.0

        # History for waveform oscilloscope (always active)
        self._history = collections.deque(maxlen=300)
        self.last_flick_waveform: List[Tuple[float, float]] = []
        self.last_flick_axis: str = "X"
        self._tracking_release = False
        self._release_start_time = 0.0
        self._release_start_x = 0.0
        self._release_start_y = 0.0
        self._release_raw_history: List[Tuple[float, float, float]] = []
        self._release_max_overshoot: float = 0.0
        self._release_overshoot_axis: str = "X"

        # Stage 4: Snapback dynamics & series
        self.target_flicks_count: int = 10
        self.total_flicks: int = 0
        self.total_flicks_x: int = 0
        self.total_flicks_y: int = 0
        self.snapback_flicks: int = 0
        self.snapback_flicks_x: int = 0
        self.snapback_flicks_y: int = 0
        self.snapback_rate_pct: float = 0.0
        self.snapback_rate_x_pct: float = 0.0
        self.snapback_rate_y_pct: float = 0.0
        self.peak_snapback_pct: float = 0.0
        self.peak_snapback_x_pct: float = 0.0
        self.peak_snapback_y_pct: float = 0.0
        self.snapback_events: List[SnapbackEvent] = []

        # ADC Quantization & Resolution measurement (discrete buffer in Stage 0)
        self._prev_raw_x: Optional[int] = None
        self._prev_raw_y: Optional[int] = None
        self._adc_raw_buffer_x = collections.deque(maxlen=120)
        self._adc_raw_buffer_y = collections.deque(maxlen=120)
        self._adc_sample_counter: int = 0
        self.adc_step_x: int = 0
        self.adc_step_y: int = 0
        self.adc_levels_x: int = 0
        self.adc_levels_y: int = 0
        self.adc_bits_x: float = 0.0
        self.adc_bits_y: float = 0.0
        self.adc_step: int = 0
        self.adc_levels: int = 0
        self.adc_bits: float = 0.0

    def reset(self):
        """Resets all metrics and trajectory buffers."""
        self.boundary_points.clear()
        self._outer_envelope.clear()
        self._outer_points.clear()
        self.circularity_error_pct = 0.0
        self.max_radial_reach = 0.0
        self.gate_shape_detected = "Круглый (с безелем)"
        self.center_drift_pct = 0.0
        self.center_drift_x_pct = 0.0
        self.center_drift_y_pct = 0.0
        self.total_flicks = 0
        self.total_flicks_x = 0
        self.total_flicks_y = 0
        self.snapback_flicks = 0
        self.snapback_flicks_x = 0
        self.snapback_flicks_y = 0
        self.snapback_rate_pct = 0.0
        self.snapback_rate_x_pct = 0.0
        self.snapback_rate_y_pct = 0.0
        self.peak_snapback_pct = 0.0
        self.peak_snapback_x_pct = 0.0
        self.peak_snapback_y_pct = 0.0
        self.snapback_events.clear()
        self.last_flick_waveform.clear()
        self._history.clear()
        self._target_samples.clear()
        self.held_jitter_x = 0.0
        self.held_jitter_y = 0.0
        self.peak_jitter_x_pct = 0.0
        self.peak_jitter_y_pct = 0.0
        self.peak_jitter_pct = 0.0

        self.center_tested = False
        self.circularity_tested = False
        self.jitter_tested = False
        self.snapback_tested = False
        self._tracking_release = False
        self._release_max_overshoot = 0.0

        # Reset ADC measurements
        self._prev_raw_x = None
        self._prev_raw_y = None
        self._adc_raw_buffer_x.clear()
        self._adc_raw_buffer_y.clear()
        self._adc_sample_counter = 0
        self.adc_step_x = 0
        self.adc_step_y = 0
        self.adc_levels_x = 0
        self.adc_levels_y = 0
        self.adc_bits_x = 0.0
        self.adc_bits_y = 0.0
        self.adc_step = 0
        self.adc_levels = 0
        self.adc_bits = 0.0

    def clear_target_samples(self):
        """Clears target samples when entering/leaving a target circle."""
        self._target_samples.clear()
        self.held_jitter_x = 0.0
        self.held_jitter_y = 0.0

    def clear_circularity_track(self):
        """Clears circularity boundary track and outer envelope for a fresh run."""
        self.boundary_points.clear()
        self._outer_envelope.clear()
        self._outer_points.clear()
        self.circularity_error_pct = 0.0
        self.circularity_tested = False
        self.gate_shape_detected = "Круглый (с безелем)"

    def update_axis(self, axis_code: int, raw_value: int, timestamp: float, is_x: bool):
        """Updates X or Y coordinate and runs stage-gated diagnostics."""
        if is_x:
            self.curr_raw_x = raw_value
            # ADC estimation is strictly gated to Stage 0 (Free mode) with zero overhead in other stages!
            if self.active_stage == 0:
                self._collect_adc_buffer(raw_value, is_x=True)
            self._prev_raw_x = raw_value

            span = max(1, self.raw_max_x - self.raw_min_x)
            center = (self.raw_max_x + self.raw_min_x) / 2.0
            self.curr_x = (raw_value - center) / (span / 2.0)
            self.curr_x = max(-1.0, min(1.0, self.curr_x))
        else:
            self.curr_raw_y = raw_value
            # ADC estimation is strictly gated to Stage 0 (Free mode) with zero overhead in other stages!
            if self.active_stage == 0:
                self._collect_adc_buffer(raw_value, is_x=False)
            self._prev_raw_y = raw_value

            span = max(1, self.raw_max_y - self.raw_min_y)
            center = (self.raw_max_y + self.raw_min_y) / 2.0
            # Invert Y so Up is +1.0, Down is -1.0
            self.curr_y = -((raw_value - center) / (span / 2.0))
            self.curr_y = max(-1.0, min(1.0, self.curr_y))

        self._history.append((timestamp, self.curr_x, self.curr_y))

        # Always track release waveform for bottom oscilloscope
        self._track_waveform_and_snapback(timestamp)

        # STAGE-GATED ANALYTICS:
        if self.active_stage == 1:
            # Stage 1: Center & Drift (separated per axis)
            dist = math.hypot(self.curr_x, self.curr_y)
            if dist < 0.20:
                self.center_drift_pct = dist * 100.0
                self.center_drift_x_pct = abs(self.curr_x) * 100.0
                self.center_drift_y_pct = abs(self.curr_y) * 100.0
                self.center_tested = True

        elif self.active_stage == 2:
            # Stage 2: Circularity 360°
            self._analyze_circularity(self.curr_x, self.curr_y)

        elif self.active_stage == 3:
            # Stage 3: Jitter in target zones per axis
            if self.is_inside_target:
                self._record_target_jitter_sample(self.curr_x, self.curr_y)

    def _collect_adc_buffer(self, raw_value: int, is_x: bool):
        """
        Gathers raw coordinate samples into discrete rolling buffers in Stage 0.
        Analysis is performed discretely over the small buffer rather than continuously.
        """
        if is_x:
            self._adc_raw_buffer_x.append(raw_value)
        else:
            self._adc_raw_buffer_y.append(raw_value)

        self._adc_sample_counter += 1
        # Discretely evaluate buffer every 20 samples
        if self._adc_sample_counter % 20 == 0:
            self._analyze_adc_buffers()

    def _analyze_buffer_for_axis(self, span: int, raw_buf: collections.deque) -> Optional[Tuple[float, int, int]]:
        """
        Robustly extracts the physical hardware ADC step from raw coordinate stream.
        1. Stationary Deadband: If the stick is held still or resting (span < 120),
           returns None to prevent capturing smoothed wiper/thermal sensor noise as 15-bit!
        2. High-speed cutoff: Rejects fast flick intervals (> 250 units/sample).
        3. Direct hardware quantum: Detects unsmoothed steps (multiples of 8, 16, 32, 64...).
        4. Transition jerk peaks: Under firmware EMA/IIR filtering, isolates the acceleration
           spikes occurring at each physical raw quantum conversion (+16 for 12-bit, +64 for 10-bit),
           yielding the exact hardware step completely independent of hand velocity!
        5. Fine ADC (13..16 bit): Requires wide physical travel (span >= 800) with >= 20 unique levels.
        """
        if len(raw_buf) < 15:
            return None

        samples = list(raw_buf)
        total_range = max(samples) - min(samples)
        # Stationary rejection: stationary wiper noise has peak-to-peak < 120 (out of 65535)
        if total_range < 120:
            return None

        diffs = [samples[i] - samples[i-1] for i in range(1, len(samples))]
        mean_speed = sum(abs(d) for d in diffs) / len(diffs)
        if mean_speed > 250.0:
            # Too fast for micro-quantization
            return None

        # Check 1: Direct unsmoothed hardware ADC steps
        non_zero_d = [abs(d) for d in diffs if d != 0]
        if len(non_zero_d) >= 6:
            counts = Counter(non_zero_d)
            c_step, c_count = counts.most_common(1)[0]
            if c_step >= 8 and (c_count / len(non_zero_d)) >= 0.35:
                cand_q = [8, 16, 32, 64, 128, 256]
                best_q = min(cand_q, key=lambda q: abs(q - c_step))
                if abs(best_q - c_step) <= max(1, round(best_q * 0.15)):
                    levels = max(1, round((span + 1) / best_q))
                    return float(round(math.log2(levels), 1)), best_q, levels

        # Check 2: Transition jerk peaks under firmware low-pass (EMA) filtering
        pos_peaks = []
        for i in range(1, len(diffs) - 1):
            if diffs[i] >= 2 and diffs[i] > diffs[i-1] and diffs[i] >= diffs[i+1]:
                pos_peaks.append(i)

        neg_peaks = []
        for i in range(1, len(diffs) - 1):
            if diffs[i] <= -2 and diffs[i] < diffs[i-1] and diffs[i] <= diffs[i+1]:
                neg_peaks.append(i)

        peak_diffs = []
        if len(pos_peaks) >= 2:
            for j in range(1, len(pos_peaks)):
                d_pos = abs(samples[pos_peaks[j]] - samples[pos_peaks[j-1]])
                if 6 <= d_pos <= 256:
                    peak_diffs.append(d_pos)
        if len(neg_peaks) >= 2:
            for j in range(1, len(neg_peaks)):
                d_neg = abs(samples[neg_peaks[j]] - samples[neg_peaks[j-1]])
                if 6 <= d_neg <= 256:
                    peak_diffs.append(d_neg)

        if len(peak_diffs) >= 3:
            sorted_p = sorted(peak_diffs)
            med = sorted_p[len(sorted_p) // 2]
            cand_q = [8, 16, 32, 64, 128, 256]
            best_q = min(cand_q, key=lambda q: abs(q - med))
            if abs(best_q - med) <= best_q * 0.40:
                levels = max(1, round((span + 1) / best_q))
                return float(round(math.log2(levels), 1)), best_q, levels

        # Check 3: Genuine fine ADC (13..16 bit) only on wide physical movement
        unique_vals = set(samples)
        if total_range >= 800 and len(unique_vals) >= 20:
            s_vals = sorted(unique_vals)
            u_diffs = [s_vals[i] - s_vals[i-1] for i in range(1, len(s_vals)) if 1 <= (s_vals[i] - s_vals[i-1]) <= 64]
            if len(u_diffs) >= 10:
                sorted_u = sorted(u_diffs)
                med_u = sorted_u[len(sorted_u) // 2]
                for b in [16, 15, 14, 13]:
                    q = max(1, round((span + 1) / (2 ** b)))
                    if abs(med_u - q) <= max(1, round(q * 0.35)):
                        levels = 2 ** b
                        return float(b), q, levels

        return None

    def _analyze_adc_buffers(self, flush_in_flight: bool = False):
        """Updates adc_bits, adc_step, and adc_levels from discrete buffers."""
        span_x = max(1, self.raw_max_x - self.raw_min_x)
        span_y = max(1, self.raw_max_y - self.raw_min_y)

        res_x = self._analyze_buffer_for_axis(span_x, self._adc_raw_buffer_x)
        res_y = self._analyze_buffer_for_axis(span_y, self._adc_raw_buffer_y)

        if res_x is not None:
            self.adc_bits_x, self.adc_step_x, self.adc_levels_x = res_x
        if res_y is not None:
            self.adc_bits_y, self.adc_step_y, self.adc_levels_y = res_y

        if self.adc_bits_x > 0 and self.adc_bits_y > 0:
            self.adc_bits = max(self.adc_bits_x, self.adc_bits_y)
            self.adc_step = min(self.adc_step_x, self.adc_step_y)
            self.adc_levels = max(self.adc_levels_x, self.adc_levels_y)
        elif self.adc_bits_x > 0:
            self.adc_bits = self.adc_bits_x
            self.adc_step = self.adc_step_x
            self.adc_levels = self.adc_levels_x
        elif self.adc_bits_y > 0:
            self.adc_bits = self.adc_bits_y
            self.adc_step = self.adc_step_y
            self.adc_levels = self.adc_levels_y

    def _analyze_circularity(self, x: float, y: float):
        """
        Only runs during Stage 2: captures the outer physical gate perimeter and computes circularity error.
        Uses 72 angular bins (5° each) tracking the maximum radial deflection reached in each sector.
        This fundamentally excludes lead-in (moving stick from center to rim) and lead-out (releasing back to center)
        distortions, calculating the pure geometry of the outer gate without false errors!
        Also detects whether the gate is Circular (bezel) or Square (unbezeled/raw).
        """
        r = math.hypot(x, y)
        if r > self.max_radial_reach:
            self.max_radial_reach = r

        if r >= 0.50:
            angle = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
            bin_idx = int(angle // 5.0)  # 72 bins of 5 degrees each (0..71)

            # Store the outermost reached coordinate in this sector
            prev_max = self._outer_envelope.get(bin_idx, 0.0)
            if r > prev_max:
                self._outer_envelope[bin_idx] = r
                self._outer_points[bin_idx] = (x, y)
                self._rebuild_perimeter_track()

            if len(self._outer_envelope) >= 12:
                # Calculate deviation of outer envelope from ideal circle (r = 1.0)
                deviations = [abs(r_val - 1.0) for r_val in self._outer_envelope.values()]
                self.circularity_error_pct = (sum(deviations) / len(deviations)) * 100.0
                self.circularity_tested = True

                # Gate shape classification:
                # In square gates, corners at 45°, 135°, 225°, 315° (bins 9, 27, 45, 63)
                # overshoot up to sqrt(2) ≈ 1.41 (+41.4%)
                diag_bins = [9, 27, 45, 63]
                diag_reaches = [self._outer_envelope.get(b, 0.0) for b in diag_bins]
                max_diag = max(diag_reaches) if diag_reaches else 0.0
                if max_diag >= 1.22 and self.circularity_error_pct >= 10.0:
                    self.gate_shape_detected = "Квадратный (без безеля)"
                elif max(self._outer_envelope.values(), default=0.0) <= 1.15:
                    self.gate_shape_detected = "Круглый (с безелем)"
                else:
                    self.gate_shape_detected = "Нестандартный"

    def _rebuild_perimeter_track(self):
        """
        Reconstructs boundary_points strictly from the outer envelope points.
        Builds smooth continuous perimeter segments along the physical rim without
        spurious radial lines to/from the center.
        """
        if not self._outer_points:
            self.boundary_points = []
            return

        visited = sorted(self._outer_points.keys())
        total_bins = 72

        if len(visited) == total_bins:
            # Closed 360° ring
            pts = [self._outer_points[b] for b in range(total_bins)]
            pts.append(self._outer_points[0])
            self.boundary_points = pts
            return

        # Partial arc: find start bin preceded by an unvisited gap
        start_bin = visited[0]
        for b in visited:
            prev_b = (b - 1) % total_bins
            if prev_b not in self._outer_points:
                start_bin = b
                break

        idx = start_bin
        ordered_pts = []
        visited_set = set()

        for _ in range(total_bins):
            if idx in self._outer_points and idx not in visited_set:
                ordered_pts.append(self._outer_points[idx])
                visited_set.add(idx)
                next_idx = (idx + 1) % total_bins
                if next_idx not in self._outer_points:
                    ordered_pts.append((float('nan'), float('nan')))
            idx = (idx + 1) % total_bins

        self.boundary_points = ordered_pts

    def get_circularity_coverage_pct(self) -> float:
        """Returns 0..100% of 360° perimeter covered."""
        return min(100.0, (len(self._outer_envelope) / 72.0) * 100.0)

    def _record_target_jitter_sample(self, x: float, y: float):
        """
        Only runs during Stage 3 when inside a target circle.
        Uses first-order successive differences (delta_x = x[i+1] - x[i]) to extract
        pure high-frequency sensor/ADC noise while eliminating slow hand drift!
        For white noise: sigma_noise = std(delta) / sqrt(2).
        """
        self._target_samples.append((x, y))
        if len(self._target_samples) >= 12:
            recent = self._target_samples[-40:]
            diffs_x = [recent[i + 1][0] - recent[i][0] for i in range(len(recent) - 1)]
            diffs_y = [recent[i + 1][1] - recent[i][1] for i in range(len(recent) - 1)]

            # Filter out intentional gross manual motion jumps (> 0.05 per frame is stick movement)
            valid_dx = [d for d in diffs_x if abs(d) < 0.05]
            valid_dy = [d for d in diffs_y if abs(d) < 0.05]

            if len(valid_dx) >= 8:
                var_dx = sum(d ** 2 for d in valid_dx) / len(valid_dx)
                self.held_jitter_x = math.sqrt(var_dx / 2.0) * 100.0
                if self.held_jitter_x > self.peak_jitter_x_pct:
                    self.peak_jitter_x_pct = self.held_jitter_x

            if len(valid_dy) >= 8:
                var_dy = sum(d ** 2 for d in valid_dy) / len(valid_dy)
                self.held_jitter_y = math.sqrt(var_dy / 2.0) * 100.0
                if self.held_jitter_y > self.peak_jitter_y_pct:
                    self.peak_jitter_y_pct = self.held_jitter_y

            total_jitter = math.hypot(self.held_jitter_x, self.held_jitter_y)
            if total_jitter > self.peak_jitter_pct:
                self.peak_jitter_pct = total_jitter

            self.jitter_tested = True

    def _track_waveform_and_snapback(self, timestamp: float):
        """
        Tracks release dynamics for the bottom oscilloscope and evaluates snapback probability.
        A complete flick is measured across the full release window (~65 ms), capturing the
        true maximum overshoot peak, total flick count, and snapback probability (%).
        """
        r = math.hypot(self.curr_x, self.curr_y)

        # 1. Arming state: stick deflected to the edge
        if not self._tracking_release:
            if r >= 0.65:
                self._release_start_time = timestamp
                self._release_start_x = self.curr_x
                self._release_start_y = self.curr_y
                self._release_max_overshoot = 0.0
                self._release_overshoot_axis = "X" if abs(self.curr_x) >= abs(self.curr_y) else "Y"
                self._release_raw_history = [(timestamp, self.curr_x, self.curr_y)]
                self._tracking_release = True
        else:
            # 2. In release motion
            self._release_raw_history.append((timestamp, self.curr_x, self.curr_y))
            dt_release_ms = (timestamp - self._release_start_time) * 1000.0

            # If user is simply holding the stick at the rim (r stays >= 0.60):
            # Shift start time continuously until the stick is actually released!
            if r >= 0.60 and dt_release_ms > 30.0:
                self._release_start_time = timestamp
                self._release_start_x = self.curr_x
                self._release_start_y = self.curr_y
                self._release_max_overshoot = 0.0
                self._release_overshoot_axis = "X" if abs(self.curr_x) >= abs(self.curr_y) else "Y"
                self._release_raw_history = [(timestamp, self.curr_x, self.curr_y)]
                return

            # Check for overshoot in the opposite half-plane
            dot_prod = (self.curr_x * self._release_start_x) + (self.curr_y * self._release_start_y)
            primary_x = (abs(self._release_start_x) >= abs(self._release_start_y))

            if dot_prod < -0.01:
                opp_mag = abs(self.curr_x) if primary_x else abs(self.curr_y)
                if opp_mag > self._release_max_overshoot:
                    self._release_max_overshoot = opp_mag
                    self._release_overshoot_axis = "X" if primary_x else "Y"

            # 3. Completion of the flick (window reaches 65 ms or stick settled at center)
            settled_at_center = (r < 0.10 and dt_release_ms >= 15.0)
            if dt_release_ms >= 65.0 or settled_at_center:
                t0 = self._release_raw_history[0][0]
                valid_pts = [p for p in self._release_raw_history if (p[0] - t0) * 1000.0 <= 70.0]
                rel_waveform = []
                for t_ev, x_val, y_val in valid_pts:
                    rel_ms = (t_ev - t0) * 1000.0
                    val = x_val if primary_x else y_val
                    rel_waveform.append((rel_ms, val))

                self.last_flick_waveform = rel_waveform
                self.last_flick_axis = "X" if primary_x else "Y"

                # If in Stage 4: evaluate flick series and snapback probability
                if self.active_stage == 4:
                    self.snapback_tested = True
                    overshoot_pct = self._release_max_overshoot * 100.0
                    has_snap = (self._release_max_overshoot >= 0.05)

                    if primary_x:
                        self.total_flicks_x += 1
                        if overshoot_pct > self.peak_snapback_x_pct:
                            self.peak_snapback_x_pct = overshoot_pct
                        if has_snap:
                            self.snapback_flicks_x += 1
                        self.snapback_rate_x_pct = (self.snapback_flicks_x / self.total_flicks_x) * 100.0
                    else:
                        self.total_flicks_y += 1
                        if overshoot_pct > self.peak_snapback_y_pct:
                            self.peak_snapback_y_pct = overshoot_pct
                        if has_snap:
                            self.snapback_flicks_y += 1
                        self.snapback_rate_y_pct = (self.snapback_flicks_y / self.total_flicks_y) * 100.0

                    self.total_flicks = self.total_flicks_x + self.total_flicks_y
                    self.snapback_flicks = self.snapback_flicks_x + self.snapback_flicks_y
                    self.snapback_rate_pct = (self.snapback_flicks / self.total_flicks) * 100.0
                    self.peak_snapback_pct = max(self.peak_snapback_x_pct, self.peak_snapback_y_pct)

                    # Snapback occurs if overshoot exceeds 5.0%
                    if has_snap:
                        axis_name = "X-Axis" if primary_x else "Y-Axis"
                        event = SnapbackEvent(
                            timestamp=timestamp,
                            axis_name=axis_name,
                            release_from=math.hypot(self._release_start_x, self._release_start_y),
                            overshoot_peak=self._release_max_overshoot,
                            return_duration_ms=dt_release_ms,
                            waveform=rel_waveform
                        )
                        self.snapback_events.append(event)

                self._tracking_release = False

    def get_summary(self) -> Dict:
        snapback_count = len(self.snapback_events)
        max_snapback_pct = self.peak_snapback_pct
        max_snap_x = self.peak_snapback_x_pct
        max_snap_y = self.peak_snapback_y_pct

        status = "PASS"
        issues = []
        if self.circularity_tested and self.circularity_error_pct > 8.0:
            status = "WARNING"
            issues.append(f"Повышенная ошибка геометрии ({self.circularity_error_pct:.1f}%)")
        if self.snapback_tested and self.snapback_rate_pct > 20.0 and max_snapback_pct > 5.0:
            status = "FAIL_SNAPBACK"
            issues.append(f"Высокая вероятность Snapback ({self.snapback_rate_pct:.0f}%, пик {max_snapback_pct:.1f}%)")
        elif self.snapback_tested and self.snapback_rate_pct > 0.0:
            status = "WARNING"
            issues.append(f"Зафиксирован Snapback (вероятность {self.snapback_rate_pct:.0f}%, пик {max_snapback_pct:.1f}%)")
        if self.jitter_tested and self.peak_jitter_pct > 2.0:
            status = "WARNING"
            issues.append(f"Повышенный джиттер ({self.peak_jitter_pct:.2f}%)")

        # Finalize any in-flight ADC calculations
        if self._adc_raw_buffer_x or self._adc_raw_buffer_y:
            self._analyze_adc_buffers(flush_in_flight=True)

        return {
            "name": self.name,
            "center_drift_pct": self.center_drift_pct,
            "center_drift_x_pct": self.center_drift_x_pct,
            "center_drift_y_pct": self.center_drift_y_pct,
            "center_tested": self.center_tested,
            "circularity_error_pct": self.circularity_error_pct,
            "circularity_tested": self.circularity_tested,
            "gate_shape": self.gate_shape_detected,
            "max_reach": self.max_radial_reach,
            "peak_jitter_pct": self.peak_jitter_pct,
            "peak_jitter_x_pct": self.peak_jitter_x_pct,
            "peak_jitter_y_pct": self.peak_jitter_y_pct,
            "jitter_tested": self.jitter_tested,
            "total_flicks": self.total_flicks,
            "total_flicks_x": self.total_flicks_x,
            "total_flicks_y": self.total_flicks_y,
            "snapback_flicks": self.snapback_flicks,
            "snapback_flicks_x": self.snapback_flicks_x,
            "snapback_flicks_y": self.snapback_flicks_y,
            "snapback_rate_pct": self.snapback_rate_pct,
            "snapback_rate_x_pct": self.snapback_rate_x_pct,
            "snapback_rate_y_pct": self.snapback_rate_y_pct,
            "snapback_count": snapback_count,
            "max_snapback_overshoot_pct": max_snapback_pct,
            "max_snapback_x_pct": max_snap_x,
            "max_snapback_y_pct": max_snap_y,
            "snapback_tested": self.snapback_tested,
            "adc_bits": self.adc_bits,
            "adc_step": self.adc_step,
            "adc_levels": self.adc_levels,
            "adc_bits_x": self.adc_bits_x,
            "adc_step_x": self.adc_step_x,
            "adc_levels_x": self.adc_levels_x,
            "adc_bits_y": self.adc_bits_y,
            "adc_step_y": self.adc_step_y,
            "adc_levels_y": self.adc_levels_y,
            "status": status,
            "issues": issues
        }
