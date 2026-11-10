#!/usr/bin/env python3
"""Losing-streak / sizing Monte Carlo (₹15,000). YEH BACKTEST NAHI: market data nahi, sirf maani hui sambhavnayein.

Har trade ka nateeja (har number [ASSUMPTION], STRATEGY.md mein wajah):
- jeet (p):          +win_r * R  - kharcha
- time-stop (q):     -0.3 * R    - kharcha
- tail (g):          -tail_frac * lot_cost  (SL gap/fill nahi hua; niyam Worst_Case_Nuksan_Guna = 40% Andaza)
- baaki (haar):      -R          - kharcha
- har trade par server ka hissa: vps_month / trades_per_month
Ruk jaata hai jab: kul nuksan >= kul_jeb, ya balance < 1 lot ka kharcha.
"""

from __future__ import annotations

import random
import statistics
import sys
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Policy:
    name: str
    lot_cost: float  # 1 lot ka premium x qty
    risk_r: float  # SL par nuksan (₹)
    costs: float  # round-trip kharcha (₹) [ESTIMATE]


@dataclass(frozen=True, slots=True)
class World:
    p_win: float
    win_r: float = 2.0
    q_time: float = 0.25
    g_tail: float = 0.03
    tail_frac: float = 0.40
    vps_month: float = 1330.0
    trades_per_month: float = 12.0


@dataclass(frozen=True, slots=True)
class Result:
    p_lock: float  # kul jeb taala laga
    p_cant_trade: float  # balance 1 lot se kam
    median_end: float
    p5_end: float
    p95_end: float


def simulate(
    pol: Policy,
    w: World,
    *,
    capital: float = 15000.0,
    kul_jeb: float = 4000.0,
    trades: int = 60,
    paths: int = 20000,
    seed: int = 7,
) -> Result:
    rnd = random.Random(seed)  # noqa: S311 (simulation, crypto nahi)
    infra = w.vps_month / w.trades_per_month
    ends: list[float] = []
    lock = cant = 0
    for _ in range(paths):
        bal = capital
        for _t in range(trades):
            if capital - bal >= kul_jeb:
                lock += 1
                break
            if bal < pol.lot_cost + pol.costs:
                cant += 1
                break
            u = rnd.random()
            if u < w.g_tail:
                pnl = -w.tail_frac * pol.lot_cost - pol.costs
            elif u < w.g_tail + w.p_win:
                pnl = w.win_r * pol.risk_r - pol.costs
            elif u < w.g_tail + w.p_win + w.q_time:
                pnl = -0.3 * pol.risk_r - pol.costs
            else:
                pnl = -pol.risk_r - pol.costs
            bal += pnl - infra
        ends.append(bal)
    ends.sort()
    return Result(
        p_lock=lock / paths,
        p_cant_trade=cant / paths,
        median_end=statistics.median(ends),
        p5_end=ends[int(0.05 * paths)],
        p95_end=ends[int(0.95 * paths)],
    )


POLICIES = (
    # A: "best premium par 1 lot" - Nifty ITM ~₹140 x 65 (lot 65, code: SPECS)
    Policy("A: Nifty ITM 1 lot (~₹9,100, 61% capital)", lot_cost=9100, risk_r=900, costs=70),
    # B: "25-30% cap" - Sensex ATM ~₹200 x 20 (lot 20)
    Policy("B: Sensex ATM 1 lot (~₹4,000, 27% capital)", lot_cost=4000, risk_r=900, costs=55),
    # C: B jaisa par risk aadha (₹450 = idea ka Daily_Loss_Risk_Limit 3%)
    Policy("C: Sensex 1 lot, risk ₹450", lot_cost=4000, risk_r=450, costs=55),
)


def main() -> int:
    print("NAKLI SIMULATION (backtest nahi). 60 trade (~5 mahine @12/mahina), 20,000 raaste, kul jeb ₹4,000.\n")
    for p_win in (0.30, 0.36, 0.42):
        print(f"--- jeet-dar {p_win:.0%} (+2R), time-stop 25%, tail 3% ---")
        for pol in POLICIES:
            r = simulate(pol, World(p_win=p_win))
            print(
                f"{pol.name:44} taala {r.p_lock:6.1%} | lot nahi {r.p_cant_trade:5.1%} | "
                f"median ₹{r.median_end:8,.0f} | 5% ₹{r.p5_end:8,.0f} | 95% ₹{r.p95_end:8,.0f}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
