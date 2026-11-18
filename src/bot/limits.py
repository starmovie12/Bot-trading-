"""The ONE source of risk limits (MISSION V19 RULES K1): `limits.toml` at the repository root.

Every risk limit the bot uses is read from there by name. The only allowed second source is the gateway's
hard-coded `ABS_MAX_LOTS` (defence in depth), exempt by name. Money is integer rupees.

Fixed rupees: every `_RS` limit is the same number at every balance; `derive_day_limits(effective_balance)` moves
only EQUITY_FLOOR_RS = effective_balance − MAX_TOTAL_LOSS_RS. Chain (tested): 2 × MAX_TRADE_LOSS_RS ≤ MAX_DRAWDOWN_RS
≤ MAX_TOTAL_LOSS_RS ≤ effective balance; MAX_TRADE_LOSS_RS ≤ DAILY ≤ WEEKLY ≤ MONTHLY lock ≤ MAX_TOTAL_LOSS_RS;
LIVE_POSSIBLE = true needs MIN_LIVE_BALANCE_RS ≤ MAX_BALANCE_RS (CAPITAL_RS = MIN); false needs both absent.
"""

from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIMITS_FILE = ROOT / "limits.toml"
ABS_MAX_LOTS = 1  # hard-coded cap per F&O leg (R2); the effective cap is min(MAX_LOTS, ABS_MAX_LOTS)
MIN_COOLOFF = 15  # RULES K1: COOLOFF_MIN >= 15


class InvalidLimits(ValueError):
    """limits.toml is missing a value or breaks the chain: no trading."""


@dataclass(frozen=True, slots=True)
class RiskLimits:
    live_possible: bool
    capital_rs: int
    max_total_loss_rs: int
    equity_floor_rs: int
    max_drawdown_rs: int
    max_trade_loss_rs: int
    daily_loss_lock_rs: int
    weekly_loss_lock_rs: int
    monthly_loss_lock_rs: int
    cooloff_min: int
    max_lots: int
    h2_monthly_rs: int
    min_live_balance_rs: int | None = None
    max_balance_rs: int | None = None

    @property
    def lots_cap(self) -> int:
        return min(self.max_lots, ABS_MAX_LOTS)


def chain_problems(lim: RiskLimits) -> list[str]:
    p = []
    if not 2 * lim.max_trade_loss_rs <= lim.max_drawdown_rs <= lim.max_total_loss_rs <= lim.capital_rs:
        p.append("2 × MAX_TRADE_LOSS_RS ≤ MAX_DRAWDOWN_RS ≤ MAX_TOTAL_LOSS_RS ≤ balance is broken")
    if lim.equity_floor_rs != lim.capital_rs - lim.max_total_loss_rs:
        p.append("EQUITY_FLOOR_RS must equal the balance − MAX_TOTAL_LOSS_RS")
    locks = (lim.daily_loss_lock_rs, lim.weekly_loss_lock_rs, lim.monthly_loss_lock_rs)
    if not lim.max_trade_loss_rs <= locks[0] <= locks[1] <= locks[2] <= lim.max_total_loss_rs:
        p.append("MAX_TRADE_LOSS_RS ≤ DAILY ≤ WEEKLY ≤ MONTHLY loss lock ≤ MAX_TOTAL_LOSS_RS is broken")
    if lim.cooloff_min < MIN_COOLOFF or lim.max_lots < 1:
        p.append(f"COOLOFF_MIN must be ≥ {MIN_COOLOFF} and MAX_LOTS ≥ 1")
    lo, hi = lim.min_live_balance_rs, lim.max_balance_rs
    if lim.live_possible and (lo is None or hi is None or not lim.capital_rs == lo <= hi):
        p.append("LIVE_POSSIBLE = true needs CAPITAL_RS = MIN_LIVE_BALANCE_RS ≤ MAX_BALANCE_RS")
    if not lim.live_possible and (lo, hi) != (None, None):
        p.append("LIVE_POSSIBLE = false: MIN_LIVE_BALANCE_RS and MAX_BALANCE_RS must be absent")
    return p


def load_limits(path: Path = LIMITS_FILE) -> RiskLimits:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))

    def v(name: str, optional: bool = False) -> int | None:
        if name not in raw or "value" not in raw[name]:
            if optional:
                return None
            raise InvalidLimits(f"limits.toml: {name} missing")
        value = raw[name]["value"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidLimits(f"limits.toml: {name} must be an integer")
        return value

    def req(name: str) -> int:
        value = v(name)
        if value is None:  # unreachable: v() raises for a missing required name
            raise InvalidLimits(f"limits.toml: {name} missing")
        return value

    live = raw.get("LIVE_POSSIBLE", {}).get("value", False)  # absent = false (RULES K3: LIVE_BLOCKED)
    if not isinstance(live, bool):
        raise InvalidLimits("limits.toml: LIVE_POSSIBLE must be a boolean")
    lim = RiskLimits(
        live_possible=live,
        capital_rs=req("CAPITAL_RS"),
        max_total_loss_rs=req("MAX_TOTAL_LOSS_RS"),
        equity_floor_rs=req("EQUITY_FLOOR_RS"),
        max_drawdown_rs=req("MAX_DRAWDOWN_RS"),
        max_trade_loss_rs=req("MAX_TRADE_LOSS_RS"),
        daily_loss_lock_rs=req("DAILY_LOSS_LOCK_RS"),
        weekly_loss_lock_rs=req("WEEKLY_LOSS_LOCK_RS"),
        monthly_loss_lock_rs=req("MONTHLY_LOSS_LOCK_RS"),
        cooloff_min=req("COOLOFF_MIN"),
        max_lots=req("MAX_LOTS"),
        h2_monthly_rs=req("H2_MONTHLY_RS"),
        min_live_balance_rs=v("MIN_LIVE_BALANCE_RS", optional=True),
        max_balance_rs=v("MAX_BALANCE_RS", optional=True),
    )
    problems = chain_problems(lim)
    if problems:
        raise InvalidLimits("; ".join(problems))
    return lim


def derive_day_limits(lim: RiskLimits, effective_balance: int) -> RiskLimits:
    """The fixed rupee limits at this balance; only EQUITY_FLOOR_RS follows it. A balance that breaks the chain
    (below MAX_TOTAL_LOSS_RS) raises InvalidLimits: no entry."""
    out = dataclasses.replace(
        lim, capital_rs=effective_balance, equity_floor_rs=effective_balance - lim.max_total_loss_rs
    )
    problems = [p for p in chain_problems(out) if "LIVE_POSSIBLE" not in p]
    if problems:
        raise InvalidLimits("; ".join(problems))
    return out
