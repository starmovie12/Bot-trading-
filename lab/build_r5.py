"""P3R round 5 (PLAN.md §PREREG-R5): prior-day features per decision row. DESIGN only, no look-ahead.

  python -m lab.build_r5 -> data/lab/matrix_r5.npz (matrix_r2.npz + F_prev_*), prints the feature scales
The prior day is the previous DESIGN day only when it is at most 4 calendar days back (else NaN: the G3 gap).
prev_hi / prev_lo = the prior day's high / low through 14:30 (its last decision row); prev_close = the true prior close
(today's open / (1 + gap)); prev_cl = (prev_close - prev_lo) / (prev_hi - prev_lo); prev_ret = prev_close / prior
open - 1; prev_rr = prior range / median range of the 10 days before it.
"""

import datetime as dt
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ROWS = 61


def main() -> int:
    days = [dt.date.fromisoformat(d) for d in json.loads((ROOT / "data/lab/split.json").read_text())["design"]]
    m = np.load(ROOT / "data/lab/matrix_r2.npz")
    g = {k: m[f"F_{k}"].reshape(-1, ROWS) for k in ("spot", "ret_open", "gap", "day_hi", "day_lo")}
    opn = g["spot"][:, 0] / (1 + g["ret_open"][:, 0])  # today's open
    close_prev = opn / (1 + g["gap"][:, 0])  # the prior day's true close
    hi, lo = g["day_hi"][:, -1], g["day_lo"][:, -1]  # through 14:30
    rng = (hi - lo) / opn
    n = len(days)
    prev = {k: np.full(n, np.nan) for k in ("hi", "lo", "close", "cl", "ret", "rr")}
    for i in range(1, n):
        if (days[i] - days[i - 1]).days > 4:
            continue
        prev["hi"][i], prev["lo"][i], prev["close"][i] = hi[i - 1], lo[i - 1], close_prev[i]
        prev["cl"][i] = (close_prev[i] - lo[i - 1]) / (hi[i - 1] - lo[i - 1])
        prev["ret"][i] = close_prev[i] / opn[i - 1] - 1
        if i >= 11:
            prev["rr"][i] = rng[i - 1] / np.median(rng[i - 11 : i - 1])
    arrays: dict[str, Any] = {k: m[k] for k in m.files}
    for k, v in prev.items():
        arrays[f"F_prev_{k}"] = np.repeat(v, ROWS)
    np.savez_compressed(ROOT / "data/lab/matrix_r5.npz", **arrays)
    for k in ("cl", "ret", "rr"):
        print(k, np.round(np.nanpercentile(prev[k], [5, 10, 25, 50, 75, 90, 95]), 4), int(np.isnan(prev[k]).sum()))
    up = g["spot"] > np.repeat(prev["hi"][:, None], ROWS, axis=1)
    print("share of rows above prev_hi", round(float(np.nanmean(up)), 3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
