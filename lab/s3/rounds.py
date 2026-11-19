# ruff: noqa: E501 (card / markdown lines)
"""S3 rounds R1-R12 (BANKNIFTY_STRATEGY_V3.md §13.3, §13.4): nested walk-forward over the 362 DESIGN days.

Per OOS window k (train blocks 1..k, test block k+1) the window's base config (carried from the previous round's
training choice of that window) and the round's candidates are fitted on the training blocks; the best training
net_base wins (the base wins ties); the winner's test block is the OOS result. Every fit is one ledger row.
Unfinished rounds write only to wip/; results/ gets a round's files when it is complete.
"""

from __future__ import annotations

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)

import datetime as dt
import json
import math
import pickle
import sys
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

from lab.s3 import costs
from lab.s3 import report as rp
from lab.s3 import run as R
from lab.s3.data import design_days
from lab.s3.engine import BASE, Mode, half_hour, opt_atr5, path_net, run_day
from lab.s3.features import SigParams, signals
from lab.s3.ledger import Ledger, s3_rows
from lab.s3.registry import FAMILY, FILTER_CHECKS, FIX, SEED, STATS, Cfg
from tools import preflight
from tools.nested_wf import blocks, windows
from tools.overfit import dsr, pbo, sharpe

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "wip/cache/runs"
CHAIN = ROOT / "wip/s3_chain.json"
WIP = ROOT / "wip/rounds"


def log(rnd: str, msg: str) -> None:
    WIP.mkdir(parents=True, exist_ok=True)
    with (WIP / f"{rnd}.log").open("a") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


def to_json(c: Cfg) -> dict[str, Any]:
    return {
        "variant": c.variant,
        "overrides": c.overrides,
        "flags": c.flags,
        "checks": list(c.checks),
        "slots_off": list(c.slots_off),
    }


def from_json(x: dict[str, Any]) -> Cfg:
    return Cfg(
        x["variant"],
        dict(x.get("overrides", {})),
        dict(x.get("flags", {})),
        checks=tuple(x.get("checks", ())),
        slots_off=tuple(x.get("slots_off", ())),
    )


def apply(
    base: Cfg,
    ov: dict[str, Any] | None = None,
    fl: dict[str, bool] | None = None,
    checks: tuple[str, ...] | None = None,
    slots: tuple[str, ...] | None = None,
) -> Cfg:
    return Cfg(
        base.variant,
        {**base.overrides, **(ov or {})},
        {**base.flags, **(fl or {})},
        checks=tuple(sorted(set(base.checks) | set(checks or ()))),
        slots_off=tuple(sorted(slots)) if slots is not None else base.slots_off,
    )


def describe(c: Cfg) -> str:
    parts = [f"{k}={v}" for k, v in sorted(c.overrides.items())] + [k for k, v in sorted(c.flags.items()) if v]
    parts += list(c.checks) + ([f"slots_off={','.join(c.slots_off)}"] if c.slots_off else [])
    return "T1-P" + (" + " + " + ".join(parts) if parts else "")


# ---------- one config over all DESIGN days (cached) ----------


@dataclass
class Ev:
    cfg: Cfg
    trades: list[dict[str, Any]]
    daily: np.ndarray[Any, Any]
    days: tuple[Any, ...] = field(default_factory=tuple)


def mid_rs(d: Any, p: Any) -> float:
    """Mid P&L before any cost: (exit level - entry level) x qty; entry level = the entry bar open (or the
    intrabar entry level), exit level = the exit trigger (open, SL level or the stale base)."""
    lvl = float(d.opt["o"][p.k, p.e]) if math.isnan(p.entry_level) else p.entry_level
    if p.book_lots:
        qb = p.book_lots * p.lot
        return (p.book_level - lvl) * qb + (p.exit_level - lvl) * (p.n * p.lot - qb)
    return (p.exit_level - lvl) * p.n * p.lot


