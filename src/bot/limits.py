"""The ONE source of risk limits (MISSION V11 §5.4): `limits.toml` at the repository root.

Every risk limit the bot uses is read from there by name. The only allowed second source is the gateway's
hard-coded `ABS_MAX_LOTS` (I9, defence in depth), exempt by name. Money is integer rupees (I12).

Chain (S11, tested): 2 × MAX_TRADE_LOSS_RS ≤ MAX_DRAWDOWN_RS ≤ MAX_TOTAL_LOSS_RS ≤ CAPITAL_RS,
EQUITY_FLOOR_RS = CAPITAL_RS − MAX_TOTAL_LOSS_RS, MAX_TRADE_LOSS_RS ≤ DAILY_LOSS_LOCK_RS ≤ WEEKLY_LOSS_LOCK_RS
≤ MONTHLY_LOSS_LOCK_RS ≤ MAX_DRAWDOWN_RS.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIMITS_FILE = ROOT / "limits.toml"
ABS_MAX_LOTS = 1  # I9: hard-coded cap per F&O leg; the effective cap is min(MAX_LOTS, ABS_MAX_LOTS)


class InvalidLimits(ValueError):
    """limits.toml is missing a value or breaks the chain: no trading."""


@dataclass(frozen=True, slots=True)
class RiskLimits:
    capital_rs: int
    max_total_loss_rs: int
    equity_floor_rs: int
    max_drawdown_rs: int
    max_trade_loss_rs: int
    daily_loss_lock_rs: int
    weekly_loss_lock_rs: int
    monthly_loss_lock_rs: int
    daily_sl_lock_count: int
    weekly_sl_lock_count: int
    monthly_sl_lock_count: int
    cooloff_min: int
    consecutive_loss_day_stop: int
    max_lots: int
    h2_monthly_rs: int

    @property
    def lots_cap(self) -> int:
        return min(self.max_lots, ABS_MAX_LOTS)


def chain_problems(lim: RiskLimits) -> list[str]:
    p = []
    if not 2 * lim.max_trade_loss_rs <= lim.max_drawdown_rs <= lim.max_total_loss_rs <= lim.capital_rs:
        p.append("2 × MAX_TRADE_LOSS_RS ≤ MAX_DRAWDOWN_RS ≤ MAX_TOTAL_LOSS_RS ≤ CAPITAL_RS is broken")
    if lim.equity_floor_rs != lim.capital_rs - lim.max_total_loss_rs:
        p.append("EQUITY_FLOOR_RS must equal CAPITAL_RS − MAX_TOTAL_LOSS_RS")
    if not lim.max_trade_loss_rs <= lim.daily_loss_lock_rs <= lim.weekly_loss_lock_rs <= lim.monthly_loss_lock_rs:
        p.append("MAX_TRADE_LOSS_RS ≤ DAILY ≤ WEEKLY ≤ MONTHLY loss lock is broken")
    if lim.monthly_loss_lock_rs > lim.max_drawdown_rs:
        p.append("MONTHLY_LOSS_LOCK_RS must not exceed MAX_DRAWDOWN_RS")
    if min(lim.daily_sl_lock_count, lim.cooloff_min, lim.consecutive_loss_day_stop, lim.max_lots) < 1:
        p.append("counts and the cool-off must be positive")
    return p


def load_limits(path: Path = LIMITS_FILE) -> RiskLimits:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))

    def v(name: str) -> int:
        if name not in raw or "value" not in raw[name]:
            raise InvalidLimits(f"limits.toml: {name} missing")
        value = raw[name]["value"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidLimits(f"limits.toml: {name} must be an integer")
        return value

    lim = RiskLimits(
        capital_rs=v("CAPITAL_RS"),
        max_total_loss_rs=v("MAX_TOTAL_LOSS_RS"),
        equity_floor_rs=v("EQUITY_FLOOR_RS"),
        max_drawdown_rs=v("MAX_DRAWDOWN_RS"),
        max_trade_loss_rs=v("MAX_TRADE_LOSS_RS"),
        daily_loss_lock_rs=v("DAILY_LOSS_LOCK_RS"),
        weekly_loss_lock_rs=v("WEEKLY_LOSS_LOCK_RS"),
        monthly_loss_lock_rs=v("MONTHLY_LOSS_LOCK_RS"),
        daily_sl_lock_count=v("DAILY_SL_LOCK_COUNT"),
        weekly_sl_lock_count=v("WEEKLY_SL_LOCK_COUNT"),
        monthly_sl_lock_count=v("MONTHLY_SL_LOCK_COUNT"),
        cooloff_min=v("COOLOFF_MIN"),
        consecutive_loss_day_stop=v("CONSECUTIVE_LOSS_DAY_STOP"),
        max_lots=v("MAX_LOTS"),
        h2_monthly_rs=v("H2_MONTHLY_RS"),
    )
    problems = chain_problems(lim)
    if problems:
        raise InvalidLimits("; ".join(problems))
    return lim
