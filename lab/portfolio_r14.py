"""Owner order 4 R14 (PLAN.md §PREREG-R14): a portfolio of the positive DESIGN setups, one position at a time.

  python -m lab.portfolio_r14 -> trials.jsonl (9 lines), results/r14_board.md, data/lab/r14_rows.json. DESIGN only.
Also used by R15 / R16 (union candidates + sequencing).
"""

import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from lab import ideas, p3r
from lab.f1_r10 import boot_p
from lab.run_round import VIX_MEDIAN
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
CAP, LOCK, COOL = 35_700.0, 71_400.0, 15
FIELDS = (
    "row",
    "day",
    "t",
    "dir",
    "entry_m",
    "exit_m",
    "gross",
    "charges",
    "fill_stressed",
    "net_stressed",
    "net_kill",
    "max_loss",
    "mae",
    "vix",
)
_CACHE: dict[str, tuple[le.A, dict[str, le.A], list[str]]] = {}


def matrix(path: str) -> tuple[le.A, dict[str, le.A], list[str]]:
    if path not in _CACHE:
        _CACHE[path] = le.load(ROOT / path)
    return _CACHE[path]


def member(mid: str) -> tuple[le.Trades, np.ndarray, str, le.A]:
    """The member's trade table, its candidate indices, its outcome matrix path and its features."""
    if mid.startswith("A2"):
        path, key = "data/lab/matrix.npz", "EXIT0|LONG"
        f, outs, days = matrix(path)
        idea = next(i for i in ideas.BRACKET if i.id == "A2")
        mask, side = idea.rule(f, idea.params)
        if mid.endswith("+b1"):
            mask = mask & (f["vix_chg"] < 0)
    else:
        m = re.match(r"(R\d+-\d+)-([\d.]+)-(.*)", mid)
        if not m:
            raise ValueError(mid)
        iid, x, rest = m.group(1), float(m.group(2)), m.group(3)
        struct, ex = rest.split("-") if "-" in rest else ("LONG", rest)
        spec = p3r.ROUNDS[iid.split("-")[0]]
        path, key = spec.get("matrix", "data/lab/matrix.npz"), f"{ex}|{struct}"
        f, outs, days = matrix(path)
        mask, side, _ = spec["ideas"][iid][1](f, x)
    tr = le.trades(f, outs[key], days)
    return tr, le.select(tr, np.nan_to_num(mask).astype(bool), side), path, f


def union(ids: list[str]) -> tuple[le.Trades, np.ndarray]:
    """All members' candidate trades as one table, with each row's member priority (0 = highest)."""
    cols: dict[str, list[np.ndarray]] = {k: [] for k in FIELDS}
    prio: list[np.ndarray] = []
    for p, mid in enumerate(ids):
        tr, cand, _, _ = member(mid)
        for k in FIELDS:
            cols[k].append(np.asarray(getattr(tr, k))[cand])
        prio.append(np.full(len(cand), p))
    return le.Trades(*(np.concatenate(cols[k]) for k in FIELDS)), np.concatenate(prio)


def sequence(tr: le.Trades, prio: np.ndarray, max_e: int, cap: float = CAP) -> np.ndarray:
    taken: list[int] = []
    day, n, free, cool_at, lost = -1, 0, -1, -1, 0.0
    for i in np.lexsort((prio, tr.entry_m, tr.day)):
        if tr.day[i] != day:
            day, n, free, cool_at, lost = int(tr.day[i]), 0, -1, -1, 0.0
        if n >= max_e or tr.entry_m[i] <= free or tr.entry_m[i] < cool_at or lost >= LOCK or tr.max_loss[i] > cap:
            continue
        taken.append(int(i))
        n, free = n + 1, int(tr.exit_m[i])
        if tr.net_stressed[i] < 0:
            cool_at, lost = int(tr.exit_m[i]) + COOL, lost - float(tr.net_stressed[i])
    return np.array(taken, dtype=int)


