"""
Polling Rate & Stability Analysis Module
Measures controller communication bus frequency, timing jitter, and stability.
Accurately accounts for Linux kernel input subsystem event deduplication
(where identical axis/button values are filtered into integer multiples k * T_bus).
"""

import math
import collections
from typing import Dict, List, Tuple


class PollingAnalyzer:
    """
    Measures controller communication bus frequency and timing jitter.
    Distinguishes genuine bus jitter from kernel event deduplication on wired USB.
    """

    def __init__(self, window_size: int = 500, is_wireless: bool = False):
        self.window_size = window_size
        self.is_wireless = is_wireless

        self._timestamps = collections.deque(maxlen=window_size)
        self._deltas_ms = collections.deque(maxlen=window_size)
        self._k1_deltas_ms = collections.deque(maxlen=window_size)
        self._norm_deltas_ms = collections.deque(maxlen=window_size)

        # Real-time metrics
        self.base_interval_ms: float = 4.0
        self.nominal_hz: int = 250
        self.current_hz: float = 0.0
        self.avg_delta_ms: float = 4.0
        self.min_delta_ms: float = float('inf')
        self.max_delta_ms: float = 0.0
        self.min_k1_ms: float = float('inf')
        self.max_k1_ms: float = 0.0
        self.jitter_stddev_ms: float = 0.0
        self.packet_count: int = 0
        self.dedup_packets_count: int = 0
        self.dropped_packets_count: int = 0

    def reset(self):
        """Resets all polling metrics."""
        self._timestamps.clear()
        self._deltas_ms.clear()
        self._k1_deltas_ms.clear()
        self._norm_deltas_ms.clear()
        self.current_hz = 0.0
        self.avg_delta_ms = self.base_interval_ms
        self.min_delta_ms = float('inf')
        self.max_delta_ms = 0.0
        self.min_k1_ms = float('inf')
        self.max_k1_ms = 0.0
        self.jitter_stddev_ms = 0.0
        self.packet_count = 0
        self.dedup_packets_count = 0
        self.dropped_packets_count = 0

    def record_packet(self, timestamp: float):
        """Records arrival of an input event packet with microsecond precision."""
        self.packet_count += 1

        if self._timestamps:
            prev_t = self._timestamps[-1]
            delta_ms = (timestamp - prev_t) * 1000.0

            if 0.1 <= delta_ms <= 100.0:
                self._deltas_ms.append(delta_ms)
                if delta_ms < self.min_delta_ms:
                    self.min_delta_ms = delta_ms
                if delta_ms > self.max_delta_ms:
                    self.max_delta_ms = delta_ms

                # Sliding evaluation every 10 packets
                if len(self._deltas_ms) >= 15 and self.packet_count % 10 == 0:
                    self._recalculate_bus_metrics()

                # Calculate normalized delta using detected base interval
                if self.base_interval_ms > 0:
                    k = max(1, round(delta_ms / self.base_interval_ms))
                    if k > 1 and k <= 6 and abs(delta_ms - k * self.base_interval_ms) <= 0.45 * self.base_interval_ms:
                        self.dedup_packets_count += (k - 1)
                        norm_d = delta_ms / k
                    else:
                        norm_d = delta_ms
                        if self.is_wireless and delta_ms > (self.base_interval_ms * 2.5):
                            self.dropped_packets_count += 1

                    self._norm_deltas_ms.append(norm_d)
                    if abs(delta_ms - self.base_interval_ms) <= 0.30 * self.base_interval_ms:
                        self._k1_deltas_ms.append(delta_ms)
                        if delta_ms < self.min_k1_ms:
                            self.min_k1_ms = delta_ms
                        if delta_ms > self.max_k1_ms:
                            self.max_k1_ms = delta_ms

        self._timestamps.append(timestamp)

    def _recalculate_bus_metrics(self):
        """Extracts the underlying hardware bus clock period T_bus and pure bus jitter."""
        active = [d for d in self._deltas_ms if 0.4 <= d <= 35.0]
        if len(active) < 10:
            return

        # Candidate standard hardware bus intervals: 1.0 (1000Hz), 2.0 (500Hz), 4.0 (250Hz), 8.0 (125Hz)
        candidates = [1.0, 2.0, 4.0, 8.0]
        best_cand = None
        best_score = -1

        for c in candidates:
            k1_hits = sum(1 for d in active if abs(d - c) <= max(0.35, c * 0.18))
            harmonic_hits = sum(1 for d in active if min(abs(d - k * c) for k in (1, 2, 3, 4)) <= max(0.4, c * 0.20))
            score = k1_hits * 2 + harmonic_hits
            if k1_hits >= max(3, len(active) * 0.12) and score > best_score:
                best_score = score
                best_cand = c

        if best_cand is not None:
            self.base_interval_ms = best_cand
            self.nominal_hz = round(1000.0 / best_cand)
            self.current_hz = float(self.nominal_hz)

        # Pure hardware bus jitter measured on consecutive (k=1) packets
        k1_samples = [d for d in active if abs(d - self.base_interval_ms) <= self.base_interval_ms * 0.30]
        if len(k1_samples) >= 6:
            self.avg_delta_ms = sum(k1_samples) / len(k1_samples)
            var = sum((d - self.avg_delta_ms) ** 2 for d in k1_samples) / len(k1_samples)
            self.jitter_stddev_ms = math.sqrt(var)
            self.min_k1_ms = min(k1_samples)
            self.max_k1_ms = max(k1_samples)
        elif self.base_interval_ms > 0:
            self.avg_delta_ms = self.base_interval_ms

    def get_summary(self) -> Dict:
        """Returns polling rate diagnostic summary for reports."""
        status = "PASS"
        if self.jitter_stddev_ms > 1.5:
            status = "WARNING_HIGH_JITTER"

        return {
            "current_hz": round(self.current_hz if self.current_hz > 0 else float(self.nominal_hz), 1),
            "nominal_target_hz": self.nominal_hz,
            "base_interval_ms": round(self.base_interval_ms, 2),
            "avg_interval_ms": round(self.avg_delta_ms, 3),
            "min_interval_ms": round(self.min_k1_ms if self.min_k1_ms != float('inf') else self.base_interval_ms, 3),
            "max_interval_ms": round(self.max_k1_ms if self.max_k1_ms > 0 else self.base_interval_ms, 3),
            "jitter_stddev_ms": round(self.jitter_stddev_ms, 3),
            "total_packets": self.packet_count,
            "dedup_packets": self.dedup_packets_count,
            "dropped_packets": self.dropped_packets_count,
            "is_wireless": self.is_wireless,
            "status": status
        }


