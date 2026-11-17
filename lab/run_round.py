"""Run pre-registered trials (MISSION V19 3c): python -m lab.run_round <round> <id> [<id> ...].

Each id is one trial line in trials.jsonl (ST1) and one row in results/scoreboard.md. Screening null = 1,000 runs (ST3).
"""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from lab import ideas
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "results/scoreboard.json"
VIX_MEDIAN = 13.57  # DESIGN median VIX (results/market_facts.md)


def run_trial(
    idea: ideas.Idea, rnd: str, feats: le.A, outs: dict[str, le.A], days: list[str], extra: dict[str, Any]
) -> dict[str, Any]:
    params = idea.params | extra.get("params", {})
    structure, preset = extra.get("structure", idea.structure), extra.get("preset", idea.preset)
    mask, direction = idea.rule(feats, params)
    if extra.get("vix_falling"):
        mask = mask & (feats["vix_chg"] < 0)
    tr = le.trades(feats, outs[f"{preset}|{structure}"], days)
    cand = le.select(tr, np.nan_to_num(mask).astype(bool), direction)
    taken = le.sequence(tr, cand)
    n_days = len(days)
    met = le.metrics(tr, taken, n_days, VIX_MEDIAN)
    fold = le.folds(tr, taken, n_days)
    t_lo, t_hi = (int(tr.t[taken].min()), int(tr.t[taken].max())) if len(taken) else (0, 0)
    pool = np.nonzero((tr.t >= t_lo) & (tr.t <= t_hi))[0]
    p = le.null_p(tr, taken, pool, 1000) if len(taken) else 1.0
    lot = feats["lot"][tr.row[taken]] if len(taken) else np.array([1.0])
    row = {
        "id": extra.get("id", idea.id),
        "round": rnd,
        "idea": idea.text,
        "edge": idea.edge,
        "structure": structure,
        "preset": preset,
        "params": params | ({"vix_falling": 1} if extra.get("vix_falling") else {}),
        "per_month": round(met["trades"] / n_days * 21, 1),
        "gross_pts": round(float(np.mean(tr.gross[taken] / lot)), 2) if len(taken) else 0.0,
        "be_pts": round(float(np.mean((le.STRESS_CHARGES * tr.charges[taken] + tr.fill_stressed[taken]) / lot)), 2)
        if len(taken)
        else 0.0,
        "null_p": round(p, 4),
        "folds_positive": fold["positive"],
        "folds_thin": fold["thin"],
        "st4": fold["pass"],
        "st11": met["per_day"] >= 0.5,
        "n_params": len(params),
    } | met
    trial = {
        "id": row["id"],
        "cycle": 1,
        "idea": idea.text,
        "params": row["params"],
        "structure": structure,
        "preset": preset,
        "design_net_stressed": met["net_total"],
        "p_screen": round(p, 4),
        "source": "lead",
    }
    le.append_trial(trial)
    return row


def board(rows: list[dict[str, Any]]) -> list[str]:
    cols = (
        "id",
        "round",
        "per_month",
        "per_day",
        "gross_pts",
        "be_pts",
        "net_mean",
        "max_dd",
        "folds_positive",
        "null_p",
        "net_mean_wo_best5",
        "profit_factor",
        "losing_streak",
        "net_mean_high_vix",
        "net_mean_low_vix",
        "n_params",
        "trades",
        "structure",
        "preset",
    )
    out = [
        "# SCOREBOARD (MISSION V19 3c; DESIGN 362 days; stressed ₹ PRE-TAX; screening only)",
        "",
        "| " + " | ".join(cols) + " |",
        "|" + "---|" * len(cols),
    ]
    out += ["| " + " | ".join(str(r.get(c)) for c in cols) + " |" for r in rows]
    return out


def main(argv: list[str]) -> int:
    rnd, ids = argv[0], argv[1:]
    feats, outs, days = le.load()
    rows = json.loads(BOARD.read_text(encoding="utf-8")) if BOARD.is_file() else []
    by_id = {i.id: i for i in ideas.BRACKET}
    for spec in ids:
        base, _, variant = spec.partition("+")
        extra: dict[str, Any] = {"id": spec}
        if variant == "b1":
            extra["vix_falling"] = True
        elif variant == "b2":
            extra["structure"] = "SPREAD"
        elif variant in ("C1", "C2", "C3", "C4"):
            extra["preset"] = variant
        r = run_trial(by_id[base], rnd, feats, outs, days, extra)
        rows = [x for x in rows if x["id"] != r["id"]] + [r]
        print(
            f"{r['id']}: n {r['trades']} ({r['per_day']}/day) net {r['net_mean']} dd {r['max_dd']}"
            f" folds {r['folds_positive']}/4 p {r['null_p']}"
        )
    BOARD.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    (ROOT / "results/scoreboard.md").write_text("\n".join(board(rows)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
