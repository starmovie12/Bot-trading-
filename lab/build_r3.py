"""P3R round 3 (PLAN.md §PREREG-R3): new features and the passive-entry outcomes. DESIGN only.

  python -m lab.build_r3 features  -> data/lab/feat_r3.npz (oi_skew, basis_chg, vix_pct per decision row)
  python -m lab.build_r3 outcomes  -> data/lab/matrix_r3.npz (F_* + the three new; O_XI2|CAP15, O_XI2|CAP15P)
oi_skew = (PE OI change - CE OI change) / (CE + PE OI at 09:29), ATM +- 5 strikes of the nearest monthly expiry,
OI as last known before the decision minute; basis_chg = basis now - basis at 09:30; vix_pct = vix_chg / VIX open.
Passive entry (CAP15P): a buy limit at the last closed option bar's close, filled only when a bar in the next 3 minutes
trades THROUGH it (low < limit), at the limit; no fill -> no trade; the entry pays no half spread (exit pays it).
"""

import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from lab import build_r2 as b2
from lab import data
from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
ROWS, N = 61, eor.N


def oi_day(day: dt.date, spot: np.ndarray) -> np.ndarray:
    tb = data.read_day(
        ROOT / "data/banknifty/repo", "options", day, columns=["expiry_date", "strike", "option_type", "ts_open", "oi"]
    ).to_pylist()
    out = np.full(ROWS, math.nan)
    if not tb:
        return out
    near = min(r["expiry_date"] for r in tb if r["expiry_date"] >= day)
    oi: dict[tuple[float, str], list[float]] = {}
    for r in tb:
        m = (r["ts_open"].hour - 9) * 60 + r["ts_open"].minute - 15
        if r["expiry_date"] == near and 0 <= m < N and r["oi"] is not None:
            oi.setdefault((r["strike"], r["option_type"]), [math.nan] * N)[m] = float(r["oi"])
    for a in oi.values():  # forward fill: the last known OI
        for m in range(1, N):
            if math.isnan(a[m]):
                a[m] = a[m - 1]
    for j in range(ROWS):
        t = 15 + 5 * j
        if math.isnan(spot[j]):
            continue
        atm = round(spot[j] / 100) * 100
        tot = {"CE": [0.0, 0.0], "PE": [0.0, 0.0]}
        for k in range(-5, 6):
            for typ in ("CE", "PE"):
                ser = oi.get((float(atm + 100 * k), typ))
                if ser and not math.isnan(ser[14]) and not math.isnan(ser[t - 1]):
                    tot[typ][0] += ser[14]
                    tot[typ][1] += ser[t - 1]
        base = tot["CE"][0] + tot["PE"][0]
        if base > 0:
            out[j] = ((tot["PE"][1] - tot["PE"][0]) - (tot["CE"][1] - tot["CE"][0])) / base
    return out


def features() -> dict[str, np.ndarray]:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    m = np.load(ROOT / "data/lab/matrix.npz")
    spot = m["F_spot"].reshape(-1, ROWS)
    basis = m["F_basis"].reshape(-1, ROWS)
    oi = np.vstack([oi_day(dt.date.fromisoformat(d), spot[i]) for i, d in enumerate(days)])
    vix, chg = m["F_vix"], m["F_vix_chg"]
    out = {"oi_skew": oi.ravel(), "basis_chg": (basis - basis[:, :1]).ravel(), "vix_pct": chg / (vix - chg)}
    np.savez_compressed(ROOT / "data/lab/feat_r3.npz", **out)
    return out


def passive_day(d: eor.Day, base: int, spot: np.ndarray, rv30: np.ndarray) -> list[dict[str, float]]:
    ih, il, io = [b.h for b in d.index], [b.l for b in d.index], [b.o for b in d.index]
    out: list[dict[str, float]] = []
    for j in range(ROWS):
        t, s0 = 15 + 5 * j, float(spot[j])
        if math.isnan(s0):
            continue
        atm = round(s0 / 100) * 100
        r = max(0.0015, float(rv30[j]) * math.sqrt(60) if not math.isnan(float(rv30[j])) else 0.0) * s0
        for side in (1, -1):
            typ = "CE" if side > 0 else "PE"
            pick = None
            for k in range(11):
                a = d.opts.get((float(atm + side * 100 * k), typ))
                lim = a["c"][t - 1] if a else math.nan
                if a and lim > 0 and lim * d.lot <= b2.CAP_RS:
                    pick = (float(atm + side * 100 * k), a, lim)
                    break
            if pick is None:
                continue
            strike, a, lim = pick
            e = next((m for m in range(t, min(t + 3, b2.FF)) if a["live"][m] and a["l"][m] < lim), -1)
            if e < 0:
                continue  # never traded through the limit: no fill, no trade
            ent_ix = io[e] if not math.isnan(io[e]) else s0
            x, why = b2.index_exit(ih, il, e, side, ent_ix, r, "XI2")
            px, stale = b2.opt_price(a, x, "low" if why in ("stop", "breakeven", "trail") else "close")
            if math.isnan(px):
                continue
            lows = [v for v in a["l"][e : x + 1] if not math.isnan(v)]
            highs = [v for v in a["h"][e : x + 1] if not math.isnan(v)]
            out.append(
                {
                    "row": base + j,
                    "dir": side,
                    "t": t,
                    "entry_m": e,
                    "exit_m": x,
                    "entry": lim,
                    "exit": px,
                    "legs": 1,
                    "long_in": lim,
                    "long_out": px,
                    "short_in": 0.0,
                    "short_out": 0.0,
                    "reason": b2.REASON[why],
                    "mae": min(lows, default=lim) - lim,
                    "mfe": max(highs, default=lim) - lim,
                    "stale_exit": float(stale),
                    "strike": strike,
                    "passive": 1.0,
                }
            )
    return out


def outcomes() -> dict[str, int]:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    m, r2, f3 = (np.load(ROOT / f"data/lab/{n}.npz") for n in ("matrix", "matrix_r2", "feat_r3"))
    arrays: dict[str, Any] = {k: m[k] for k in m.files if k.startswith("F_")}
    arrays |= {f"F_{k}": f3[k] for k in f3.files}
    arrays |= {k: r2[k] for k in r2.files if k.startswith("O_XI2|CAP15_")}
    spot, rv30 = m["F_spot"].reshape(-1, ROWS), m["F_rv30"].reshape(-1, ROWS)
    rows: list[dict[str, float]] = []
    for i, ds in enumerate(days):
        d = eor.load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(ds), lots)
        rows += passive_day(d, i * ROWS, spot[i], rv30[i])
    for col in rows[0]:
        arrays[f"O_XI2|CAP15P_{col}"] = np.array([r[col] for r in rows], dtype=float)
    np.savez_compressed(ROOT / "data/lab/matrix_r3.npz", **arrays)
    return {"XI2|CAP15": len(r2["O_XI2|CAP15_row"]), "XI2|CAP15P": len(rows)}


def main(argv: list[str]) -> int:
    if argv[:1] == ["features"]:
        for k, v in features().items():
            print(k, np.round(np.nanpercentile(v, [1, 5, 10, 25, 50, 75, 90, 95, 99]), 5), int(np.isnan(v).sum()))
        return 0
    if argv[:1] == ["outcomes"]:
        print(outcomes())
        return 0
    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
