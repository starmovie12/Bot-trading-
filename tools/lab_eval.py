#!/usr/bin/env python3
"""Lab evaluator (MISSION V19 3a/3c): an idea = mask over FEATURES rows + direction + structure + exit preset.

The evaluator owns the sequencing (one structure at a time, <= 2 entries a day, cool-off 30 min after a loss,
the day ends after a full loss) and the cost model (charges by date, ST7 stress); it never recomputes prices
(data/lab/matrix.npz).
Screening only: every number that feeds the verdict comes from tools/engine_of_record.py (C10).
"""

import datetime as dt
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261116
SHELL_COOLOFF = 30  # pre-registered shell constant (PLAN.md §PREREG-0); 3e writes it to limits.toml
MAX_ENTRIES = 2
HALF_SPREAD, SLIP = 0.50, 0.20  # ₹ per unit per side: ESTIMATE (D-21)
STRESS_CHARGES, STRESS_SLIP, BASE_SPREAD_MULT = 1.5, 2.0, 2.0
STT_SWITCH = dt.date(2026, 4, 1)
A = dict[str, np.ndarray]


def load(path: Path = ROOT / "data/lab/matrix.npz") -> tuple[A, dict[str, A], list[str]]:
    m = np.load(path)
    feats = {k[2:]: m[k] for k in m.files if k.startswith("F_")}
    outs: dict[str, A] = {}
    for k in m.files:
        if k.startswith("O_"):
            key, col = k[2:].split("_", 1)  # "EXIT0|LONG_entry_m" -> ("EXIT0|LONG", "entry_m")
            outs.setdefault(key, {})[col] = m[k]
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    return feats, outs, days


def charges(o: A, lot: np.ndarray, dates: list[dt.date]) -> np.ndarray:
    """Unstressed statutory + broker charges per trade (₹), by date (constants.toml SOURCE rows)."""
    stt = np.array([0.15 if d >= STT_SWITCH else 0.10 for d in dates]) / 100
    legs = o["legs"]
    two = legs == 2
    exit_long = np.where(two, o["long_out"], o["exit"])
    buy = (o["long_in"] + np.where(two, o["short_out"], 0.0)) * lot
    sell = (exit_long + np.where(two, o["short_in"], 0.0)) * lot
    turnover = buy + sell
    brokerage = 20.0 * 2 * legs
    exch = turnover * 0.03503 / 100
    ipft = turnover * 0.0005 / 100
    sebi = turnover * 0.0001 / 100
    gst = (brokerage + exch + ipft + sebi) * 0.18
    return np.asarray(brokerage + exch + ipft + sebi + gst + buy * 0.003 / 100 + sell * stt)


def spread_mult(minute: np.ndarray, expiry_day: np.ndarray) -> np.ndarray:
    """ST7 grade-B spread multiplier: 2 x base, 4 x in 09:15-09:25 and 14:45-15:10, 3 x on an expiry day."""
    m = np.full(minute.shape, BASE_SPREAD_MULT)
    m = np.where(expiry_day, np.maximum(m, 3.0), m)
    return np.where((minute < 10) | ((minute >= 330) & (minute <= 355)), 4.0, m)


@dataclass(frozen=True)
class Trades:
    """Per-trade table of one structure + preset, aligned with its OUTCOMES rows."""

    row: np.ndarray
    day: np.ndarray
    t: np.ndarray
    dir: np.ndarray
    entry_m: np.ndarray
    exit_m: np.ndarray
    gross: np.ndarray
    charges: np.ndarray
    fill_stressed: np.ndarray
    net_stressed: np.ndarray
    net_kill: np.ndarray
    max_loss: np.ndarray
    mae: np.ndarray
    vix: np.ndarray


def trades(feats: A, o: A, days: list[str]) -> Trades:
    row = o["row"].astype(int)
    day = feats["day_i"][row].astype(int)
    lot = feats["lot"][row]
    dates = [dt.date.fromisoformat(days[i]) for i in day]
    expiry = feats["dte"][row] == 0
    legs = o["legs"]
    gross = (o["exit"] - o["entry"]) * lot
    ch = charges(o, lot, dates)
    passive = o["passive"] if "passive" in o else np.zeros(len(row))  # P3R R3: a limit filled THROUGH pays no spread
    m_in, m_out = (
        spread_mult(o["entry_m"], expiry) * (1 - passive),
        spread_mult(o["exit_m"], expiry) * np.where(o["stale_exit"] > 0, 2, 1),
    )
    fill = lot * legs * ((HALF_SPREAD * m_in + SLIP * STRESS_SLIP) + (HALF_SPREAD * m_out + SLIP * STRESS_SLIP))
    net = gross - STRESS_CHARGES * ch - fill
    return Trades(row, day, o["t"].astype(int), o["dir"].astype(int), o["entry_m"].astype(int), o["exit_m"].astype(int),
                  gross, ch, fill, net, gross - ch, o["entry"] * lot + STRESS_CHARGES * ch + fill, o["mae"] * lot,
                  feats["vix"][row])  # fmt: skip


def sequence(tr: Trades, idx: np.ndarray) -> np.ndarray:
    """Apply the shell's day rules to candidate trade indices (time order); returns the trades actually taken."""
    taken: list[int] = []
    order = idx[np.lexsort((tr.t[idx], tr.day[idx]))]
    day, entries, free_at, cool_at, over = -1, 0, -1, -1, False
    for i in order:
        if tr.day[i] != day:
            day, entries, free_at, cool_at, over = tr.day[i], 0, -1, -1, False
        if over or entries >= MAX_ENTRIES or tr.entry_m[i] <= free_at or tr.entry_m[i] < cool_at:
            continue
        taken.append(int(i))
        entries += 1
        free_at = tr.exit_m[i]
        if tr.net_stressed[i] < 0:
            cool_at = tr.exit_m[i] + SHELL_COOLOFF
        if tr.net_stressed[i] <= -0.5 * tr.max_loss[i]:
            over = True
    return np.array(taken, dtype=int)


