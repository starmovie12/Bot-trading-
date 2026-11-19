"""S3 runner: config x days -> trades / signals rows (§15.1, §15.3); every fit logged to the ledger (§13.2);
nulls (§13.5), exit check, and the §14.1 statistics."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np

from lab.s3 import costs
from lab.s3.checks import adx, shadow
from lab.s3.data import Day, design_days, load
from lab.s3.engine import (
    BARCLOSE,
    BASE,
    M_EXP,
    M_FF,
    DayState,
    Event,
    Mode,
    Px,
    TradePath,
    dec,
    fills,
    k03_ok,
    k03_on,
    k05_ok,
    net,
    opt_atr5,
    pick_strike,
    proxy_px,
    regular_events,
    run_day,
    shock_state,
    simulate,
    sl_points,
    windows,
)
from lab.s3.features import SigParams, signals
from lab.s3.ledger import Ledger
from lab.s3.registry import CHK, FIX, SEED, STATS, Cfg, hhmm
from tools.nested_wf import blocks, oos_days

ROOT = Path(__file__).resolve().parents[2]
STRESS_FILE = ROOT / "wip/s3_stress.json"


@cache
def day(d: dt.date) -> Day:
    return load(d)


def code_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def stress_px() -> Px:
    """STRESS half spread = max(2 x BASE half, median half_spread_PROXY of T1-P entry bars), slip x 2 (§5.3).
    Frozen once in wip/s3_stress.json (from the R0 T1-P OOS entries) so the series never moves."""
    if STRESS_FILE.exists():
        v = Decimal(json.loads(STRESS_FILE.read_text())["half_spread"])
        return Px(v, BASE.slip * Decimal(str(costs.COST["STRESS_SLIP_MULT"])))
    raise FileNotFoundError("stress series not frozen yet: run freeze_stress() on the T1-P OOS entries first")


def freeze_stress(proxy_halves: list[float]) -> Px:
    med = float(np.median(proxy_halves)) if proxy_halves else 0.0
    floor = BASE.hs * Decimal(str(costs.COST["STRESS_SPREAD_MULT"]))
    hs = max(floor, dec(med).quantize(Decimal("0.01")))
    STRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STRESS_FILE.write_text(json.dumps({"half_spread": str(hs), "median_proxy": med, "n": len(proxy_halves)}))
    return stress_px()


def series_ids() -> dict[str, str]:
    out = {"base": costs.base().series_id}
    if STRESS_FILE.exists():
        out["stress"] = costs.stress(stress_px().hs).series_id
    return out


@dataclass
class Run:
    cfg: Cfg
    trades: list[dict[str, Any]]
    signals: list[dict[str, Any]]


def run_days(cfg: Cfg, days: Sequence[dt.date], mode: Mode = BARCLOSE, record: bool = True, full: bool = True) -> Run:
    sp = SigParams.of(cfg)
    trades: list[dict[str, Any]] = []
    sigs: list[dict[str, Any]] = []
    for x in days:
        d = day(x)
        sg = signals(d, sp)
        r = run_day(d, sg, cfg, run=mode, record=record)
        for tr in r.trades:
            trades.append(
                trade_row(d, sg, cfg, tr, mode)
                if full
                else {"date": x.isoformat(), "net_base": float(tr["net_base"]), "t": tr["t"]}
            )
        if record:
            for s in r.signals:
                sigs.append(signal_row(d, sg, cfg, s))
    return Run(cfg, trades, sigs)


def ts(d: Day, m: int) -> str:
    return f"{d.day.isoformat()} {hhmm(m)}"


def trade_row(d: Day, sg: Any, cfg: Cfg, tr: dict[str, Any], mode: Mode) -> dict[str, Any]:
    p: TradePath = tr["path"]
    ev: Event = tr["event"]
    t = tr["t"]
    qty = p.n * p.lot
    fe, fx = fills(d, p, mode.px)
    ch = costs.round_trip(fe, fx, qty, d.day)
    nb = net(fe, fx, qty, d.day)
    out: dict[str, Any] = {}
    try:
        sp = stress_px()
        out["net_stress"] = float(net(*fills(d, p, sp), qty, d.day))
    except FileNotFoundError:
        out["net_stress"] = math.nan
    pe_, px_ = proxy_px(d, p.k, p.e), proxy_px(d, p.k, p.exit_bar)
    f_p = costs.buy_fill(dec(d.opt["o"][p.k, p.e]), pe_.hs, pe_.slip)
    m = Decimal(str(FIX["STALE_SPREAD_MULT"])) if p.stale_forced else Decimal(1)
    x_p = costs.sell_fill(dec(p.exit_level), px_.hs * m, px_.slip * m)
    out["net_proxy"] = float(net(f_p, x_p, qty, d.day))
    trig, _ = shock_state(d)
    for name in ("PATH", "WORST"):
        q = simulate(d, p.k, p.e, p.f, p.n, cfg, trig, Mode(name, mode.px))
        out[f"net_{name.lower()}"] = float(net(*fills(d, q, mode.px), qty, d.day))
    delta = float(d.opt["delta"][p.k, t])
    side = str(d.cp[p.k])
    ck = shadow(d, sg, t, side, p.k, float(p.f) - p.sl_init, ev.pattern, cfg)
    hs_slip = (fe - dec(d.opt["o"][p.k, p.e])) + (dec(p.exit_level) - fx)
    return {
        "series_id": costs.base().series_id if mode.px == BASE else f"custom:{mode.px.hs}/{mode.px.slip}",
        "config_hash": cfg.config_hash(),
        "date": d.day.isoformat(),
        "signal_ts": ts(d, t),
        "pattern": ev.pattern,
        "side": side,
        "expiry": d.meta["expiry"],
        "dte": d.dte,
        "strike": float(d.strikes[p.k]),
        "delta_at_entry": delta,
        "premium_at_signal": float(d.opt["c"][p.k, t]),
        "entry_ts": ts(d, p.e),
        "entry_fill": float(fe),
        "lots": p.n,
        "lots_reason": tr["lots_reason"],
        "lot_size": p.lot,
        "qty": qty,
        "sl_init": round(p.sl_init, 2),
        "be_level": round(p.be_level, 2),
        "index_risk_pts": ck["index_risk_pts"],
        "room_pts": ck["room_pts"],
        "peak": p.peak,
        "peak_ts": ts(d, p.peak_bar),
        "max_gear": p.max_gear,
        "mfe_pts": round(p.mfe, 2),
        "mae_pts": round(p.mae, 2),
        "bars_held": p.exit_bar - p.e,
        "exit_ts": ts(d, p.exit_bar),
        "exit_level": round(p.exit_level, 4),
        "exit_fill": float(fx),
        "exit_reason": p.exit_reason,
        "stale_forced": p.stale_forced,
        "gross_rs": float((fx - fe) * qty),
        **{c: float(ch[c].quantize(Decimal("0.01"))) for c in costs.COMPONENTS},
        "charges_total": float(ch["total"]),
        "spread_slip_rs": float(hs_slip * qty),
        "net_base": float(nb),
        **out,
        "score": ck["score"],
        "checks_green": ck["checks_green"],
        "wf_window": wf_block(d.day),
        "vix_open": float(d.base["vix_o"][0]),
        "vix_half": vix_half(d.day),
        "day_state": day_state(d.day),
        "strike_how": tr["how"],
    }


def signal_row(d: Day, sg: Any, cfg: Cfg, s: dict[str, Any]) -> dict[str, Any]:
    t, side, k = s["t"], s["side"], s["k"]
    row = {
        "date": d.day.isoformat(),
        "signal_ts": ts(d, t),
        "side": side,
        "pattern": s["pattern"],
        "strike": float(d.strikes[k]) if k >= 0 else math.nan,
        "decision": s["decision"],
    }
    b = d.base
    row |= {
        "spot_c": float(b["spot_c"][t]),
        "fut_c": float(b["fut_c"][t]),
        "vwap": float(sg.f["vwap"][t]),
        "ema9": float(sg.f["ema9"][t]),
        "atr10": float(sg.f["atr10"][t]),
    }
    if side in ("CE", "PE"):
        sl = (
            sl_points(cfg, opt_atr5((d.opt["h"][k] - d.opt["l"][k]).tolist(), d.stale[k].tolist(), t))
            if k >= 0
            else float(cfg["SL_INIT_PTS"])
        )
        row |= {x: v for x, v in shadow(d, sg, t, side, k, sl, s["pattern"], cfg).items()}
    return row


@cache
def wf_map() -> dict[dt.date, int]:
    return {x: i + 1 for i, blk in enumerate(blocks(design_days())) for x in blk}


def wf_block(x: dt.date) -> int:
    return wf_map().get(x, 0)


@cache
def vix_median() -> float:
    return float(np.median([day(x).base["vix_o"][0] for x in design_days()]))


def vix_half(x: dt.date) -> str:
    return "HIGH" if day(x).base["vix_o"][0] > vix_median() else "LOW"


@cache
def day_state_all() -> dict[dt.date, str]:
    """§4.3 DAY_STATE (diagnosis only; EOD data): TREND / CHOP / DEAD / NORMAL."""
    out: dict[dt.date, str] = {}
    ranges: list[float] = []
    for x in design_days():
        d = day(x)
        b = d.base
        rng = float(np.nanmax(b["spot_h"]) - np.nanmin(b["spot_l"]))
        mv = abs(float(b["spot_c"][~np.isnan(b["spot_c"])][-1] - b["spot_o"][0]))
        b3 = d.b3
        k3 = {c: b3[c].to_numpy().astype(float) for c in ("h", "l", "c")}
        a = adx(k3["h"], k3["l"], k3["c"], int(CHK["K01_ADX_N"]))
        sg = signals(d, SigParams.of(Cfg("T1")))
        above = (b["fut_c"] > sg.f["vwap"]).astype(int)
        crosses = int(np.sum(np.abs(np.diff(above[~np.isnan(sg.f["vwap"])]))))
        prior = ranges[-int(CHK["DEAD_DAYS"]) :]
        if mv >= CHK["TREND_FRAC"] * rng and a >= CHK["TREND_ADX"]:
            out[x] = "TREND"
        elif crosses >= CHK["CHOP_CROSSINGS_DAY"]:
            out[x] = "CHOP"
        elif len(prior) == int(CHK["DEAD_DAYS"]) and rng < CHK["DEAD_RANGE_FRAC"] * float(np.mean(prior)):
            out[x] = "DEAD"
        else:
            out[x] = "NORMAL"
        ranges.append(rng)
    return out


def day_state(x: dt.date) -> str:
    return day_state_all().get(x, "NA")


# ---------- ledger ----------


def summary(trades: list[dict[str, Any]]) -> dict[str, Any]:
    nb = [t["net_base"] for t in trades]
    ns = [t.get("net_stress", math.nan) for t in trades]
    return {
        "trades": len(nb),
        "net_base": round(float(np.sum(nb)), 2) if nb else 0.0,
        "net_stress": round(float(np.sum(ns)), 2) if ns else 0.0,
        "per_trade": round(float(np.mean(nb)), 2) if nb else 0.0,
    }


def fit(led: Ledger, rnd: str, cfg: Cfg, run: Run, window: int, role: str) -> str:
    """One fit = one config on one window's days: one ledger row + one result file."""
    tw = [t for t in run.trades if t["wf_window"] == window] if window else run.trades
    row = {
        "round": rnd,
        "config_hash": cfg.config_hash(),
        "series_id": costs.base().series_id,
        "variant": cfg.variant,
        "overrides": cfg.overrides,
        "flags": cfg.flags,
        "window": window,
        "role": role,
        "code_commit": code_commit(),
    }
    return led.record(row, summary(tw))


