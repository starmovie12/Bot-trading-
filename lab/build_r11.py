"""P3R v2 round 11 (PLAN.md §PREREG-R11): F2 implied vs realised move, from the opening ATM straddle. DESIGN only.

  python -m lab.build_r11 -> data/lab/matrix_r11.npz (matrix_r9 + F_impl_ratio, F_rv_iv), prints the scales
straddle0 = ATM CE + ATM PE close at 09:29 (nearest monthly; ATM by the index close at 09:29) = the market's expected
absolute move to expiry; per trading day m_d = straddle0 / sqrt(max(1, dte x 5 / 7)). impl_ratio = abs(spot - open) /
m_d; rv_iv = (rv30 x sqrt(375)) / (m_d / spot) (realised daily vol from the last 30 one-minute returns vs implied).
"""

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
ROWS = 61


def main() -> int:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    m = np.load(ROOT / "data/lab/matrix_r9.npz")
    f = {k[2:]: m[k] for k in m.files if k.startswith("F_")}
    straddle = np.full(len(days), math.nan)
    for i, ds in enumerate(days):
        d = eor.load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(ds), lots)
        s14 = d.index[14].c
        if math.isnan(s14):
            continue
        atm = float(round(s14 / 100) * 100)
        ce, pe = d.opts.get((atm, "CE")), d.opts.get((atm, "PE"))
        if ce and pe and not math.isnan(ce["c"][14]) and not math.isnan(pe["c"][14]):
            straddle[i] = ce["c"][14] + pe["c"][14]
    s0 = np.repeat(straddle, ROWS)
    md = s0 / np.sqrt(np.maximum(1.0, f["dte"] * 5 / 7))
    opn = f["spot"] / (1 + f["ret_open"])
    arrays: dict[str, Any] = {k: m[k] for k in m.files}
    arrays["F_impl_ratio"] = np.abs(f["spot"] - opn) / md
    arrays["F_rv_iv"] = (f["rv30"] * math.sqrt(375)) / (md / f["spot"])
    np.savez_compressed(ROOT / "data/lab/matrix_r11.npz", **arrays)
    t = f["t"]
    for k in ("impl_ratio", "rv_iv"):
        v = arrays[f"F_{k}"][(t >= 45) & (t <= 255)]
        print(k, np.round(np.nanpercentile(v, [10, 25, 50, 75, 90, 95]), 3), int(np.isnan(v).sum()))
    print(
        "days with a straddle",
        int(np.isfinite(straddle).sum()),
        "median straddle pts",
        round(float(np.nanmedian(straddle)), 1),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
