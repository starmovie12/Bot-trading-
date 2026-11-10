from __future__ import annotations

from datetime import date, time

import pytest

from bot.strategy.costs import CostModel, breakeven_points, round_trip
from bot.strategy.instruments import SPECS, days_to_expiry, is_expiry_day, next_expiry
from bot.strategy.rules import DayState, OpenTrade, Params, after_exit, can_enter, on_tick
from bot.strategy.selection import Limits, Quote, choose_strike


def test_specs_2026() -> None:
    assert (SPECS["Nifty50"].lot, SPECS["Sensex"].lot, SPECS["BankNifty"].lot) == (65, 20, 30)
    assert SPECS["BankNifty"].weekly is False and SPECS["BankNifty"].tradable is False


def test_expiry_days() -> None:
    # 10 Nov 2026 = Tuesday, 12 Nov 2026 = Thursday
    assert is_expiry_day("Nifty50", date(2026, 11, 10))
    assert next_expiry("Nifty50", date(2026, 11, 11)) == date(2026, 11, 17)
    assert is_expiry_day("Sensex", date(2026, 11, 12))
    assert days_to_expiry("Sensex", date(2026, 11, 11)) == 1
    # Bank Nifty: sirf monthly, Nov 2026 ka aakhri Tuesday = 24 Nov
    assert next_expiry("BankNifty", date(2026, 11, 11)) == date(2026, 11, 24)
    assert next_expiry("BankNifty", date(2026, 11, 25)) == date(2026, 12, 29)


def test_costs_round_trip() -> None:
    c = round_trip(100.0, 120.0, 65)
    assert c.brokerage == 40.0
    assert c.stt == pytest.approx(120 * 65 * 0.0015, abs=0.01)  # 0.15% bechne par
    assert c.total > c.brokerage + c.stt
    assert breakeven_points(100.0, 65) > 0.5
    assert "exchange_txn_pct" in CostModel().unverified()
    with pytest.raises(ValueError):
        round_trip(-1, 1, 1)


def chain(
    atm: int, step: int, ce: dict[int, float], pe: dict[int, float], spread: float = 0.5, oi: int = 200_000
) -> list[Quote]:
    out = [Quote(k, "CE", v - spread, v, oi) for k, v in ce.items()]
    out += [Quote(k, "PE", v - spread, v, oi) for k, v in pe.items()]
    return out


def test_choose_prefers_itm_never_otm() -> None:
    q = chain(25000, 50, {24950: 140.0, 25000: 110.0, 25050: 85.0}, {25000: 105.0, 25050: 135.0, 24950: 80.0})
    lim = Limits(capital=15000, max_risk_rupees=3000)
    p = choose_strike("Nifty50", 25010.0, "CALL", q, lim)
    assert p.ok and p.strike == 24950 and p.opt == "CE" and p.qty == 65
    p2 = choose_strike("Nifty50", 25010.0, "PUT", q, lim)
    assert p2.ok and p2.strike == 25050 and p2.opt == "PE"


def test_skip_when_unaffordable_or_risky() -> None:
    q = chain(25000, 50, {24950: 240.0, 25000: 210.0}, {})
    tiny = Limits(capital=10000, max_risk_rupees=5000)
    p = choose_strike("Nifty50", 25000.0, "CALL", q, tiny)
    assert not p.ok and p.reason.startswith("SKIP") and "capital" in p.reason
    strict = Limits(capital=50000, max_risk_rupees=1000)
    assert "SL par nuksan" in choose_strike("Nifty50", 25000.0, "CALL", q, strict).reason
    wide = chain(25000, 50, {24950: 140.0, 25000: 110.0}, {}, spread=5.0)
    assert "spread" in choose_strike("Nifty50", 25000.0, "CALL", wide, Limits(15000, 3000)).reason
    assert not choose_strike("BankNifty", 56000.0, "CALL", q, tiny).ok  # sirf signal


