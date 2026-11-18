# ruff: noqa: E501 (markdown report lines)
"""S3 round R0 (BANKNIFTY_STRATEGY_V3.md §13.3): T1-RAW + T1 (comparison) and T1-P (main) on the 4 OOS windows,
nulls, diagnosis, cost curve, intrabar, CSVs. Work goes to wip/r0/ and moves to results/ only when R0 is complete."""

from __future__ import annotations

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)

import json
import shutil
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from lab.s3 import costs
from lab.s3 import report as rp
from lab.s3 import run as R
from lab.s3.engine import BASE, Mode, Px
from lab.s3.features import SigParams, signals
from lab.s3.ledger import Ledger
from lab.s3.registry import COST, SEED, Cfg
from tools import preflight
from tools.overfit import dsr

ROOT = Path(__file__).resolve().parents[2]
WIP = ROOT / "wip/r0"
LOG = ROOT / "wip/r0/progress.log"


def log(msg: str) -> None:
    WIP.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def freeze() -> Px:
    if R.STRESS_FILE.exists():
        return R.stress_px()
    cfg = Cfg("T1-P")
    halves = []
    for x in R.oos():
        d = R.day(x)
        r = R.run_day(d, signals(d, SigParams.of(cfg)), cfg, record=False)
        halves += [float(d.opt["hs_proxy"][t["path"].k, t["path"].e]) for t in r.trades]
    halves = [h for h in halves if h > 0]
    return R.freeze_stress(halves)


