"""Owner order 5 R20 / R21 / R22 (PLAN.md §PREREG-R20/R21/R22): nested walk-forward. DESIGN only.

python -m lab.nested_more R20|R21|R22 -> trials.jsonl lines, results/r2x_board.md, data/lab/r2x_rows.json
"""

import dataclasses
import math
import sys
from collections.abc import Callable
from typing import Any

import numpy as np

from lab import meta_r18 as mr
from lab import nested_r17 as nr
from lab import portfolio_r14 as pf
from lab import shrink_r19 as sh
from lab import sizing_r15 as sz
from lab import universe as uv
from tools import lab_eval as le

Want = Callable[[le.Trades, np.ndarray], np.ndarray]
Keep = Callable[[le.Trades], np.ndarray]


def daily_series() -> tuple[np.ndarray, np.ndarray]:
    f = pf.matrix("data/lab/matrix.npz")[0]
    g = {k: f[k].reshape(-1, nr.ROWS) for k in ("spot", "ret_open", "gap", "day_hi", "day_lo")}
    opn = g["spot"][:, 0] / (1 + g["ret_open"][:, 0])
    prev_close = opn / (1 + g["gap"][:, 0])
    rng = g["day_hi"][:, -1] - g["day_lo"][:, -1]
    atr10 = np.full(len(rng), math.nan)
    for d in range(10, len(rng)):
        atr10[d] = float(np.nanmean(rng[d - 10 : d]))
    return prev_close, atr10


def trade_custom(
    members: list[uv.Setup], test: np.ndarray, want: Want, keep: Keep | None = None, max_e: int = 3, consensus: int = 0
) -> dict[str, np.ndarray]:
    cols: dict[str, list[np.ndarray]] = {k: [] for k in pf.FIELDS}
    prio, legs = [], []
    for p, s in enumerate(members):
        c = s.cand[np.isin(s.tr.day[s.cand], test)]
        for k in pf.FIELDS:
            cols[k].append(np.asarray(getattr(s.tr, k))[c])
        prio.append(np.full(len(c), p))
        legs.append(np.full(len(c), s.legs))
    if not members or not sum(len(x) for x in prio):
        return {k: np.zeros(0) for k in (*pf.FIELDS, "lots")}
    tr = le.Trades(*(np.concatenate(cols[k]) for k in pf.FIELDS))
    pr, lg = np.concatenate(prio), np.concatenate(legs)
    if keep is not None:
        tr = dataclasses.replace(tr, max_loss=np.where(keep(tr), tr.max_loss, np.inf))
    if consensus > 1:  # §PREREG-R26: >= K different selected setups, same day, same side, within 15 minutes
        votes = np.array(
            [
                len(
                    {
                        int(pr[j])
                        for j in np.nonzero(
                            (tr.day == tr.day[i]) & (tr.dir == tr.dir[i]) & (np.abs(tr.t - tr.t[i]) <= 15)
                        )[0]
                    }
                )
                for i in range(len(pr))
            ]
        )
        tr = dataclasses.replace(tr, max_loss=np.where(votes >= consensus, tr.max_loss, np.inf))
    taken = pf.sequence(tr, pr, max_e)
    per = tr.max_loss[taken]
    n = np.minimum(want(tr, pr)[taken], np.maximum(1, np.floor(pf.CAP / per))).astype(float)
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


def one(tr: le.Trades, pr: np.ndarray) -> np.ndarray:
    return np.ones(len(pr))


def tiers(tr: le.Trades, pr: np.ndarray) -> np.ndarray:
    return np.array(
        [min(sz.lots_for(int(p) + 1, 1.0), 3) for p in pr], dtype=float
    )  # rank tier only; cap applied later


