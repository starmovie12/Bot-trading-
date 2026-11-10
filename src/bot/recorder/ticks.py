"""Journal ke tick se 1-min candles aur option book (backtest ke liye). Future ka data kabhi nahi (lookahead nahi).

Tick record: kind "tick", data {"key": str, "ltp": float, "bid": float?, "ask": float?, "oi": int?}.
Samay: ts_ns (UTC epoch ns) -> din ka IST minute.
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal

from bot.dimaag.candles import OPEN_MIN, Candle
from bot.recorder.journal import Record
from bot.strategy.selection import Quote

IST_OFFSET_NS = (5 * 60 + 30) * 60 * 1_000_000_000
CLOSE_MIN = 15 * 60 + 30


def ist_minute(ts_ns: int) -> int:
    return ((ts_ns + IST_OFFSET_NS) // 60_000_000_000) % (24 * 60)


def candles_from_ticks(records: Iterable[Record], key: str) -> list[Candle]:
    """Session (9:15-15:30) ke ticks se 1-min OHLC. Bina tick wali minute skip (bhari nahi jaati)."""
    bars: dict[int, list[float]] = {}
    for r in records:
        if r.kind != "tick" or r.data.get("key") != key:
            continue
        m = ist_minute(r.ts_ns)
        if not OPEN_MIN <= m < CLOSE_MIN:
            continue
        px = float(r.data["ltp"])
        b = bars.get(m)
        if b is None:
            bars[m] = [px, px, px, px]
        else:
            b[1] = max(b[1], px)
            b[2] = min(b[2], px)
            b[3] = px
    return [Candle(m, o, h, lo, c) for m, (o, h, lo, c) in sorted(bars.items())]


@dataclass(slots=True)
class _Series:
    minutes: list[int] = field(default_factory=list)
    quotes: list[tuple[float, float, int]] = field(default_factory=list)  # bid, ask, oi


class RecordedBook:
    """Recorded option ticks se `OptionBook`. Kisi minute par wahi quote jo us minute ke ANT tak aa chuka tha."""

    def __init__(self, records: Iterable[Record], keymap: Mapping[str, tuple[int, Literal["CE", "PE"]]]) -> None:
        self._s: dict[tuple[int, str], _Series] = {}
        for r in records:
            if r.kind != "tick":
                continue
            k = keymap.get(str(r.data.get("key")))
            if k is None or r.data.get("bid") is None or r.data.get("ask") is None:
                continue
            s = self._s.setdefault(k, _Series())
            m = ist_minute(r.ts_ns)
            q = (float(r.data["bid"]), float(r.data["ask"]), int(r.data.get("oi") or 0))
            if s.minutes and s.minutes[-1] == m:
                s.quotes[-1] = q  # usi minute ka naya quote
            else:
                s.minutes.append(m)
                s.quotes.append(q)

    def _at(self, key: tuple[int, str], minute: int) -> tuple[float, float, int] | None:
        s = self._s.get(key)
        if s is None:
            return None
        i = bisect.bisect_right(s.minutes, minute) - 1
        return s.quotes[i] if i >= 0 else None

    def quote(self, minute: int, strike: int, opt: str) -> tuple[float, float] | None:
        q = self._at((strike, opt), minute)
        return (q[0], q[1]) if q else None

    def chain(self, minute: int, spot: float) -> list[Quote]:
        out: list[Quote] = []
        for (strike, opt), _s in self._s.items():
            q = self._at((strike, opt), minute)
            if q is not None and opt in ("CE", "PE"):
                out.append(Quote(strike, "CE" if opt == "CE" else "PE", q[0], q[1], q[2]))
        return out
