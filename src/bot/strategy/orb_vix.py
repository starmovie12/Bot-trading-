"""A1+b1 (EXPERIMENTAL: paper only, MISSION V19 3d): 30-minute range break on a trending day while India VIX falls.

Reads only the bars it is given (all closed before `state.minute`) and the day's VIX; LONG ATM option of the nearest
monthly expiry; exits by the RISK SHELL preset EXIT0 (PLAN.md §PREREG-0).
"""

import itertools
import math

from bot.contracts import Bar, Intent, Leg, MarketState, NoTrade, OptType

EFF_MIN = 0.35  # trend-day efficiency gate (lab/ideas.py A1)
RANGE_MIN = 30  # minutes of the opening range (09:15-09:44)
STRIKE = 100


class OrbVix:
    """The A1+b1 rule as a bot strategy (the lab mask of lab/ideas.py or30_break with vix_falling)."""

    def decide(self, state: MarketState, bars: tuple[Bar, ...]) -> Intent | NoTrade:
        closes = [b.c for b in bars if not math.isnan(b.c)]
        if state.minute < RANGE_MIN or len(closes) < 16:
            return NoTrade("before 09:45")
        last, open0 = closes[-1], bars[0].o
        path = sum(abs(b - a) for a, b in itertools.pairwise(closes))
        eff = abs(last - open0) / path if path > 0 else 0.0
        ret15 = last / closes[-16] - 1
        high = max(b.h for b in bars[:RANGE_MIN] if not math.isnan(b.h))
        low = min(b.l for b in bars[:RANGE_MIN] if not math.isnan(b.l))
        if eff < EFF_MIN or not state.vix_last < state.vix_open:
            return NoTrade("not a trend day, or VIX not falling")
        side: OptType
        if last > high and ret15 > 0:
            side = "CE"
        elif last < low and ret15 < 0:
            side = "PE"
        else:
            return NoTrade("no 30-minute range break")
        leg = Leg(float(round(last / STRIKE) * STRIKE), state.expiry, side, "BUY")
        return Intent(
            f"{state.day:%Y%m%d}-{state.minute:03d}",
            (leg,),
            stop_frac=0.30,  # EXIT0 (PLAN.md §PREREG-0)
            target_r=2.0,
            scratch_min=30,
            time_stop_min=120,
            reason="A1+b1 range break, VIX falling",
        )