def _light(d: Any, tr: dict[str, Any], sp: Any) -> dict[str, Any]:
    p = tr["path"]
    ns = path_net(d, p, sp)[0]
    rng_ = (d.opt["h"][p.k] - d.opt["l"][p.k]).tolist()
    return {
        "mid": mid_rs(d, p),
        "qty": p.n * p.lot,
        "atr5": opt_atr5(rng_, d.stale[p.k].tolist(), tr["t"]),
        "bars_held": p.exit_bar - p.e,
        "date": d.day.isoformat(),
        "t": tr["t"],
        "e": p.e,
        "side": str(d.cp[p.k]),
        "pattern": tr["event"].pattern,
        "net_base": float(tr["net_base"]),
        "net_stress": float(ns),
        "exit_reason": p.exit_reason,
        "max_gear": p.max_gear,
        "lots": p.n,
        "wf_window": R.wf_block(d.day),
        "vix_half": R.vix_half(d.day),
        "slot": half_hour(p.e),
    }


def code_hash() -> str:
    """Engine source version: a cached run is reused only by the same code (a fix invalidates it)."""
    import hashlib  # noqa: PLC0415

    h = hashlib.sha256()
    for name in ("data", "features", "engine", "checks", "p3", "costs", "registry"):
        h.update((ROOT / f"lab/s3/{name}.py").read_bytes())
    return h.hexdigest()[:10]


def evaluate(cfg: Cfg) -> Ev:
    """All 362 DESIGN days, light trade rows + daily net; cached in wip/cache/runs (gitignored)."""
    f = RUNS / f"{cfg.config_hash()}_{code_hash()}.pkl"
    if f.exists():
        out: Ev = pickle.loads(f.read_bytes())  # noqa: S301 (our own cache)
        return out
    sp_ = SigParams.of(cfg)
    stress = R.stress_px()
    days = design_days()
    trades: list[dict[str, Any]] = []
    daily = np.zeros(len(days))
    eq = peak = float(FIX["CAPITAL_RS"])
    for i, x in enumerate(days):
        d = R.day(x)
        dd = cfg["LOT_MODE"] != "L1" and eq < (1 - float(FIX["DD_CUT"])) * peak
        r = run_day(d, signals(d, sp_), cfg, run=Mode("BARCLOSE", BASE, dd), record=False)
        for tr in r.trades:
            trades.append(_light(d, tr, stress))
        daily[i] = sum(float(t["net_base"]) for t in r.trades)
        eq += daily[i]
        peak = max(peak, eq)
    ev = Ev(cfg, trades, daily, days)
    RUNS.mkdir(parents=True, exist_ok=True)
    f.write_bytes(pickle.dumps(ev))
    return ev


def evaluate_many(cfgs: list[Cfg], workers: int = 4) -> list[Ev]:
    todo = [c for c in cfgs if not (RUNS / f"{c.config_hash()}_{code_hash()}.pkl").exists()]
    if len(todo) > 1:
        with ProcessPoolExecutor(min(workers, len(todo))) as ex:
            list(ex.map(evaluate, todo))
    return [evaluate(c) for c in cfgs]


def train_score(ev: Ev, k: int) -> float:
    return float(sum(t["net_base"] for t in ev.trades if t["wf_window"] <= k))


def test_trades(ev: Ev, k: int) -> list[dict[str, Any]]:
    return [t for t in ev.trades if t["wf_window"] == k + 1]


def summ(trs: list[dict[str, Any]]) -> dict[str, Any]:
    nb = [t["net_base"] for t in trs]
    return {
        "trades": len(nb),
        "net_base": round(float(np.sum(nb)), 2) if nb else 0.0,
        "net_stress": round(float(np.sum([t["net_stress"] for t in trs])), 2) if nb else 0.0,
    }


