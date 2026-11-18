"""Owner order 5 R17 (PLAN.md §PREREG-R17): nested walk-forward of the R14 + R15 pipeline. DESIGN only.

python -m lab.nested_r17 -> trials.jsonl (2 lines), results/r17_board.md, data/lab/r17_rows.json,
                            data/lab/pbo_matrix.npz (the daily P&L columns used for PBO / DSR)
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from lab import p3r
from lab import portfolio_r14 as pf
from lab import sizing_r15 as sz
from lab import universe as uv
from lab.select_spec import dd95
from tools import lab_eval as le
from tools import overfit

ROOT = Path(__file__).resolve().parent.parent
N_DAYS, ROWS, BROKER_ORDER = 362, 61, 23.6  # ₹20 an order + 18% GST: the part of the charges that does not scale
FIELDS = pf.FIELDS


def block(b: int, n: int = N_DAYS) -> np.ndarray:
    size = n // 5
    return np.arange(size * b, size * (b + 1) if b < 4 else n)


def select(setups: list[uv.Setup], train: np.ndarray) -> list[uv.Setup]:
    s2: dict[tuple[str, str, float], bool] = {}
    keep: list[tuple[float, int, uv.Setup]] = []
    for k, s in enumerate(setups):
        if s.s2_key is not None:
            if s.s2_key not in s2:
                f = pf.matrix(s.path)[0]
                rows_in = np.isin(np.arange(len(f["t"])) // ROWS, train)
                s2[s.s2_key] = bool(p3r.index_stage(f, s.mask & rows_in, s.side, s.win, s.to_close)["s2"])
            if not s2[s.s2_key]:
                continue
        c = s.cand[np.isin(s.tr.day[s.cand], train)]
        taken = le.sequence(s.tr, c)
        if len(taken) >= 20 * len(train) / N_DAYS and float(s.tr.net_stressed[taken].mean()) > 0:
            keep.append((float(s.tr.net_stressed[taken].mean()), k, s))
    keep.sort(key=lambda z: (-z[0], z[1]))
    return [s for _, _, s in keep]


def trade(members: list[uv.Setup], test: np.ndarray, tiers: bool, max_e: int = 3) -> dict[str, np.ndarray]:
    cols: dict[str, list[np.ndarray]] = {k: [] for k in FIELDS}
    prio, legs = [], []
    for p, s in enumerate(members):
        c = s.cand[np.isin(s.tr.day[s.cand], test)]
        for k in FIELDS:
            cols[k].append(np.asarray(getattr(s.tr, k))[c])
        prio.append(np.full(len(c), p))
        legs.append(np.full(len(c), s.legs))
    if not members or not sum(len(x) for x in prio):
        return {k: np.zeros(0) for k in (*FIELDS, "lots")}
    tr = le.Trades(*(np.concatenate(cols[k]) for k in FIELDS))
    pr, lg = np.concatenate(prio), np.concatenate(legs)
    taken = pf.sequence(tr, pr, max_e)
    n = np.array([sz.lots_for(int(pr[i]) + 1, float(tr.max_loss[i])) if tiers else 1 for i in taken], dtype=float)
    ch = n * tr.charges[taken] - (n - 1) * lg[taken] * 2 * BROKER_ORDER
    out = {k: np.asarray(getattr(tr, k))[taken] for k in FIELDS}
    out |= {
        "gross": n * tr.gross[taken],
        "charges": ch,
        "fill_stressed": n * tr.fill_stressed[taken],
        "max_loss": n * tr.max_loss[taken],
        "lots": n,
    }
    out["net_stressed"] = out["gross"] - 1.5 * ch - out["fill_stressed"]
    out["net_kill"] = out["gross"] - ch
    return out


def gates(t: dict[str, np.ndarray], windows: list[np.ndarray], n_trials: int, sr_var: float) -> dict[str, Any]:
    test_days = np.concatenate(windows)
    net = t["net_stressed"]
    daily = np.zeros(N_DAYS)
    np.add.at(daily, t["day"].astype(int), net)
    d = daily[test_days]
    wins = [float(net[np.isin(t["day"], w)].sum()) for w in windows]
    k = len(net)
    top5 = np.sort(net)[-5:].sum() if k >= 5 else net.sum()
    cost = 1.5 * t["charges"] + t["fill_stressed"]
    exp12 = float(d.mean()) * 250
    d95 = dd95(d, np.minimum(d, 0.0)) if k else 0.0
    dsr = overfit.dsr(d, n_trials, sr_var)
    res: dict[str, Any] = {
        "trades": k,
        "per_day": round(k / len(test_days), 3),
        "net_mean": round(float(net.mean()), 2) if k else 0.0,
        "net_total": round(float(net.sum()), 0),
        "windows_net": [round(w, 0) for w in wins],
        "windows_trades": [int(np.isin(t["day"], w).sum()) for w in windows],
        "wo_best5": round(float((net.sum() - top5) / (k - 5)), 2) if k > 5 else None,
        "cost_1_5": round(float(np.mean(t["gross"] - 1.5 * cost)), 2) if k else None,
        "exp_12m": round(exp12, 0),
        "dd95": round(d95, 0),
        "dsr": round(dsr, 4),
        "max_loss": round(float(t["max_loss"].max()), 0) if k else 0.0,
        "lots_mean": round(float(t["lots"].mean()), 2) if k else 0.0,
    }
    res["gates"] = {
        "net": res["net_mean"] > 0,
        "windows_3of4": sum(w > 0 for w in wins) >= 3,
        "per_day_0_5": res["per_day"] >= 0.5,
        "wo_best5": (res["wo_best5"] or 0) > 0,
        "cost_1_5": (res["cost_1_5"] or -1) >= 0,
        "exp12_ge_dd95": exp12 >= d95 and k > 0,
        "dsr_0_95": dsr >= 0.95,
    }
    return res


def daily(net: np.ndarray, day: np.ndarray) -> np.ndarray:
    out = np.zeros(N_DAYS)
    np.add.at(out, day.astype(int), net)
    return out


def pbo_columns(setups: list[uv.Setup]) -> dict[str, np.ndarray]:
    """Every trial with a DESIGN P&L series so far: each universe setup alone, the R14 / R15 / R16 portfolios."""
    from lab import filter_r16  # noqa: PLC0415

    cols = {s.id: uv.alone_daily(s) for s in setups}
    allm = json.loads((ROOT / "results/r14_members.json").read_text(encoding="utf-8"))
    sets = {
        "P1": ["R7-2-0.004-CAP15-XH2", "R12-1-5-CAP15-XH", "R13-3-0.001-ITM2-XH"],
        "P2": allm,
        "P3": [m for m in allm if pf.member(m)[1].size >= 20],
    }
    for name, ids in sets.items():
        tr, prio = pf.union(ids)
        for e in (2, 3, 5):
            tk = pf.sequence(tr, prio, e)
            cols[f"R14-{name}-e{e}"] = daily(tr.net_stressed[tk], tr.day[tk])
    for v in ("a", "b", "c"):
        sz.run(v)
        t = sz.LAST["trades"]
        cols[f"R15-{v}"] = daily(t.net_stressed, t.day)
    for x in (2, 4, 6):
        sz.run("a", filter_r16.keeper(x), f"R16-x{x}")
        t = sz.LAST["trades"]
        cols[f"R16-x{x}"] = daily(t.net_stressed, t.day)
    return cols


def main() -> int:
    setups = uv.build()
    windows = [block(b) for b in range(1, 5)]
    members = [select(setups, np.arange(0, w[0] - 1)) for w in windows]
    results: dict[str, dict[str, np.ndarray]] = {}
    for name, tiers in (("R17-a", True), ("R17-b", False)):
        parts = [trade(m, w, tiers) for m, w in zip(members, windows, strict=True)]
        results[name] = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    cols = pbo_columns(setups)
    for name, t in results.items():
        cols[name] = daily(t["net_stressed"], t["day"])
    mat = np.column_stack(list(cols.values()))
    np.savez_compressed(ROOT / "data/lab/pbo_matrix.npz", names=np.array(list(cols)), m=mat)
    pbo, _ = overfit.pbo(mat, 16)
    srs = np.array([overfit.sharpe(c) for c in mat.T if np.std(c) > 0])
    sr_var = float(np.var(srs, ddof=1))
    n_trials = len((ROOT / "trials.jsonl").read_text(encoding="utf-8").splitlines()) + len(results)
    rows: list[dict[str, Any]] = []
    for name, t in results.items():
        r: dict[str, Any] = {
            "id": name,
            "members_per_window": [len(m) for m in members],
            "pbo": round(pbo, 4),
            "n_trials": n_trials,
            "sr_var": round(sr_var, 6),
        } | gates(t, windows, n_trials, sr_var)
        r["gates"]["pbo_0_25"] = pbo <= 0.25
        rows.append(r)
        le.append_trial(
            {
                "id": name,
                "cycle": 1,
                "idea": f"nested WF of the R14 + R15 pipeline ({'tiers' if name.endswith('a') else '1 lot'})",
                "params": {"tiers": name.endswith("a"), "max_entries": 3},
                "design_net_stressed": r["net_total"],
                "p_screen": None,
                "source": "owner order 5 R17 (nested walk-forward, OOS on 4 test blocks)",
            }
        )
    (ROOT / "data/lab/r17_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    out = [
        "# R17 BOARD (owner order 5: NESTED walk-forward; OUT-OF-SAMPLE on the 4 test blocks, 290 DESIGN days;",
        "stressed ₹, PRE-TAX, [BACKTEST·out-of-sample of the selection process]; PBO over every trial with a P&L "
        "series)",
        "",
        "| id | members per window | trades | per day | net / trade | windows net ₹ | w/o best 5 | 1.5x cost | "
        "12m exp ₹ | DD95 ₹ | PBO | DSR | failed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        bad = [k for k, v in r["gates"].items() if not v] or ["none: HOLDOUT RULE MET"]
        out.append(
            f"| {r['id']} | {r['members_per_window']} | {r['trades']} | {r['per_day']} | {r['net_mean']} | "
            f"{r['windows_net']} | {r['wo_best5']} | {r['cost_1_5']} | {r['exp_12m']:,.0f} | {r['dd95']:,.0f} | "
            f"{r['pbo']} | {r['dsr']} | {', '.join(bad)} |"
        )
    (ROOT / "results/r17_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