# ---------- nulls ----------


def _eligible(d: Day, cfg: Cfg) -> np.ndarray[Any, Any]:
    w = windows(cfg, d.dte)
    if k03_on(cfg) and k03_ok(d) is False:
        w[:] = False
    return w


def null_random_day(cfg: Cfg, d: Day, need: int, rng: np.random.Generator) -> Any:
    """One NULL-RANDOM day: `need` entries at random eligible bars (direction-free filters only: time window,
    K03), random side; K05 checked for the random side (fail -> pick again); engine, sizing, exits, day rules
    and costs unchanged."""
    sg = signals(d, SigParams.of(cfg))
    elig = np.flatnonzero(_eligible(d, cfg))
    state = {"cursor": -1}

    def provider(free_at: int, st: DayState) -> Event | None:
        for _ in range(10 * max(1, elig.size)):
            lo = max(free_at, st.cool_until - 1, state["cursor"] + 1)
            pool = elig[elig >= lo]
            if pool.size == 0:
                return None
            remaining = max(1, need - st.trades)
            pick = int(np.min(rng.choice(pool, size=min(remaining, pool.size), replace=False)))
            side = "CE" if rng.integers(0, 2) == 0 else "PE"
            if cfg.var("gate_k05"):
                k, _ = pick_strike(d, pick, side, cfg)
                if k >= 0:
                    f = float(d.opt["o"][k, min(pick + 1, d.opt["o"].shape[1] - 1)])
                    sl = min(float(cfg["SL_INIT_PTS"]), f * float(FIX["SL_MAX_PCT"]))
                    if k05_ok(d, pick, side, k, sl) is False:
                        continue
            state["cursor"] = pick
            return Event(pick, side, "RANDOM")
        return None

    return run_day(d, sg, cfg, provider=provider, record=False, max_entries=need)


