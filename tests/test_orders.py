"""Order manager (PAPER) ke tests: har iron law ka ek test. Saare daam NAKLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from bot.haath.orders import Limits, LiveTradingForbidden, OrderManager, PaperBroker, Status
from bot.recorder.journal import JournalWriter, read_journal

SYM = "SENSEX 82000 CE"
M = 10 * 60  # 10:00


class Clock:
    def __init__(self) -> None:
        self.t = 1_000.0

    def __call__(self) -> float:
        return self.t

    def tick(self, s: float = 0.5) -> None:
        self.t += s


def make(tmp: Path | None = None, **kw: float) -> tuple[OrderManager, PaperBroker, Clock]:
    b = PaperBroker()
    c = Clock()
    lim = Limits(max_loss_per_trade=900, daily_loss_limit=1500, kul_jeb_limit=4000, start_capital=15000)
    for k, v in kw.items():
        setattr(lim, k, v)
    j = JournalWriter(tmp / "om.jsonl") if tmp else None
    return OrderManager(b, lim, journal=j, clock=c), b, c


def test_live_mode_is_impossible() -> None:
    with pytest.raises(LiveTradingForbidden):
        OrderManager(PaperBroker(), Limits(900, 1500, 4000, 15000), mode="real", clock=lambda: 0.0)


def test_max_loss_per_trade_enforced_before_order() -> None:
    om, b, _ = make()
    # 20 qty, entry 200, SL 150 -> ₹1,000 + kharcha > ₹900
    assert "max nuksan" in om.open("k1", SYM, 20, 200.0, 150.0, M)
    assert b.orders == {}  # broker tak kuch nahi gaya


def test_duplicate_signal_and_single_position() -> None:
    om, b, _ = make()
    b.set_quote(SYM, 199.0, 200.0)
    assert om.open("k1", SYM, 20, 200.0, 170.0, M) == "submitted"
    assert om.open("k1", SYM, 20, 200.0, 170.0, M).startswith("duplicate")
    assert om.open("k2", SYM, 20, 200.0, 170.0, M).startswith("pehle se")
    assert len(b.orders) == 1


def test_fill_places_sl_immediately_for_filled_qty() -> None:
    om, b, c = make()
    b.set_quote(SYM, 199.0, 200.0)
    om.open("k1", SYM, 20, 200.0, 170.0, M)
    c.tick()
    om.on_tick(M)
    assert om.pos is not None and om.pos.qty == 20 and om.pos.sl_oid
    sl = b.orders[om.pos.sl_oid]
    assert sl.kind == "SL" and sl.qty == 20 and sl.trigger == 170.0 and sl.status == Status.OPEN


def test_partial_fill_cancels_rest_and_protects_filled() -> None:
    om, b, c = make()
    b.max_fill_per_step = 8
    b.set_quote(SYM, 199.0, 200.0)
    om.open("k1", SYM, 20, 200.0, 170.0, M)
    c.tick()
    om.on_tick(M)  # 8 bhare
    assert om.pos is not None and om.pos.qty == 8 and b.orders[om.pos.sl_oid or ""].qty == 8
    b.set_quote(SYM, 204.0, 205.0)  # daam bhaag gaya, baaki nahi bharega
    c.tick(3.0)
    om.on_tick(M)
    entry = b.orders[om.pos.entry_oid]
    assert entry.status == Status.CANCELLED and om.pos.qty == 8
    assert b.orders[om.pos.sl_oid or ""].qty == 8


def test_sl_rejected_means_immediate_exit_and_halt() -> None:
    om, b, c = make()
    b.set_quote(SYM, 199.0, 200.0)
    b.reject_next.add("SL")
    om.open("k1", SYM, 20, 200.0, 170.0, M)
    c.tick()
    om.on_tick(M)
    assert om.led.halted == "SL lagana fail"
    assert om.pos is not None and om.pos.exit_oid  # exit order gaya
    c.tick()
    om.on_tick(M)
    assert om.pos is None and om.led.realised < 0  # band, kharcha laga
    assert om.open("k2", SYM, 20, 200.0, 170.0, M).startswith("kill-switch")


def test_gap_through_sl_triggers_aggressive_exit() -> None:
    om, b, c = make()
    b.set_quote(SYM, 199.0, 200.0)
    om.open("k1", SYM, 20, 200.0, 170.0, M)
    c.tick()
    om.on_tick(M)
    b.set_quote(SYM, 150.0, 151.0)  # gap: trigger 170 se neeche, SL limit 169.9 par fill nahi
    c.tick()
    om.on_tick(M)
    sl = b.orders[om.pos.sl_oid or ""]  # type: ignore[union-attr]
    assert sl.status == Status.TRIGGERED and sl.filled == 0
    c.tick(2.0)
    om.on_tick(M)  # 2 s baad: SL radd, aggressive exit
    assert b.orders[sl.oid].status == Status.CANCELLED
    c.tick(0.5)
    om.on_tick(M)
    assert om.pos is None
    # exit ~149.9 par: (149.9 - 200) x 20 = -₹1,002 + kharcha. Gap ne ₹900 ki seema paar ki;
    # isiliye lot ka kharcha capital ke 30% tak (tail nuksan chhota) - RISK.md
    assert -1100 < om.led.realised < -1000


def test_square_off_at_1515_and_no_new_entries() -> None:
    om, b, c = make()
    b.set_quote(SYM, 199.0, 200.0)
    om.open("k1", SYM, 20, 200.0, 170.0, M)
    c.tick()
    om.on_tick(M)
    b.set_quote(SYM, 210.0, 211.0)
    c.tick()
    om.on_tick(15 * 60 + 15)
    c.tick()
    om.on_tick(15 * 60 + 15)
    assert om.pos is None and om.led.realised > 0
    assert "square-off" in om.open("k2", SYM, 20, 210.0, 190.0, 15 * 60 + 15)


def test_daily_loss_kill_switch() -> None:
    om, b, c = make(daily_loss_limit=500)
    b.set_quote(SYM, 199.0, 200.0)
    om.open("k1", SYM, 20, 200.0, 180.0, M)
    c.tick()
    om.on_tick(M)
    b.set_quote(SYM, 179.0, 180.0)  # SL lagega (limit 179.9 se upar bid nahi) -> gap path
    c.tick()
    om.on_tick(M)
    b.set_quote(SYM, 178.0, 179.0)
    c.tick(2.5)
    om.on_tick(M)
    c.tick()
    om.on_tick(M)
    assert om.pos is None and -om.led.realised >= 380
    om.led.realised -= 200  # aur nuksan
    assert om.kill_reasons(M) == "din ki nuksan seema"


def test_reject_storm_halts() -> None:
    om, b, c = make()
    b.set_quote(SYM, 199.0, 200.0)
    for i in range(3):
        b.reject_next.add("BUY")
        assert om.open(f"k{i}", SYM, 20, 200.0, 170.0, M) == "entry reject"
        c.tick()
    assert om.led.halted is not None and "reject" in om.led.halted


def test_rate_limit_second_minute_window() -> None:
    om, _b, c = make(max_orders_per_s=2, max_orders_per_min=3)
    assert om._rate_ok() and om._rate_ok()
    assert not om._rate_ok()  # 1 second mein 3rd nahi
    c.tick(1.1)
    assert om._rate_ok()  # naya second
    c.tick(1.1)
    assert not om._rate_ok()  # minute mein 3 ho chuke
    c.tick(60.0)
    assert om._rate_ok()


def test_restart_restores_state_and_reprotects(tmp_path: Path) -> None:
    om, b, c = make(tmp_path)
    b.set_quote(SYM, 199.0, 200.0)
    om.open("k1", SYM, 20, 200.0, 170.0, M)
    c.tick()
    om.on_tick(M)
    assert om.journal is not None
    om.journal.close()
    # --- crash; naya process ---
    om2, b2, _c2 = make()
    om2.restore(list(read_journal(tmp_path / "om.jsonl")))
    assert "k1" in om2.led.used_keys and om2.pos is not None
    assert om2.open("k1", SYM, 20, 200.0, 170.0, M).startswith("duplicate")  # restart par dobara order nahi
    b2.set_quote(SYM, 199.0, 200.0)
    msg = om2.reconcile(20, SYM, 200.0)
    assert "SL dobara" in msg and om2.pos is not None and om2.pos.sl_oid
    om2.on_tick(M)  # entry oid "?" par crash nahi


def test_unknown_broker_position_is_exited_and_halts() -> None:
    om, b, _ = make()
    b.set_quote("NIFTY X", 99.0, 100.0)
    assert "anjaan" in om.reconcile(65, "NIFTY X", 100.0)
    assert om.led.halted is not None and om.pos is not None and om.pos.exit_oid


def test_kul_jeb_is_permanent_across_days() -> None:
    om, _b, _c = make()
    om.restore([], lifetime_before_today=-4100.0)
    assert om.led.halted is not None and om.led.halted.startswith("kul jeb")
    om.new_day()
    assert om.led.halted is not None  # naya din bhi band
    om2, _, _ = make(daily_loss_limit=100)
    om2._halt("din ki nuksan seema")
    om2.new_day()
    assert om2.led.halted is None  # din wala halt agle din khulta hai
