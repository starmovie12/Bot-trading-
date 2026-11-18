"""Owner order 5 R18 (PLAN.md §PREREG-R18): meta-labeling on per-window primaries, nested walk-forward. DESIGN only.

python -m lab.meta_r18 -> trials.jsonl (3 lines), results/r18_board.md, data/lab/r18_rows.json
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from lab import ml_r8
from lab import nested_r17 as nr
from lab import portfolio_r14 as pf
from lab import universe as uv
from tools import lab_eval as le
from tools import overfit

ROOT = Path(__file__).resolve().parent.parent
STRUCT = {"ATM": 0, "LONG": 0, "CAP15": 1, "CAP15P": 1, "ITM2": 2, "SPREAD": 3}


def select_mb(setups: list[uv.Setup], train: np.ndarray) -> list[uv.Setup]:
    keep = []
    for k, s in enumerate(setups):
        taken = le.sequence(s.tr, s.cand[np.isin(s.tr.day[s.cand], train)])
        if len(taken) >= 20 * len(train) / nr.N_DAYS and float(s.tr.net_stressed[taken].mean()) > 0:
            keep.append((float(s.tr.net_stressed[taken].mean()), k, s))
    keep.sort(key=lambda z: (-z[0], z[1]))
    return [s for _, _, s in keep]


def table(members: list[uv.Setup], days: np.ndarray) -> tuple[le.Trades, np.ndarray, np.ndarray]:
    cols: dict[str, list[np.ndarray]] = {k: [] for k in pf.FIELDS}
    extra, legs = [], []
    for s in members:
        c = s.cand[np.isin(s.tr.day[s.cand], days)]
        for k in pf.FIELDS:
            cols[k].append(np.asarray(getattr(s.tr, k))[c])
        ex, st = s.key.split("|")
        one = np.zeros((len(c), 5))
        one[:, STRUCT[st]] = 1.0
        one[:, 4] = float(ex in ("XH", "XH2"))
        extra.append(one)
        legs.append(np.full(len(c), s.legs))
    if not members:
        return le.Trades(*(np.zeros(0) for _ in pf.FIELDS)), np.zeros((0, 5)), np.zeros(0)
    tr = le.Trades(*(np.concatenate(cols[k]) for k in pf.FIELDS))
    return tr, np.concatenate(extra), np.concatenate(legs)


def run_trial(primary: str, kind: str, setups: list[uv.Setup], f: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    parts = []
    for b in range(1, 5):
        test = nr.block(b)
        train = np.arange(0, test[0] - 1)
        members = nr.select(setups, train) if primary == "a" else select_mb(setups, train)
        tr_a, ex_a, _ = table(members, train)
        tr_b, ex_b, lg_b = table(members, test)
        if len(tr_a.row) < 30 or len(tr_b.row) == 0:
            continue
        x_a = np.column_stack([ml_r8.design(f, tr_a.row.astype(int), tr_a.row.astype(int)), ex_a])
        x_b = np.column_stack([ml_r8.design(f, tr_b.row.astype(int), tr_a.row.astype(int)), ex_b])
        y = (tr_a.net_stressed > 0).astype(float)
        if kind == "L":
            p = ml_r8.predict(ml_r8.logit(x_a, y), x_b, "M1")
        else:
            p = ml_r8.predict(ml_r8.stumps(x_a[:, 1:], y), x_b[:, 1:], "M2")
        ok = p >= 0.50
        prio = np.argsort(np.argsort(-p))  # rank by probability, highest first
        trk = le.Trades(
            *(np.where(ok, getattr(tr_b, k), np.inf) if k == "max_loss" else getattr(tr_b, k) for k in pf.FIELDS)
        )
        taken = pf.sequence(trk, prio, 3)
        want = np.where(p[taken] >= 0.70, 3, np.where(p[taken] >= 0.60, 2, 1)).astype(float)
        per = tr_b.max_loss[taken]
        n = np.minimum(want, np.maximum(1, np.floor(pf.CAP / per)))
        ch = n * tr_b.charges[taken] - (n - 1) * lg_b[taken] * 2 * nr.BROKER_ORDER
        out = {k: np.asarray(getattr(tr_b, k))[taken] for k in pf.FIELDS}
        out |= {
            "gross": n * tr_b.gross[taken],
            "charges": ch,
            "fill_stressed": n * tr_b.fill_stressed[taken],
            "max_loss": n * per,
            "lots": n,
        }
        out["net_stressed"] = out["gross"] - 1.5 * ch - out["fill_stressed"]
        out["net_kill"] = out["gross"] - ch
        parts.append(out)
    if not parts:
        return {k: np.zeros(0) for k in (*pf.FIELDS, "lots")}
    return {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}


def main() -> int:
    setups = uv.build()
    f = ml_r8.load()[0]
    windows = [nr.block(b) for b in range(1, 5)]
    trials = {"R18-Ma-L": ("a", "L"), "R18-Ma-S": ("a", "S"), "R18-Mb-L": ("b", "L")}
    res = {tid: run_trial(pr, kd, setups, f) for tid, (pr, kd) in trials.items()}
    z = np.load(ROOT / "data/lab/pbo_matrix.npz")
    names, mat = list(z["names"]), z["m"]
    for tid, t in res.items():
        names.append(tid)
        mat = np.column_stack([mat, nr.daily(t["net_stressed"], t["day"])])
    np.savez_compressed(ROOT / "data/lab/pbo_matrix.npz", names=np.array(names), m=mat)
    pbo, _ = overfit.pbo(mat, 16)
    sr_var = float(np.var([overfit.sharpe(c) for c in mat.T if np.std(c) > 0], ddof=1))
    n_trials = len((ROOT / "trials.jsonl").read_text(encoding="utf-8").splitlines()) + len(res)
    rows: list[dict[str, Any]] = []
    for tid, t in res.items():
        r: dict[str, Any] = {"id": tid, "pbo": round(pbo, 4), "n_trials": n_trials} | nr.gates(
            t, windows, n_trials, sr_var
        )
        r["gates"]["pbo_0_25"] = pbo <= 0.25
        rows.append(r)
        le.append_trial(
            {
                "id": tid,
                "cycle": 1,
                "idea": f"meta-labeling, primaries {trials[tid][0]}, model {trials[tid][1]}",
                "params": {"primary": trials[tid][0], "model": trials[tid][1], "thresholds": [0.5, 0.6, 0.7]},
                "design_net_stressed": r["net_total"],
                "p_screen": None,
                "source": "owner order 5 R18 (nested walk-forward, OOS on 4 test blocks)",
            }
        )
    (ROOT / "data/lab/r18_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    out = [
        "# R18 BOARD (owner order 5: meta-labeling; nested WF OUT-OF-SAMPLE on 290 DESIGN days; stressed ₹, PRE-TAX)",
        "",
        "| id | trades | per day | lots mean | net / trade | windows net ₹ | w/o best 5 | 1.5x cost | 12m exp ₹ | "
        "DD95 ₹ | PBO | DSR | failed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        bad = [k for k, v in r["gates"].items() if not v] or ["none: HOLDOUT RULE MET"]
        out.append(
            f"| {r['id']} | {r['trades']} | {r['per_day']} | {r['lots_mean']} | {r['net_mean']} | {r['windows_net']} | "
            f"{r['wo_best5']} | {r['cost_1_5']} | {r['exp_12m']:,.0f} | {r['dd95']:,.0f} | {r['pbo']} | {r['dsr']} | "
            f"{', '.join(bad)} |"
        )
    (ROOT / "results/r18_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
