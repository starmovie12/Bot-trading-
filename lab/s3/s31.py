# ruff: noqa: E501 (card / markdown lines)
"""S3.1 (owner order 7; BANKNIFTY_STRATEGY_V3.md §V3.1): D1 signal test -> R13 exit X-T -> R14 chaal gate (K28)
-> R15 strike -> FINAL (§14.1). Nested like S3 (train blocks 1..k, test block k+1); every fit is one ledger row.
`python -m lab.s3.s31 D1|R13|R14|R15|FINAL`."""

from __future__ import annotations

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)

import datetime as dt
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from lab.s3 import report as rp
from lab.s3 import run as R
from lab.s3.data import design_days
from lab.s3.ledger import Ledger
from lab.s3.registry import SEED, STATS, Cfg
from lab.s3.rounds import (
    apply,
    describe,
    evaluate,
    evaluate_many,
    from_json,
    log,
    log_fit,
    mid_rs,
    n_eff,
    preflight_or_die,
    to_json,
    train_score,
)
from tools.nested_wf import windows
from tools.overfit import dsr, pbo

ROOT = Path(__file__).resolve().parents[2]
CHAIN = ROOT / "wip/s31_chain.json"
OUT = ROOT / "results/s3_s31.md"
T1P = Cfg("T1-P")


def xt0(c: Cfg, h: int = 10) -> Cfg:
    return apply(c, {"EXIT_MODE": "X-T0", "XT_H": h})


def oos_of(c: Cfg) -> list[dict[str, Any]]:
    return [t for t in evaluate(c).trades if t["wf_window"] >= 2]


def per_window(trs: list[dict[str, Any]]) -> dict[int, tuple[float, float, int]]:
    out = {}
    for w in (2, 3, 4, 5):
        x = [t for t in trs if t["wf_window"] == w]
        out[w] = (sum(t["mid"] for t in x), sum(t["net_base"] for t in x), len(x))
    return out


# ---------- NULL-RANDOM with mid ----------


def _null_seed(args: tuple[list[tuple[dict[str, Any], list[tuple[str, int]]]], int]) -> tuple[float, float, int]:
    segs, seed = args
    rng = np.random.default_rng([SEED, seed])
    net = mid = 0.0
    n = 0
    for cj, plan in segs:
        cfg = from_json(cj)
        for x, need in plan:
            d = R.day(dt.date.fromisoformat(x))
            r = R.null_random_day(cfg, d, need, rng)
            for t in r.trades:
                net += float(t["net_base"])
                mid += mid_rs(d, t["path"])
                n += 1
    return net, mid, n


