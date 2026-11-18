"""Owner order 5 R29 / R30 features: index vs HDFCBANK + ICICIBANK divergence; near-futures volume surge. DESIGN only.

  python -m lab.build_r29 -> data/lab/matrix_r29.npz (matrix_r9 + F_div, F_fvol_ratio, F_fret15), prints the scales
div = index return since the open - the mean of the two stocks' returns since their opens (as of the last closed bar);
fvol_ratio = near-futures volume of the last 15 closed minutes / its mean 15-minute volume earlier in the same day
(>= 30 minutes of history, else NaN); fret15 = the near-futures 15-minute return.
"""

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from lab import data

ROOT = Path(__file__).resolve().parent.parent
ROWS, N = 61, 375


def grid(tb: Any, cols: tuple[str, ...]) -> dict[str, np.ndarray]:
    out = {c: np.full(N, math.nan) for c in cols}
    for r in tb.to_pylist():
        m = (r["ts_open"].hour - 9) * 60 + r["ts_open"].minute - 15
        if 0 <= m < N:
            for c in cols:
                out[c][m] = r[c] if r[c] is not None else math.nan
    return out


def first(x: np.ndarray) -> float:
    ok = x[~np.isnan(x)]
    return float(ok[0]) if len(ok) else math.nan


def last_before(x: np.ndarray, t: int) -> float:
    ok = x[:t][~np.isnan(x[:t])]
    return float(ok[-1]) if len(ok) else math.nan


def main() -> int:
    repo = ROOT / "data/banknifty/repo"
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    m = np.load(ROOT / "data/lab/matrix_r9.npz")
    arrays: dict[str, Any] = {k: m[k] for k in m.files}
    cols: dict[str, list[float]] = {"div": [], "fvol_ratio": [], "fret15": []}
    for ds in days:
        day = dt.date.fromisoformat(ds)
        spot = grid(data.read_day(repo, "spot_1m", day, columns=["ts_open", "c"]), ("c",))["c"]
        st = [
            grid(data.read_day(repo, "stock_1m", day, underlying=s, columns=["ts_open", "c"]), ("c",))["c"]
            for s in ("HDFCBANK", "ICICIBANK")
        ]
        ft = data.read_day(repo, "fut_1m", day, columns=["expiry_date", "ts_open", "c", "v"])
        near = min(e for e in set(ft["expiry_date"].to_pylist()) if e >= day)
        fut = grid(ft.filter(np.array([e == near for e in ft["expiry_date"].to_pylist()])), ("c", "v"))
        for j in range(ROWS):
            t = 15 + 5 * j
            r_ix = last_before(spot, t) / first(spot) - 1
            r_st = np.mean([last_before(s, t) / first(s) - 1 for s in st])
            cols["div"].append(float(r_ix - r_st))
            v = np.nan_to_num(fut["v"][:t])
            past = v[: t - 15]
            cols["fvol_ratio"].append(
                float(v[t - 15 : t].sum() / (past.sum() / (len(past) / 15))) if t >= 45 and past.sum() > 0 else math.nan
            )
            c15 = last_before(fut["c"], t - 15) if t >= 16 else math.nan
            cols["fret15"].append(float(last_before(fut["c"], t) / c15 - 1) if not math.isnan(c15) else math.nan)
    for k, vals in cols.items():
        arrays[f"F_{k}"] = np.array(vals)
    np.savez_compressed(ROOT / "data/lab/matrix_r29.npz", **arrays)
    t = m["F_t"]
    for k in cols:
        v = arrays[f"F_{k}"][(t >= 45) & (t <= 285)]
        print(k, np.round(np.nanpercentile(v, [5, 10, 25, 50, 75, 90, 95]), 5), int(np.isnan(v).sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
