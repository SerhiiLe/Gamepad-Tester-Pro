"""
Gamepad Touchpad Analysis Module
Tracks multitouch finger positions (slots 0..1), single-touch fallback,
recent motion trails, and physical touchpad clicks (DualSense / DualShock 4).
"""

import collections
import threading
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Tuple

from ..core.constants import (
    EV_KEY, EV_ABS,
    ABS_X, ABS_Y,
    ABS_MT_SLOT, ABS_MT_POSITION_X, ABS_MT_POSITION_Y, ABS_MT_TRACKING_ID,
    BTN_LEFT, BTN_TOUCH
)


@dataclass
class TouchPoint:
    """State of a single multitouch finger slot."""
    slot: int
    tracking_id: int = -1
    active: bool = False
    raw_x: int = 0
    raw_y: int = 0
    norm_x: float = 0.0  # 0.0 .. 1.0 (left -> right)
    norm_y: float = 0.0  # 0.0 .. 1.0 (top -> bottom)
    trail: Deque[Tuple[float, float]] = field(
        default_factory=lambda: collections.deque(maxlen=32)
    )


class TouchpadAnalyzer:
    """Analyzes multitouch touchpad events in real time (thread-safe)."""

    def __init__(self):
        self._lock = threading.Lock()
        self.raw_min_x: int = 0
        self.raw_max_x: int = 1919
        self.raw_min_y: int = 0
        self.raw_max_y: int = 1079

        self._current_slot: int = 0
        self._uses_mt: bool = False
        self.slots: Dict[int, TouchPoint] = {
            0: TouchPoint(slot=0),
            1: TouchPoint(slot=1),
        }

        self.is_clicked: bool = False
        self.click_count: int = 0
        self.total_touches: int = 0

    def reset(self):
        """Resets all touch points, trails, and click counters."""
        with self._lock:
            self._current_slot = 0
            self._uses_mt = False
            for s in self.slots.values():
                s.tracking_id = -1
                s.active = False
                s.raw_x = 0
                s.raw_y = 0
                s.norm_x = 0.0
                s.norm_y = 0.0
                s.trail.clear()
            self.is_clicked = False
            self.click_count = 0
            self.total_touches = 0

    def set_raw_ranges(self, min_x: int, max_x: int, min_y: int, max_y: int):
        """Configures physical touchpad coordinate bounds from evdev absinfo."""
        with self._lock:
            self.raw_min_x = min_x
            self.raw_max_x = max_x if max_x > min_x else min_x + 1919
            self.raw_min_y = min_y
            self.raw_max_y = max_y if max_y > min_y else min_y + 1079

    def _norm_x(self, raw: int) -> float:
        span = max(1, self.raw_max_x - self.raw_min_x)
        return max(0.0, min(1.0, (raw - self.raw_min_x) / float(span)))

    def _norm_y(self, raw: int) -> float:
        span = max(1, self.raw_max_y - self.raw_min_y)
        return max(0.0, min(1.0, (raw - self.raw_min_y) / float(span)))

    def _get_or_create_slot(self, slot_idx: int) -> TouchPoint:
        if slot_idx not in self.slots:
            self.slots[slot_idx] = TouchPoint(slot=slot_idx)
        return self.slots[slot_idx]

    def process_event(self, ev_type: int, code: int, value: int):
        """Processes a raw Linux input event from the touchpad node."""
        with self._lock:
            if ev_type == EV_KEY:
                if code == BTN_LEFT:
                    pressed = (value == 1)
                    if pressed and not self.is_clicked:
                        self.click_count += 1
                    self.is_clicked = pressed
                elif code == BTN_TOUCH and not self._uses_mt:
                    pt = self._get_or_create_slot(0)
                    now_active = (value == 1)
                    if now_active and not pt.active:
                        self.total_touches += 1
                        pt.trail.clear()
                    pt.active = now_active

            elif ev_type == EV_ABS:
                if code == ABS_MT_SLOT:
                    self._uses_mt = True
                    self._current_slot = max(0, value)
                elif code == ABS_MT_TRACKING_ID:
                    self._uses_mt = True
                    pt = self._get_or_create_slot(self._current_slot)
                    pt.tracking_id = value
                    if value >= 0:
                        if not pt.active:
                            self.total_touches += 1
                            pt.trail.clear()
                        pt.active = True
                    else:
                        pt.active = False
                elif code == ABS_MT_POSITION_X:
                    self._uses_mt = True
                    pt = self._get_or_create_slot(self._current_slot)
                    pt.raw_x = value
                    pt.norm_x = self._norm_x(value)
                    if pt.active:
                        pt.trail.append((pt.norm_x, pt.norm_y))
                elif code == ABS_MT_POSITION_Y:
                    self._uses_mt = True
                    pt = self._get_or_create_slot(self._current_slot)
                    pt.raw_y = value
                    pt.norm_y = self._norm_y(value)
                    if pt.active:
                        pt.trail.append((pt.norm_x, pt.norm_y))
                elif code == ABS_X and not self._uses_mt:
                    pt = self._get_or_create_slot(0)
                    pt.raw_x = value
                    pt.norm_x = self._norm_x(value)
                    if pt.active:
                        pt.trail.append((pt.norm_x, pt.norm_y))
                elif code == ABS_Y and not self._uses_mt:
                    pt = self._get_or_create_slot(0)
                    pt.raw_y = value
                    pt.norm_y = self._norm_y(value)
                    if pt.active:
                        pt.trail.append((pt.norm_x, pt.norm_y))

    def clear_trails(self):
        """Clears finger motion trails and click counters."""
        with self._lock:
            for pt in self.slots.values():
                pt.trail.clear()
            self.click_count = 0
            self.total_touches = 0

    def get_snapshot(self) -> Tuple[List[Dict], bool, int, int]:
        """Returns a thread-safe UI snapshot: (slots_data, is_clicked, click_count, total_touches)."""
        with self._lock:
            slots_data = []
            for idx in sorted(self.slots.keys()):
                pt = self.slots[idx]
                slots_data.append({
                    "slot": pt.slot,
                    "active": pt.active,
                    "raw_x": pt.raw_x,
                    "raw_y": pt.raw_y,
                    "norm_x": pt.norm_x,
                    "norm_y": pt.norm_y,
                    "trail": list(pt.trail),
                })
            return slots_data, self.is_clicked, self.click_count, self.total_touches
