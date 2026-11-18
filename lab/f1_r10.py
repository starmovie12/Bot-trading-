"""P3R v2 round 10 (PLAN.md §PREREG-R10): F1 defined-risk volatility premium (iron fly / condor). RESEARCH ONLY.

  python -m lab.f1_r10 -> trials.jsonl (24 lines), results/r10_board.md, data/lab/r10_rows.json. DESIGN only.
Long wings are bought first (an execution rule; the backtest fills all 4 legs at the same minute's opens); never naked.
"""

import datetime as dt
import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from lab.run_round import VIX_MEDIAN
from tools import bn_economics as be
from tools import engine_of_record as eor
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
ROWS = 61
SHAPES = {"IF300": (0, 300), "IF500": (0, 500), "IC": (200, 500)}  # (short distance, long distance) from ATM


def legs(atm: float, shape: str) -> list[tuple[float, str, int]]:
    s, w = SHAPES[shape]
    return [(atm + w, "CE", 1), (atm - w, "PE", 1), (atm + s, "CE", -1), (atm - s, "PE", -1)]  # wings first


def outcome(d: eor.Day, t: int, shape: str, ex: str, s0: float) -> dict[str, float] | None:
    atm = round(s0 / 100) * 100
    ls = legs(atm, shape)
    arrs = [d.opts.get((float(k), typ)) for k, typ, _ in ls]
    if any(a is None for a in arrs):
        return None
    a4 = [a for a in arrs if a is not None]
    e = next((m for m in range(t, min(t + 3, eor.FORCE_FLAT)) if all(a["live"][m] and a["o"][m] > 0 for a in a4)), -1)
    if e < 0:
        return None
    ent = [a["o"][e] for a in a4]
    credit = sum(-sg * p for (_, _, sg), p in zip(ls, ent, strict=True))  # shorts add, longs subtract
    if credit <= 0:
        return None
    x, out, why = eor.FORCE_FLAT, math.nan, "force_flat"
    for m in range(e, eor.FORCE_FLAT + 1):
        if ex == "E2":
            worst = [a["h"][m] if sg < 0 else a["l"][m] for (_, _, sg), a in zip(ls, a4, strict=True)]
            if all(not math.isnan(v) for v in worst):
                debit = sum(-sg * v for (_, _, sg), v in zip(ls, worst, strict=True))
                if debit - credit >= credit:
                    x, out, why = m, debit, "stop"
                    break
    if why == "force_flat":
        closes = [next((a["c"][k] for k in range(x, e - 1, -1) if not math.isnan(a["c"][k])), math.nan) for a in a4]
        if any(math.isnan(v) for v in closes):
            return None
        out = sum(-sg * v for (_, _, sg), v in zip(ls, closes, strict=True))
        exits = closes
    else:
        exits = [a["h"][x] if sg < 0 else a["l"][x] for (_, _, sg), a in zip(ls, a4, strict=True)]
    c = be.consts()
    charges = sum(
        float(be.round_trip(Decimal(str(p_in)), Decimal(str(p_out)), d.lot, d.day, c, long=sg > 0))
        for (_, _, sg), p_in, p_out in zip(ls, ent, exits, strict=True)
    )
    fill = float(eor.StressedCosts().fill_stressed(4, d.lot, (e, x), d.expiry == d.day, False))
    gross = (credit - out) * d.lot
    s, w = SHAPES[shape]
    return {
        "entry_m": e,
        "exit_m": x,
        "credit": credit,
        "gross": gross,
        "charges": charges,
        "fill": fill,
        "net": gross - 1.5 * charges - fill,
        "max_loss": (w - s - credit) * d.lot + 1.5 * charges + fill,
        "stop": float(why == "stop"),
    }


