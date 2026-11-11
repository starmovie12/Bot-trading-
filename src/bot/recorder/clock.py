"""IST time helpers for the Recorder (I11). Standard library only, so the Recorder bundle needs no strategy code."""

from __future__ import annotations

IST_OFFSET_NS = (5 * 60 + 30) * 60 * 1_000_000_000


def ist_minute(ts_ns: int) -> int:
    """Minute of the IST day for a UTC epoch timestamp in nanoseconds (09:15 IST = 555)."""
    return ((ts_ns + IST_OFFSET_NS) // 60_000_000_000) % (24 * 60)
