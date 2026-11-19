"""Program S3 tests T01-T25 (BANKNIFTY_STRATEGY_V3.md §13.0). Synthetic fixtures only (never real data)."""

from __future__ import annotations

import ast
import datetime as dt
import json
import math
import re
from decimal import Decimal as D
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pytest

from lab.s3 import costs, data, engine, run
from lab.s3.checks import known_bars, shadow
from lab.s3.engine import BASE, Event, Mode, cap_ok, risk_lots, run_day, simulate, size_at_fill
from lab.s3.features import SigParams, base_feats, signals
from lab.s3.ledger import Ledger
from lab.s3.p3 import p3
from lab.s3.registry import Cfg, minute
from tests.s3_fixture import make_day, refresh, set_path
from tools import preflight
from tools.nested_wf import blocks, nested, windows

ROOT = Path(__file__).resolve().parents[1]
APR = dt.date(2026, 5, 4)
NOSHOCK = np.zeros(375, dtype=bool)


def flat_atr(monkeypatch: pytest.MonkeyPatch, v: float) -> None:
    monkeypatch.setattr(engine, "opt_atr5", lambda *a, **k: v)


def sig(d: Any, cfg: Cfg) -> Any:
    return signals(d, SigParams.of(cfg))


def decisions(r: Any) -> dict[int, str]:
    return {s["t"]: s["decision"] for s in r.signals}


# T01
def test_t01_fix_defined_once() -> None:
    spec = (ROOT / "BANKNIFTY_STRATEGY_V3.md").read_text(encoding="utf-8")
    for n in range(1, 9):
        assert len(re.findall(rf"^\| FIX-{n} \|", spec, re.M)) == 1, n


# T02
ALLOWED = {0, 1, 2, 3, 6, 16, 64, 4096, 100.0}


def test_t02_no_unregistered_numbers() -> None:
    """Strategy modules hold no number outside the registry: only structural literals (gear ids 1-3, 0/1, the
    typical-price /3 and EMA 2/(n+1) formulas, the percent scale, cache sizes, Decimal digits)."""
    bad = []
    for f in ("engine", "features", "checks", "p3"):
        for node in ast.walk(ast.parse((ROOT / f"lab/s3/{f}.py").read_text())):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, int | float)
                and not isinstance(node.value, bool)
                and node.value not in ALLOWED
            ):
                bad.append((f, node.value, node.lineno))
    assert bad == []


# T03
def test_t03_step0_cost_examples() -> None:
    f = costs.buy_fill(D("350.00"), BASE.hs, BASE.slip)
    assert f == D("350.70")
    x = costs.sell_fill(D("388.40"), BASE.hs, BASE.slip)
    assert x == D("387.70")
    a = costs.round_trip(f, x, 90, APR)
    assert a["total"] == D("128.43") and (x - f) * 90 - a["total"] == D("3201.57")
    b = costs.round_trip(f, D("335.00"), 90, APR)
    assert b["total"] == D("119.32") and (D("335.00") - f) * 90 - b["total"] == D("-1532.32")
    c = costs.round_trip(f, x, 60, dt.date(2026, 2, 10))
    assert c["total"] == D("89.72") and (x - f) * 60 - c["total"] == D("2130.28")
    lock = costs.sell_fill(D("352.70"), BASE.hs, BASE.slip)
    assert engine.net(f, lock, 90, APR) == D("-5.26")
    assert engine.net(f, lock, 30, APR) == D("-33.22")
    st = costs.sell_fill(D("352.70"), D("1.00"), D("0.40"))
    assert engine.net(f, st, 90, APR) == D("-68.14")
    assert [engine.be_pts(f, q, APR) for q in (30, 60, 90)] == [D("3.15"), D("2.35"), D("2.10")]