def evaluate(tid: str, tr: le.Trades, taken: np.ndarray, n_days: int = 362) -> dict[str, Any]:
    met = le.metrics(tr, taken, n_days, VIX_MEDIAN)
    fold = le.folds(tr, taken, n_days)
    cost = le.STRESS_CHARGES * tr.charges[taken] + tr.fill_stressed[taken]
    day_net, day_cnt = np.zeros(n_days), np.zeros(n_days)
    np.add.at(day_net, tr.day[taken], tr.net_stressed[taken])
    np.add.at(day_cnt, tr.day[taken], 1)
    p = boot_p(day_net, day_cnt) if len(taken) else 1.0
    hi, lo = met["n_high_vix"], met["n_low_vix"]
    gates = {
        "net": met["net_mean"] > 0,
        "folds": fold["pass"],
        "vix_halves": hi >= 15
        and lo >= 15
        and (met["net_mean_high_vix"] or 0) > 0
        and (met["net_mean_low_vix"] or 0) > 0,
        "st11": met["per_day"] >= 0.5,
        "cost_1_5": bool(len(taken)) and float(np.mean(tr.gross[taken] - 1.5 * cost)) >= 0,
        "st4c": (met["net_mean_wo_best5"] or 0) > 0,
        "boot_p01": p < 0.01,
    }
    return {
        "id": tid,
        "p": round(p, 4),
        "folds_positive": fold["positive"],
        "folds": fold["folds"],
        "gates": gates,
        "max_loss_rs": round(float(tr.max_loss[taken].max()), 0) if len(taken) else 0.0,
    } | met


def board(title: str, rows: list[dict[str, Any]]) -> list[str]:
    out = [
        title,
        "",
        "| id | trades | per day | net / trade | net total | folds + | high / low VIX | w/o best 5 | max DD ₹ "
        "| boot p | max loss ₹ | failed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        bad = [k for k, v in r["gates"].items() if not v] or ["none (PASSES the EXPLORE screen)"]
        out.append(
            f"| {r['id']} | {r['trades']} | {r['per_day']} | {r['net_mean']} | {r['net_total']:,.0f} | "
            f"{r['folds_positive']}/4 | {r['net_mean_high_vix']} / {r['net_mean_low_vix']} | "
            f"{r['net_mean_wo_best5']} | {r['max_dd']:,.0f} | {r['p']} | {r['max_loss_rs']:,.0f} | {', '.join(bad)} |"
        )
    return out


def main() -> int:
    allm = json.loads((ROOT / "results/r14_members.json").read_text(encoding="utf-8"))
    sets = {
        "P1": ["R7-2-0.004-CAP15-XH2", "R12-1-5-CAP15-XH", "R13-3-0.001-ITM2-XH"],
        "P2": allm,
        "P3": [m for m in allm if member(m)[1].size >= 20],
    }
    rows = []
    for name, ids in sets.items():
        tr, prio = union(ids)
        for e in (2, 3, 5):
            r = evaluate(f"R14-{name}-e{e}", tr, sequence(tr, prio, e))
            r |= {"set": name, "max_e": e, "members": len(ids)}
            rows.append(r)
    by = {(r["set"], r["max_e"]): r for r in rows}
    es = (2, 3, 5)
    for r in rows:
        i = es.index(r["max_e"])
        r["gates"]["neighbours"] = all(by[(r["set"], es[j])]["net_mean"] > 0 for j in (i - 1, i + 1) if 0 <= j < 3)
    for r in rows:
        le.append_trial(
            {
                "id": r["id"],
                "cycle": 1,
                "idea": f"portfolio {r['set']} ({r['members']} members), max {r['max_e']} a day",
                "params": {"set": r["set"], "max_entries": r["max_e"]},
                "design_net_stressed": r["net_total"],
                "p_screen": r["p"],
                "source": "owner order 4 R14 EXPLORE (portfolio)",
            }
        )
    (ROOT / "data/lab/r14_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    out = board(
        "# R14 BOARD (owner order 4: portfolio of setups; DESIGN 362 days; stressed ₹, PRE-TAX, "
        "[BACKTEST·in-sample, selection-biased: the members were picked on these days])",
        rows,
    )
    (ROOT / "results/r14_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