def select(tr: Trades, mask_rows: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Trade indices whose decision row is in the mask and whose side matches the idea's direction for that row."""
    want = direction[tr.row]
    return np.asarray(np.nonzero(mask_rows[tr.row] & (tr.dir == want))[0])


def drawdown(x: np.ndarray) -> float:
    if len(x) == 0:
        return 0.0
    eq = np.cumsum(x)
    return float(np.max(np.maximum.accumulate(np.maximum(eq, 0)) - eq))


def metrics(tr: Trades, taken: np.ndarray, n_days: int, vix_median: float) -> dict[str, Any]:
    net = tr.net_stressed[taken]
    n = len(net)
    wins, losses = net[net > 0].sum(), -net[net < 0].sum()
    streak = best = 0
    for x in net:
        streak = streak + 1 if x < 0 else 0
        best = max(best, streak)
    top5 = np.sort(net)[-5:].sum() if n >= 5 else net.sum()
    hi, lo = tr.vix[taken] > vix_median, tr.vix[taken] <= vix_median
    return {"trades": n, "per_day": round(n / n_days, 3), "net_mean": round(float(net.mean()), 2) if n else 0.0,
            "net_total": round(float(net.sum()), 2),
            "gross_mean": round(float(tr.gross[taken].mean()), 2) if n else 0.0,
            "max_dd": round(drawdown(net), 2), "profit_factor": round(float(wins / losses), 3) if losses > 0 else None,
            "losing_streak": best, "best5_share": round(float(top5 / net.sum()), 3) if net.sum() > 0 else None,
            "net_mean_wo_best5": round(float((net.sum() - top5) / (n - 5)), 2) if n > 5 else None,
            "net_mean_high_vix": round(float(net[hi].mean()), 2) if hi.any() else None, "n_high_vix": int(hi.sum()),
            "net_mean_low_vix": round(float(net[lo].mean()), 2) if lo.any() else None, "n_low_vix": int(lo.sum()),
            "kill_net_mean": round(float(tr.net_kill[taken].mean()), 2) if n else 0.0}  # fmt: skip


def folds(tr: Trades, taken: np.ndarray, n_days: int, k: int = 4, min_trades: int = 15) -> dict[str, Any]:
    """ST4: 4 anchored walk-forward test windows over DESIGN (equal day blocks after the first); thin < 15 trades."""
    size = n_days // (k + 1)
    out = []
    for f in range(k):
        lo, hi = size * (f + 1), size * (f + 2) if f < k - 1 else n_days
        sel = taken[(tr.day[taken] >= lo) & (tr.day[taken] < hi)]
        out.append({"trades": len(sel), "net_mean": round(float(tr.net_stressed[sel].mean()), 2) if len(sel) else None,
                    "thin": len(sel) < min_trades})  # fmt: skip
    positive = sum(1 for x in out if not x["thin"] and (x["net_mean"] or 0) > 0)
    return {"folds": out, "positive": positive, "thin": sum(x["thin"] for x in out), "pass": positive >= 3}


def null_p(tr: Trades, taken: np.ndarray, pool: np.ndarray, runs: int, seed: int = SEED) -> float:
    """ST3 matched null: per day the same number of random entries from the pool (same window, structure, preset,
    side mix), sequenced by the same shell; p = (1 + #null total >= observed) / (runs + 1)."""
    rng = np.random.default_rng(seed)
    observed = tr.net_stressed[taken].sum()
    per_day = np.bincount(tr.day[taken], minlength=int(tr.day.max()) + 1)
    by_day: dict[int, np.ndarray] = {}
    for d in np.nonzero(per_day)[0]:
        by_day[int(d)] = pool[tr.day[pool] == d]
    ups = float(np.mean(tr.dir[taken] > 0)) if len(taken) else 0.5
    ge: int = 0
    for _ in range(runs):
        picks = []
        for day_i, cands in by_day.items():
            if len(cands):
                side = np.where(rng.random(len(cands)) < ups, 1, -1)
                c = cands[tr.dir[cands] == side]
                if len(c):
                    picks.append(rng.choice(c, size=min(len(c), 3 * per_day[day_i]), replace=False))
        sel = sequence(tr, np.concatenate(picks)) if picks else np.array([], dtype=int)
        sel = _cap_per_day(tr, sel, per_day)
        ge += int(tr.net_stressed[sel].sum() >= observed)
    return (1 + ge) / (runs + 1)


def _cap_per_day(tr: Trades, sel: np.ndarray, per_day: np.ndarray) -> np.ndarray:
    keep: list[int] = []
    count: dict[int, int] = {}
    for i in sel:
        d = int(tr.day[i])
        if count.get(d, 0) < per_day[d]:
            keep.append(int(i))
            count[d] = count.get(d, 0) + 1
    return np.array(keep, dtype=int)


def append_trial(trial: dict[str, Any], path: Path = ROOT / "trials.jsonl") -> int:
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    if any(json.loads(x)["id"] == trial["id"] for x in lines):
        raise ValueError(f"trial {trial['id']} already recorded")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(trial, sort_keys=True) + "\n")
    return len(lines) + 1


if __name__ == "__main__":
    f, o, d = load()
    print(len(d), "days;", ", ".join(f"{k}: {len(v['row'])}" for k, v in o.items()))
    sys.exit(0)