# T04
def _snapshot(d: Any, t: int, cfg: Cfg) -> list[Any]:
    f = base_feats(d)
    s = sig(d, cfg)
    out: list[Any] = [float(v[t]) for v in f.values()]
    out += [bool(getattr(s, a)[t]) for a in ("a_ce", "a_pe", "p1_ce", "p1_pe", "p2_ce", "p2_pe", "c_ok")]
    for side in ("CE", "PE"):
        k, how = engine.pick_strike(d, t, side, cfg)
        out += [k, how, engine.k05_ok(d, t, side, k, 15.0) if k >= 0 else None]
        out += sorted((a, str(b)) for a, b in shadow(d, s, t, side, k, 15.0, "P1", cfg).items())
    return out


def test_t04_future_bars_do_not_change_features() -> None:
    cfg = Cfg("T1-P")
    d = make_day(walk=True, seed=4)
    t = 100
    before = _snapshot(d, t, cfg)
    rng = np.random.default_rng(9)
    w = slice(t + 1, t + 16)
    for v in d.base.values():
        v[w] = v[w] * rng.uniform(0.9, 1.1, 15)
    for k in ("o", "h", "l", "c", "v", "oi", "delta", "hs_proxy"):
        d.opt[k][:, w] *= rng.uniform(0.5, 1.5, (d.opt[k].shape[0], 15))
    d.stale[:, w] = True
    refresh(d)
    assert before == _snapshot(d, t, cfg)


# T05
def test_t05_3m_15m_availability() -> None:
    d = make_day()
    b3 = known_bars(d.b3, minute("09:20"))
    assert b3["avail_m"][-1] == minute("09:21")  # the 09:18-09:21 bar
    b15 = known_bars(d.b15, minute("09:20"))
    assert b15["avail_m"][-1] < 0  # only yesterday's 15m bars
    assert known_bars(d.b15, minute("09:29"))["avail_m"][-1] == minute("09:30")


# T06
def test_t06_daily_metric_intraday_only() -> None:
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    day = APR
    tb = pa.table(
        {
            "trading_date": [day, day],
            "version": ["EOD_INCLUSIVE", "INTRADAY_PREV_CLOSE"],
            "rv20_DERIVED": [0.5, 0.1],
            "available_from_ts": [
                dt.datetime(2026, 5, 4, 15, 30, tzinfo=ist),
                dt.datetime(2026, 5, 4, 9, 15, tzinfo=ist),
            ],
            "ivp_vix_PROXY": [90.0, 30.0],
            "ivp_status": ["OK", "OK"],
        }
    )
    out = data.daily_from(tb, day)
    assert out["ivp"] == 30.0 and out["rv20"] == 0.1


# T07
def test_t07_pe_delta_index_risk_and_k05_fail() -> None:
    d = make_day()
    k = d.k(50000.0, "PE")
    d.opt["delta"][k, :] = -0.35
    t = 60
    assert 15.0 / abs(d.opt["delta"][k, t]) > 0
    d.base["cm_put_wall"][:] = 49950.0  # 50 pts away < 2 x 42.9
    assert engine.k05_ok(d, t, "PE", k, 15.0) is False
    d.base["cm_put_wall"][:] = 49800.0  # 200 pts away
    assert engine.k05_ok(d, t, "PE", k, 15.0) is True


# T08 / T09 helpers
def _gear2_path(d: Any, e: int, n_bars: int, strike: float = 50000.0) -> int:
    bars = [(350.0, 362.0, 349.5, 361.0)] + [(361.0, 361.5, 360.5, 361.0)] * n_bars
    return set_path(d, strike, "CE", e, bars)


def test_t08_force_flat_on_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    flat_atr(monkeypatch, 10.0)
    cfg = Cfg("T1")
    for stale_from, why, bar in (
        (minute("15:08"), "FORCE_FLAT_1510", minute("15:10")),
        (minute("15:05"), "ILLIQUID_EXIT", minute("15:08")),
    ):
        d = make_day()
        e = minute("14:15")
        k = _gear2_path(d, e, 80)
        d.stale[k, stale_from:] = True
        p = simulate(d, k, e, D("350.70"), 3, cfg, NOSHOCK)
        assert (p.exit_reason, p.stale_forced, p.exit_bar) == (why, True, bar)
        assert p.exit_bar <= minute("15:10")  # nothing open at 15:11


