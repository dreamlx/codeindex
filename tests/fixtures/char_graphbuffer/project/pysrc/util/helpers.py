"""Small stateless helpers."""

import time


def now_ts() -> int:
    """Return the current unix timestamp."""
    return int(time.time())


def clamp(value: int, low: int, high: int) -> int:
    """Clamp value into the inclusive range [low, high]."""
    return max(low, min(high, value))
