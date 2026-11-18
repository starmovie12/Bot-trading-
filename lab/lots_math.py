"""Owner order 4 (D-47) section B: cost and break-even for 1, 2, 3 lots per strike (arithmetic, not a trial).

  python -m lab.lots_math -> results/lots_math.md
Premium and delta per strike: results/f6_breakeven.md (30-min hold, DESIGN medians). Charges: constants.toml SOURCE rows
in force on 2026-11-18, x 1.5 (ST7); spread + slippage: the engine's stressed fill (normal bucket, x 2); lot = 30.
"""

import datetime as dt
from decimal import Decimal
from pathlib import Path

from tools import bn_economics as be
from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
ON, LOT = dt.date(2026, 11, 18), 30
STRIKES = {"ITM2": (711, 0.55), "ITM1": (652, 0.52), "ATM": (600, 0.49), "CAP15": (417, 0.39)}


def main() -> int:
    c, costs = be.consts(), eor.StressedCosts()
    brokerage = be.dated(c["brokerage_option_per_order"], ON)
    out = [
        "# LOTS MATH (owner order 4, D-47 B; arithmetic, not a trial)",
        "",
        f"Brokerage is FLAT per order: ₹{brokerage} an order whatever the quantity (constants.toml SOURCE), so 1 round",
        "trip pays ₹40 + GST for 1, 2 or 3 lots. Spread, slippage, STT, exchange, SEBI, IPFT and stamp grow with the",
        "quantity. Stressed: charges x 1.5, spread / slippage x 2 (ST7). Premium and delta: F6 medians (30-min hold).",
        "",
        "| strike | lots | qty | stressed cost ₹ | cost ₹ per lot | cost pts per unit | break-even index pts | "
        "premium x qty ₹ (max loss by construction) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, (prem, delta) in STRIKES.items():
        for n in (1, 2, 3):
            qty = LOT * n
            p = Decimal(prem)
            ch = Decimal("1.5") * be.round_trip(p, p, qty, ON, c)
            fill = costs.fill_stressed(1, qty, (60, 120), False, False)
            total = float(ch + fill)
            out.append(
                f"| {name} | {n} | {qty} | {total:,.0f} | {total / n:,.0f} | {total / qty:.2f} | "
                f"{total / qty / delta:.1f} | {prem * qty:,} |"
            )
    out += [
        "",
        "Reading:",
        "- The flat brokerage (₹20 an order, ~₹71 a round trip after GST and the x1.5 stress) is shared by more",
        "  lots: ATM costs ₹219 a lot at 1 lot, ₹183 at 2, ₹172 at 3, so the break-even falls from 14.9 to 12.5",
        "  to 11.7 index points (CAP15 17.0 -> 13.0): a real but modest cut, about 3 points at 3 lots.",
        "- It does not create an edge: a trade still needs its average index move to beat ~12-14 points, and",
        "  profit AND loss both scale with the lots (3 lots = 3 x the swing).",
        "- Loss-first cap (pinned MAX_TRADE_LOSS_RS ₹35,700 per trade, D-47): the by-construction max loss is",
        "  premium x qty, so 2 ATM lots (₹36,000), 2 ITM2 lots (₹42,660) and every 3-lot size are above it;",
        "  only CAP15 fits 2 lots (₹25,020), and 1 lot fits for every strike. Larger sizes are skipped.",
        "- Size only helps a strategy that ALREADY has a positive stressed net per trade; on a negative one",
        "  it multiplies the loss.",
    ]
    (ROOT / "results/lots_math.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
