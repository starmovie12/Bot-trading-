"""Candles aur indicators (pure functions, koi network nahi). Samay = din ka minute (IST), jaise 9:15 = 555."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

OPEN_MIN = 9 * 60 + 15


@dataclass(frozen=True, slots=True)
class Candle:
    t: int  # candle shuru hone ka minute (IST)
    o: float
    h: float
    l: float  # noqa: E741 (OHLC ka standard naam)
    c: float
    v: float = 0.0

    def __post_init__(self) -> None:
        if not (self.l <= min(self.o, self.c) and self.h >= max(self.o, self.c)):
            raise ValueError(f"galat candle @ {self.t}: o={self.o} h={self.h} l={self.l} c={self.c}")


def resample(c1: Sequence[Candle], n: int) -> list[Candle]:
    """1-min candles ko n-min mein jodo (session 9:15 se gina). Adhuri aakhri candle bhi aati hai."""
    if n <= 0:
        raise ValueError("n > 0")
    groups: dict[int, list[Candle]] = {}
    for c in c1:
        groups.setdefault(OPEN_MIN + (c.t - OPEN_MIN) // n * n, []).append(c)
    return [
        Candle(t, g[0].o, max(x.h for x in g), min(x.l for x in g), g[-1].c, sum(x.v for x in g))
        for t, g in sorted(groups.items())
    ]


def ema(values: Sequence[float], n: int) -> list[float]:
    if n <= 0:
        raise ValueError("n > 0")
    if not values:
        return []
    k = 2 / (n + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def vwap(cs: Sequence[Candle]) -> list[float]:
    """VWAP. Index ka volume nahi hota.

    Volume 0 ho toh typical price ka barabar-vazan average (saaf naam: session average).
    """
    out: list[float] = []
    pv = vol = 0.0
    tp_sum = 0.0
    for i, c in enumerate(cs, 1):
        tp = (c.h + c.l + c.c) / 3
        pv += tp * c.v
        vol += c.v
        tp_sum += tp
        out.append(pv / vol if vol > 0 else tp_sum / i)
    return out


def atr(cs: Sequence[Candle], n: int = 14) -> float:
    if len(cs) < 2:
        return 0.0
    trs = [max(c.h - c.l, abs(c.h - p.c), abs(c.l - p.c)) for p, c in pairwise(cs)]
    tail = trs[-n:]
    return sum(tail) / len(tail)