def log_fit(
    led: Ledger,
    rnd: str,
    c: Cfg,
    k: int,
    role: str,
    trs: list[dict[str, Any]],
    grid_hashes: set[str],
    extra: dict[str, Any] | None = None,
) -> str:
    row = {
        "round": rnd,
        "config_hash": c.config_hash(),
        "series_id": costs.base().series_id,
        "variant": c.variant,
        "overrides": c.overrides,
        "flags": c.flags,
        "checks": list(c.checks),
        "slots_off": list(c.slots_off),
        "window": k,
        "role": role,
        "nested_choice": c.config_hash() not in grid_hashes,
        "code_commit": R.code_commit(),
        **(extra or {}),
    }
    return led.record(row, summ(trs))


# ---------- nested round ----------

Gen = Callable[[Cfg, int], list[Cfg]]


@dataclass
class Round:
    name: str
    gen: Gen  # (window base, k) -> candidate configs (the base is added first by the runner)
    stage2: Callable[[Cfg, int, list[tuple[Cfg, float]]], list[Cfg]] | None = None
    forward: bool = False  # R7 forward selection
    backward: bool = False  # R10 backward elimination


def chain_load() -> dict[int, Cfg]:
    if CHAIN.exists():
        raw = json.loads(CHAIN.read_text())
        return {int(k): from_json(v) for k, v in raw["bases"].items()}
    return {k: Cfg("T1-P") for k in (1, 2, 3, 4)}


def chain_save(bases: dict[int, Cfg], rnd: str, history: dict[str, Any]) -> None:
    old = json.loads(CHAIN.read_text()) if CHAIN.exists() else {"history": {}}
    old["history"][rnd] = history
    old["bases"] = {str(k): to_json(v) for k, v in bases.items()}
    CHAIN.write_text(json.dumps(old, indent=1, default=str))


def run_round(rnd: Round, plan_cfgs: list[Cfg]) -> dict[str, Any]:
    led = Ledger()
    grid_hashes = {c.config_hash() for c in plan_cfgs}
    bases = chain_load()
    chosen: dict[int, Cfg] = {}
    oos: list[dict[str, Any]] = []
    tried: dict[str, Cfg] = {}
    fits = 0
    hist: dict[str, Any] = {}
    for w in windows(design_days()):
        k = w.k
        base = bases[k]
        if rnd.forward:
            best, nf = _forward(led, rnd.name, base, k, grid_hashes, tried)
        elif rnd.backward:
            best, nf = _backward(led, rnd.name, base, k, grid_hashes, tried)
        else:
            cands = _dedupe([base, *rnd.gen(base, k)])
            evs = evaluate_many(cands)
            scored = []
            for c, ev in zip(cands, evs, strict=True):
                tried[c.config_hash()] = c
                log_fit(led, rnd.name, c, k, f"train:{k}", [t for t in ev.trades if t["wf_window"] <= k], grid_hashes)
                scored.append((c, train_score(ev, k)))
            nf = len(cands)
            if rnd.stage2 is not None:
                extra = _dedupe(
                    [
                        c
                        for c in rnd.stage2(base, k, scored)
                        if c.config_hash() not in {x.config_hash() for x, _ in scored}
                    ]
                )
                for c, ev in zip(extra, evaluate_many(extra), strict=True):
                    tried[c.config_hash()] = c
                    log_fit(
                        led, rnd.name, c, k, f"train:{k}", [t for t in ev.trades if t["wf_window"] <= k], grid_hashes
                    )
                    scored.append((c, train_score(ev, k)))
                    nf += 1
            best = max(scored, key=lambda x: x[1])[0] if scored else base
            if train_score(evaluate(base), k) >= train_score(evaluate(best), k):
                best = base
        fits += nf
        ev = evaluate(best)
        tt = test_trades(ev, k)
        log_fit(led, rnd.name, best, k, f"test:{k}", tt, grid_hashes)
        fits += 1
        chosen[k] = best
        for t in tt:
            t["config"] = describe(best)
        oos += tt
        hist[str(k)] = {
            "chosen": describe(best),
            "hash": best.config_hash(),
            "train": train_score(ev, k),
            "test": summ(tt),
        }
        log(rnd.name, f"window {k}: {describe(best)} train {train_score(ev, k):.0f} test {summ(tt)}")
    return {"chosen": chosen, "oos": oos, "tried": tried, "fits": fits, "history": hist, "bases_before": bases}


