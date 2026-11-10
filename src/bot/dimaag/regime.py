"""Din ka Mausam (regime): sirf Trend din par entry. Range din = koi trade nahi (sabse bada bachav).

Shartein (STRATEGY_v2 Parat 1): daam VWAP ke ek taraf + EMA 9/21 usi taraf + breadth (top 10 mein >= 7) usi taraf.
Mausam ek jhatke mein na badle: `RegimeTracker` lagatar N candle ek jaisa hone par hi badalta hai.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

from bot.dimaag.candles import Candle, ema, vwap


class Regime(Enum):
    TREND_UP = "trend-up"
    TREND_DOWN = "trend-down"
    RANGE = "range"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RegimeParams:
    min_candles: int = 4  # 5-min candles (pehle 20 min mausam nahi)
    breadth_min: int = 7  # 10 mein se
    min_or_width_ratio: float = 0.5  # opening range pichhle 10 din ke average ka kam se kam itna
    gap_pct_block: float = 1.0
    gap_block_minutes: int = 30
    stable_bars: int = 2


@dataclass(frozen=True, slots=True)
class Reading:
    regime: Regime
    reasons: tuple[str, ...]


def opening_range(cs5: Sequence[Candle], bars: int = 3) -> tuple[float, float] | None:
    """Pehli `bars` 5-min candles (default 9:15-9:30) ka (high, low)."""
    if len(cs5) < bars:
        return None
    first = cs5[:bars]
    return max(c.h for c in first), min(c.l for c in first)


def classify(
    cs5: Sequence[Candle], *, breadth_up: int, breadth_total: int, or_width_avg: float, p: RegimeParams
) -> Reading:
    if len(cs5) < p.min_candles or breadth_total <= 0:
        return Reading(Regime.UNKNOWN, ("abhi data kam",))
    closes = [c.c for c in cs5]
    e9 = ema(closes, 9)[-1]
    e21 = ema(closes, 21)[-1]
    vw = vwap(cs5)[-1]
    last = closes[-1]
    rng = opening_range(cs5)
    reasons: list[str] = []
    if rng and or_width_avg > 0 and (rng[0] - rng[1]) < p.min_or_width_ratio * or_width_avg:
        reasons.append("opening range bahut patla (sust din)")
    up = last > vw and e9 > e21 and breadth_up >= p.breadth_min
    down = last < vw and e9 < e21 and (breadth_total - breadth_up) >= p.breadth_min
    if reasons:
        return Reading(Regime.RANGE, tuple(reasons))
    if up:
        return Reading(Regime.TREND_UP, (f"VWAP ke upar, EMA9>EMA21, breadth {breadth_up}/{breadth_total}",))
    if down:
        return Reading(
            Regime.TREND_DOWN,
            (f"VWAP ke neeche, EMA9<EMA21, breadth {breadth_total - breadth_up}/{breadth_total} neeche",),
        )
    return Reading(Regime.RANGE, ("VWAP/EMA/breadth ek taraf nahi",))


@dataclass(slots=True)
class RegimeTracker:
    p: RegimeParams = field(default_factory=RegimeParams)
    current: Regime = Regime.UNKNOWN
    _candidate: Regime = Regime.UNKNOWN
    _count: int = 0

    def update(self, r: Regime) -> Regime:
        if r == self.current:
            self._count = 0
            return self.current
        if r == self._candidate:
            self._count += 1
        else:
            self._candidate, self._count = r, 1
        if self._count >= self.p.stable_bars:
            self.current, self._count = r, 0
        return self.current


def gap_pct(day_open: float, prev_close: float) -> float:
    if prev_close <= 0:
        raise ValueError("prev_close > 0")
    return (day_open - prev_close) / prev_close * 100


def gap_blocks_entry(minute: int, gap: float, p: RegimeParams) -> bool:
    """Bada gap (>1%) ho toh 9:15 ke baad pehle 30 min koi entry nahi."""
    return abs(gap) > p.gap_pct_block and minute < 9 * 60 + 15 + p.gap_block_minutes
