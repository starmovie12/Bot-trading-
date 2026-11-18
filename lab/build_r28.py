"""Owner order 5 R28 (PLAN.md §PREREG-R28): classic indicators on 1-minute index bars. DESIGN only, no look-ahead.

  python -m lab.build_r28 -> data/lab/matrix_r28.npz (matrix_r9 + F_rsi14, F_bbz20, F_macd_h, F_macd_hp, F_st_dir2/3/4,
                             F_st_prev2/3/4), prints the scales
Every value at a decision row uses only the 1-minute bars that closed before the decision minute (same day only).
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


def ema(x: np.ndarray, n: int) -> np.ndarray:
    out, a, prev = np.full(len(x), math.nan), 2 / (n + 1), math.nan
    for i, v in enumerate(x):
        if math.isnan(v):
            out[i] = prev
            continue
        prev = v if math.isnan(prev) else a * v + (1 - a) * prev
        out[i] = prev
    return out


def rsi(c: np.ndarray, n: int = 14) -> np.ndarray:
    d = np.diff(c, prepend=np.nan)
    up, dn = np.where(d > 0, d, 0.0), np.where(d < 0, -d, 0.0)
    out, au, ad = np.full(len(c), math.nan), math.nan, math.nan
    for i in range(1, len(c)):
        if i == n:
            au, ad = float(np.nanmean(up[1 : n + 1])), float(np.nanmean(dn[1 : n + 1]))
        elif i > n:
            au, ad = (au * (n - 1) + up[i]) / n, (ad * (n - 1) + dn[i]) / n
        if i >= n:
            out[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return out


def supertrend(h: np.ndarray, lo: np.ndarray, c: np.ndarray, n: int, mult: float) -> np.ndarray:
    tr = np.maximum(h - lo, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(lo - np.roll(c, 1))))
    tr[0] = h[0] - lo[0]
    atr = np.full(len(c), math.nan)
    for i in range(n - 1, len(c)):
        atr[i] = float(np.nanmean(tr[i - n + 1 : i + 1])) if i == n - 1 else (atr[i - 1] * (n - 1) + tr[i]) / n
    mid = (h + lo) / 2
    up_b, dn_b, dirn = mid - mult * atr, mid + mult * atr, np.zeros(len(c))
    for i in range(1, len(c)):
        if math.isnan(atr[i]):
            continue
        if not math.isnan(atr[i - 1]):
            up_b[i] = max(up_b[i], up_b[i - 1]) if c[i - 1] > up_b[i - 1] else up_b[i]
            dn_b[i] = min(dn_b[i], dn_b[i - 1]) if c[i - 1] < dn_b[i - 1] else dn_b[i]
        prev = dirn[i - 1] if dirn[i - 1] != 0 else 1
        dirn[i] = 1 if c[i] > dn_b[i] else -1 if c[i] < up_b[i] else prev
    return dirn


def day_feats(day: dt.date) -> dict[str, np.ndarray]:
    tb = data.read_day(
        ROOT / "data/banknifty/repo", "spot_1m", day, columns=["ts_open", "o", "h", "l", "c"]
    ).to_pylist()
    g = {k: np.full(N, math.nan) for k in ("h", "l", "c")}
    for r in tb:
        m = (r["ts_open"].hour - 9) * 60 + r["ts_open"].minute - 15
        if 0 <= m < N:
            g["h"][m], g["l"][m], g["c"][m] = r["h"], r["l"], r["c"]
    c = g["c"]
    sma = np.array([np.nanmean(c[max(0, i - 19) : i + 1]) if i >= 19 else math.nan for i in range(N)])
    sd = np.array([np.nanstd(c[max(0, i - 19) : i + 1], ddof=1) if i >= 19 else math.nan for i in range(N)])
    macd = ema(c, 12) - ema(c, 26)
    hist = macd - ema(macd, 9)
    hist[:34] = math.nan
    out = {"rsi14": rsi(c), "bbz20": (c - sma) / sd, "macd_h": hist / c}
    for mult in (2, 3, 4):
        out[f"st_dir{mult}"] = supertrend(g["h"], g["l"], c, 10, float(mult))
    return out


def main() -> int:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    m = np.load(ROOT / "data/lab/matrix_r9.npz")
    arrays: dict[str, Any] = {k: m[k] for k in m.files}
    cols: dict[str, list[float]] = {}
    for ds in days:
        fd = day_feats(dt.date.fromisoformat(ds))
        for j in range(ROWS):
            t = 15 + 5 * j
            for k, v in fd.items():  # the value of the last bar that closed before minute t, and the one before it
                cols.setdefault(k, []).append(float(v[t - 1]))
                cols.setdefault(k + "_prev", []).append(float(v[t - 2]) if t >= 2 else math.nan)
    for k, vals in cols.items():
        arrays[f"F_{k}"] = np.array(vals)
    np.savez_compressed(ROOT / "data/lab/matrix_r28.npz", **arrays)
    t = m["F_t"]
    for k in ("rsi14", "bbz20", "macd_h", "st_dir3"):
        v = arrays[f"F_{k}"][(t >= 45) & (t <= 285)]
        print(k, np.round(np.nanpercentile(v, [5, 10, 25, 50, 75, 90, 95]), 6), int(np.isnan(v).sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
