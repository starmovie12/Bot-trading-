"""Backtest + dimaag ke tests. Saara data NAKLI (synthetic, seed se); asli market ka nahi."""

from __future__ import annotations

import math
import random
from datetime import date

import pytest

import bot.backtest.engine as eng
from bot.backtest.engine import BtConfig, DayData, Trade, run, run_day
from bot.backtest.metrics import backtest_gate, summarize
from bot.dimaag.candles import Candle, atr, ema, resample, vwap
from bot.dimaag.regime import Regime, RegimeParams, RegimeTracker, classify, gap_blocks_entry
from bot.dimaag.setups import SetupParams, s1_orb_retest
from bot.strategy.selection import Quote

OPEN = 9 * 60 + 15


def make_day(kind: str, seed: int, base: float = 25000.0) -> list[Candle]:
    rnd = random.Random(seed)  # noqa: S311 (nakli test data, crypto nahi)
    out: list[Candle] = []
    p = base
    for i in range(375):
        if kind == "trend":
            phase = i % 45
            drift = -3.0 if 35 <= phase < 43 else 1.6  # har 45 min mein ek gehra pullback
        else:
            drift = 6 * math.cos(i / 10)  # upar-neeche, kahin nahi jaata
        o = p
        c = p + drift + rnd.gauss(0, 1.2)
        h = max(o, c) + abs(rnd.gauss(0, 1.0))
        lo = min(o, c) - abs(rnd.gauss(0, 1.0))
        out.append(Candle(OPEN + i, round(o, 2), round(h, 2), round(lo, 2), round(c, 2)))
        p = c
    return out


class Book:
    """Nakli option daam: intrinsic + time value (din bhar ghatta). Spread 0.5."""

    def __init__(self, c1: list[Candle], step: int = 50) -> None:
        self.spot = {c.t: c.c for c in c1}
        self.step = step

    def _px(self, minute: int, strike: int, opt: str) -> float:
        s = self.spot[minute]
        intr = max(0.0, s - strike) if opt == "CE" else max(0.0, strike - s)
        tv = s * 0.0042 * (1 - 0.18 * (minute - OPEN) / 375) * math.exp(-abs(s - strike) / (self.step * 7))
        return round(intr + tv, 2)

    def chain(self, minute: int, spot: float) -> list[Quote]:
        atm = round(spot / self.step) * self.step
        out = []
        for k in range(-5, 6):
            strike = atm + k * self.step
            for opt in ("CE", "PE"):
                px = self._px(minute, strike, opt)
                out.append(Quote(strike, opt, px - 0.25, px + 0.25, 200_000))
        return out

    def quote(self, minute: int, strike: int, opt: str) -> tuple[float, float] | None:
        px = self._px(minute, strike, opt)
        return px - 0.25, px + 0.25


def day_data(kind: str, seed: int, d: date = date(2026, 11, 11)) -> DayData:
    c1 = make_day(kind, seed)
    up = (8, 10) if kind == "trend" else (5, 10)
    return DayData(d, "Nifty50", c1, c1[0].o - 5, 40.0, lambda _m: up, lambda _m: 0.5, Book(c1))


# Nakli din Nifty (lot 65) par hain; 30% cap Nifty ko rok deta (alag test). Yahan engine ka logic jaanchna hai.
CFG = BtConfig(capital=15000, daily_loss_limit=1500, kul_jeb_limit=4000, max_capital_use_pct=90)


