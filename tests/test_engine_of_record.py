"""tools/engine_of_record.py on a hand-computed 3-trade day (MISSION V19 3c, F3-3) and the contracts it shares."""

import datetime as dt
import math
from decimal import Decimal

import pytest

from bot.contracts import Bar, Intent, Leg, MarketState, NoTrade
from tools import bn_economics as bn
from tools import engine_of_record as eor

DAY = dt.date(2026, 6, 15)
EXPIRY = dt.date(2026, 6, 30)


class Scripted:
    """Buys the 50000 CE at decision minutes 30, 100 and 200 (a test strategy, not a bot strategy)."""

    def decide(self, state: MarketState, bars: tuple[Bar, ...]) -> Intent | NoTrade:
        if state.minute not in (30, 100, 200):
            return NoTrade("not a scripted minute")
        leg = Leg(50000.0, EXPIRY, "CE", "BUY")
        return Intent(f"t{state.minute}", (leg,), stop_frac=0.30, target_r=2.0, scratch_min=30, time_stop_min=120)


def synthetic_day() -> eor.Day:
    n = eor.N
    o = [100.0] * n
    h = [101.0] * n
    lo = [99.0] * n
    c = [100.0] * n
    h[40] = 165.0  # trade 1 (entry 100 at minute 30): target 100 + 2 x 30 = 160 -> exit 160 at minute 40
    lo[105], o[105] = 65.0, 95.0  # trade 2 (entry 100 at minute 100): stop 70 -> exit min(70, open 95) = 70 at 105
    opts = {(50000.0, "CE"): {"o": o, "h": h, "l": lo, "c": c, "live": [1.0] * n}}
    start = dt.datetime.combine(DAY, dt.time(9, 15))
    index = tuple(Bar(start + dt.timedelta(minutes=m), 50000.0, 50001.0, 49999.0, 50000.0) for m in range(n))
    return eor.Day(DAY, EXPIRY, 30, index, [15.0] * n, opts)


def test_the_hand_computed_three_trade_day() -> None:
    trades = eor.run_day(synthetic_day(), Scripted(), eor.StressedCosts(), max_entries=3)
    got = [(t.entry_minute, t.exit_minute, t.exit_value, t.exit_reason, t.gross_rs) for t in trades]
    # trade 3 (entry 100 at minute 200, flat prices): scratch after 30 minutes (minute 229), value 100, gross 0
    assert got == [
        (30, 40, 160.0, "target", Decimal("1800.00")),
        (100, 105, 70.0, "stop", Decimal("-900.00")),
        (200, 229, 100.0, "scratch", Decimal("0.00")),
    ]
    for t in trades:
        assert t.net_stressed_rs == bn.money(t.gross_rs - Decimal("1.5") * t.charges_rs - t.fill_cost_stressed_rs)
        assert t.charges_rs > 0 and t.fill_cost_stressed_rs == Decimal("84.00")  # 30 x (0.5 x 2 + 0.4) x 2 sides


def test_the_shell_allows_two_entries_and_a_cool_off_after_a_loss() -> None:
    trades = eor.run_day(synthetic_day(), Scripted(), eor.StressedCosts())
    assert [t.entry_minute for t in trades] == [30, 100]


def test_contracts_refuse_more_than_one_lot_a_credit_structure_and_another_index() -> None:
    buy = Leg(50000.0, EXPIRY, "CE", "BUY")
    with pytest.raises(ValueError, match="1 BUY leg"):
        Intent("x", (Leg(50000.0, EXPIRY, "CE", "BUY", lots=2),), 0.3, 2.0, 30, 120)
    with pytest.raises(ValueError, match="1 BUY leg"):
        Intent("x", (Leg(50000.0, EXPIRY, "CE", "SELL"), buy), 0.3, 2.0, 30, 120)
    with pytest.raises(ValueError, match="1 BUY leg"):
        Intent("x", (Leg(50000.0, EXPIRY, "CE", "BUY", underlying="X" + "IDX"),), 0.3, 2.0, 30, 120)
    assert len(Intent("ok", (buy, Leg(50200.0, EXPIRY, "CE", "SELL")), 0.4, 2.0, 30, 120).legs) == 2


def test_the_strategy_reads_only_closed_bars() -> None:
    from bot.strategy.orb_vix import OrbVix

    start = dt.datetime.combine(DAY, dt.time(9, 15))
    up = tuple(
        Bar(start + dt.timedelta(minutes=m), 50000 + 10 * m, 50005 + 10 * m, 49995 + 10 * m, 50000 + 10 * m)
        for m in range(60)
    )
    falling = MarketState(DAY, 45, EXPIRY, vix_open=15.0, vix_last=14.0)
    res = OrbVix().decide(falling, up[:45])
    assert isinstance(res, Intent) and res.legs[0].opt_type == "CE" and res.legs[0].strike == 50400.0
    assert isinstance(OrbVix().decide(MarketState(DAY, 45, EXPIRY, 15.0, 15.5), up[:45]), NoTrade)
    assert isinstance(OrbVix().decide(falling, up[:20]), NoTrade) and not math.isnan(up[44].c)
