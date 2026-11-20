"""
Polling Rate & Stability Analysis Module
Calculates polling frequency (Hz), inter-packet interval delta (dt),
jitter (standard deviation of dt), min/max delta, and detects dropped packets.
"""

import math
import collections
from typing import Dict, List, Tuple


class PollingAnalyzer:
    """
    Measures controller communication bus frequency and timing jitter.
    Tracks packet arrivals with microsecond precision.
    """

    def __init__(self, window_size: int = 500):
        self.window_size = window_size
        self._timestamps = collections.deque(maxlen=window_size)
        self._deltas_ms = collections.deque(maxlen=window_size)

        # Real-time metrics
        self.current_hz: float = 0.0
        self.avg_delta_ms: float = 0.0
        self.min_delta_ms: float = float('inf')
        self.max_delta_ms: float = 0.0
        self.jitter_stddev_ms: float = 0.0
        self.packet_count: int = 0
        self.dropped_packets_count: int = 0

    def reset(self):
        """Resets all polling metrics."""
        self._timestamps.clear()
        self._deltas_ms.clear()
        self.current_hz = 0.0
        self.avg_delta_ms = 0.0
        self.min_delta_ms = float('inf')
        self.max_delta_ms = 0.0
        self.jitter_stddev_ms = 0.0
        self.packet_count = 0
        self.dropped_packets_count = 0

    def record_packet(self, timestamp: float):
        """Records arrival of an input packet."""
        self.packet_count += 1

        if self._timestamps:
            prev_t = self._timestamps[-1]
            delta_ms = (timestamp - prev_t) * 1000.0

            # Ignore non-positive deltas
            if delta_ms > 0:
                self._deltas_ms.append(delta_ms)
                if delta_ms < self.min_delta_ms:
                    self.min_delta_ms = delta_ms
                if delta_ms > self.max_delta_ms:
                    self.max_delta_ms = delta_ms

                # Detect dropped packet (interval > 2.5x of expected)
                if self.avg_delta_ms > 0 and delta_ms > (self.avg_delta_ms * 2.5):
                    self.dropped_packets_count += 1

        self._timestamps.append(timestamp)

        # Compute sliding metrics if we have enough samples
        if len(self._timestamps) >= 10:
            duration = self._timestamps[-1] - self._timestamps[0]
            if duration > 0:
                self.current_hz = (len(self._timestamps) - 1) / duration

            if self._deltas_ms:
                self.avg_delta_ms = sum(self._deltas_ms) / len(self._deltas_ms)
                variance = sum((d - self.avg_delta_ms) ** 2 for d in self._deltas_ms) / len(self._deltas_ms)
                self.jitter_stddev_ms = math.sqrt(variance)

    def get_summary(self) -> Dict:
        """Returns polling rate diagnostic summary for reports."""
        nominal_hz = 125
        if self.current_hz > 700:
            nominal_hz = 1000
        elif self.current_hz > 350:
            nominal_hz = 500
        elif self.current_hz > 180:
            nominal_hz = 250

        # Quality rating
        status = "PASS"
        if self.jitter_stddev_ms > 1.5 and nominal_hz >= 500:
            status = "WARNING_HIGH_JITTER"

        return {
            "current_hz": round(self.current_hz, 1),
            "nominal_target_hz": nominal_hz,
            "avg_interval_ms": round(self.avg_delta_ms, 3),
            "min_interval_ms": round(self.min_delta_ms if self.min_delta_ms != float('inf') else 0, 3),
            "max_interval_ms": round(self.max_delta_ms, 3),
            "jitter_stddev_ms": round(self.jitter_stddev_ms, 3),
            "total_packets": self.packet_count,
            "dropped_packets": self.dropped_packets_count,
            "status": status
        }