def null_random_seed(args: tuple[Cfg, list[tuple[dt.date, int]], int]) -> float:
    """One NULL-RANDOM draw over the candidate's trading days (same entry count per day)."""
    cfg, plan, seed = args
    rng = np.random.default_rng([SEED, seed])
    tot = Decimal(0)
    for x, need in plan:
        r = null_random_day(cfg, day(x), need, rng)
        tot += sum((t["net_base"] for t in r.trades), Decimal(0))
    return float(tot)


def null_random(cfg: Cfg, cand: list[dict[str, Any]], seeds: int | None = None, workers: int = 4) -> dict[str, Any]:
    n_seeds = int(seeds if seeds is not None else STATS["NULL_SEEDS"])
    per: dict[str, int] = {}
    for t in cand:
        if t["pattern"] != "REENTRY":
            per[t["date"]] = per.get(t["date"], 0) + 1
    plan = [(dt.date.fromisoformat(x), n) for x, n in sorted(per.items())]
    with ProcessPoolExecutor(workers) as ex:
        draws = list(
            ex.map(
                null_random_seed, [(cfg, plan, s) for s in range(n_seeds)], chunksize=max(1, n_seeds // (workers * 8))
            )
        )
    c = float(sum(t["net_base"] for t in cand))
    k = sum(1 for v in draws if v >= c)
    return {
        "candidate": c,
        "p": (k + 1) / (n_seeds + 1),
        "pct": float(np.mean([v < c for v in draws])),
        "median": float(np.median(draws)),
        "draws": draws,
        "seeds": n_seeds,
    }


def null_flip(cfg: Cfg, days: Sequence[dt.date]) -> dict[str, Any]:
    sp = SigParams.of(cfg)
    tot, n = Decimal(0), 0
    for x in days:
        d = day(x)
        sg = signals(d, sp)
        evs = [Event(e.t, {"CE": "PE", "PE": "CE"}.get(e.side, e.side), "FLIP") for e in regular_events(sg)]
        r = run_day(d, sg, cfg, events=evs, record=False)
        tot += sum((t["net_base"] for t in r.trades), Decimal(0))
        n += len(r.trades)
    return {"net_base": float(tot), "trades": n}


def exit_check(trades: list[dict[str, Any]]) -> dict[int, dict[str, float]]:
    """Same entries, fixed N-bar exit (no stop), clock exits still apply."""
    out = {}
    for nb in STATS["EXIT_CHECK_BARS"]:
        tot, wins = Decimal(0), 0
        for t in trades:
            d = day(dt.date.fromisoformat(t["date"]))
            k = d.k(t["strike"], t["side"])
            e = int(t["entry_ts"][-5:-3]) * 60 + int(t["entry_ts"][-2:]) - (9 * 60 + 15)
            clock = M_EXP if d.dte == 0 else M_FF
            x = min(e + int(nb), clock)
            st = d.stale[k]
            fe = Decimal(str(t["entry_fill"]))
            if not st[x]:
                fx = costs.sell_fill(dec(d.opt["o"][k, x]), BASE.hs, BASE.slip)
            else:
                ns = [j for j in range(e, x) if not st[j]]
                j = ns[-1] if ns else e
                lvl = min(d.opt["l"][k, j], d.opt["c"][k, j])
                mlt = Decimal(str(FIX["STALE_SPREAD_MULT"]))
                fx = costs.sell_fill(dec(lvl), BASE.hs * mlt, BASE.slip * mlt)
            v = net(fe, fx, int(t["qty"]), d.day)
            tot += v
            wins += v > 0
        out[int(nb)] = {"net_base": float(tot), "win_rate": wins / max(1, len(trades))}
    return out


# ---------- statistics (§14.1) ----------


def daily(trades: list[dict[str, Any]], days: Sequence[dt.date], col: str = "net_base") -> np.ndarray[Any, Any]:
    idx = {x.isoformat(): i for i, x in enumerate(days)}
    v = np.zeros(len(days))
    for t in trades:
        v[idx[t["date"]]] += t[col]
    return v


def block_boot(v: np.ndarray[Any, Any], n_out: int, rng: np.random.Generator) -> np.ndarray[Any, Any]:
    bl = int(STATS["BOOT_BLOCK_DAYS"])
    starts = rng.integers(0, max(1, v.size - bl + 1), size=math.ceil(n_out / bl))
    return np.concatenate([v[s : s + bl] for s in starts])[:n_out]


def boot_p(v: np.ndarray[Any, Any]) -> float:
    rng = np.random.default_rng(SEED)
    b = int(STATS["BOOT_N"])
    means = np.array([block_boot(v, v.size, rng).mean() for _ in range(b)])
    return float((np.sum(means <= 0) + 1) / (b + 1))


def dd95(v: np.ndarray[Any, Any]) -> float:
    rng = np.random.default_rng(SEED + 1)
    yd = int(STATS["YEAR_DAYS"])
    dds = []
    for _ in range(int(STATS["BOOT_N"])):
        eq = np.cumsum(block_boot(v, yd, rng))
        dds.append(float(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq])) - np.concatenate([[0.0], eq]))))
    return float(np.percentile(dds, 95))