def test_can_enter_rules() -> None:
    p = Params()
    day = DayState(daily_loss_limit=1500)
    ok = can_enter(time(10, 0), day, p, expiry_day=False, vix_change_pct=1.0, open_position=False)
    assert ok == (True, "theek")
    assert not can_enter(time(12, 0), day, p, expiry_day=False, vix_change_pct=1.0, open_position=False)[0]
    assert not can_enter(time(13, 40), day, p, expiry_day=True, vix_change_pct=1.0, open_position=False)[0]
    assert not can_enter(time(10, 0), day, p, expiry_day=False, vix_change_pct=9.0, open_position=False)[0]
    assert not can_enter(time(10, 0), day, p, expiry_day=False, vix_change_pct=1.0, open_position=True)[0]
    assert (
        "tay nahi" in can_enter(time(10, 0), DayState(), p, expiry_day=False, vix_change_pct=0, open_position=False)[1]
    )
    after_exit(day, -700)
    after_exit(day, -900)
    assert day.halted
    assert not can_enter(time(10, 0), day, p, expiry_day=False, vix_change_pct=0, open_position=False)[0]


def test_exits_sl_time_trail_hard() -> None:
    p = Params()
    t = OpenTrade(entry_price=100.0, entry_minute=600, best_price=100.0, sl_price=75.0)
    assert on_tick(t, 74.0, 601, time(10, 1), p, structure_broken=False) == "stop-loss"
    t = OpenTrade(100.0, 600, 100.0, 75.0)
    assert "chaal nahi" in (on_tick(t, 102.0, 616, time(10, 16), p, structure_broken=False) or "")
    t = OpenTrade(100.0, 600, 100.0, 75.0)
    assert on_tick(t, 140.0, 605, time(10, 5), p, structure_broken=False) is None
    assert t.sl_price == 100.0  # +1R ke baad breakeven
    assert "trailing" in (on_tick(t, 125.0, 606, time(10, 6), p, structure_broken=False) or "")
    t = OpenTrade(100.0, 600, 100.0, 75.0)
    assert "hard exit" in (on_tick(t, 110.0, 915, time(15, 15), p, structure_broken=False) or "")
    t = OpenTrade(100.0, 600, 100.0, 75.0)
    assert "dhaancha" in (on_tick(t, 99.0, 602, time(10, 2), p, structure_broken=True) or "")


def test_risk_per_trade_small_capital() -> None:
    from bot.strategy.rules import risk_per_trade

    assert risk_per_trade(15000, 1500) == 900.0  # min(900, 900)
    assert risk_per_trade(15000, 1000) == 600.0
    assert risk_per_trade(15000, 0) == 0.0
    # ₹15k par Nifty ITM ₹140 ka 25% SL (~₹2,275) is seema se upar: trade SKIP hona chahiye
    q = chain(25000, 50, {24950: 140.0, 25000: 110.0}, {})
    p = choose_strike("Nifty50", 25000.0, "CALL", q, Limits(capital=15000, max_risk_rupees=risk_per_trade(15000, 1500)))
    assert not p.ok and "SL par nuksan" in p.reason


def test_kul_jeb_lock_protects_last_capital() -> None:
    from bot.strategy.rules import account_allows_trading

    assert account_allows_trading(15000, 15000, 0)[0] is False  # seema tay nahi = trade nahi
    assert account_allows_trading(15000, 15000, 15000)[0] is False  # poora capital seema = galat
    ok, msg = account_allows_trading(15000, 13000, 4000)
    assert ok and "2,000" in msg
    stop, msg2 = account_allows_trading(15000, 11000, 4000)
    assert not stop and "hamesha ke liye band" in msg2
    assert account_allows_trading(15000, 10500, 4000)[0] is False  # seema ke paar bhi band hi rahe


def test_chart_sl_makes_small_capital_tradable() -> None:
    from bot.strategy.rules import risk_per_trade

    q = chain(25000, 50, {24950: 140.0, 25000: 110.0}, {})
    lim = Limits(capital=15000, max_risk_rupees=risk_per_trade(15000, 1500))  # ₹900
    assert not choose_strike("Nifty50", 25000.0, "CALL", q, lim).ok  # sirf 25% SL: kabhi trade nahi (purani kami)
    p = choose_strike("Nifty50", 25000.0, "CALL", q, lim, underlying_sl_points=15.0)  # chart SL 15 point paas
    assert p.ok and p.strike == 24950
    assert p.sl_price == pytest.approx(140.0 - 15.0 * 0.6)
    assert p.risk_rupees <= 900
    far = choose_strike("Nifty50", 25000.0, "CALL", q, lim, underlying_sl_points=60.0)
    assert not far.ok and "SL par nuksan" in far.reason  # chart SL door = SKIP
