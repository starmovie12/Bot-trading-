"""Owner order 5 R19 (PLAN.md §PREREG-R19): James-Stein shrinkage sizing, nested walk-forward. DESIGN only.

  python -m lab.shrink_r19 -> trials.jsonl (2 lines), results/r19_board.md, data/lab/r19_rows.json
Also provides trade_lots() and finish() for later nested rounds.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from lab import nested_r17 as nr
from lab import p3r
from lab import portfolio_r14 as pf
from lab import universe as uv
from tools import lab_eval as le
from tools import overfit

ROOT = Path(__file__).resolve().parent.parent


def trade_lots(members: list[uv.Setup], lots: list[int], test: np.ndarray, max_e: int = 3) -> dict[str, np.ndarray]:
    """Test-window trading with a fixed lot count per member (capped at the ₹35,700 by-construction max loss)."""
    cols: dict[str, list[np.ndarray]] = {k: [] for k in pf.FIELDS}
    prio, legs, want = [], [], []
    for p, (s, n) in enumerate(zip(members, lots, strict=True)):
        c = s.cand[np.isin(s.tr.day[s.cand], test)]
        for k in pf.FIELDS:
            cols[k].append(np.asarray(getattr(s.tr, k))[c])
        prio.append(np.full(len(c), p))
        legs.append(np.full(len(c), s.legs))
        want.append(np.full(len(c), n))
    if not members or not sum(len(x) for x in prio):
        return {k: np.zeros(0) for k in (*pf.FIELDS, "lots")}
    tr = le.Trades(*(np.concatenate(cols[k]) for k in pf.FIELDS))
    pr, lg, wn = np.concatenate(prio), np.concatenate(legs), np.concatenate(want)
    taken = pf.sequence(tr, pr, max_e)
    per = tr.max_loss[taken]
    n = np.minimum(wn[taken], np.maximum(1, np.floor(pf.CAP / per))).astype(float)
    ch = n * tr.charges[taken] - (n - 1) * lg[taken] * 2 * nr.BROKER_ORDER
    out = {k: np.asarray(getattr(tr, k))[taken] for k in pf.FIELDS}
    out |= {
        "gross": n * tr.gross[taken],
        "charges": ch,
        "fill_stressed": n * tr.fill_stressed[taken],
        "max_loss": n * per,
        "lots": n,
    }
    out["net_stressed"] = out["gross"] - 1.5 * ch - out["fill_stressed"]
    out["net_kill"] = out["gross"] - ch
    return out


def concat(parts: list[dict[str, np.ndarray]]) -> dict[str, np.ndarray]:
    parts = [q for q in parts if len(q["day"])]
    if not parts:
        return {k: np.zeros(0) for k in (*pf.FIELDS, "lots")}
    return {k: np.concatenate([q[k] for q in parts]) for k in parts[0]}


def s2_pass(setups: list[uv.Setup], train: np.ndarray) -> dict[tuple[str, str, float], bool]:
    out: dict[tuple[str, str, float], bool] = {}
    for s in setups:
        if s.s2_key is not None and s.s2_key not in out:
            f = pf.matrix(s.path)[0]
            rows_in = np.isin(np.arange(len(f["t"])) // nr.ROWS, train)
            out[s.s2_key] = bool(p3r.index_stage(f, s.mask & rows_in, s.side, s.win, s.to_close)["s2"])
    return out


def shrink(setups: list[uv.Setup], train: np.ndarray, need_s2: bool) -> tuple[list[uv.Setup], list[int]]:
    s2 = s2_pass(setups, train) if need_s2 else {}
    stats = []
    for k, s in enumerate(setups):
        if need_s2 and s.s2_key is not None and not s2[s.s2_key]:
            continue
        taken = le.sequence(s.tr, s.cand[np.isin(s.tr.day[s.cand], train)])
        if len(taken) >= max(2, 20 * len(train) / nr.N_DAYS):
            x = s.tr.net_stressed[taken]
            stats.append((k, s, float(x.mean()), float(x.var(ddof=1)) / len(x), len(x)))
    if len(stats) < 4:
        return [], []
    m = np.array([z[2] for z in stats])
    se2 = np.array([z[3] for z in stats])
    nn = np.array([z[4] for z in stats], dtype=float)
    grand = float((m * nn).sum() / nn.sum())
    b = (len(m) - 3) * float(se2.mean()) / float(((m - grand) ** 2).sum())
    mu = grand + max(0.0, 1 - b) * (m - grand)
    keep = sorted(
        [(float(u), z[0], z[1]) for u, z in zip(mu, stats, strict=True) if u > 0], key=lambda q: (-q[0], q[1])
    )
    return [s for _, _, s in keep], [3 if u >= 600 else 2 if u >= 300 else 1 for u, _, _ in keep]


def finish(res: dict[str, dict[str, np.ndarray]], meta: dict[str, dict[str, Any]], rnd: str, title: str) -> int:
    """PBO (adds the new OOS columns), DSR, gates, trials, board: shared by the nested rounds."""
    windows = [nr.block(b) for b in range(1, 5)]
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
                "idea": meta[tid]["idea"],
                "params": meta[tid]["params"],
                "design_net_stressed": r["net_total"],
                "p_screen": None,
                "source": f"owner order 5 {rnd} (nested walk-forward, OOS on 4 test blocks)",
            }
        )
    (ROOT / f"data/lab/{rnd.lower()}_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    out = [
        f"# {rnd} BOARD (owner order 5: {title}; nested WF OUT-OF-SAMPLE on 290 DESIGN days; stressed ₹, PRE-TAX)",
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
    (ROOT / f"results/{rnd.lower()}_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


def main() -> int:
    setups = uv.build()
    res: dict[str, dict[str, np.ndarray]] = {}
    meta: dict[str, dict[str, Any]] = {}
    for tid, need in (("R19-a", False), ("R19-b", True)):
        parts = []
        for b in range(1, 5):
            test = nr.block(b)
            mem, lots = shrink(setups, np.arange(0, test[0] - 1), need)
            parts.append(trade_lots(mem, lots, test))
        res[tid] = concat(parts)
        meta[tid] = {
            "idea": f"James-Stein shrinkage sizing ({'S2-passed' if need else 'all'} eligible setups)",
            "params": {"need_s2": need, "lots_at": [300, 600]},
        }
    return finish(res, meta, "R19", "James-Stein shrinkage sizing")


if __name__ == "__main__":
    raise SystemExit(main())
