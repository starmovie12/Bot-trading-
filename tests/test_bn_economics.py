"""tools/bn_economics.py: charges anchors, dated STT, money in paise (I12), chain floor (MISSION V19 Phase 2c)."""

import datetime as dt
from decimal import Decimal

from tools import bn_economics as be

C = be.consts()
ON = dt.date(2026, 11, 18)
P300 = Decimal("300")


def test_one_leg_round_trip_matches_the_reference_anchor() -> None:
    rt = be.round_trip(P300, P300, 30, ON, C)
    assert Decimal(68) <= rt <= Decimal(70)  # ~₹69 unstressed at lot 30, ₹300 premium
    stressed = rt + be.fill_cost(30, 1, True)
    assert Decimal(150) <= stressed <= Decimal(160)


def test_two_leg_spread_stressed_cost_is_in_the_reference_band() -> None:
    s = be.debit_spread(P300, Decimal("150"), 30, Decimal("58000"), ON, C)
    assert Decimal(260) <= s["round_trip_stressed_rs"] <= Decimal(310)


def test_stt_follows_its_dated_rows() -> None:
    assert be.dated(C["stt_option_sell"], dt.date(2026, 3, 31)) == Decimal("0.1")
    assert be.dated(C["stt_option_sell"], dt.date(2026, 4, 1)) == Decimal("0.15")
    sell_before = be.side_charges(Decimal(9000), "SELL", dt.date(2026, 3, 31), C)
    assert be.side_charges(Decimal(9000), "SELL", dt.date(2026, 4, 1), C) - sell_before == Decimal("4.50")


def test_every_amount_is_decimal_paise() -> None:
    rows = [be.long_option(P300, 30, ON, C), be.debit_spread(P300, Decimal("150"), 30, Decimal("58000"), ON, C)]
    for row in rows:
        for v in row.values():
            assert isinstance(v, Decimal) and v.as_tuple().exponent == -2


def test_chain_floor_and_break_even() -> None:
    lo = be.long_option(P300, 30, ON, C)
    assert be.chain_floor(lo["max_loss_rs"]) == 2 * lo["max_loss_rs"]
    assert be.breakeven(Decimal(150), Decimal("0.5"), 30) == Decimal("10.00")


def test_the_kill_side_uses_zero_fill_and_no_leg2_margin() -> None:
    assert be.fill_cost(30, 1, True, Decimal(0)) == Decimal("0.00")
    s = be.debit_spread(P300, Decimal("150"), 30, Decimal("58000"), ON, C)
    assert s["cash_needed_favourable_rs"] == Decimal("9000.00") < s["cash_needed_stressed_rs"]


def test_indian_grouping() -> None:
    assert be.rs(Decimal("208259.4")) == "2,08,259" and be.rs(10000) == "10,000" and be.rs(950) == "950"