def _dedupe(cs: list[Cfg]) -> list[Cfg]:
    seen: set[str] = set()
    out = []
    for c in cs:
        h = c.config_hash()
        if h not in seen:
            seen.add(h)
            out.append(c)
    return out


def _forward(led: Ledger, rnd: str, base: Cfg, k: int, gh: set[str], tried: dict[str, Cfg]) -> tuple[Cfg, int]:
    """R7: forward selection of filter checks on the training blocks; max 2 per family, max 6 steps."""
    cur, cur_s, nf = base, train_score(evaluate(base), k), 0
    log_fit(led, rnd, base, k, f"train:{k}", [t for t in evaluate(base).trades if t["wf_window"] <= k], gh)
    nf += 1
    for _ in range(int(STATS["R7_MAX_STEPS"])):
        fam: dict[str, int] = {}
        for c in cur.checks:
            fam[FAMILY[c]] = fam.get(FAMILY[c], 0) + 1
        cands = [
            apply(cur, checks=(c,))
            for c in FILTER_CHECKS
            if c not in cur.checks and fam.get(FAMILY[c], 0) < int(STATS["R7_FAMILY_MAX"])
        ]
        if not cands:
            break
        evs = evaluate_many(cands)
        best, best_s = cur, cur_s
        for c, ev in zip(cands, evs, strict=True):
            tried[c.config_hash()] = c
            log_fit(led, rnd, c, k, f"train:{k}", [t for t in ev.trades if t["wf_window"] <= k], gh)
            nf += 1
            s = train_score(ev, k)
            if s > best_s:
                best, best_s = c, s
        if best is cur:
            break
        cur, cur_s = best, best_s
    return cur, nf


def _backward(led: Ledger, rnd: str, base: Cfg, k: int, gh: set[str], tried: dict[str, Cfg]) -> tuple[Cfg, int]:
    """R10: re-choose the R1-R9 changes per training window: drop one change at a time while training improves."""
    cur, cur_s, nf = base, train_score(evaluate(base), k), 1
    log_fit(led, rnd, base, k, f"train:{k}", [t for t in evaluate(base).trades if t["wf_window"] <= k], gh)
    while True:
        cands = []
        for key in cur.overrides:
            ov = dict(cur.overrides)
            ov.pop(key)
            cands.append(Cfg(cur.variant, ov, dict(cur.flags), checks=cur.checks, slots_off=cur.slots_off))
        for key, v in cur.flags.items():
            if v:
                fl = {**cur.flags, key: False}
                fl.pop(key)
                cands.append(Cfg(cur.variant, dict(cur.overrides), fl, checks=cur.checks, slots_off=cur.slots_off))
        for c in cur.checks:
            cands.append(
                Cfg(
                    cur.variant,
                    dict(cur.overrides),
                    dict(cur.flags),
                    checks=tuple(x for x in cur.checks if x != c),
                    slots_off=cur.slots_off,
                )
            )
        if cur.slots_off:
            cands.append(Cfg(cur.variant, dict(cur.overrides), dict(cur.flags), checks=cur.checks))
        if not cands:
            break
        best, best_s = cur, cur_s
        for c, ev in zip(cands, evaluate_many(cands), strict=True):
            tried[c.config_hash()] = c
            log_fit(led, rnd, c, k, f"train:{k}", [t for t in ev.trades if t["wf_window"] <= k], gh)
            nf += 1
            if train_score(ev, k) > best_s:
                best, best_s = c, train_score(ev, k)
        if best is cur:
            break
        cur, cur_s = best, best_s
    return cur, nf


# ---------- statistics after a round ----------