def test_t09_expiry_day(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = Cfg("T1")
    d = make_day(dte=0)
    r = run_day(d, sig(d, cfg), cfg, events=[Event(minute("13:01"), "CE", "P1")])
    assert decisions(r)[minute("13:01")] == "EXPIRY_AFTER_1259"
    flat_atr(monkeypatch, 10.0)
    for stale_from, why in ((minute("13:28"), "EXPIRY_1330"), (minute("13:26"), "ILLIQUID_EXIT")):
        d = make_day(dte=0)
        e = minute("12:50")
        k = _gear2_path(d, e, 80)
        d.stale[k, stale_from:] = True
        p = simulate(d, k, e, D("350.70"), 3, cfg, NOSHOCK)
        assert p.exit_reason == why and p.stale_forced and p.exit_bar <= minute("13:30")


# T10
def test_t10_n13_time_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    flat_atr(monkeypatch, 20.0)
    cfg = Cfg("T1-P", flags={"FLAG_N13": True})
    d = make_day()
    e = 100
    k = set_path(d, 50000.0, "CE", e, [(350.0, 362.7, 349.8, 356.0)] + [(356.0, 356.5, 355.5, 356.0)] * 40)
    p = simulate(d, k, e, D("350.70"), 3, cfg, NOSHOCK)
    assert p.max_gear == 1 and p.exit_reason == "TIME_STOP" and p.exit_bar == e + 20


# T11
MODULE_REASONS = {"STRUCTURE_STOP", "REASON_REVERSAL", "NO_ROOM", "CHOP", "DEAD", "STRETCH"}


def _busy_day(seed: int, **kw: Any) -> Any:
    return make_day(walk=True, seed=seed, **kw)


def test_t11_r0_has_no_module_reasons() -> None:
    for variant in ("T1-RAW", "T1", "T1-P"):
        cfg = Cfg(variant)
        seen: set[str] = set()
        for seed in range(3):
            d = _busy_day(seed, ivp=70.0 if seed == 0 else 40.0)
            evs = [Event(t, "CE" if t % 2 else "PE", "P1") for t in range(5, 330, 7)]
            r = run_day(d, sig(d, cfg), cfg, events=evs)
            seen |= {s["decision"] for s in r.signals} | {tr["path"].exit_reason for tr in r.trades}
            for tr in r.trades:
                assert cap_ok(tr["path"].n, tr["path"].lot, tr["path"].f, d.day)
        assert not seen & MODULE_REASONS
        if variant != "T1-P":
            assert not seen & {"GATE_IVP", "GATE_OI_WALL"}
        else:
            assert "GATE_IVP" in seen


# T12
def test_t12_size_at_fill() -> None:
    cfg = Cfg("T1-P")
    room = (D(0), None)
    assert size_at_fill(D("401"), 30, APR, D("15"), room, cfg, 3) == (2, "CAP")
    assert size_at_fill(D("350.70"), 35, APR, D("15"), room, cfg, 3) == (2, "CAP")
    assert size_at_fill(D("350.70"), 30, APR, D("15"), room, cfg, 3) == (3, "MODE")
    assert cap_ok(3, 30, D("395.95"), APR) and not cap_ok(3, 30, D("396.00"), APR)
    assert cap_ok(3, 35, D("339.35"), APR) and not cap_ok(3, 35, D("339.40"), APR)


# T13
def test_t13_n17_risk_lots() -> None:
    f = D("350.70")
    assert risk_lots(f, 30, D(15), D(1600), APR) == (3, "RISK")
    assert engine.risk(3, 30, f, D(15), APR) == D("1532.32")
    assert risk_lots(f, 30, D(18), D(1600), APR) == (2, "RISK")
    assert engine.risk(2, 30, f, D(18), APR) == D("1216.93")
    assert risk_lots(f, 30, D(25), D(1600), APR) == (1, "RISK")
    assert engine.risk(1, 30, f, D(25), APR) == D("841.66")
    assert risk_lots(f, 35, D(15), D(1600), APR) == (2, "RISK")
    assert engine.risk(2, 35, f, D(15), APR) == D("1202.29")
    assert risk_lots(f, 30, D(15), D(500), APR) == (0, "RISK_TOO_BIG")


# T14
def test_t14_day_room() -> None:
    cfg = Cfg("T1-P")
    assert size_at_fill(D("350.70"), 30, APR, D("15"), (D(-3000), None), cfg, 3) == (1, "DAY")


# T15
def test_t15_lock_loss_counts_and_reset() -> None:
    cfg = Cfg("T1-RAW")
    d = make_day()
    set_path(d, 50000.0, "CE", 61, [(350.0, 355.8, 349.8, 355.0), (354.0, 354.5, 352.0, 352.5)])
    set_path(d, 50000.0, "CE", 81, [(350.0, 351.0, 330.0, 331.0), (331.0, 331.5, 330.5, 331.0)])
    set_path(d, 50000.0, "CE", 101, [(331.0, 331.5, 330.5, 331.0)])
    d.opt["c"][d.k(50000.0, "CE"), 80] = 350.0
    r = run_day(d, sig(d, cfg), cfg, events=[Event(60, "CE", "P1"), Event(80, "CE", "P1"), Event(100, "CE", "P1")])
    nets = [float(tr["net_base"]) for tr in r.trades]
    assert nets[0] == -5.26 and nets[1] < 0
    assert decisions(r)[100] == "DAY_STOP_2LOSS"
    d = make_day()
    set_path(d, 50000.0, "CE", 61, [(350.0, 355.8, 349.8, 355.0), (354.0, 354.5, 352.0, 352.5)])
    set_path(d, 50000.0, "CE", 81, [(350.0, 362.0, 349.8, 361.0), (361.0, 361.5, 357.0, 357.5)])
    set_path(d, 50000.0, "CE", 101, [(350.0, 351.0, 330.0, 331.0), (331.0, 331.5, 330.5, 331.0)])
    k = d.k(50000.0, "CE")
    d.opt["c"][k, 80] = d.opt["c"][k, 100] = d.opt["c"][k, 120] = 350.0
    evs = [Event(60, "CE", "P1"), Event(80, "CE", "P1"), Event(100, "CE", "P1"), Event(120, "CE", "P1")]
    r = run_day(d, sig(d, cfg), cfg, events=evs)
    nets = [float(tr["net_base"]) for tr in r.trades]
    assert nets[0] < 0 and nets[1] >= 0 and nets[2] < 0
    assert decisions(r)[120] != "DAY_STOP_2LOSS"


# T16
def test_t16_reentry_sizing_and_gate() -> None:
    for ivp, expect in ((40.0, "TAKEN"), (70.0, "GATE_IVP")):
        cfg = Cfg("T1-P")
        d = make_day(ivp=ivp)
        k = set_path(d, 50000.0, "CE", 101, [(400.3, 401.0, 399.0, 400.5)])
        r = run_day(d, sig(d, cfg), cfg, events=[Event(100, "CE", "REENTRY", k=k, peak=395.0, step=6.0)])
        assert decisions(r)[100] == expect
        if expect == "TAKEN":
            tr = r.trades[0]
            assert tr["path"].f == D("401.00") and tr["path"].n == 2 and tr["lots_reason"] == "CAP"


# T17
def test_t17_fill_band_and_stale() -> None:
    cfg = Cfg("T1")
    for stale in (False, True):
        d = make_day()
        t = 100
        k = d.k(50000.0, "CE")
        d.opt["c"][d.k(50100.0, "CE"), t] = 290.0
        d.opt["c"][d.k(49900.0, "CE"), t] = 430.0
        d.opt["c"][d.k(49800.0, "CE"), t] = 480.0
        d.opt["c"][k, t] = 415.0
        d.opt["o"][k, t + 1] = 425.0
        d.stale[k, t + 1] = stale
        r = run_day(d, sig(d, cfg), cfg, events=[Event(t, "CE", "P1")])
        assert decisions(r)[t] == ("NO_FILL_STALE" if stale else "NO_FILL_BAND")


# T18
def test_t18_entry_windows() -> None:
    cfg = Cfg("T1")
    taken = {}
    for hm in ("09:19", "09:20", "11:29", "11:30", "13:14", "13:15", "14:44", "14:45"):
        d = make_day()
        t = minute(hm)
        r = run_day(d, sig(d, cfg), cfg, events=[Event(t, "CE", "P1")])
        taken[hm] = [tr["path"].e for tr in r.trades]
    assert taken["09:20"] == [minute("09:21")] and taken["11:29"] == [minute("11:30")]
    assert taken["13:15"] == [minute("13:16")] and taken["14:44"] == [minute("14:45")]
    assert taken["09:19"] == taken["11:30"] == taken["13:14"] == taken["14:45"] == []
    for es in taken.values():
        assert all(not (minute("11:31") <= e <= minute("13:15")) for e in es)


# T19
SEVEN_TEN = [
    (352.0, 356.5, 349.0, 355.5),
    (356.0, 359.0, 354.0, 358.5),
    (358.5, 364.5, 356.0, 364.0),
    (364.0, 371.0, 360.5, 370.5),
    (370.0, 380.0, 367.0, 379.0),
    (379.0, 391.0, 377.5, 390.0),
    (390.0, 402.0, 388.0, 401.0),
    (401.0, 404.0, 397.5, 398.0),
]


def _replay(monkeypatch: pytest.MonkeyPatch, mode: str, cfg: Cfg, bars: list[Any] = SEVEN_TEN) -> tuple[Any, D]:
    flat_atr(monkeypatch, 10.0)
    d = make_day()
    e = minute("10:15")
    k = set_path(d, 50000.0, "CE", e, bars)
    f = costs.buy_fill(D("352.00"), BASE.hs, BASE.slip)
    p = simulate(d, k, e, f, 3, cfg, NOSHOCK, Mode(mode, BASE))
    return p, engine.net(*engine.fills(d, p, BASE), 90, d.day)


def test_t19_hand_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    p, n = _replay(monkeypatch, "BARCLOSE", Cfg("T1"))
    assert (p.f, round(p.sl_init, 2), round(p.be_level, 2), round(p.g1_trig, 2)) == (
        D("352.70"),
        337.70,
        355.30,
        357.70,
    )
    assert (p.exit_bar, p.exit_reason, round(p.exit_level, 2), n) == (minute("10:22"), "TRAIL_G3", 398.40, D("3919.76"))
    p, n = _replay(monkeypatch, "WORST", Cfg("T1"))
    assert (p.exit_bar, n) == (minute("10:16"), D("48.21"))
    p, n = _replay(monkeypatch, "PATH", Cfg("T1"))
    assert n == D("4099.42")
    p, n = _replay(monkeypatch, "BARCLOSE", Cfg("T1", overrides={"EXIT_MODE": "X-B"}))
    assert (p.exit_bar, p.exit_reason, n) == (minute("10:20"), "TARGET30", D("2509.48"))
    p, n = _replay(monkeypatch, "BARCLOSE", Cfg("T1"), [(352.0, 353.0, 337.0, 338.0)])
    # spec §7.10 prints -1,532.75; the §5.1 total (one half-up rounding) is 119.74492 -> 119.74 (D-55 g)
    assert (p.exit_reason, n) == ("SL_G0", D("-1532.74"))


# T20
def test_t20_null(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = Cfg("T1-P")
    hot = make_day(ivp=70.0)
    assert not run._eligible(hot, cfg).any()  # K03 removes the whole day from the null
    d = _busy_day(5)
    res = run.null_random_day(cfg, d, 9, np.random.default_rng(1))
    assert 0 < len(res.trades) <= int(cfg["MAX_TRADES_DAY"])
    days = {dt.date(2026, 5, 4) + dt.timedelta(days=i): _busy_day(10 + i) for i in range(6)}
    monkeypatch.setattr(run, "day", lambda x: days[x])
    plan = [(x, 2) for x in days]
    draws = [run.null_random_seed((cfg, plan, s)) for s in range(41)]
    cand, rest = draws[0], draws[1:]
    pct = float(np.mean([v < cand for v in rest]))
    assert 0.05 <= pct <= 0.95 or len(set(rest)) == 1


# T21
def _grid_text(cfgs: list[dict[str, Any]], rnd: str = "R0") -> str:
    return f"# plan\n<!-- S3-GRID {rnd} -->\n```json\n{json.dumps(cfgs)}\n```\n"


def test_t21_preflight(tmp_path: Path) -> None:
    led = Ledger(tmp_path / "trials.jsonl", tmp_path / "runs", tmp_path / "calls.json")
    plan = tmp_path / "PLAN.md"
    plan.write_text(_grid_text([{"variant": "T1-P"}]))
    sid = costs.base().series_id
    old = lambda _p: dt.datetime(2020, 1, 1, tzinfo=dt.UTC)  # noqa: E731
    row = {"round": "R0", "config_hash": Cfg("T1-P").config_hash(), "series_id": sid}
    led.record(row, {})
    led.record(row, {})
    assert preflight.check("R0", sid, plan, led, old)["rows"] == 2
    lines = led.trials.read_text().splitlines()
    led.trials.write_text("\n".join(lines[:-1]) + "\n")
    with pytest.raises(preflight.PreflightError):
        preflight.check("R0", sid, plan, led, old)
    led.trials.write_text("\n".join(lines) + "\n")
    late = lambda _p: dt.datetime(2100, 1, 1, tzinfo=dt.UTC)  # noqa: E731
    with pytest.raises(preflight.PreflightError):
        preflight.check("R0", sid, plan, led, late)
    with pytest.raises(preflight.PreflightError):
        preflight.check("R1", sid, plan, led, old)


# T22
def test_t22_holdout_guard(tmp_path: Path) -> None:
    log = tmp_path / "access.log"
    h = data.split()["holdout"][0]
    with pytest.raises(data.HoldoutLocked):
        data.guard(h, log)
    assert data.access_count(log) == 1
    assert data.access_count() == 0  # the real program log: no holdout read so far
    uses = tmp_path / "uses.json"
    with data.holdout_session("cand", uses):
        data.guard(h, log)
    with pytest.raises(data.HoldoutLocked), data.holdout_session("cand2", uses):
        pass
    data.guard(data.split()["design"][0], log)


# T23
def test_t23_deterministic() -> None:
    cfg = Cfg("T1-P")
    outs = []
    for _ in range(2):
        d = _busy_day(3)
        evs = [Event(t, "CE" if t % 2 else "PE", "P1") for t in range(5, 330, 9)]
        r = run_day(d, sig(d, cfg), cfg, events=evs)
        outs.append([(tr["t"], str(tr["net_base"]), tr["path"].exit_reason) for tr in r.trades])
        outs.append(len(run.null_random_day(cfg, d, 3, np.random.default_rng(7)).trades))
    assert outs[0] == outs[2] and outs[1] == outs[3]


# T24
def test_t24_series_id(tmp_path: Path) -> None:
    a, b = costs.full_spread(D("1.00")), costs.full_spread(D("1.50"))
    assert a.series_id != b.series_id and costs.base().series_id == costs.base().series_id
    led = Ledger(tmp_path / "t.jsonl", tmp_path / "r", tmp_path / "c.json")
    plan = tmp_path / "PLAN.md"
    plan.write_text(_grid_text([{"variant": "T1-P"}]))
    led.record({"round": "R0", "config_hash": Cfg("T1-P").config_hash(), "series_id": b.series_id}, {})
    with pytest.raises(preflight.PreflightError):
        preflight.check("R0", costs.base().series_id, plan, led, lambda _p: dt.datetime(2020, 1, 1, tzinfo=dt.UTC))


# T25
def test_t25_early_bars() -> None:
    d = make_day(walk=True, seed=2)
    f = base_feats(d)
    t = minute("09:20")
    assert math.isnan(f["atr10"][t - 1])
    assert f["atr10"][t] == pytest.approx(float(np.mean(d.base["spot_h"][:5] - d.base["spot_l"][:5])))
    assert f["fvol_avg"][t] == pytest.approx(float(np.mean(d.base["fut_v"][:5])))
    cfg = Cfg("T1-P")
    s = sig(d, cfg)
    assert shadow(d, s, minute("09:40"), "CE", -1, 15.0, "P1", cfg)["K27"] == "NA"
    b = d.base
    for m in range(5, 9):  # a textbook trap at 09:20-09:23, before P3_START
        b["spot_c"][m] = 50300.0 if m % 2 else 49700.0
    b["fut_v"][:] = 5000.0
    pe, ce = p3(d, s, 1.25, {"HDFCBANK": np.full(375, -0.01), "ICICIBANK": np.full(375, -0.01)})
    assert not pe[: minute("09:30")].any() and not ce[: minute("09:30")].any()


# nested walk-forward fixture (§13.4): 5 blocks, 4 OOS windows, training-only choice
def test_nested_wf_fixture() -> None:
    days = [dt.date(2025, 1, 1) + dt.timedelta(days=i) for i in range(362)]
    b = blocks(days)
    assert [len(x) for x in b] == [72, 72, 72, 72, 74]
    w = windows(days)
    assert [x.k for x in w] == [1, 2, 3, 4] and w[0].train == b[0] and w[3].test == b[4]
    calls: list[tuple[int, str]] = []

    def fit(c: int, ds: tuple[dt.date, ...], role: str) -> float:
        calls.append((c, role))
        return float(c if role.startswith("train") else -c)

    out = nested(days, [1, 3, 2], fit, lambda v: v)
    assert [o.chosen for o in out] == [1, 1, 1, 1] and all(o.test == -3.0 for o in out)
    assert len(calls) == 4 * 3 + 4


# R2 strike modes and the R5 K12 confirmation (module tests, D-56)
def test_r2_strike_modes() -> None:
    d = make_day()
    t = 100
    d.opt["delta"][d.cp == "CE", t] = 0.1
    for s in (49800.0, 49900.0, 50000.0, 50100.0, 50200.0):
        k = d.k(s, "CE")
        d.opt["delta"][k, t] = {49800.0: 0.70, 49900.0: 0.60, 50000.0: 0.25, 50100.0: 0.50, 50200.0: 0.40}[s]
        d.opt["c"][k, t] = {49800.0: 450.0, 49900.0: 430.0, 50000.0: 350.0, 50100.0: 290.0, 50200.0: 250.0}[s]
    pick = lambda m: float(d.strikes[engine.pick_strike(d, t, "CE", Cfg("T1-P", overrides={"STRIKE_MODE": m}))[0]])  # noqa: E731
    assert pick("PREMIUM_BAND") == 50000.0
    assert pick("DELTA_BAND") == 49900.0  # |Delta| 0.60 and 0.50 tie at 0.05 from 0.55; the lower index wins
    assert pick("N15") == 50100.0  # CE: nearest 0.50 inside 0.45-0.55
    assert pick("N6") == 49900.0  # band strike Delta 0.25 < 0.30 -> one strike in, premium 430 <= 500
    d.opt["c"][d.k(49900.0, "CE"), t] = 520.0
    assert engine.pick_strike(d, t, "CE", Cfg("T1-P", overrides={"STRIKE_MODE": "N6"})) == (-1, "N6_FAIL")


def test_r5_k12_confirmation() -> None:
    cfg = Cfg("T1", checks=("K12",))
    for back_inside, expect in ((True, "GATE_TRAP_K12"), (False, "TAKEN")):
        d = make_day()
        t = 100
        s = sig(d, cfg)
        s.f["hi_l"][t] = 50010.0
        d.base["spot_c"][t + 1] = 50000.0 if back_inside else 50020.0
        r = run_day(d, s, cfg, events=[Event(t, "CE", "P1")])
        assert decisions(r)[t] == expect
        if expect == "TAKEN":
            assert r.trades[0]["path"].e == t + 2
