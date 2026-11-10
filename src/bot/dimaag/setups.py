"""Entry setups (STRATEGY_v2 Parat 2). Har setup ek PARIKALPANA hai; backtest hi batayega chalta hai ya nahi.

Lookahead se bachav: function ko sirf ab tak BAND ho chuki candles milti hain (`cs5[:i+1]`), aur signal
"agli candle ke open par entry" maanta hai. Underlying SL hamesha signal ke saath aata hai.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from bot.dimaag.candles import Candle, ema, vwap
from bot.dimaag.regime import Regime, opening_range

Side = Literal["CALL", "PUT"]


@dataclass(frozen=True, slots=True)
class SetupParams:
    retest_tol_pct: float = 0.05  # retest: OR line se itna paas
    pullback_tol_pct: float = 0.04
    sl_buffer_pct: float = 0.03
    s3_start: int = 13 * 60 + 30
    s3_end: int = 14 * 60 + 45
    first_half_hour_min_pct: float = 0.2  # S3: 9:15-9:45 ki chaal kam se kam itni


@dataclass(frozen=True, slots=True)
class Signal:
    setup: str
    side: Side
    bar_t: int  # signal candle ka minute (entry iske BAAD wali candle par)
    underlying_sl: float
    reason: str


def _side(reg: Regime) -> Side | None:
    return "CALL" if reg == Regime.TREND_UP else "PUT" if reg == Regime.TREND_DOWN else None


def s1_orb_retest(cs5: Sequence[Candle], reg: Regime, p: SetupParams) -> Signal | None:
    """Range ke bahar BAND, phir retest hold: aakhri candle line ko chhu kar trend ki taraf band ho."""
    side = _side(reg)
    rng = opening_range(cs5)
    if side is None or rng is None or len(cs5) < 5:
        return None
    hi, lo = rng
    after = cs5[3:-1]  # range ke baad, aakhri (signal) candle se pehle
    last = cs5[-1]
    vw = vwap(cs5)[-1]
    if side == "CALL":
        broke = any(c.c > hi for c in after)
        retest = last.l <= hi * (1 + p.retest_tol_pct / 100) and last.c > hi and last.c > last.o and last.c > vw
        if broke and retest:
            return Signal("S1", side, last.t, hi * (1 - p.sl_buffer_pct / 100), f"ORB {hi:.2f} ke upar retest hold")
    else:
        broke = any(c.c < lo for c in after)
        retest = last.h >= lo * (1 - p.retest_tol_pct / 100) and last.c < lo and last.c < last.o and last.c < vw
        if broke and retest:
            return Signal("S1", side, last.t, lo * (1 + p.sl_buffer_pct / 100), f"ORB {lo:.2f} ke neeche retest hold")
    return None


def s2_vwap_pullback(cs5: Sequence[Candle], reg: Regime, p: SetupParams, name: str = "S2") -> Signal | None:
    """Trend din: daam VWAP/EMA21 tak wapas aaye aur trend ki taraf band ho."""
    side = _side(reg)
    if side is None or len(cs5) < 5:
        return None
    last = cs5[-1]
    vw = vwap(cs5)[-1]
    e21 = ema([c.c for c in cs5], 21)[-1]
    if side == "CALL":
        touch = last.l <= max(vw, e21) * (1 + p.pullback_tol_pct / 100)
        if touch and last.c > vw and last.c > last.o:
            return Signal(
                name, side, last.t, min(last.l, vw) * (1 - p.sl_buffer_pct / 100), "VWAP pullback ke baad upar band"
            )
    else:
        touch = last.h >= min(vw, e21) * (1 - p.pullback_tol_pct / 100)
        if touch and last.c < vw and last.c < last.o:
            return Signal(
                name, side, last.t, max(last.h, vw) * (1 + p.sl_buffer_pct / 100), "VWAP pullback ke baad neeche band"
            )
    return None


def s3_afternoon(cs5: Sequence[Candle], reg: Regime, p: SetupParams) -> Signal | None:
    """Dopahar momentum: 9:15-9:45 ki chaal aur din ka trend ek taraf, 13:30-14:45 mein S2 jaisa trigger."""
    side = _side(reg)
    if side is None or len(cs5) < 7 or not (p.s3_start <= cs5[-1].t + 5 <= p.s3_end):
        return None
    first = (cs5[5].c - cs5[0].o) / cs5[0].o * 100  # 9:15 open se 9:45 close
    if (side == "CALL" and first < p.first_half_hour_min_pct) or (side == "PUT" and first > -p.first_half_hour_min_pct):
        return None
    return s2_vwap_pullback(cs5, reg, p, name="S3")


def first_signal(cs5: Sequence[Candle], reg: Regime, p: SetupParams) -> Signal | None:
    """Kram: S1, phir S3 (dopahar), phir S2. Pehla jo mile."""
    return s1_orb_retest(cs5, reg, p) or s3_afternoon(cs5, reg, p) or s2_vwap_pullback(cs5, reg, p)
