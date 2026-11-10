"""Backtest engine: din-ba-din, minute-ba-minute. Live bot jaise hi niyam (dimaag + strategy).

Niyam:
- Signal sirf BAND 5-min candle par; entry AGLI minute ke ask (+ slippage) par. Lookahead nahi.
- Exit bid (- slippage) par. Har trade ka kharcha `round_trip` se.
- Kul jeb ka taala: kul nuksan seema par backtest bhi ruk jaata hai (live jaisa).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date, time
from typing import Protocol

from bot.dimaag.candles import OPEN_MIN, Candle, resample
from bot.dimaag.regime import RegimeParams, RegimeTracker, classify, gap_blocks_entry, gap_pct
from bot.dimaag.setups import SetupParams, Signal, first_signal
from bot.strategy.costs import CostModel, round_trip
from bot.strategy.instruments import SPECS, is_expiry_day
from bot.strategy.rules import (
    DayState,
    OpenTrade,
    Params,
    account_allows_trading,
    after_exit,
    can_enter,
    on_tick,
    risk_per_trade,
)
from bot.strategy.selection import Limits, Quote, choose_strike


class OptionBook(Protocol):
    def chain(self, minute: int, spot: float) -> list[Quote]: ...
    def quote(self, minute: int, strike: int, opt: str) -> tuple[float, float] | None: ...  # (bid, ask)


@dataclass(frozen=True, slots=True)
class DayData:
    day: date
    index: str
    c1: Sequence[Candle]  # 1-min underlying candles
    prev_close: float
    or_width_avg: float
    breadth: Callable[[int], tuple[int, int]]  # minute -> (upar, kul)
    vix_change_pct: Callable[[int], float]
    book: OptionBook


@dataclass(frozen=True, slots=True)
class BtConfig:
    capital: float
    daily_loss_limit: float
    kul_jeb_limit: float
    rules: Params = field(default_factory=Params)
    regime: RegimeParams = field(default_factory=RegimeParams)
    setup: SetupParams = field(default_factory=SetupParams)
    costs: CostModel = field(default_factory=CostModel)
    slippage: float = 0.05  # ek tick


@dataclass(frozen=True, slots=True)
class Trade:
    day: date
    index: str
    setup: str
    side: str
    strike: int
    opt: str
    signal_t: int
    entry_t: int
    exit_t: int
    entry: float
    exit: float
    qty: int
    costs: float
    pnl: float
    reason: str


def _hhmm(minute: int) -> time:
    return time(minute // 60, minute % 60)


def run_day(d: DayData, cfg: BtConfig, equity: float) -> list[Trade]:
    spec = SPECS[d.index]
    expiry = is_expiry_day(d.index, d.day)
    gap = gap_pct(d.c1[0].o, d.prev_close) if d.c1 else 0.0
    day = DayState(daily_loss_limit=cfg.daily_loss_limit)
    tracker = RegimeTracker(cfg.regime)
    seen: list[Candle] = []
    pending: Signal | None = None
    open_: tuple[OpenTrade, Signal, int, str, int, int] | None = None  # trade, signal, strike, opt, qty, entry_t
    trades: list[Trade] = []

    def close(price: float, minute: int, reason: str) -> None:
        nonlocal open_, equity
        assert open_ is not None  # noqa: S101
        t, sig, strike, opt, qty, entry_t = open_
        exit_px = round(max(0.05, price - cfg.slippage), 2)
        fees = round_trip(t.entry_price, exit_px, qty, cfg.costs).total
        pnl = round((exit_px - t.entry_price) * qty - fees, 2)
        trades.append(
            Trade(
                d.day,
                d.index,
                sig.setup,
                sig.side,
                strike,
                opt,
                sig.bar_t,
                entry_t,
                minute,
                t.entry_price,
                exit_px,
                qty,
                fees,
                pnl,
                reason,
            )
        )
        after_exit(day, pnl)
        equity += pnl
        open_ = None

    for c in d.c1:
        seen.append(c)
        m = c.t
        if pending is not None and open_ is None:  # entry: signal ke baad wali minute
            sig, pending = pending, None
            sl_points = abs(c.o - sig.underlying_sl)
            lim = Limits(
                capital=equity,
                max_risk_rupees=risk_per_trade(cfg.capital, cfg.daily_loss_limit),
                sl_pct=cfg.rules.sl_pct,
            )
            pick = choose_strike(
                d.index, c.o, sig.side, d.book.chain(m, c.o), lim, cfg.costs, underlying_sl_points=sl_points
            )
            if (
                pick.ok
                and pick.strike is not None
                and pick.opt is not None
                and pick.price is not None
                and pick.sl_price is not None
            ):
                entry = round(pick.price + cfg.slippage, 2)
                ot = OpenTrade(entry_price=entry, entry_minute=m, best_price=entry, sl_price=pick.sl_price)
                open_ = (ot, sig, pick.strike, pick.opt, spec.lot, m)
        if open_ is not None:
            t, sig, strike, opt, _qty, _et = open_
            q = d.book.quote(m, strike, opt)
            if q is not None:
                broken = c.c < sig.underlying_sl if sig.side == "CALL" else c.c > sig.underlying_sl
                why = on_tick(t, q[0], m, _hhmm(m), cfg.rules, structure_broken=broken)
                if why:
                    close(q[0], m, why)
        if (m + 1 - OPEN_MIN) % 5 == 0 and open_ is None and pending is None:  # 5-min candle band hui
            cs5 = resample(seen, 5)
            up, total = d.breadth(m)
            reading = classify(cs5, breadth_up=up, breadth_total=total, or_width_avg=d.or_width_avg, p=cfg.regime)
            reg = tracker.update(reading.regime)
            ok_acc, _ = account_allows_trading(cfg.capital, equity, cfg.kul_jeb_limit)
            ok, _why = can_enter(
                _hhmm(m + 1), day, cfg.rules, expiry_day=expiry, vix_change_pct=d.vix_change_pct(m), open_position=False
            )
            if ok_acc and ok and not gap_blocks_entry(m + 1, gap, cfg.regime):
                pending = first_signal(cs5, reg, cfg.setup)
    if open_ is not None and d.c1:  # data khatam: zabardasti exit
        last = d.c1[-1]
        q = d.book.quote(last.t, open_[2], open_[3])
        close(q[0] if q else open_[0].entry_price, last.t, "data khatam")
    return trades


def run(days: Sequence[DayData], cfg: BtConfig) -> list[Trade]:
    equity = cfg.capital
    out: list[Trade] = []
    for d in days:
        if not account_allows_trading(cfg.capital, equity, cfg.kul_jeb_limit)[0]:
            break
        got = run_day(d, cfg, equity)
        equity += sum(t.pnl for t in got)
        out.extend(got)
    return out
