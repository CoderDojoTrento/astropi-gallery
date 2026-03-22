"""
Virtual timer for recording animations without real-time delays.

When activated, `time.sleep()` no longer blocks — it just advances an
internal clock. The SenseHat mock reads this clock for frame timestamps,
so the video output has correct timing even though the script finishes
in milliseconds.
"""

import time as _real_time

_virtual_clock = 0.0
_active = False
_real_sleep = _real_time.sleep
_real_monotonic = _real_time.monotonic
_base_monotonic = 0.0


def activate():
    """
    Monkey-patch time.sleep and time.monotonic so scripts run instantly
    while preserving correct relative timestamps.
    """
    global _virtual_clock, _active, _base_monotonic
    _virtual_clock = 0.0
    _active = True
    _base_monotonic = _real_monotonic()
    _real_time.sleep = _virtual_sleep
    _real_time.monotonic = _virtual_monotonic


def deactivate():
    """Restore real time functions."""
    global _active
    _active = False
    _real_time.sleep = _real_sleep
    _real_time.monotonic = _real_monotonic


def _virtual_sleep(seconds):
    """Advance the virtual clock instead of actually sleeping."""
    global _virtual_clock
    if seconds > 0:
        _virtual_clock += seconds
    # Yield briefly so the process can be killed if needed
    _real_sleep(0.0001)


def _virtual_monotonic():
    """Return base + virtual elapsed time."""
    return _base_monotonic + _virtual_clock


def now():
    """Return the current virtual time offset (seconds since activation)."""
    return _virtual_clock
