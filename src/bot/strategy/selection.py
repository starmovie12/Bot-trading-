"""Strike chunna: "premium quality pehle, sirf 1 lot, sasta OTM kabhi nahi, paisa/risk kam ho toh SKIP".

Kram: 1-step ITM (zyada delta) -> ATM. Har candidate par chaar jaanch:
  1) spread chhota (bid-ask), 2) OI kaafi, 3) 1 lot + kharcha capital ke andar, 4) SL par nuksan max risk ke andar.
Koi pass na ho toh trade SKIP (wajah ke saath). OTM kabhi candidate nahi.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from bot.strategy.costs import CostModel, round_trip
from bot.strategy.instruments import SPECS

Side = Literal["CALL", "PUT"]


@dataclass(frozen=True, slots=True)
class Quote:
    strike: int
    opt: Literal["CE", "PE"]
    bid: float
    ask: float
    oi: int


@dataclass(frozen=True, slots=True)
class Limits:
    capital: float
    max_risk_rupees: float  # ek trade mein SL lagne par max nuksan (kharche samet)
    sl_pct: float = 25.0  # premium par hard SL (%)
    max_capital_use_pct: float = 90.0
    max_spread_pct: float = 1.0  # (ask-bid)/ask
    min_oi: int = 50_000


@dataclass(frozen=True, slots=True)
class Pick:
    ok: bool
    reason: str
    strike: int | None = None
    opt: str | None = None
    price: float | None = None
    qty: int = 0
    cost_rupees: float = 0.0
    risk_rupees: float = 0.0


def _check(q: Quote, qty: int, lim: Limits, costs: CostModel) -> str | None:
    if q.ask <= 0 or q.bid <= 0 or q.bid > q.ask:
        return "quote galat (bid/ask)"
    spread = (q.ask - q.bid) / q.ask * 100
    if spread > lim.max_spread_pct:
        return f"spread {spread:.2f}% > {lim.max_spread_pct}%"
    if q.oi < lim.min_oi:
        return f"OI kam ({q.oi})"
    sl_price = q.ask * (1 - lim.sl_pct / 100)
    fees = round_trip(q.ask, sl_price, qty, costs).total
    cost = q.ask * qty + fees
    if cost > lim.capital * lim.max_capital_use_pct / 100:
        return f"1 lot ₹{cost:,.0f} capital ke {lim.max_capital_use_pct:.0f}% se zyada"
    risk = (q.ask - sl_price) * qty + fees
    if risk > lim.max_risk_rupees:
        return f"SL par nuksan ₹{risk:,.0f} > seema ₹{lim.max_risk_rupees:,.0f}"
    return None


def choose_strike(
    index: str, spot: float, side: Side, chain: list[Quote], lim: Limits, costs: CostModel | None = None
) -> Pick:
    spec = SPECS[index]
    if not spec.tradable:
        return Pick(False, f"{spec.label} sirf signal ke liye (trade nahi)")
    if spot <= 0:
        return Pick(False, "spot galat")
    costs = costs or CostModel()
    atm = round(spot / spec.strike_step) * spec.strike_step
    opt: Literal["CE", "PE"] = "CE" if side == "CALL" else "PE"
    itm = atm - spec.strike_step if side == "CALL" else atm + spec.strike_step
    book = {(q.strike, q.opt): q for q in chain}
    first_reason = None
    for strike in (itm, atm):  # premium quality: pehle ITM, phir ATM; OTM kabhi nahi
        q = book.get((strike, opt))
        if q is None:
            first_reason = first_reason or f"{strike} {opt} ka quote nahi"
            continue
        bad = _check(q, spec.lot, lim, costs)
        if bad:
            first_reason = first_reason or f"{strike} {opt}: {bad}"
            continue
        sl_price = q.ask * (1 - lim.sl_pct / 100)
        fees = round_trip(q.ask, sl_price, spec.lot, costs).total
        return Pick(
            True,
            "theek",
            strike=strike,
            opt=opt,
            price=q.ask,
            qty=spec.lot,
            cost_rupees=round(q.ask * spec.lot + fees, 2),
            risk_rupees=round((q.ask - sl_price) * spec.lot + fees, 2),
        )
    return Pick(False, f"SKIP: {first_reason}")
