"""P3R v2 round 8 (PLAN.md §PREREG-R8): F3 ML probability, walk-forward, day-rule grid. EXPLORE on DESIGN only.

  python -m lab.ml_r8 -> trials.jsonl (96 lines), results/r8_board.md, data/lab/r8_rows.json
Models are numpy-only (M1 logistic L2 Newton, M2 boosted stumps). H and the threshold are chosen inside the training
blocks only (last 20% of training days validate, 1-day embargo), then the model is refit on all training blocks and
predicts the next block (out of sample). Option P&L from OUTCOMES (stressed costs) with the trial's day rules.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from lab.run_round import VIX_MEDIAN
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
ROWS, BLOCKS, BUF = 61, 5, 5.0
FEATS = (
    "t",
    "dte",
    "gap",
    "ret_open",
    "ret15",
    "ret30",
    "eff",
    "rv5",
    "rv15",
    "rv30",
    "vwap_dist",
    "basis",
    "basis_chg",
    "vix",
    "vix_chg",
    "vix_pct",
    "oi_skew",
    "hdfc15",
    "icici15",
    "prev_ret",
)
HS, THRS = {"30": 6, "60": 12, "close": None}, (0.55, 0.60, 0.65, 0.70)
EXITS = {"XH": "data/lab/matrix_r7.npz", "XI2": "data/lab/matrix_r2.npz"}
RULES = [(e, s, c) for e in (1, 2, 3, 5, 10, 15) for s in (True, False) for c in (15, 30)]


def load() -> tuple[dict[str, np.ndarray], dict[str, le.A], list[str]]:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    m5, f3 = np.load(ROOT / "data/lab/matrix_r5.npz"), np.load(ROOT / "data/lab/feat_r3.npz")
    f = {k[2:]: m5[k] for k in m5.files if k.startswith("F_")} | {k: f3[k] for k in f3.files}
    outs = {}
    for ex, path in EXITS.items():
        m = np.load(ROOT / path)
        pre = f"O_{ex}|CAP15_"
        outs[ex] = {k[len(pre) :]: m[k] for k in m.files if k.startswith(pre)}
    return f, outs, days


def labels(f: dict[str, np.ndarray], h: str) -> tuple[np.ndarray, np.ndarray]:
    spot = f["spot"].reshape(-1, ROWS)
    j = np.arange(ROWS)
    step = HS[h]
    end = np.full(ROWS, 60) if step is None else np.minimum(j + step, 60)
    fwd = (spot[:, end] - spot).ravel()
    return (fwd >= 14.2 + BUF).astype(float), (-fwd >= 14.2 + BUF).astype(float)


def logit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    w = np.zeros(x.shape[1])
    for _ in range(15):
        p = 1 / (1 + np.exp(-np.clip(x @ w, -30, 30)))
        g = x.T @ (p - y) + 1.0 * np.r_[0, w[1:]]
        hss = (x * (p * (1 - p))[:, None]).T @ x + np.diag(np.r_[0, np.ones(x.shape[1] - 1)])
        w -= np.linalg.solve(hss, g)
    return w


def stumps(x: np.ndarray, y: np.ndarray) -> list[tuple[int, float, float, float]]:
    base = float(np.log((y.mean() + 1e-6) / (1 - y.mean() + 1e-6)))
    fx, model = np.full(len(y), base), [(-1, 0.0, base, base)]
    qs = [np.unique(np.quantile(x[:, k], np.linspace(0.06, 0.94, 16))) for k in range(x.shape[1])]
    for _ in range(50):
        r = y - 1 / (1 + np.exp(-fx))
        best = (np.inf, 0, 0.0, 0.0, 0.0)
        for k, q in enumerate(qs):
            for c in q:
                left = x[:, k] <= c
                nl = left.sum()
                if 0 < nl < len(y):
                    ml, mr = r[left].mean(), r[~left].mean()
                    sse = -(nl * ml * ml + (len(y) - nl) * mr * mr)
                    if sse < best[0]:
                        best = (sse, k, float(c), float(ml), float(mr))
        _, k, c, ml, mr = best
        fx += 0.1 * 4 * np.where(x[:, k] <= c, ml, mr)  # x4: a Newton-like step for the logistic loss
        model.append((k, c, 0.4 * ml, 0.4 * mr))
    return model


def predict(model: Any, x: np.ndarray, kind: str) -> np.ndarray:
    if kind == "M1":
        return np.asarray(1 / (1 + np.exp(-np.clip(x @ model, -30, 30))))
    fx = np.full(len(x), model[0][2])
    for k, c, ml, mr in model[1:]:
        fx += np.where(x[:, k] <= c, ml, mr)
    return np.asarray(1 / (1 + np.exp(-fx)))


def design(f: dict[str, np.ndarray], rows: np.ndarray, fit: np.ndarray) -> np.ndarray:
    raw = np.column_stack([f[k][rows] for k in FEATS]).astype(float)
    ref = np.column_stack([f[k][fit] for k in FEATS]).astype(float)
    med = np.nanmedian(ref, axis=0)
    raw, ref = np.where(np.isnan(raw), med, raw), np.where(np.isnan(ref), med, ref)
    mu, sd = ref.mean(axis=0), ref.std(axis=0) + 1e-12
    return np.column_stack([np.ones(len(rows)), (raw - mu) / sd])


LOCK = 2 * (15_000 + 500)  # daily ₹ loss lock = 2 x the CAP15 max loss (premium cap + stressed costs), loss-first


def seq(tr: le.Trades, idx: np.ndarray, rule: tuple[int, bool, int]) -> np.ndarray:
    max_e, stop, cool = rule
    taken: list[int] = []
    day, n, free, cool_at, over, lost = -1, 0, -1, -1, False, 0.0
    for i in idx[np.lexsort((tr.t[idx], tr.day[idx]))]:
        if tr.day[i] != day:
            day, n, free, cool_at, over, lost = tr.day[i], 0, -1, -1, False, 0.0
        if over or n >= max_e or tr.entry_m[i] <= free or tr.entry_m[i] < cool_at:
            continue
        taken.append(int(i))
        n, free = n + 1, tr.exit_m[i]
        if tr.net_stressed[i] < 0:
            cool_at, lost = tr.exit_m[i] + cool, lost - tr.net_stressed[i]
            over = stop
        over = over or lost >= LOCK
    return np.array(taken, dtype=int)


def signal(pu: np.ndarray, pd: np.ndarray, thr: float) -> tuple[np.ndarray, np.ndarray]:
    up = (pu >= pd) & (pu >= thr)
    return up | ((pd > pu) & (pd >= thr)), np.where(up, 1, -1)


def picks(
    tr: le.Trades, rows: np.ndarray, pu: np.ndarray, pd: np.ndarray, thr: float, rule: tuple[int, bool, int]
) -> np.ndarray:
    size = max(int(tr.row.max()), int(rows.max()) if len(rows) else 0) + 1
    mask, side = np.zeros(size, bool), np.zeros(size, int)
    m, s = signal(pu, pd, thr)
    mask[rows], side[rows] = m, s
    return seq(tr, np.asarray(np.nonzero(mask[tr.row] & (tr.dir == side[tr.row]))[0]), rule)


def block_days(n: int, b: int) -> tuple[int, int]:
    size = n // BLOCKS
    return size * b, (size * (b + 1) if b < BLOCKS - 1 else n)


def run() -> list[dict[str, Any]]:
    f, outs, days = load()
    n = len(days)
    col = np.arange(len(f["t"])) % ROWS
    ok_row = (col >= 3) & (col <= 54)
    day_of = np.arange(len(f["t"])) // ROWS
    lab = {h: labels(f, h) for h in HS}
    trs = {ex: le.trades(f, o, days) for ex, o in outs.items()}
    chosen: dict[tuple[str, str, tuple[int, bool, int]], list[np.ndarray]] = {}
    for b in range(1, BLOCKS):
        lo, hi = block_days(n, b)
        tr_days = np.arange(0, lo - 1)  # 1-day embargo before the test block
        cut = int(len(tr_days) * 0.8)
        inner, val = tr_days[: cut - 1], tr_days[cut:]
        rows = {
            k: np.nonzero(ok_row & np.isin(day_of, d))[0]
            for k, d in (("inner", inner), ("val", val), ("train", tr_days), ("test", np.arange(lo, hi)))
        }
        for kind in ("M1", "M2"):
            prob: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
            for h in HS:
                for part, fit, pred in (("val", "inner", "val"), ("test", "train", "test")):
                    x_fit = design(f, rows[fit], rows[fit])
                    x_pred = design(f, rows[pred], rows[fit])
                    ps = []
                    for y in lab[h]:
                        mdl = logit(x_fit, y[rows[fit]]) if kind == "M1" else stumps(x_fit, y[rows[fit]])
                        ps.append(predict(mdl, x_pred, kind))
                    prob[(part, h)] = (ps[0], ps[1])
            for ex, tr in trs.items():
                for rule in RULES:
                    best, key = (-np.inf, -np.inf), ("60", 0.6)
                    for h in HS:
                        for thr in THRS:
                            t_v = picks(tr, rows["val"], *prob[("val", h)], thr, rule)
                            net, per = float(tr.net_stressed[t_v].sum()), len(t_v) / max(len(val), 1)
                            score = (float(per >= 0.5), net)
                            if score > best:
                                best, key = score, (h, thr)
                    t_t = picks(tr, rows["test"], *prob[("test", key[0])], key[1], rule)
                    chosen.setdefault((kind, ex, rule), []).append(t_t)
    out = []
    test_days = n - block_days(n, 1)[0]
    for (kind, ex, rule), parts in chosen.items():
        tr = trs[ex]
        taken = np.concatenate(parts) if parts else np.array([], int)
        out.append(evaluate(kind, ex, rule, tr, taken, n, test_days))
    neighbours(out)
    return out


def null_p(tr: le.Trades, taken: np.ndarray, rule: tuple[int, bool, int], runs: int = 2000) -> float:
    rng = np.random.default_rng(le.SEED)
    obs = tr.net_stressed[taken].sum()
    per_day = np.bincount(tr.day[taken], minlength=int(tr.day.max()) + 1)
    win = (tr.t >= 30) & (tr.t <= 285)
    pools = {int(d): np.nonzero(win & (tr.day == d))[0] for d in np.nonzero(per_day)[0]}
    ups = float(np.mean(tr.dir[taken] > 0)) if len(taken) else 0.5
    ge = 0
    for _ in range(runs):
        sel = []
        for d, pool in pools.items():
            side = np.where(rng.random(len(pool)) < ups, 1, -1)
            c = pool[tr.dir[pool] == side]
            if len(c):
                sel.append(rng.choice(c, size=min(len(c), 3 * per_day[d]), replace=False))
        got = seq(tr, np.concatenate(sel), rule) if sel else np.array([], int)
        keep, cnt = [], dict.fromkeys(pools, 0)
        for i in got:
            d = int(tr.day[i])
            if cnt[d] < per_day[d]:
                keep.append(i)
                cnt[d] += 1
        ge += int(tr.net_stressed[np.array(keep, int)].sum() >= obs)
    return (1 + ge) / (runs + 1)


def evaluate(
    kind: str, ex: str, rule: tuple[int, bool, int], tr: le.Trades, taken: np.ndarray, n: int, td: int
) -> dict[str, Any]:
    met = le.metrics(tr, taken, td, VIX_MEDIAN)
    fold = le.folds(tr, taken, n)
    cost = le.STRESS_CHARGES * tr.charges[taken] + tr.fill_stressed[taken]
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
    }
    p = null_p(tr, taken, rule) if all(gates.values()) else None
    gates["null_p01"] = p is not None and p < 0.01
    e, s, c = rule
    return {
        "id": f"R8-{kind}-{ex}-e{e}-s{'y' if s else 'n'}-c{c}",
        "kind": kind,
        "exit": ex,
        "rule": list(rule),
        "folds_positive": fold["positive"],
        "p": p,
        "gates": gates,
        "max_loss_rs": round(float(tr.max_loss[taken].max()), 0) if len(taken) else 0.0,
    } | met


def neighbours(rows: list[dict[str, Any]]) -> None:
    by = {(r["kind"], r["exit"], *r["rule"]): r for r in rows}
    es = (1, 2, 3, 5, 10, 15)
    for r in rows:
        if all(r["gates"].values()):
            k, ex, (e, stop, cool) = str(r["kind"]), str(r["exit"]), r["rule"]
            i = es.index(e)
            nb = [by[(k, ex, es[j], stop, cool)]["net_mean"] > 0 for j in (i - 1, i + 1) if 0 <= j < len(es)]
            r["gates"]["neighbours"] = all(nb)


def main() -> int:
    rows = run()
    for r in rows:
        le.append_trial(
            {
                "id": r["id"],
                "cycle": 1,
                "idea": f"F3 ML {r['kind']} -> {r['exit']}, day rule {r['rule']}",
                "params": {
                    "model": r["kind"],
                    "exit": r["exit"],
                    "max_entries": r["rule"][0],
                    "stop_after_loss": r["rule"][1],
                    "cooloff": r["rule"][2],
                },
                "design_net_stressed": r["net_total"],
                "p_screen": r["p"],
                "source": "P3R v2 R8 EXPLORE (walk-forward out-of-sample, 4 test blocks)",
            }
        )
    (ROOT / "data/lab/r8_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    rows.sort(key=lambda r: -r["net_mean"])
    out = [
        "# R8 BOARD (P3R v2, F3 ML; EXPLORE; DESIGN walk-forward OUT-OF-SAMPLE on 4 test blocks, 290 days;",
        "stressed ₹ per trade, PRE-TAX, [BACKTEST]; null only where every other gate passed)",
        "",
        "| id | trades | per day | net / trade | folds + | high / low VIX | w/o best 5 | null p | max loss ₹ "
        "| failed |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        bad = [k for k, v in r["gates"].items() if not v] or ["none (PASSES the EXPLORE screen)"]
        out.append(
            f"| {r['id']} | {r['trades']} | {r['per_day']} | {r['net_mean']} | {r['folds_positive']}/4 | "
            f"{r['net_mean_high_vix']} / {r['net_mean_low_vix']} | {r['net_mean_wo_best5']} | {r['p']} | "
            f"{r['max_loss_rs']:,.0f} | {', '.join(bad)} |"
        )
    (ROOT / "results/r8_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:14]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
