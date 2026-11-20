"""
High-Precision Input Event Reader
Reads raw Linux input events with hardware microsecond timestamps in a dedicated thread.
"""

import os
import time
import struct
import select
import threading
from typing import Callable, Optional

from .constants import EV_SYN, EV_KEY, EV_ABS, EV_FF


class RawInputEvent:
    """Represents a decoded Linux input event with hardware microsecond timestamp."""
    __slots__ = ('timestamp', 'ev_type', 'code', 'value')

    def __init__(self, timestamp: float, ev_type: int, code: int, value: int):
        self.timestamp = timestamp  # Time in seconds with microsecond resolution (sec + usec / 1e6)
        self.ev_type = ev_type      # EV_KEY, EV_ABS, EV_SYN, etc.
        self.code = code            # Axis code or Key code
        self.value = value          # 0/1 for key, or coordinate value for axis

    def __repr__(self) -> str:
        return f"Event(t={self.timestamp:.6f}, type={self.ev_type}, code={self.code}, val={self.value})"


class InputReader:
    """
    Dedicated worker thread that continuously polls /dev/input/event*
    using select() and unpacks 24-byte kernel input_event structs.
    """

    def __init__(self, event_path: str, event_callback: Optional[Callable[[RawInputEvent], None]] = None):
        self.event_path = event_path
        self.event_callback = event_callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._fd: Optional[int] = None

    def start(self):
        """Starts background reading thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True, name="InputReaderThread")
        self._thread.start()

    def stop(self):
        """Stops background reading thread and closes file descriptor."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.3)
        self._thread = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None

    def _worker(self):
        """Worker loop reading 24-byte Linux input_event structs with hardware timestamps."""
        try:
            self._fd = os.open(self.event_path, os.O_RDONLY | os.O_NONBLOCK)
        except Exception as e:
            print(f"[InputReader] Cannot open {self.event_path}: {e}")
            self._running = False
            return

        # 64-bit Linux struct input_event:
        # struct timeval time (16 bytes: 8 sec + 8 usec)
        # __u16 type (2 bytes)
        # __u16 code (2 bytes)
        # __s32 value (4 bytes)
        # Total: 24 bytes
        event_struct_format = 'qqHHi'
        struct_size = 24

        while self._running:
            try:
                # Wait for data with 50ms timeout to allow clean shutdown
                r, _, _ = select.select([self._fd], [], [], 0.05)
                if not r:
                    continue

                raw_bytes = os.read(self._fd, struct_size * 64)
                if not raw_bytes:
                    continue

                num_events = len(raw_bytes) // struct_size
                for i in range(num_events):
                    chunk = raw_bytes[i * struct_size:(i + 1) * struct_size]
                    sec, usec, ev_type, ev_code, ev_val = struct.unpack(event_struct_format, chunk)
                    ev_time = sec + (usec / 1_000_000.0)

                    event = RawInputEvent(ev_time, ev_type, ev_code, ev_val)
                    if self.event_callback:
                        self.event_callback(event)

            except (BlockingIOError, InterruptedError):
                continue
            except Exception as e:
                if self._running:
                    print(f"[InputReader] Exception in reader loop: {e}")
                break

        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None

