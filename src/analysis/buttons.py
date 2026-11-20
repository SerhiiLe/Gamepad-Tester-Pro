"""
Buttons Analysis Module
Tracks button presses, release times, hold durations, and detects contact chatter (bounce) < 7 ms.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ChatterEvent:
    """Represents a detected contact chatter / debounce violation."""
    button_code: int
    button_name: str
    timestamp: float
    delta_ms: float
    transition: str  # 'press-after-release' or 'release-after-press'


@dataclass
class ButtonStats:
    """Statistics for a single button."""
    code: int
    name: str = ""
    description: str = ""
    is_pressed: bool = False
    press_count: int = 0
    chatter_count: int = 0
    last_press_time: float = 0.0
    last_release_time: float = 0.0
    last_hold_duration_ms: float = 0.0
    min_press_interval_ms: float = float('inf')
    chatter_history: List[ChatterEvent] = field(default_factory=list)


class ButtonsAnalyzer:
    """
    Analyzes button press events in real time.
    Flags physical contact chatter whenever state changes faster than 7 ms threshold.
    """

    CHATTER_THRESHOLD_MS: float = 7.0

    def __init__(self):
        self.buttons: Dict[int, ButtonStats] = {}
        self.all_chatter_events: List[ChatterEvent] = []

    def reset(self):
        """Resets all button counters and histories."""
        self.buttons.clear()
        self.all_chatter_events.clear()

    def process_button_event(self, code: int, is_pressed: bool, timestamp: float,
                             name: str = "", desc: str = ""):
        """Processes a single button state change."""
        if code not in self.buttons:
            self.buttons[code] = ButtonStats(
                code=code,
                name=name or f"0x{code:03X}",
                description=desc
            )

        btn = self.buttons[code]
        if name and not btn.name.startswith("0x"):
            btn.name = name
        if desc:
            btn.description = desc

        now_ms = timestamp * 1000.0

        if is_pressed:
            btn.press_count += 1
            btn.is_pressed = True

            # If button was recently released, check interval
            if btn.last_release_time > 0:
                delta_ms = now_ms - (btn.last_release_time * 1000.0)
                if delta_ms < btn.min_press_interval_ms:
                    btn.min_press_interval_ms = delta_ms

                # Chatter check: rapid re-press (< 7 ms) indicates contact bounce
                if 0.0 < delta_ms < self.CHATTER_THRESHOLD_MS:
                    btn.chatter_count += 1
                    event = ChatterEvent(
                        button_code=code,
                        button_name=btn.name,
                        timestamp=timestamp,
                        delta_ms=delta_ms,
                        transition="Rapid re-press (Bounce)"
                    )
                    btn.chatter_history.append(event)
                    self.all_chatter_events.append(event)

            btn.last_press_time = timestamp

        else:
            # Button released
            btn.is_pressed = False
            if btn.last_press_time > 0:
                hold_ms = now_ms - (btn.last_press_time * 1000.0)
                btn.last_hold_duration_ms = hold_ms

                # Chatter check: micro-release (< 7 ms hold)
                if 0.0 < hold_ms < self.CHATTER_THRESHOLD_MS:
                    btn.chatter_count += 1
                    event = ChatterEvent(
                        button_code=code,
                        button_name=btn.name,
                        timestamp=timestamp,
                        delta_ms=hold_ms,
                        transition="Micro-release (< 7ms hold)"
                    )
                    btn.chatter_history.append(event)
                    self.all_chatter_events.append(event)

            btn.last_release_time = timestamp

    def get_summary(self) -> Dict:
        """Returns overall button test summary for reports."""
        total_pressed = len([b for b in self.buttons.values() if b.press_count > 0])
        total_chatter = len(self.all_chatter_events)
        faulty_buttons = [b.name for b in self.buttons.values() if b.chatter_count > 0]

        return {
            "total_buttons_tested": total_pressed,
            "total_chatter_events": total_chatter,
            "faulty_buttons": faulty_buttons,
            "status": "PASS" if total_chatter == 0 else "FAIL_CHATTER"
        }

