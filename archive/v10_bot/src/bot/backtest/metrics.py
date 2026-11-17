"""Backtest ke number aur Backtest Gate (STRATEGY_v2 Section 5)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from bot.backtest.engine import Trade


@dataclass(frozen=True, slots=True)
class Summary:
    trades: int
    wins: int
    win_rate: float
    net: float
    profit_factor: float
    expectancy: float
    max_drawdown: float
    max_drawdown_pct: float


def summarize(trades: Sequence[Trade], capital: float) -> Summary:
    pnls = [t.pnl for t in trades]
    gp = sum(p for p in pnls if p > 0)
    gl = -sum(p for p in pnls if p < 0)
    eq = peak = capital
    mdd = 0.0
    for p in pnls:
        eq += p
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    n = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    return Summary(
        trades=n,
        wins=wins,
        win_rate=round(wins / n * 100, 2) if n else 0.0,
        net=round(sum(pnls), 2),
        profit_factor=round(gp / gl, 3) if gl > 0 else (float("inf") if gp > 0 else 0.0),
        expectancy=round(sum(pnls) / n, 2) if n else 0.0,
        max_drawdown=round(mdd, 2),
        max_drawdown_pct=round(mdd / capital * 100, 2) if capital else 0.0,
    )


@dataclass(frozen=True, slots=True)
class GateResult:
    ok: bool
    reasons: tuple[str, ...]


def backtest_gate(
    trades: Sequence[Trade],
    capital: float,
    *,
    min_trades: int = 200,
    min_pf: float = 1.3,
    max_dd_pct: float = 20.0,
    oos_frac: float = 0.3,
    max_oos_drop_pct: float = 30.0,
) -> GateResult:
    """Pass tabhi jab saari shartein poori hon. Out-of-sample = samay ke hisaab se aakhri 30% trade."""
    s = summarize(trades, capital)
    bad: list[str] = []
    if s.trades < min_trades:
        bad.append(f"trade kam: {s.trades} < {min_trades}")
    if s.profit_factor < min_pf:
        bad.append(f"profit factor {s.profit_factor} < {min_pf}")
    if s.max_drawdown_pct > max_dd_pct:
        bad.append(f"drawdown {s.max_drawdown_pct}% > {max_dd_pct}%")
    cut = int(len(trades) * (1 - oos_frac))
    ins, oos = summarize(trades[:cut], capital), summarize(trades[cut:], capital)
    if ins.expectancy <= 0:
        bad.append("in-sample mein hi munafa nahi")
    elif (ins.expectancy - oos.expectancy) / ins.expectancy * 100 > max_oos_drop_pct:
        bad.append(f"out-of-sample mein girawat zyada (₹{ins.expectancy}/trade -> ₹{oos.expectancy}/trade)")
    return GateResult(not bad, tuple(bad) if bad else ("saari shartein poori",))
