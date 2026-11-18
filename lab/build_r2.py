"""P3R round 2 outcomes (PLAN.md §PREREG-R2): index-based exits on the engine-of-record data reader.

  python -m lab.build_r2 -> data/lab/matrix_r2.npz (F_* copied from matrix.npz; O_<exit>|<structure>_<column>)
Every DESIGN decision row (09:30 .. 14:30, 5 min), both sides, structures ATM / CAP15, exits XI1 / XI2. DESIGN only.
"""

import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
FF, CAP_RS, ROWS = eor.FORCE_FLAT, 15_000.0, 61
REASON = {"stop": 1, "breakeven": 2, "target": 3, "time": 5, "force_flat": 6, "trail": 8}
KEYS = [f"{x}|{s}" for x in ("XI1", "XI2") for s in ("ATM", "CAP15")]


def nz(x: float) -> bool:
    return not math.isnan(x)


def index_exit(ih: list[float], il: list[float], e: int, side: int, ent: float, r: float, ex: str) -> tuple[int, str]:
    if ex == "XH":  # §PREREG-R7: no index stop, hold to force-flat (loss bounded by the premium)
        return FF, "force_flat"
    wide = ex == "XH2"  # §PREREG-R7: index stop -2R only, no break-even / trail / target
    stop, best, be_on, trail = ent - side * r * (2 if wide else 1), ent, False, False
    for m in range(e, FF + 1):
        h, lo = ih[m], il[m]
        if nz(h) and nz(lo):
            worst, good = (lo, h) if side > 0 else (h, lo)
            if side * (worst - stop) <= 0:
                return m, "trail" if trail else ("breakeven" if be_on else "stop")
            if ex == "XI1" and side * (good - ent) >= 2 * r:
                return m, "target"
            best = max(best, good) if side > 0 else min(best, good)
            if not wide and not be_on and side * (best - ent) >= r:
                be_on, stop = True, ent
            if ex == "XI2" and side * (best - ent) >= 2 * r and side * (best - side * r - stop) > 0:
                stop, trail = best - side * r, True
        if ex == "XI1" and m - e + 1 >= 120:
            return m, "time"
    return FF, "force_flat"


def opt_price(a: dict[str, list[float]], m: int, kind: str) -> tuple[float, bool]:
    v = a["l" if kind == "low" else "c"][m]
    if nz(v) and a["live"][m]:
        return v, False
    back = next((a["c"][k] for k in range(m, -1, -1) if nz(a["c"][k])), math.nan)
    return (v if nz(v) else back), True


def entry(a: dict[str, list[float]], t: int) -> int:
    return next((m for m in range(t, min(t + 3, FF)) if a["live"][m] and a["o"][m] > 0), -1)


def day_outcomes(
    d: eor.Day,
    base: int,
    spot: np.ndarray,
    rv30: np.ndarray,
    exits: tuple[str, ...] = ("XI1", "XI2"),
    structs: tuple[str, ...] = ("ATM", "CAP15"),
) -> dict[str, list[dict[str, float]]]:
    ih = [b.h for b in d.index]
    il = [b.l for b in d.index]
    io = [b.o for b in d.index]
    out: dict[str, list[dict[str, float]]] = {f"{x}|{s}": [] for x in exits for s in structs}
    for j in range(ROWS):
        t, s0 = 15 + 5 * j, float(spot[j])
        if not nz(s0):
            continue
        atm = round(s0 / 100) * 100
        r = max(0.0015, float(rv30[j]) * math.sqrt(60) if nz(float(rv30[j])) else 0.0) * s0
        for side in (1, -1):
            typ = "CE" if side > 0 else "PE"
            for struct in structs:
                pick = None
                for k in range(11 if struct == "CAP15" else 1):  # ATM / ITM2: one strike; CAP15: walk OTM
                    key = (float(atm + side * 100 * k - (side * 200 if struct == "ITM2" else 0)), typ)
                    ok = key in d.opts and (e := entry(d.opts[key], t)) >= 0
                    if ok and (struct != "CAP15" or d.opts[key]["o"][e] * d.lot <= CAP_RS):
                        pick = (key, e)
                        break
                if pick is None:
                    continue
                (strike, _), e = pick
                a = d.opts[pick[0]]
                ent_ix = io[e] if nz(io[e]) else s0
                for ex in exits:
                    x, why = index_exit(ih, il, e, side, ent_ix, r, ex)
                    px, stale = opt_price(a, x, "low" if why in ("stop", "breakeven", "trail") else "close")
                    if not nz(px):
                        continue
                    lows = [v for v in a["l"][e : x + 1] if nz(v)]
                    highs = [v for v in a["h"][e : x + 1] if nz(v)]
                    en = a["o"][e]
                    out[f"{ex}|{struct}"].append(
                        {
                            "row": base + j,
                            "dir": side,
                            "t": t,
                            "entry_m": e,
                            "exit_m": x,
                            "entry": en,
                            "exit": px,
                            "legs": 1,
                            "long_in": en,
                            "long_out": px,
                            "short_in": 0.0,
                            "short_out": 0.0,
                            "reason": REASON[why],
                            "mae": min(lows, default=en) - en,
                            "mfe": max(highs, default=en) - en,
                            "stale_exit": float(stale),
                            "strike": strike,
                        }
                    )
    return out


def main(argv: list[str]) -> int:
    mode = argv[0] if argv[:1] in (["r7"], ["r13"]) else "r2"  # §PREREG-R7 / §PREREG-R13 builds
    exits, structs = {"r7": (("XH", "XH2"), ("CAP15",)), "r13": (("XH", "XH2"), ("ITM2",))}.get(
        mode, (("XI1", "XI2"), ("ATM", "CAP15"))
    )
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    m = np.load(ROOT / "data/lab/matrix.npz")
    feats: dict[str, Any] = {k: m[k] for k in m.files if k.startswith("F_")}
    spot, rv30 = feats["F_spot"].reshape(-1, ROWS), feats["F_rv30"].reshape(-1, ROWS)
    allout: dict[str, list[dict[str, float]]] = {f"{x}|{s}": [] for x in exits for s in structs}
    for i, ds in enumerate(days):
        d = eor.load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(ds), lots)
        for k, v in day_outcomes(d, i * ROWS, spot[i], rv30[i], exits, structs).items():
            allout[k] += v
    arrays = dict(feats)
    for k, rows in allout.items():
        for col in rows[0]:
            arrays[f"O_{k}_{col}"] = np.array([r[col] for r in rows], dtype=float)
    np.savez_compressed(ROOT / f"data/lab/matrix_{mode}.npz", **arrays)
    print({k: len(v) for k, v in allout.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