def n_eff() -> tuple[int, int, float]:
    """N_eff (§13.2): clusters of all S3 configs' daily nets (distance 1 - rho, average linkage, cut NEFF_CORR)."""
    latest: dict[str, Path] = {}
    for f in sorted(RUNS.glob("*.pkl"), key=lambda x: x.stat().st_mtime):
        latest[f.name.split("_")[0]] = f  # every S3 config once (its latest run)
    mats = []
    for f in latest.values():
        ev: Ev = pickle.loads(f.read_bytes())  # noqa: S301
        if ev.daily.std() > 0:
            mats.append(ev.daily)
    if len(mats) < 2:
        return len(mats), len(mats), 0.0
    m = np.vstack(mats)
    rho = np.corrcoef(m)
    dist = 1 - rho[np.triu_indices(len(mats), 1)]
    z = linkage(np.clip(dist, 0, None), "average")
    n = int(fcluster(z, float(STATS["NEFF_CORR"]), "distance").max())
    srs = [sharpe(x) for x in mats]
    return n, len(mats), float(np.var(srs))


def null_multi_seed(args: tuple[list[tuple[dict[str, Any], list[tuple[Any, int]]]], int]) -> float:
    segs, seed = args
    rng = np.random.default_rng([SEED, seed])
    tot = Decimal(0)
    for cj, plan in segs:
        cfg = from_json(cj)
        for x, need in plan:
            r = R.null_random_day(cfg, R.day(x), need, rng)
            tot += sum((t["net_base"] for t in r.trades), Decimal(0))
    return float(tot)