def gates(trades: list[dict[str, Any]], days: Sequence[dt.date], null_p: float | None) -> dict[str, Any]:
    v = daily(trades, days)
    nb = np.array([t["net_base"] for t in trades]) if trades else np.zeros(0)
    ns = float(np.sum([t["net_stress"] for t in trades])) if trades else 0.0
    wins = {}
    for w in (2, 3, 4, 5):
        tw = [t["net_base"] for t in trades if t["wf_window"] == w]
        wins[w] = (round(float(np.sum(tw)), 2), len(tw))
    best5 = float(np.sum(np.sort(nb)[:-5])) if nb.size > 5 else math.nan
    halves = {h: float(np.sum([t["net_base"] for t in trades if t["vix_half"] == h])) for h in ("LOW", "HIGH")}
    e12 = float(v.mean() * float(STATS["YEAR_DAYS"])) if v.size else 0.0
    d95 = dd95(v) if v.size else math.nan
    bp = boot_p(v) if v.size else math.nan
    g = {
        "1_net_base_pos": bool(nb.size and nb.sum() > 0),
        "2_net_stress_ge0": ns >= 0,
        "3_windows_3of4_25tr": sum(1 for s, n in wins.values() if s > 0 and n >= STATS["MIN_TRADES_WINDOW"]) >= 3,
        "4_best5_removed_pos": bool(best5 > 0),
        "5_vix_halves_ge0": all(x >= 0 for x in halves.values()),
        "6_trades_ge150": int(nb.size) >= int(STATS["MIN_TRADES_OOS"]),
        "7_boot_p_lt_005": bool(bp < STATS["P_MAX"]),
        "8_e12_ge_dd95": bool(e12 >= d95),
        "9_null_p_le_005": bool(null_p is not None and null_p <= STATS["NULL_P_MAX"]),
    }
    return {
        "gates": g,
        "all_pass": all(g.values()),
        "net_base": float(nb.sum()) if nb.size else 0.0,
        "net_stress": ns,
        "per_trade": float(nb.mean()) if nb.size else 0.0,
        "trades": int(nb.size),
        "trades_per_day": nb.size / max(1, len(days)),
        "windows": wins,
        "best5_removed": best5,
        "vix_halves": halves,
        "e12": e12,
        "dd95": d95,
        "boot_p": bp,
        "null_p": null_p,
    }


def trades_hash(trades: list[dict[str, Any]]) -> str:
    keys = (
        "date",
        "signal_ts",
        "side",
        "strike",
        "entry_fill",
        "lots",
        "exit_ts",
        "exit_fill",
        "exit_reason",
        "net_base",
    )
    blob = json.dumps([[t[k] for k in keys] for t in trades], sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def oos() -> tuple[dt.date, ...]:
    return oos_days(design_days())