def best_exit(setups: list[uv.Setup], train: np.ndarray) -> list[uv.Setup]:
    """R21: per idea value keep the structure / exit with the best training net; then S2 + S3 as R17."""
    groups: dict[Any, list[uv.Setup]] = {}
    for s in setups:
        groups.setdefault(s.s2_key or s.id, []).append(s)
    chosen = []
    for grp in groups.values():
        scored = []
        for s in grp:
            tk = le.sequence(s.tr, s.cand[np.isin(s.tr.day[s.cand], train)])
            scored.append((float(s.tr.net_stressed[tk].mean()) if len(tk) else -1e18, s))
        chosen.append(max(scored, key=lambda z: z[0])[1])
    return nr.select(chosen, train)


def run(rnd: str) -> int:
    setups = uv.build()
    prev_close, atr10 = daily_series()
    res: dict[str, dict[str, np.ndarray]] = {}
    meta: dict[str, dict[str, Any]] = {}
    plans: dict[str, tuple[str, Any, Any]] = {}
    if rnd == "R20":
        plans = {"R20-a": ("r17", "vol", None), "R20-b": ("mb", "vol", None)}
    elif rnd == "R21":
        plans = {"R21-a": ("best", "one", None), "R21-b": ("best", "tiers", None)}
    elif rnd == "R22":
        plans = {f"R22-n{n}": ("r17", "one", n) for n in (5, 10, 20)}
    elif rnd == "R24":
        plans = {"R24-a": ("r17", "tiers", 20), "R24-b": ("r17", "vol", 20), "R24-c": ("r17", "tiers", 5)}
    elif rnd == "R26":
        plans = {f"R26-{sel}-k{k}": (sel, "one", -k) for sel in ("r17", "mb") for k in (2, 3)}
    elif rnd == "R23":
        plans = {"R23-a": ("r17", "one", None), "R23-b": ("r17", "tiers", None), "R23-c": ("mb", "one", None)}
    for tid, (sel, lots, trend_n) in plans.items():
        parts = []
        for b in range(1, 5):
            test = nr.block(b)
            train = np.arange(nr.block(b - 1)[0] if rnd == "R23" else 0, test[0] - 1)  # R23: the previous block only
            members = {"r17": nr.select, "mb": mr.select_mb, "best": best_exit}[sel](setups, train)
            target = float(np.nanmedian(atr10[train]))
            want: Want = {"one": one, "tiers": tiers}.get(lots, one)
            if lots == "vol":

                def want(tr: le.Trades, pr: np.ndarray, t: float = target) -> np.ndarray:
                    a = atr10[tr.day.astype(int)]
                    return np.where(np.isnan(a), 1.0, np.clip(np.round(2 * t / a), 1, 3))

            keep: Keep | None = None
            votes_k = -trend_n if trend_n and trend_n < 0 else 0  # R26 passes the consensus K as a negative number
            if trend_n and trend_n > 0:

                def keep(tr: le.Trades, n: int = trend_n) -> np.ndarray:
                    d = tr.day.astype(int)
                    past = np.where(d >= n, prev_close[np.maximum(d - n, 0)], np.nan)
                    tr_n = prev_close[d] / past - 1
                    return np.asarray(np.nan_to_num(np.sign(tr_n)) == tr.dir)

            parts.append(trade_custom(members, test, want, keep, consensus=votes_k))
        res[tid] = sh.concat(parts)
        meta[tid] = {
            "idea": f"{rnd} {tid}: selection {sel}, lots {lots}, trend N {trend_n}",
            "params": {"selection": sel, "lots": lots, "trend_n": trend_n},
        }
    titles = {
        "R20": "volatility-targeted lots",
        "R21": "per-setup hold and trail",
        "R22": "daily trend bias",
        "R23": "rolling one-block selection",
        "R24": "combinations of the nested pieces",
        "R26": "consensus voting across the selected setups",
    }
    rc = sh.finish(res, meta, rnd, titles[rnd])
    if rnd == "R22":  # neighbours = the adjacent N (§PREREG-R22): recorded in the rows file
        import json  # noqa: PLC0415

        path = sh.ROOT / "data/lab/r22_rows.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        for i, r in enumerate(rows):
            r["gates"]["neighbours"] = all(rows[j]["net_mean"] > 0 for j in (i - 1, i + 1) if 0 <= j < len(rows))
        path.write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1]))