def null_nested(res: dict[str, Any], seeds: int | None = None) -> dict[str, Any]:
    n_seeds = int(seeds if seeds is not None else STATS["NULL_SEEDS"])
    segs = []
    for k, c in res["chosen"].items():
        per: dict[str, int] = {}
        for t in res["oos"]:
            if t["wf_window"] == k + 1 and t["pattern"] != "REENTRY":
                per[t["date"]] = per.get(t["date"], 0) + 1
        segs.append((to_json(c), [(dt.date.fromisoformat(x), n) for x, n in sorted(per.items())]))
    with ProcessPoolExecutor(4) as ex:
        draws = list(ex.map(null_multi_seed, [(segs, s) for s in range(n_seeds)], chunksize=max(1, n_seeds // 32)))
    c = float(sum(t["net_base"] for t in res["oos"]))
    kk = sum(1 for v in draws if v >= c)
    return {"candidate": c, "p": (kk + 1) / (n_seeds + 1), "median": float(np.median(draws)), "seeds": n_seeds}


def full_rows(res: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    b = blocks(design_days())
    for k, c in res["chosen"].items():
        r = R.run_days(c, b[k], record=False, full=True)
        for t in r.trades:
            t["config"] = describe(c)
        rows += r.trades
    return rows


def finish(rnd: str, res: dict[str, Any], note: tuple[str, str]) -> str:
    """Stats, card, files; returns the card text."""
    oos_days = R.oos()
    nr = null_nested(res)
    g = R.gates(res["oos"], oos_days, nr["p"])
    ne, nraw, srv = n_eff()
    v = R.daily(res["oos"], oos_days)
    d_eff, d_raw = dsr(v, max(ne, 1), srv), dsr(v, max(nraw, 1), srv)
    cols = list(res["tried"].values())
    m = np.column_stack([evaluate(c).daily for c in cols]) if len(cols) >= 2 else None
    p_bo = float(pbo(m, int(STATS["PBO_BLOCKS"]))[0]) if m is not None else float("nan")
    rows = full_rows(res)
    if abs(sum(t["net_base"] for t in rows) - g["net_base"]) > 0.05:
        raise AssertionError(f"{rnd}: full re-run differs from the nested result")
    intr = {"PATH": sum(t["net_path"] for t in rows), "WORST": sum(t["net_worst"] for t in rows)}
    sens = any(x < 0 for x in intr.values())
    ce = sum(t["net_base"] for t in rows if t["side"] == "CE")
    pe = sum(t["net_base"] for t in rows if t["side"] == "PE")
    nce = sum(1 for t in rows if t["side"] == "CE")
    w = g["windows"]
    picks = "; ".join(f"w{k}: {h['chosen']}" for k, h in res["history"].items())
    total_trials = len({r["config_hash"] for r in s3_rows()})
    card = [
        f"## {rnd} CARD · [BACKTEST·OOS] PRE-TAX · nested, 290 OOS din · series BASE",
        f"1. Configs {len(cols)} (is round mein), fits {res['fits']}; S3 kul distinct configs {total_trials}. Chune gaye (training se): {picks}.",
        f"2. Net base {rp.rs(g['net_base'])} ({rp.rs(g['per_trade'])}/trade) · stress {rp.rs(g['net_stress'])} · {g['trades']} trade ({g['trades_per_day']:.2f}/din).",
        "3. OOS windows: "
        + " · ".join(f"{rp.rs(s)} ({n})" for s, n in w.values())
        + f" → positive {sum(1 for s, n in w.values() if s > 0)}/4.",
        f"4. Best-5 hatakar {rp.rs(g['best5_removed'])} · E12 {rp.rs(g['e12'])} vs DD95 {rp.rs(g['dd95'])} · bootstrap p {g['boot_p']:.3f}.",
        f"5. NULL-RANDOM p {nr['p']:.3f} (2,000 seeds) · PBO {p_bo:.2f} · DSR(N_eff {ne}) {d_eff:.3f}, DSR(raw N {nraw}) {d_raw:.3f}.",
        f"6. CE {rp.rs(ce)} ({nce}) · PE {rp.rs(pe)} ({len(rows) - nce}) · VIX low {rp.rs(g['vix_halves']['LOW'])}, high {rp.rs(g['vix_halves']['HIGH'])}.",
        f"7. Intrabar: {'**INTRABAR-SENSITIVE**' if sens else 'label nahi'} (PATH {rp.rs(intr['PATH'])}, WORST {rp.rs(intr['WORST'])}). §14.1 gates pass {sum(g['gates'].values())}/9 → **{'PASS' if g['all_pass'] else 'FAIL'}**.",
        f"8. Seekha: {note[0]}",
        f"9. Aage: {note[1]}",
    ]
    WIP.mkdir(parents=True, exist_ok=True)
    rp.write_csv(WIP / f"s3_{rnd.lower()}_trades.csv", rows, ["config", *rp.TRADE_COLS])
    summary = {
        "round": rnd,
        "gates": g,
        "null": nr,
        "pbo": p_bo,
        "n_eff": ne,
        "n_raw": nraw,
        "dsr_eff": d_eff,
        "dsr_raw": d_raw,
        "intrabar": intr,
        "history": res["history"],
        "fits": res["fits"],
        "configs": len(cols),
    }
    (WIP / f"s3_{rnd.lower()}_summary.json").write_text(json.dumps(summary, indent=1, default=str))
    return "\n".join(card)


def preflight_or_die(rnd: str) -> list[Cfg]:
    try:
        preflight.check(rnd, costs.base().series_id)
    except preflight.PreflightError as e:
        print(f"PREFLIGHT ABORT: {e}")
        sys.exit(1)
    return preflight.grid((ROOT / "PLAN.md").read_text(encoding="utf-8"), rnd)


def commit_round(rnd: str, res: dict[str, Any], card: str) -> None:
    import shutil  # noqa: PLC0415

    for f in (f"s3_{rnd.lower()}_trades.csv", f"s3_{rnd.lower()}_summary.json"):
        shutil.copy(WIP / f, ROOT / "results" / f)
    with (ROOT / "results/s3_rounds.md").open("a", encoding="utf-8") as fh:
        fh.write("\n" + card + "\n")
    chain_save(res["chosen"], rnd, res["history"])
    log(rnd, "complete")