def test_indicators_basic() -> None:
    cs = [Candle(OPEN + i, 100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(10)]
    r = resample(cs, 5)
    assert [c.t for c in r] == [OPEN, OPEN + 5] and r[0].o == 100 and r[0].c == 104.5 and r[0].h == 105
    assert ema([1, 1, 1], 9) == [1, 1, 1]
    assert vwap(cs)[0] == pytest.approx((101 + 99 + 100.5) / 3)
    assert atr(cs) > 0
    with pytest.raises(ValueError):
        Candle(1, 10, 9, 8, 9.5)  # high open se neeche


def test_regime_tracker_and_gap() -> None:
    tr = RegimeTracker(RegimeParams(stable_bars=2))
    assert tr.update(Regime.TREND_UP) == Regime.UNKNOWN
    assert tr.update(Regime.TREND_UP) == Regime.TREND_UP  # 2 baar ke baad hi badla
    assert tr.update(Regime.RANGE) == Regime.TREND_UP  # ek jhatke mein nahi
    p = RegimeParams()
    assert (
        gap_blocks_entry(OPEN + 10, 1.5, p)
        and not gap_blocks_entry(OPEN + 40, 1.5, p)
        and not gap_blocks_entry(OPEN + 10, 0.3, p)
    )


def test_classify_needs_breadth() -> None:
    cs5 = resample(make_day("trend", 3), 5)[:12]
    assert classify(cs5, breadth_up=8, breadth_total=10, or_width_avg=40, p=RegimeParams()).regime == Regime.TREND_UP
    assert classify(cs5, breadth_up=5, breadth_total=10, or_width_avg=40, p=RegimeParams()).regime == Regime.RANGE


def test_s1_orb_retest_handcrafted() -> None:
    def mk(t: int, o: float, h: float, lo: float, c: float) -> Candle:
        return Candle(OPEN + 5 * t, o, h, lo, c)

    cs5 = [
        mk(0, 100, 102, 99, 101),
        mk(1, 101, 103, 100, 102),
        mk(2, 102, 103, 101, 102.5),
        mk(3, 102.5, 105, 102, 104.5),
        mk(4, 104.5, 105, 103.02, 104.8),
    ]
    sig = s1_orb_retest(cs5, Regime.TREND_UP, SetupParams())
    assert sig is not None and sig.side == "CALL" and sig.underlying_sl < 103
    assert s1_orb_retest(cs5, Regime.RANGE, SetupParams()) is None


def test_range_days_take_no_trades() -> None:
    for seed in range(5):
        assert run_day(day_data("range", seed), CFG, CFG.capital) == []


def test_trend_days_trade_without_lookahead_and_costs_counted() -> None:
    trades: list[Trade] = []
    for seed in range(8):
        got = run_day(day_data("trend", seed), CFG, CFG.capital)
        assert len(got) <= CFG.rules.max_entries, "din mein max 2 entry"
        trades += got
    assert trades, "trend din par kam se kam ek trade hona chahiye"
    for t in trades:
        assert t.entry_t >= t.signal_t + 5, "entry signal candle band hone ke BAAD"
        assert t.side == "CALL" and t.opt == "CE" and t.qty == 65
        assert t.costs > 0
        assert t.pnl == pytest.approx((t.exit - t.entry) * t.qty - t.costs, abs=0.02)
        assert t.exit_t <= 15 * 60 + 15


def test_run_stops_at_kul_jeb_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[date] = []

    def fake(d: DayData, cfg: BtConfig, equity: float) -> list[Trade]:
        calls.append(d.day)
        return [
            Trade(d.day, "Nifty50", "S1", "CALL", 25000, "CE", 600, 605, 620, 100, 60, 65, 50, -4200.0, "stop-loss")
        ]

    monkeypatch.setattr(eng, "run_day", fake)
    days = [day_data("trend", 1, date(2026, 11, d)) for d in (10, 11, 12)]
    out = run(days, CFG)
    assert len(calls) == 1 and len(out) == 1  # pehle din ₹4,200 nuksan: seema ₹4,000 paar, aage koi din nahi


def _t(pnl: float, i: int = 0) -> Trade:
    return Trade(
        date(2026, 1, 1), "Nifty50", "S2", "CALL", 25000, "CE", 600 + i, 605 + i, 620 + i, 100, 100, 65, 50, pnl, "x"
    )


def test_metrics_and_gate() -> None:
    s = summarize([_t(100), _t(-50), _t(200), _t(-100)], 15000)
    assert (s.trades, s.wins, s.net, s.profit_factor, s.max_drawdown) == (4, 2, 150, 2.0, 100)
    g = backtest_gate([_t(100), _t(-50)], 15000)
    assert not g.ok and any("trade kam" in r for r in g.reasons)
    good = [_t(60 if i % 2 == 0 else -30, i) for i in range(250)]
    assert backtest_gate(good, 15000).ok
    decay = [_t(60 if i % 2 == 0 else -30, i) for i in range(175)] + [_t(-40, i) for i in range(75)]
    assert not backtest_gate(decay, 15000).ok