def null(chosen: dict[int, Cfg], trs: list[dict[str, Any]], seeds: int, exit_cfg: Any = None) -> dict[str, Any]:
    """NULL-RANDOM over the candidate's OOS days, same entry count per day; exit_cfg(c) swaps the exit (FIX-11)."""
    segs = []
    for k, c in chosen.items():
        per: dict[str, int] = {}
        for t in trs:
            if t["wf_window"] == k + 1 and t["pattern"] != "REENTRY":
                per[t["date"]] = per.get(t["date"], 0) + 1
        cc = exit_cfg(c) if exit_cfg else c
        segs.append((to_json(cc), sorted(per.items())))
    with ProcessPoolExecutor(4) as ex:
        draws = list(ex.map(_null_seed, [(segs, s) for s in range(seeds)], chunksize=max(1, seeds // 32)))
    return {"draws": draws, "seeds": seeds}


def p_of(cand: float, draws: list[float]) -> float:
    return (sum(1 for v in draws if v >= cand) + 1) / (len(draws) + 1)


def p_pt(cand: list[dict[str, Any]], draws: list[tuple[float, float, int]], col: str) -> float:
    """FIX-13: p on the PER-TRADE mean (a draw with a different trade count no longer carries a different total
    cost). col: net_base (draw[0]) or mid (draw[1]); a draw with no trade has mean 0."""
    c = float(np.mean([t[col] for t in cand])) if cand else 0.0
    i = 0 if col == "net_base" else 1
    return p_of(c, [d[i] / d[2] if d[2] else 0.0 for d in draws])


def avg_n(draws: list[tuple[float, float, int]]) -> float:
    return float(np.mean([d[2] for d in draws])) if draws else 0.0


def windows_na(trs: list[dict[str, Any]], col: str = "mid") -> dict[int, float | None]:
    """Owner order 8 1b: per OOS window the sum of col, or None (NA) when the window has < WINDOW_MIN_TRADES."""
    out: dict[int, float | None] = {}
    for w in (2, 3, 4, 5):
        x = [t[col] for t in trs if t["wf_window"] == w]
        out[w] = float(sum(x)) if len(x) >= int(STATS["WINDOW_MIN_TRADES"]) else None
    return out


# ---------- D1 signal test ----------


def d1() -> int:
    grid = preflight_or_die("D1")
    cfg = grid[0]
    led = Ledger()
    gh = {c.config_hash() for c in grid}
    trs = oos_of(cfg)
    for w in (1, 2, 3, 4):
        log_fit(led, "D1", cfg, w, f"test:{w}", [t for t in trs if t["wf_window"] == w + 1], gh)
    chosen = {k: cfg for k in (1, 2, 3, 4)}
    nn = null(chosen, trs, int(STATS["NULL_SEEDS"]))
    net_c, mid_c = sum(t["net_base"] for t in trs), sum(t["mid"] for t in trs)
    p_net = p_of(net_c, [d[0] for d in nn["draws"]])
    p_mid = p_of(mid_c, [d[1] for d in nn["draws"]])
    log("D1", f"null p net {p_net:.4f} mid {p_mid:.4f}")
    curve = []
    for h in (3, 5, 10, 15, 20, 30):
        ch = xt0(T1P, h)
        th = oos_of(ch)
        nh = null({k: ch for k in (1, 2, 3, 4)}, th, 500)
        rn = [d[2] for d in nh["draws"]]
        curve.append(
            {
                "H": h,
                "trades": len(th),
                "mid_tr": float(np.mean([t["mid"] for t in th])),
                "net_tr": float(np.mean([t["net_base"] for t in th])),
                "rnd_mid_tr": float(np.sum([d[1] for d in nh["draws"]]) / max(1, np.sum(rn))),
                "rnd_net_tr": float(np.sum([d[0] for d in nh["draws"]]) / max(1, np.sum(rn))),
                "p_mid": p_of(sum(t["mid"] for t in th), [d[1] for d in nh["draws"]]),
            }
        )
        log("D1", f"curve H {h}: {curve[-1]}")
    terc = tercile(cfg)
    pw = per_window(trs)
    pos = sum(1 for m, _, _ in pw.values() if m > 0)
    cost_tr = float(np.mean([t["mid"] - t["net_base"] for t in trs]))
    real = p_net <= float(STATS["NULL_P_MAX"]) and pos >= 3
    ne, nraw, _ = n_eff()
    card = [
        "## D1 · SIGNAL TEST CARD · [BACKTEST·OOS] PRE-TAX · T1-P entries + X-T0 (koi SL nahi, exit open e+10) · 290 OOS din",
        f"1. Configs 1 (S3.1 naye: 1/14) · N_eff {ne} (raw {nraw}) · {len(trs)} trade ({len(trs) / 290:.2f}/din).",
        f"2. Net base {rp.rs(net_c)} · mid (kharche se pehle) {rp.rs(mid_c)} · stress {rp.rs(sum(t['net_stress'] for t in trs))}.",
        "3. Windows (mid / net / trades): "
        + " · ".join(f"{rp.rs(m)} / {rp.rs(n)} ({c})" for m, n, c in pw.values())
        + f" → mid > 0 in {pos}/4.",
        f"4. Mid edge/trade {rp.rs(mid_c / max(1, len(trs)))} vs kharcha/trade {rp.rs(cost_tr)}.",
        f"5. NULL-RANDOM (X-T0 = apna exit, 2,000 seeds): p(net) {p_net:.3f} · p(mid) {p_mid:.3f}; gear-engine wala NULL (R0) p 0.406.",
        f"6. Faisla: **{'SIGNAL REAL → R13' if real else 'SIGNAL NOT PROVEN → S3 STOP (FINAL_S3.md)'}**.",
    ]
    tab = [
        "",
        "**Edge curve (T1-P vs random, X-T0 exit e+H; random = 500 seeds; ₹/trade)**",
        "",
        "| H | trades | T1-P mid | T1-P net | random mid | random net | p(mid) |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    tab += [
        f"| {c['H']} | {c['trades']} | {rp.rs(c['mid_tr'])} | {rp.rs(c['net_tr'])} | {rp.rs(c['rnd_mid_tr'])} | {rp.rs(c['rnd_net_tr'])} | {c['p_mid']:.3f} |"
        for c in curve
    ]
    tab += [
        "",
        "**Mid edge by entry OptATR5 tercile (cuts from each window's training blocks)**",
        "",
        "| tercile | trades | mid/trade | net/trade |",
        "|---|---:|---:|---:|",
    ]
    tab += [f"| {k} | {n} | {rp.rs(m)} | {rp.rs(x)} |" for k, (n, m, x) in terc.items()]
    text = "\n".join(card + tab) + "\n"
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write("\n" + text)
    summ = {
        "p_net": p_net,
        "p_mid": p_mid,
        "mid": mid_c,
        "net": net_c,
        "windows": pw,
        "curve": curve,
        "tercile": terc,
        "real": real,
        "cost_tr": cost_tr,
        "n_eff": ne,
    }
    (ROOT / "results/s3_d1_summary.json").write_text(json.dumps(summ, indent=1, default=str))
    print(text)
    return 0


def d1_recount() -> int:
    """Owner order 8 FIX-13: the D1 NULL on per-trade means. The D1 draws were not stored, so they are rebuilt
    from the same seeds (deterministic); the old total-based p must come out exactly as recorded."""
    old = json.loads((ROOT / "results/s3_d1_summary.json").read_text())
    cfg = xt0(T1P, 10)
    trs = oos_of(cfg)
    if len(trs) != 525 or abs(sum(t["net_base"] for t in trs) - old["net"]) > 0.01:
        raise AssertionError("D1 trades do not reproduce")
    nn = null(dict.fromkeys((1, 2, 3, 4), cfg), trs, int(STATS["NULL_SEEDS"]))
    d = nn["draws"]
    tot_net = p_of(sum(t["net_base"] for t in trs), [x[0] for x in d])
    tot_mid = p_of(sum(t["mid"] for t in trs), [x[1] for x in d])
    if abs(tot_net - old["p_net"]) > 1e-12 or abs(tot_mid - old["p_mid"]) > 1e-12:
        raise AssertionError(f"draws differ from D1: {tot_net} {tot_mid}")
    (ROOT / "wip/s31_d1_draws.json").write_text(json.dumps(d))
    pn, pm = p_pt(trs, d, "net_base"), p_pt(trs, d, "mid")
    wn = windows_na(trs)
    pos = sum(1 for v in wn.values() if v is not None and v > 0)
    lines = [
        "## D1 RECOUNT (owner order 8, FIX-13: NULL p per-trade; same 2,000 seeds, rebuilt deterministically)",
        f"1. Same draws check: total-based p(net) {tot_net:.4f} / p(mid) {tot_mid:.4f} = D1 as recorded.",
        f"2. Per-trade: T1-P net {rp.rs(float(np.mean([t['net_base'] for t in trs])))} / mid {rp.rs(float(np.mean([t['mid'] for t in trs])))} per trade; random avg n {avg_n(d):.0f} vs 525.",
        f"3. **Per-trade p(net) {pn:.4f} · p(mid) {pm:.4f}** (total-based was {tot_net:.3f} / {tot_mid:.3f}).",
        "4. Windows (mid, NA if < 15 trades): "
        + " · ".join("NA" if v is None else rp.rs(v) for v in wn.values())
        + f" → mid > 0 in {pos} windows.",
        f"5. D1 rule (p <= 0.05 and mid > 0 in >= 3/4 windows): {'met' if pn <= 0.05 and pos >= 3 else 'not met'} (per-trade p; D-60 stays the record of the run as committed).",
    ]
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write("\n" + "\n".join(lines) + "\n")
    old |= {"pt_p_net": pn, "pt_p_mid": pm, "rand_n": avg_n(d)}
    (ROOT / "results/s3_d1_summary.json").write_text(json.dumps(old, indent=1, default=str))
    print("\n".join(lines))
    return 0


def tercile(cfg: Cfg) -> dict[str, tuple[int, float, float]]:
    ev = evaluate(cfg)
    out: dict[str, list[dict[str, Any]]] = {"LOW": [], "MID": [], "HIGH": []}
    for w in windows(design_days()):
        tr = [t["atr5"] for t in ev.trades if t["wf_window"] <= w.k and t["atr5"] == t["atr5"]]
        lo, hi = np.percentile(tr, [100 / 3, 200 / 3])
        for t in ev.trades:
            if t["wf_window"] == w.k + 1:
                out["LOW" if t["atr5"] <= lo else "MID" if t["atr5"] <= hi else "HIGH"].append(t)
    return {
        k: (
            len(v),
            float(np.mean([t["mid"] for t in v])) if v else 0.0,
            float(np.mean([t["net_base"] for t in v])) if v else 0.0,
        )
        for k, v in out.items()
    }


# ---------- nested rounds R13-R15 ----------


def r13_grid(base: Cfg) -> list[Cfg]:
    return [
        apply(base, {"EXIT_MODE": "X-T", "XT_H": h, "SL_K": k, "K03_SWITCH": sw})
        for sw in ("ON", "OFF")
        for h in (10, 15)
        for k in (2.0, 3.0)
    ]


def r14_grid(base: Cfg) -> list[Cfg]:
    return [apply(base, {"DEAD_MULT": m}, {"FLAG_K28": True}) for m in (2.0, 3.0)]


def r15_grid(base: Cfg) -> list[Cfg]:
    return [apply(base, {"STRIKE_MODE": m}) for m in ("PREMIUM_BAND", "DELTA_BAND")]


GRIDS = {"R13": (r13_grid, False), "R14": (r14_grid, True), "R15": (r15_grid, True)}


def nested_round(name: str) -> dict[str, Any]:
    plan = preflight_or_die(name)
    gen, keep_base = GRIDS[name]
    gh = {c.config_hash() for c in plan}
    led = Ledger()
    bases = (
        {int(k): from_json(v) for k, v in json.loads(CHAIN.read_text())["bases"].items()}
        if CHAIN.exists()
        else dict.fromkeys((1, 2, 3, 4), T1P)
    )
    chosen: dict[int, Cfg] = {}
    oos: list[dict[str, Any]] = []
    tried: dict[str, Cfg] = {}
    fits = 0
    for w in windows(design_days()):
        k = w.k
        cands = ([bases[k]] if keep_base else []) + gen(bases[k])
        seen: dict[str, Cfg] = {}
        for c in cands:
            seen.setdefault(c.config_hash(), c)
        cands = list(seen.values())
        evs = evaluate_many(cands)
        best, best_s = cands[0], -np.inf
        for c, ev in zip(cands, evs, strict=True):
            tried[c.config_hash()] = c
            log_fit(led, name, c, k, f"train:{k}", [t for t in ev.trades if t["wf_window"] <= k], gh)
            fits += 1
            if train_score(ev, k) > best_s:
                best, best_s = c, train_score(ev, k)
        tt = [t for t in evaluate(best).trades if t["wf_window"] == k + 1]
        log_fit(led, name, best, k, f"test:{k}", tt, gh)
        fits += 1
        chosen[k] = best
        oos += tt
        log(
            name,
            f"window {k}: {describe(best)} train {best_s:.0f} test {len(tt)} tr {sum(t['net_base'] for t in tt):.0f}",
        )
    return {"chosen": chosen, "oos": oos, "tried": tried, "fits": fits}


def card(name: str, res: dict[str, Any], final: bool = False) -> tuple[str, dict[str, Any]]:
    trs, chosen = res["oos"], res["chosen"]
    days = R.oos()
    own = null(chosen, trs, int(STATS["NULL_SEEDS"]))
    x0 = null(chosen, trs, int(STATS["NULL_SEEDS"]), lambda c: apply(c, {"EXIT_MODE": "X-T0", "XT_H": 10}))
    p_own, p_x0 = p_pt(trs, own["draws"], "net_base"), p_pt(trs, x0["draws"], "net_base")
    pm_own, pm_x0 = p_pt(trs, own["draws"], "mid"), p_pt(trs, x0["draws"], "mid")
    g = R.gates(trs, days, p_own)  # gate 9 on the per-trade p (FIX-13)
    ne, nraw, srv = n_eff()
    v = R.daily(trs, days)
    d_eff = dsr(v, max(ne, 1), srv)
    cols = list(res["tried"].values())
    p_bo = (
        float(pbo(np.column_stack([evaluate(c).daily for c in cols]), int(STATS["PBO_BLOCKS"]))[0])
        if len(cols) >= 2
        else float("nan")
    )
    mid_tr = float(np.mean([t["mid"] for t in trs])) if trs else 0.0
    cost_tr = float(np.mean([t["mid"] - t["net_base"] for t in trs])) if trs else 0.0
    pw = per_window(trs)
    picks = "; ".join(f"w{k}: {describe(c)}" for k, c in chosen.items())
    verdict = (
        ("PASS → HOLDOUT_REUSED" if g["all_pass"] else "FAIL → S3 STOP (FINAL_S3.md)")
        if final
        else (
            "KILL → S3 STOP"
            if name == "R13" and mid_tr <= 0
            else f"aage {'R14' if name == 'R13' else 'R15' if name == 'R14' else 'FINAL'}"
        )
    )
    lines = [
        f"## {name} CARD · [BACKTEST·OOS] PRE-TAX · nested, 290 OOS din",
        f"1. Configs {len(cols)}, fits {res['fits']} · N_eff {ne} (raw {nraw}) · PBO {p_bo:.2f} · DSR(N_eff) {d_eff:.3f} · chune: {picks}.",
        f"2. Net base {rp.rs(g['net_base'])} ({rp.rs(g['per_trade'])}/trade, {g['trades']} trade) · stress {rp.rs(g['net_stress'])}.",
        "3. Windows (mid / net / trades): "
        + " · ".join(f"{rp.rs(m)} / {rp.rs(n)} ({c})" for m, n, c in pw.values())
        + f" · best-5 hatakar {rp.rs(g['best5_removed'])} · E12 {rp.rs(g['e12'])} vs DD95 {rp.rs(g['dd95'])}.",
        f"4. Mid edge/trade {rp.rs(mid_tr)} vs kharcha/trade {rp.rs(cost_tr)}.",
        f"5. NULL-RANDOM per-trade p (net / mid): apna exit {p_own:.3f} / {pm_own:.3f} · X-T0 {p_x0:.3f} / {pm_x0:.3f} · random avg n {avg_n(own['draws']):.0f} vs {len(trs)} · §14.1 gates {sum(g['gates'].values())}/9.",
        f"6. Faisla: **{verdict}**.",
    ]
    summ = {
        "gates": g,
        "p_own": p_own,
        "p_x0": p_x0,
        "n_eff": ne,
        "pbo": p_bo,
        "dsr": d_eff,
        "mid_tr": mid_tr,
        "cost_tr": cost_tr,
        "chosen": {k: to_json(c) for k, c in chosen.items()},
        "fits": res["fits"],
    }
    return "\n".join(lines), summ


def round_main(name: str) -> int:
    res = nested_round(name)
    text, summ = card(name, res, final=False)
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write("\n" + text + "\n")
    (ROOT / f"results/s3_{name.lower()}_summary.json").write_text(json.dumps(summ, indent=1, default=str))
    CHAIN.write_text(
        json.dumps({"bases": {str(k): to_json(c) for k, c in res["chosen"].items()}, "after": name}, indent=1)
    )
    rows = []
    from tools.nested_wf import blocks  # noqa: PLC0415

    b = blocks(design_days())
    for k, c in res["chosen"].items():
        rr = R.run_days(c, b[k], record=False, full=True)
        for t in rr.trades:
            t["config"] = describe(c)
        rows += rr.trades
    rp.write_csv(ROOT / f"results/s3_{name.lower()}_trades.csv", rows, ["config", *rp.TRADE_COLS])
    print(text)
    return 0


if __name__ == "__main__":
    arg = sys.argv[1]
    sys.exit(d1() if arg == "D1" else d1_recount() if arg == "D1R" else round_main(arg))