def main() -> int:
    sid = costs.base().series_id
    try:
        pf = preflight.check("R0", sid)
    except preflight.PreflightError as e:
        print(f"PREFLIGHT ABORT: {e}")
        return 1
    log(f"preflight {pf}")
    days = R.oos()
    sp = freeze()
    log(f"stress half spread {sp.hs} slip {sp.slip}")
    led = Ledger()
    commit = R.code_commit()
    runs: dict[str, R.Run] = {}
    for v in ("T1-RAW", "T1", "T1-P"):
        cfg = Cfg(v)
        r = R.run_days(cfg, days)
        ids = {w: R.fit(led, "R0", cfg, r, w, f"test:{w - 1}") for w in (2, 3, 4, 5)}
        for t in r.trades:
            t |= {"trial_id": ids[t["wf_window"]], "variant": v, "code_commit": commit}
        for s in r.signals:
            s["variant"] = v
        runs[v] = r
        log(f"{v}: {len(r.trades)} trades net {sum(t['net_base'] for t in r.trades):.2f}")
    rp.write_csv(WIP / "s3_trades.csv", [t for r in runs.values() for t in r.trades], rp.TRADE_COLS)
    sig_cols = ["variant", *sorted({k for r in runs.values() for s in r.signals for k in s} - {"variant"})]
    rp.write_csv(WIP / "s3_signals.csv", [s for r in runs.values() for s in r.signals], sig_cols)
    main_cfg, tp = Cfg("T1-P"), runs["T1-P"].trades
    curve = []
    for full in COST["COST_CURVE_SPREADS"]:
        px = Px(Decimal(str(full)) / 2, BASE.slip)
        rr = R.run_days(main_cfg, days, Mode("BARCLOSE", px), record=False, full=False)
        curve.append((float(full), float(sum(t["net_base"] for t in rr.trades)), len(rr.trades)))
    log(f"cost curve {curve}")
    intrabar = {}
    for m in ("PATH", "WORST"):
        rr = R.run_days(main_cfg, days, Mode(m, BASE), record=False, full=False)
        intrabar[m] = (float(sum(t["net_base"] for t in rr.trades)), len(rr.trades))
    log(f"intrabar {intrabar}")
    flip = R.null_flip(main_cfg, days)
    ex = R.exit_check(tp)
    log(f"flip {flip} exit {ex}")
    nr = R.null_random(main_cfg, tp)
    log(f"null random p {nr['p']:.4f} pct {nr['pct']:.3f}")
    g = R.gates(tp, days, nr["p"])
    v = R.daily(tp, days)
    d1 = dsr(v, 1, 0.0) if v.std() > 0 else float("nan")
    summary = {
        "series": R.series_ids(),
        "stress": {"half_spread": str(sp.hs), "slip": str(sp.slip)},
        "variants": {k: R.gates(r.trades, days, None) | {"hash": R.trades_hash(r.trades)} for k, r in runs.items()},
        "t1p_gates": g,
        "dsr_n1": d1,
        "null_random": {k: nr[k] for k in ("candidate", "p", "pct", "median", "seeds")},
        "null_flip": flip,
        "exit_check": ex,
        "cost_curve": curve,
        "intrabar": intrabar,
        "fits": led.counts()[0],
    }
    (WIP / "s3_r0_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    write_reports(runs, summary, nr, days)
    for f in (
        "s3_trades.csv",
        "s3_signals.csv",
        "s3_nulls.md",
        "s3_diagnosis.md",
        "s3_cost_curve.md",
        "s3_intrabar.md",
        "s3_r0_summary.json",
    ):
        shutil.copy(WIP / f, ROOT / "results" / f)
    log("R0 complete")
    return 0


def write_reports(runs: dict[str, R.Run], s: dict[str, Any], nr: dict[str, Any], days: Any) -> None:
    tp = runs["T1-P"].trades
    hdr = "[BACKTEST·OOS] PRE-TAX · DESIGN blocks 2-5 (290 days) · series BASE " + s["series"]["base"]
    n = [
        "# S3 R0 · Nulls (T1-P)",
        "",
        hdr,
        "",
        f"- NULL-RANDOM ({nr['seeds']} seeds, SEED {SEED}): T1-P {rp.rs(nr['candidate'])} vs null median {rp.rs(nr['median'])}; percentile {nr['pct'] * 100:.1f}; **p = {nr['p']:.4f}**",
        f"- NULL-FLIP (same signal times, opposite side): {rp.rs(s['null_flip']['net_base'])} on {s['null_flip']['trades']} trades",
    ]
    n += [
        f"- EXIT-CHECK {k} bars (same entries, no stop): {rp.rs(x['net_base'])}, win rate {x['win_rate'] * 100:.1f}%"
        for k, x in s["exit_check"].items()
    ]
    n += [f"- Gear engine (T1-P actual): {rp.rs(sum(t['net_base'] for t in tp))}"]
    (WIP / "s3_nulls.md").write_text("\n".join(n) + "\n")
    c = [
        "# S3 R0 · Cost curve (T1-P, full spread; slip 0.20 per side; engine re-run per spread)",
        "",
        hdr,
        "",
        "| full spread | trades | net_base |",
        "|---:|---:|---:|",
    ]
    c += [f"| ₹{a:.2f} | {k} | {rp.rs(b)} |" for a, b, k in s["cost_curve"]]
    c += ["", f"**Spread {rp.zero_crossing([(a, b) for a, b, _ in s['cost_curve']])} hua toh strategy zero par.**"]
    (WIP / "s3_cost_curve.md").write_text("\n".join(c) + "\n")
    bc = sum(t["net_base"] for t in tp)
    sens = any(v[0] < 0 for v in s["intrabar"].values())
    i = [
        "# S3 R0 · Intrabar sensitivity (T1-P; §6.3; report, not a gate)",
        "",
        hdr,
        "",
        "| mode | trades | net_base (full re-run) |",
        "|---|---:|---:|",
        f"| BARCLOSE (the rule) | {len(tp)} | {rp.rs(bc)} |",
    ]
    i += [f"| {m} | {k} | {rp.rs(v)} |" for m, (v, k) in s["intrabar"].items()]
    i += [
        "",
        f"Per-trade re-sim (same entries): PATH {rp.rs(sum(t['net_path'] for t in tp))}, WORST {rp.rs(sum(t['net_worst'] for t in tp))}.",
    ]
    i += ["", "**Label: INTRABAR-SENSITIVE**" if sens else "Label: none (PATH and WORST net_base >= 0)"]
    (WIP / "s3_intrabar.md").write_text("\n".join(i) + "\n")
    (WIP / "s3_diagnosis.md").write_text("\n".join(diagnosis(runs, s)) + "\n")


def diagnosis(runs: dict[str, R.Run], s: dict[str, Any]) -> list[str]:
    tp = runs["T1-P"].trades
    out = ["# S3 R0 · Diagnosis (§13.6; not a trial)", "", "[BACKTEST·OOS] PRE-TAX · 290 OOS days · series BASE", ""]
    out += [
        "| variant | trades | /day | net_base | per trade | net_stress | p | R | p needed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for k, r in runs.items():
        gv, q = s["variants"][k], rp.pr(r.trades)
        out.append(
            f"| {k} | {gv['trades']} | {gv['trades_per_day']:.2f} | {rp.rs(gv['net_base'])} | {rp.rs(gv['per_trade'])} | {rp.rs(gv['net_stress'])} | {q['p']:.3f} | {q['R']:.2f} | {q['p_needed']:.3f} |"
        )
    g = s["t1p_gates"]
    out += ["", "**T1-P · §14.1 gates**", "", "| gate | pass |", "|---|---|"] + [
        f"| {a} | {'PASS' if b else 'FAIL'} |" for a, b in g["gates"].items()
    ]
    out += [
        "",
        f"windows (net, trades): {g['windows']} · best-5 removed {rp.rs(g['best5_removed'])} · VIX halves {g['vix_halves']} · E12 {rp.rs(g['e12'])} vs DD95 {rp.rs(g['dd95'])} · bootstrap p {g['boot_p']:.4f} · DSR(N=1) {s['dsr_n1']:.3f}",
        "",
    ]
    mfe = np.array([t["mfe_pts"] for t in tp])
    mae = np.array([t["mae_pts"] for t in tp])
    reach = " · ".join(f"+{x}: {np.mean(mfe >= x) * 100:.0f}%" for x in (5, 10, 25, 30))
    wins = [t for t in tp if t["net_base"] > 0]
    cap = (
        (np.mean([t["exit_fill"] - t["entry_fill"] for t in wins]) / np.mean([t["mfe_pts"] for t in wins]))
        if wins
        else float("nan")
    )
    out += [
        f"MFE median {np.median(mfe):.1f} pt, MAE median {np.median(mae):.1f} pt · reached {reach} · MFE capture (winners) {cap:.2f}",
        "",
    ]
    gaps = [t["net_base"] for t in tp if t["exit_reason"] == "GAP_SL"]
    stl = [t["net_base"] for t in tp if t["stale_forced"]]
    out += [
        f"GAP_SL {len(gaps)} (worst {rp.rs(min(gaps)) if gaps else '-'}) · STALE_FORCED {len(stl)} (worst {rp.rs(min(stl)) if stl else '-'})",
        "",
    ]
    gross = sum(t["gross_rs"] for t in tp)
    out += [
        f"Money: gross {rp.rs(gross)} · charges {rp.rs(sum(t['charges_total'] for t in tp))} · spread+slip inside fills {rp.rs(sum(t['spread_slip_rs'] for t in tp))}",
        "",
    ]
    out += rp.table("Exit reason", rp.group(tp, lambda t: t["exit_reason"]))
    out += rp.table("CE vs PE", rp.group(tp, lambda t: t["side"]))
    out += rp.table("DTE", rp.group(tp, lambda t: rp.dte_bucket(int(t["dte"]))))
    out += rp.table("Entry half-hour", rp.group(tp, rp.half_hour))
    out += rp.table("Pattern", rp.group(tp, lambda t: t["pattern"]))
    out += rp.table("DAY_STATE (EOD, diagnosis only)", rp.group(tp, lambda t: t["day_state"]))
    out += rp.table("VIX half", rp.group(tp, lambda t: t["vix_half"]))
    out += rp.table("Lot size", rp.group(tp, lambda t: t["lot_size"]))
    out += rp.table("lots_reason", rp.group(tp, lambda t: t["lots_reason"]))
    out += rp.table("max gear", rp.group(tp, lambda t: t["max_gear"]))
    return out


if __name__ == "__main__":
    sys.exit(main())
