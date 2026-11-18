"""N11 P3 Trap Reversal (§11): a breakout bar closed beyond a key level, then within TRAP_BARS a bar closed back
through it the other way. PE after a failed upside break; CE mirror. Only from P3_START (§4.4)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from lab.s3.checks import levels
from lab.s3.data import Day, N
from lab.s3.features import Sig
from lab.s3.registry import FIX, minute


def key_levels(d: Day, sig: Sig, j: int, up: bool) -> list[float]:
    lv = levels(d, sig.f, j)
    names = ("PDH", "ORH") if up else ("PDL", "ORL")
    out = [lv[x] for x in names if x in lv and not math.isnan(lv[x])]
    c = d.base["spot_c"][j]
    step = float(FIX["ROUND_STEP"])
    out.append(math.floor(c / step) * step if up else math.ceil(c / step) * step)
    lb = int(FIX["TRAP_LOOKBACK"])
    if j >= lb:
        out.append(float(np.max(d.base["spot_h"][j - lb : j]) if up else np.min(d.base["spot_l"][j - lb : j])))
    return out


def p3(d: Day, sig: Sig, vol_mult: float, hw: dict[str, Any]) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """(pe, ce) booleans per bar; hw = 3-bar returns of HDFCBANK / ICICIBANK."""
    b, f = d.base, sig.f
    o, h, lo, c = b["spot_o"], b["spot_h"], b["spot_l"], b["spot_c"]
    pe = np.zeros(N, dtype=bool)
    ce = np.zeros(N, dtype=bool)
    start = minute(str(FIX["P3_START"]))
    nb, mina = int(FIX["TRAP_BARS"]), float(FIX["TRAP_MIN_ATR"])
    bmin = float(FIX["BODY_MIN_P2"])
    for t in range(start, N):
        rng = h[t] - lo[t]
        fa = f["fvol_avg"][t]
        if not rng > 0 or not fa > 0 or not b["fut_v"][t] >= vol_mult * fa:
            continue
        body_ok = abs(c[t] - o[t]) >= bmin * rng
        for up, out, sgn in ((True, pe, -1), (False, ce, 1)):
            if not (body_ok and sgn * (c[t] - o[t]) > 0):
                continue
            if not all(sgn * hw[s][t] > 0 for s in hw):
                continue
            for j in range(max(start, t - nb), t):
                atr = f["atr10"][j]
                if not atr > 0:
                    continue
                for lv in key_levels(d, sig, j, up):
                    broke = c[j] > lv + mina * atr if up else c[j] < lv - mina * atr
                    back = c[t] < lv if up else c[t] > lv
                    if broke and back:
                        out[t] = True
                        break
                if out[t]:
                    break
    return pe, ce
