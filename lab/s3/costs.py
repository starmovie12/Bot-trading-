"""Costs of program S3 (V3 §5): dated charges to the paisa (no x1.5), fills inside the price, cost series ids.

Every component is computed unrounded; the TOTAL is rounded once, half-up, to the paisa (V3 §5.1).
"""

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal
from typing import Any

from lab.s3.registry import COST, FIX

PAISA = Decimal("0.01")
TICK = Decimal(str(FIX["TICK"]))
COMPONENTS = ("brokerage", "stt", "exchange", "gst", "sebi", "ipft", "stamp")


def rates(day: dt.date) -> dict[str, Any]:
    rows = [r for r in COST["rates"] if dt.date.fromisoformat(r["from"]) <= day]
    if not rows:
        raise ValueError(f"no §5.1 rate row for {day}")
    return max(rows, key=lambda r: r["from"])


def charges(orders: list[tuple[Decimal, int, str]], day: dt.date) -> dict[str, Decimal]:
    """orders = [(price, qty, 'BUY' | 'SELL'), ...]; returns each unrounded component and the rounded total."""
    r = {k: Decimal(str(v)) for k, v in rates(day).items() if k not in ("from", "source")}
    out = dict.fromkeys(COMPONENTS, Decimal(0))
    for price, qty, side in orders:
        turnover = price * qty
        out["brokerage"] += r["brokerage_per_order"]
        out["exchange"] += turnover * r["exchange"]
        out["ipft"] += turnover * r["ipft"]
        out["sebi"] += turnover * r["sebi"]
        if side == "BUY":
            out["stamp"] += turnover * r["stamp_buy"]
        else:
            out["stt"] += turnover * r["stt_sell"]
    out["gst"] = (out["brokerage"] + out["exchange"] + out["ipft"] + out["sebi"]) * r["gst"]
    out["total"] = sum((out[k] for k in COMPONENTS), Decimal(0)).quantize(PAISA, rounding=ROUND_HALF_UP)
    return out


def round_trip(entry: Decimal, exit_: Decimal, qty: int, day: dt.date) -> dict[str, Decimal]:
    return charges([(entry, qty, "BUY"), (exit_, qty, "SELL")], day)


def buy_fill(level: Decimal, half_spread: Decimal, slip: Decimal) -> Decimal:
    return ((level + half_spread + slip) / TICK).to_integral_value(rounding=ROUND_CEILING) * TICK


def sell_fill(level: Decimal, half_spread: Decimal, slip: Decimal) -> Decimal:
    return max(Decimal(0), ((level - half_spread - slip) / TICK).to_integral_value(rounding=ROUND_FLOOR) * TICK)


@dataclass(frozen=True)
class Series:
    """One immutable cost setting (V3 §5.5): BASE, STRESS or PROXY half spread and slippage."""

    name: str
    half_spread: Decimal
    slip: Decimal

    @property
    def series_id(self) -> str:
        blob = {"name": self.name, "half_spread": str(self.half_spread), "slip": str(self.slip), "rates": COST["rates"]}
        return self.name + "-" + hashlib.sha256(json.dumps(blob, sort_keys=True).encode()).hexdigest()[:10]


def base() -> Series:
    return Series("BASE", Decimal(str(COST["SPREAD_FULL_RS"])) / 2, Decimal(str(COST["SLIP_RS"])))


def stress(proxy_median_half: Decimal) -> Series:
    """STRESS half spread = max(2 x BASE half, the median half_spread_PROXY of the entry bars); slip x 2 (V3 §5.3)."""
    b = base()
    hs = max(b.half_spread * Decimal(str(COST["STRESS_SPREAD_MULT"])), proxy_median_half)
    return Series("STRESS", hs, b.slip * Decimal(str(COST["STRESS_SLIP_MULT"])))


def full_spread(full: Decimal) -> Series:
    """A BASE series with another full spread (the cost curve, V3 §5.6)."""
    return Series(f"SPREAD{full}", full / 2, base().slip)
