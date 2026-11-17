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
    # 1 lot ka kharcha capital ke 30% tak (Monte Carlo: gap/SL-fail ka tail nuksan = lot ka ~40%;
    # 30% par tail ~12% capital, 61% wale Nifty lot par ~24%). Isse ₹15k par Nifty (lot 65) aksar bahar.
    max_capital_use_pct: float = 30.0
    win_r: float = 2.0  # target = 2R (setup ka andaza)
    infra_per_trade: float = 111.0  # [ASSUMPTION] VPS ₹1,330/mahina / 12 trade
    kharcha_fayda_guna: float = 4.0  # niyam Kharcha_Fayda_Guna "3 se 4 guna": munafa ka target >= 4 x kharcha
    max_spread_pct: float = 1.0  # (ask-bid)/ask
    min_oi: int = 50_000


# Delta ka andaza (live mein broker ke Greeks se badlega). Underlying SL ko premium SL mein badalne ke liye.
DELTA_GUESS: dict[str, float] = {"itm": 0.6, "atm": 0.5}


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
    sl_price: float | None = None


def _sl_price(ask: float, lim: Limits, underlying_sl_points: float | None, delta: float) -> float:
    """Premium SL: 25% wala ya chart (underlying) SL x delta, jo PAAS ho (kam nuksan)."""
    pct_sl = ask * (1 - lim.sl_pct / 100)
    if underlying_sl_points is None or underlying_sl_points <= 0:
        return pct_sl
    return max(pct_sl, ask - underlying_sl_points * delta)


def _check(q: Quote, qty: int, lim: Limits, costs: CostModel, sl_price: float) -> str | None:
    if q.ask <= 0 or q.bid <= 0 or q.bid > q.ask:
        return "quote galat (bid/ask)"
    spread = (q.ask - q.bid) / q.ask * 100
    if spread > lim.max_spread_pct:
        return f"spread {spread:.2f}% > {lim.max_spread_pct}%"
    if q.oi < lim.min_oi:
        return f"OI kam ({q.oi})"
    fees = round_trip(q.ask, sl_price, qty, costs).total
    cost = q.ask * qty + fees
    if cost > lim.capital * lim.max_capital_use_pct / 100:
        return f"1 lot ₹{cost:,.0f} capital ke {lim.max_capital_use_pct:.0f}% se zyada"
    risk = (q.ask - sl_price) * qty + fees
    if risk > lim.max_risk_rupees:
        return f"SL par nuksan ₹{risk:,.0f} > seema ₹{lim.max_risk_rupees:,.0f}"
    burden = fees + lim.infra_per_trade
    if lim.win_r * (q.ask - sl_price) * qty < lim.kharcha_fayda_guna * burden:
        return f"kharcha ₹{burden:,.0f} target ke mukable bahut bhaari (COST-FIRST)"
    return None


def choose_strike(
    index: str,
    spot: float,
    side: Side,
    chain: list[Quote],
    lim: Limits,
    costs: CostModel | None = None,
    *,
    underlying_sl_points: float | None = None,
    lot: int,
) -> Pick:
    """`lot` comes from the instrument master (bot.strategy.instrument_master), never from code (S6)."""
    spec = SPECS[index]
    if lot <= 0:
        return Pick(False, "SKIP: lot size unknown (instrument file missing): no trade")
    if not spec.tradable:
        return Pick(False, f"{spec.label} sirf signal ke liye (trade nahi)")
    if spot <= 0:
        return Pick(False, "spot galat")
    costs = costs or CostModel.for_exchange(spec.exchange)
    atm = round(spot / spec.strike_step) * spec.strike_step
    opt: Literal["CE", "PE"] = "CE" if side == "CALL" else "PE"
    itm = atm - spec.strike_step if side == "CALL" else atm + spec.strike_step
    book = {(q.strike, q.opt): q for q in chain}
    reasons: list[str] = []
    for strike, kind in ((itm, "itm"), (atm, "atm")):  # premium quality: pehle ITM, phir ATM; OTM kabhi nahi
        q = book.get((strike, opt))
        if q is None:
            reasons.append(f"{strike} {opt} ka quote nahi")
            continue
        sl_price = _sl_price(q.ask, lim, underlying_sl_points, DELTA_GUESS[kind])
        bad = _check(q, lot, lim, costs, sl_price)
        if bad:
            reasons.append(f"{strike} {opt}: {bad}")
            continue
        fees = round_trip(q.ask, sl_price, lot, costs).total
        return Pick(
            True,
            "theek",
            strike=strike,
            opt=opt,
            price=q.ask,
            qty=lot,
            cost_rupees=round(q.ask * lot + fees, 2),
            risk_rupees=round((q.ask - sl_price) * lot + fees, 2),
            sl_price=round(sl_price, 2),
        )
    return Pick(False, "SKIP: " + "; ".join(reasons))