def boot_p(day_net: np.ndarray, day_cnt: np.ndarray) -> float:
    rng = np.random.default_rng(le.SEED)
    n = len(day_net)
    starts = rng.integers(0, n - 4, size=(10_000, n // 5 + 1))
    idx = (starts[:, :, None] + np.arange(5)).reshape(10_000, -1)[:, :n]
    cnt = day_cnt[idx].sum(axis=1)
    mean = np.where(cnt > 0, day_net[idx].sum(axis=1) / np.maximum(cnt, 1), 0.0)
    return float(np.mean(mean <= 0))


def main() -> int:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    m = np.load(ROOT / "data/lab/matrix.npz")
    f = {k[2:]: m[k] for k in m.files if k.startswith("F_")}
    grid = [(s, t, ex) for s in SHAPES for t in (45, 135) for ex in ("E1", "E2")]
    res: dict[tuple[str, int, str], list[tuple[int, dict[str, float]]]] = {g: [] for g in grid}
    for i, ds in enumerate(days):
        d = eor.load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(ds), lots)
        for s, t, ex in grid:
            row = i * ROWS + (t - 15) // 5
            o = outcome(d, t, s, ex, float(f["spot"][row]))
            if o is not None:
                res[(s, t, ex)].append((i, o))
    rows: list[dict[str, Any]] = []
    for (s, t, ex), lst in res.items():
        for filt in ("none", "trendskip"):
            keep = [
                (i, o)
                for i, o in lst
                if filt == "none"
                or not (
                    f["eff"][i * ROWS + (t - 15) // 5] >= 0.35 or abs(f["ret_open"][i * ROWS + (t - 15) // 5]) >= 0.006
                )
            ]
            rows.append(evaluate(s, t, ex, filt, keep, f, len(days)))
    by = {(r["shape"], r["t"], r["exit"], r["filter"]): r for r in rows}
    for r in rows:
        nb = [by[(s2, r["t"], r["exit"], r["filter"])] for s2 in SHAPES if s2 != r["shape"]]
        nb += [by[(r["shape"], t2, r["exit"], r["filter"])] for t2 in (45, 135) if t2 != r["t"]]
        r["gates"]["neighbours"] = all(x["net_mean"] > 0 for x in nb)
    for r in rows:
        le.append_trial(
            {
                "id": r["id"],
                "cycle": 1,
                "idea": f"F1 {r['shape']} at t{r['t']}, {r['exit']}, {r['filter']} (research only)",
                "params": {k: r[k] for k in ("shape", "t", "exit", "filter")},
                "design_net_stressed": r["net_total"],
                "p_screen": r["p"],
                "source": "P3R v2 R10 EXPLORE (defined-risk selling, research only)",
            }
        )
    (ROOT / "data/lab/r10_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    rows.sort(key=lambda r: -r["net_mean"])
    out = [
        "# R10 BOARD (P3R v2, F1 iron fly / condor, RESEARCH ONLY; DESIGN 362 days; stressed ₹ per trade, PRE-TAX,",
        "[BACKTEST·in-sample]; p = one-sided day-block bootstrap of the mean <= 0)",
        "",
        "| id | trades | per day | credit pts | net / trade | folds + | high / low VIX | w/o best 5 | stops | p | "
        "max loss ₹ | failed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        bad = [k for k, v in r["gates"].items() if not v] or ["none (PASSES the EXPLORE screen)"]
        out.append(
            f"| {r['id']} | {r['trades']} | {r['per_day']} | {r['credit_med']} | {r['net_mean']} | "
            f"{r['folds_positive']}/4 | {r['net_mean_high_vix']} / {r['net_mean_low_vix']} | "
            f"{r['net_mean_wo_best5']} | {r['stops']} | {r['p']} | {r['max_loss_rs']:,.0f} | {', '.join(bad)} |"
        )
    (ROOT / "results/r10_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:12]))
    return 0


def evaluate(
    s: str, t: int, ex: str, filt: str, keep: list[tuple[int, dict[str, float]]], f: dict[str, np.ndarray], n_days: int
) -> dict[str, Any]:
    k = len(keep)
    day = np.array([i for i, _ in keep], dtype=int)

    def col(key: str) -> np.ndarray:
        return np.array([o[key] for _, o in keep], dtype=float)

    row = day * ROWS + (t - 15) // 5
    gross, ch, fill, net, ml = col("gross"), col("charges"), col("fill"), col("net"), col("max_loss")
    tr = le.Trades(
        row,
        day,
        np.full(k, t),
        np.zeros(k, int),
        col("entry_m").astype(int),
        col("exit_m").astype(int),
        gross,
        ch,
        fill,
        net,
        gross - ch,
        ml,
        np.zeros(k),
        f["vix"][row] if k else np.zeros(0),
    )
    taken = np.arange(k)
    met = le.metrics(tr, taken, n_days, VIX_MEDIAN)
    fold = le.folds(tr, taken, n_days)
    day_net, day_cnt = np.zeros(n_days), np.zeros(n_days)
    np.add.at(day_net, day, net)
    np.add.at(day_cnt, day, 1)
    p = boot_p(day_net, day_cnt) if k else 1.0
    hi, lo = met["n_high_vix"], met["n_low_vix"]
    gates = {
        "net": met["net_mean"] > 0,
        "folds": fold["pass"],
        "vix_halves": hi >= 15
        and lo >= 15
        and (met["net_mean_high_vix"] or 0) > 0
        and (met["net_mean_low_vix"] or 0) > 0,
        "st11": met["per_day"] >= 0.5,
        "cost_1_5": bool(k) and float(np.mean(gross - 1.5 * (1.5 * ch + fill))) >= 0,
        "st4c": (met["net_mean_wo_best5"] or 0) > 0,
        "boot_p01": p < 0.01,
    }
    return {
        "id": f"R10-{s}-t{t}-{ex}-{filt}",
        "shape": s,
        "t": t,
        "exit": ex,
        "filter": filt,
        "p": round(p, 4),
        "credit_med": round(float(np.median(col("credit"))), 1) if k else 0.0,
        "stops": int(col("stop").sum()),
        "folds_positive": fold["positive"],
        "gates": gates,
        "max_loss_rs": round(float(ml.max()), 0) if k else 0.0,
    } | met


if __name__ == "__main__":
    raise SystemExit(main())
