"""S3 check library K01-K29 (§8, §9) and scorecard (§10.1). Shadow by default: recorded on every signal; a check
blocks only where §7.0 / a round's flag says so. Each check sees data known at decision_ts = t + 1 min only."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

import numpy as np
import pyarrow.compute as pc

from lab.data import BANK_STOCKS
from lab.s3 import costs
from lab.s3.data import F64, Day
from lab.s3.engine import dec, k03_ok, k05_ok, opt_atr5
from lab.s3.features import Sig
from lab.s3.registry import CHK, COST, FIX, SCORE, Cfg, minute

G, R, NA = "GREEN", "RED", "NA"
GROUPS = {
    "order_flow": ("K10", "K11", "K12"),
    "technical": ("K13", "K14", "K16", "K29"),
    "directional": ("K17", "K18"),
    "sentiment": ("K19", "HW", "K20"),
}


def known_bars(tb: Any, t: int) -> dict[str, F64]:
    """3m/15m bars usable at decision bar t: is_partial == False and available_from_ts <= t + 1 (§4.2)."""
    m = pc.and_(pc.invert(tb["is_partial"]), pc.less_equal(tb["avail_m"], t + 1))
    k = tb.filter(m)
    return {c: k[c].to_numpy().astype(np.float64) for c in ("o", "h", "l", "c", "avail_m")}


def wilder(x: F64, n: int) -> F64:
    out = np.full(x.size, math.nan)
    if x.size < n:
        return out
    out[n - 1] = float(np.mean(x[:n]))
    for i in range(n, x.size):
        out[i] = out[i - 1] + (x[i] - out[i - 1]) / n
    return out


def adx(h: F64, lo: F64, c: F64, n: int) -> float:
    if c.size < 2 * n + 1:
        return math.nan
    up, dn = np.diff(h), -np.diff(lo)
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum.reduce([h[1:] - lo[1:], np.abs(h[1:] - c[:-1]), np.abs(lo[1:] - c[:-1])])
    atr = wilder(tr, n)
    with np.errstate(invalid="ignore", divide="ignore"):
        pdi = 100 * wilder(pdm, n) / atr
        ndi = 100 * wilder(ndm, n) / atr
        dx = 100 * np.abs(pdi - ndi) / (pdi + ndi)
    dx = dx[~np.isnan(dx)]
    a = wilder(dx, n)
    return float(a[-1]) if a.size and not np.isnan(a[-1]) else math.nan


def rsi(c: F64, n: int) -> float:
    if c.size < n + 1:
        return math.nan
    d = np.diff(c)
    ag, al = wilder(np.clip(d, 0, None), n), wilder(np.clip(-d, 0, None), n)
    if np.isnan(ag[-1]):
        return math.nan
    return 100.0 if al[-1] == 0 else float(100 - 100 / (1 + ag[-1] / al[-1]))


def tf_dir(c: F64) -> int:
    """Direction of a timeframe: close vs EMA9 of its closes and EMA9 rising (+1 / -1 / 0)."""
    n = int(FIX["EMA_FAST"])
    if c.size < n + 1:
        return 0
    a = 2 / (n + 1)
    e = [float(c[0])]
    for v in c[1:]:
        e.append(e[-1] + a * (float(v) - e[-1]))
    if c[-1] > e[-1] and e[-1] > e[-2]:
        return 1
    if c[-1] < e[-1] and e[-1] < e[-2]:
        return -1
    return 0


@lru_cache(maxsize=4096)
def cost_per_unit(premium: float, lot: int, day: Any) -> float:
    """COST_PER_UNIT_1LOT = SPREAD_FULL_RS + 2 x SLIP_RS + 1-lot round-trip charges / lot_size (§4.3)."""
    p = dec(premium)
    ch = costs.round_trip(p, p, lot, day)["total"]
    return float(COST["SPREAD_FULL_RS"]) + 2 * float(COST["SLIP_RS"]) + float(ch) / lot


def levels(d: Day, f: dict[str, F64], t: int) -> dict[str, float]:
    b, p = d.base, d.prev
    out = {
        "PDH": float(np.nanmax(p["spot_h"])),
        "PDL": float(np.nanmin(p["spot_l"])),
        "PDC": float(p["spot_c"][~np.isnan(p["spot_c"])][-1]),
    }
    if t >= minute(str(FIX["OR_END"])):
        w = slice(minute(str(FIX["OR_START"])), minute(str(FIX["OR_END"])) + 1)
        out["ORH"], out["ORL"] = float(np.nanmax(b["spot_h"][w])), float(np.nanmin(b["spot_l"][w]))
    bs = f["basis"][t]
    v, s = f["vwap"][t], f["sigma"][t]
    for name, mult in (("VWAP", 0), ("U1", 1), ("U2", 2), ("D1", -1), ("D2", -2)):
        out[name] = v + mult * s - bs
    out["WALL_C"], out["WALL_P"] = float(b["cm_call_wall"][t]), float(b["cm_put_wall"][t])
    return out


def next_level(d: Day, f: dict[str, F64], t: int, side: str) -> float:
    spot, atr = d.base["spot_c"][t], f["atr10"][t]
    gap = float(FIX["LEVEL_IGNORE_ATR"]) * atr
    step = float(FIX["ROUND_STEP"])
    lv = [x for x in levels(d, f, t).values() if not math.isnan(x)]
    if side == "CE":
        lv.append(math.floor((spot + gap) / step) * step + step)
        ahead = [x - spot for x in lv if x > spot + gap]
    else:
        lv.append(math.ceil((spot - gap) / step) * step - step)
        ahead = [spot - x for x in lv if x < spot - gap]
    return min(ahead) if ahead else math.inf


def shadow(d: Day, sig: Sig, t: int, side: str, k: int, sl_pts: float, pattern: str, cfg: Cfg) -> dict[str, Any]:
    """All checks for one signal; values GREEN / RED / NA (+ a few SHADOW numbers)."""
    f, b = sig.f, d.base
    up = side == "CE"
    sg = 1 if up else -1
    out: dict[str, Any] = {}
    b3 = known_bars(d.b3, t)
    b15 = known_bars(d.b15, t)
    a1 = adx(b3["h"], b3["l"], b3["c"], int(CHK["K01_ADX_N"]))
    out["K01"] = NA if math.isnan(a1) else (G if a1 >= CHK["K01_ADX_GREEN"] else R if a1 <= CHK["K01_ADX_RED"] else NA)
    out["K01_adx"] = a1
    pdc = float(d.prev["spot_c"][~np.isnan(d.prev["spot_c"])][-1])
    gap = abs(b["spot_o"][0] / pdc - 1)
    out["K02"] = R if gap >= CHK["K02_GAP"] and t + 1 <= minute(str(FIX["K02_WAIT"])) else G
    k3 = k03_ok(d)
    out["K03"] = NA if k3 is None else (G if k3 else R)
    rv = float(d.meta.get("rv20", math.nan))
    aiv = b["cm_atm_iv"][t]
    out["K04"] = NA if math.isnan(rv) or math.isnan(aiv) else (G if aiv <= CHK["K04_IV_RV"] * rv else R)
    has_k = k >= 0
    if has_k:
        k5 = k05_ok(d, t, side, k, sl_pts)
        out["K05"] = NA if k5 is None else (G if k5 else R)
        v, vb = d.opt["v"][k], d.opt["vbase"][k]
        nb = int(CHK["K06_BARS"])
        out["K06"] = (
            (G if np.nanmean(v[t - nb + 1 : t + 1]) >= CHK["K06_VOL_MULT"] * vb[t] else R)
            if d.vbase_ok[k, t] and vb[t] > 0
            else NA
        )
        out["K07"] = _k07(d, k, t, side)
        oc, oh, ol = d.opt["c"][k], d.opt["h"][k], d.opt["l"][k]
        nb8 = int(CHK["K08_BARS"])
        rise = oc[t] / oc[t - nb8] - 1 if t >= nb8 and oc[t - nb8] > 0 else math.nan
        a5 = opt_atr5((oh - ol).tolist(), d.stale[k].tolist(), t)
        pull = (
            t >= nb8 and np.nanmax(oh[t - nb8 : t]) - np.nanmin(ol[t - nb8 + 1 : t + 1]) >= CHK["K08_PULLBACK_ATR"] * a5
        )
        out["K08"] = NA if math.isnan(rise) else (G if rise <= CHK["K08_RISE_MAX"] or pull else R)
        nb10 = int(CHK["K10_BARS"])
        pct = np.diff(oc[t - nb10 - 1 : t + 1]) / oc[t - nb10 - 1 : t] if t > nb10 else np.array([math.nan])
        out["K10"] = (
            NA
            if np.isnan(pct).any()
            else (G if pct[-1] > 0 and pct[-1] >= CHK["K10_MULT"] * np.mean(np.abs(pct[:-1])) else R)
        )
    else:
        for x in ("K05", "K06", "K07", "K08", "K10"):
            out[x] = NA
    o, h, lo, c = b["spot_o"][t], b["spot_h"][t], b["spot_l"][t], b["spot_c"][t]
    rng = h - lo
    wick = (h - max(o, c)) if up else (min(o, c) - lo)
    out["K09"] = NA if not rng > 0 else (G if wick <= CHK["K09_WICK_MAX"] * rng else R)
    fv, fa, vw = b["fut_v"][t], f["fvol_avg"][t], f["vwap"][t]
    out["K11"] = (
        NA
        if math.isnan(fv) or not fa > 0
        else (G if fv >= CHK["K11_MULT"] * fa and sg * (b["fut_c"][t] - vw) > 0 else R)
    )
    out["K12"] = _k12(b, t, up, int(cfg["BREAKOUT_LOOKBACK"]))
    nb13 = int(CHK["K13_BARS"])
    if b3["c"].size > nb13:
        ref = np.max(b3["h"][-nb13 - 1 : -1]) if up else np.min(b3["l"][-nb13 - 1 : -1])
        out["K13"] = G if sg * (b3["c"][-1] - ref) > 0 else R
    else:
        out["K13"] = NA
    d3, d15 = tf_dir(b3["c"]), tf_dir(b15["c"])
    out["K14"] = G if d3 == sg and d15 == sg else R
    e21 = f["ema21"]
    nsl = int(FIX["EMA_SLOPE_BARS"])
    out["K15"] = float(e21[t] - e21[t - nsl]) if t >= nsl else math.nan
    r3 = rsi(b3["c"], int(CHK["K16_RSI_N"]))
    out["K16"] = NA if math.isnan(r3) else (G if (r3 > CHK["K16_CE"] if up else r3 < CHK["K16_PE"]) else R)
    out["K17"] = _k17(d, t, up)
    n18 = int(CHK["K18_MIN"])
    pcr = b["cm_pcr"]
    out["K18"] = (
        NA
        if t < n18 or math.isnan(pcr[t]) or math.isnan(pcr[t - n18])
        else (G if sg * (pcr[t] - pcr[t - n18]) > 0 else R)
    )
    n19 = int(CHK["K19_BARS"])
    if t >= n19:
        rets = [b[f"stk_{s}"][t] / b[f"stk_{s}"][t - n19] - 1 for s in BANK_STOCKS]
        same = sum(1 for r in rets if sg * r > 0)
        opp = sum(1 for r in rets if sg * r < 0)
        out["K19"] = G if same >= CHK["K19_MIN"] else R if opp >= CHK["K19_MIN"] else NA
    else:
        out["K19"] = NA
    out["HW"] = G
    n20 = int(CHK["K20_BARS"])
    vx = b["vix_c"]
    out["K20"] = (
        NA if t < n20 or math.isnan(vx[t]) else (G if (vx[t] <= vx[t - n20] if up else vx[t] > vx[t - n20]) else R)
    )
    prem = float(d.opt["c"][k, t]) if has_k else math.nan
    dl = abs(float(d.opt["delta"][k, t])) if has_k else math.nan
    cpu = cost_per_unit(prem, d.lot, d.day) if has_k and prem > 0 else math.nan
    wall = b["cm_call_wall" if up else "cm_put_wall"][t]
    dist = sg * (wall - c)
    out["K21"] = (
        NA
        if math.isnan(cpu) or math.isnan(dl) or math.isnan(dist)
        else (G if dist > 0 and dist * dl >= CHK["K21_MULT"] * cpu else R)
    )
    out["K22_max_pain"], out["K22_gex"], out["K22_gamma_flip"] = (
        b["cm_max_pain"][t],
        b["cm_gex"][t],
        b["cm_gamma_flip"][t],
    )
    out["K23"] = NA
    out["K24"] = NA
    u2 = vw + CHK["K25_SIGMA"] * sg * f["sigma"][t]
    out["K25"] = (R if sg * (b["fut_c"][t] - u2) > 0 else G) if pattern == "P1" else NA
    irisk = sl_pts / dl if dl > 0 else math.nan
    room = next_level(d, f, t, side)
    out["room_pts"] = room
    out["index_risk_pts"] = irisk
    out["K26"] = NA if math.isnan(irisk) else (G if room >= float(cfg["ROOM_MULT"]) * irisk else R)
    n27 = int(CHK["K27_BARS"])
    if t + 1 <= minute(str(FIX["K27_START"])) or t < n27:
        out["K27"] = NA
    else:
        above = (b["fut_c"][t - n27 : t + 1] > f["vwap"][t - n27 : t + 1]).astype(int)
        out["K27"] = R if int(np.sum(np.abs(np.diff(above)))) >= float(cfg["CHOP_CROSSES"]) else G
    out["K28"] = (
        NA if math.isnan(cpu) or math.isnan(dl) else (R if f["atr10"][t] * dl < float(cfg["DEAD_MULT"]) * cpu else G)
    )
    out["K29"] = _k29(d, f, t, up) if pattern == "P1" else NA
    out.update(score(out))
    return out


def _k07(d: Day, k: int, t: int, side: str) -> str:
    """Fake_Spike: of the strikes at +-1, +-2 steps (chain_1m), >= K07_MIN_SAME moved with the traded strike."""
    if t < 1:
        return NA
    ch = chain(d)
    ks = sorted(ch)
    s0 = float(d.strikes[k])
    if s0 not in ch:
        return NA
    i = ks.index(s0)
    col = "ce_close" if side == "CE" else "pe_close"
    me = ch[s0][col][t] - ch[s0][col][t - 1]
    if not me or math.isnan(me):
        return NA
    near = [ks[j] for j in (i - 2, i - 1, i + 1, i + 2) if 0 <= j < len(ks)]
    if len(near) < int(CHK["K07_STRIKES"]):
        return NA
    moves = [ch[x][col][t] - ch[x][col][t - 1] for x in near]
    return G if sum(1 for m in moves if m * me > 0) >= CHK["K07_MIN_SAME"] else R


def chain(d: Day) -> dict[float, dict[str, F64]]:
    """chain_1m pivot per strike (cached on the Day)."""
    if "chain" in d.extra:
        out_c: dict[float, dict[str, F64]] = d.extra["chain"]
        return out_c
    tb = d.chain
    m = tb["m"].to_numpy()
    strikes = tb["strike"].to_numpy()
    width = d.opt["c"].shape[1]
    out: dict[float, dict[str, F64]] = {}
    for s in np.unique(strikes):
        sel = (strikes == s) & (m >= 0) & (m < width)
        row: dict[str, F64] = {}
        for c in ("ce_close", "ce_oi", "pe_close", "pe_oi"):
            a = np.full(width, math.nan)
            a[m[sel]] = tb[c].to_numpy(zero_copy_only=False)[sel]
            row[c] = a
        out[float(s)] = row
    d.extra["chain"] = out
    return out


def _k12(b: dict[str, F64], t: int, up: bool, lb: int) -> str:
    """Trap check at decision time: bar t-1 broke out of the prior lookback and bar t did not close back inside."""
    if t < lb + 2:
        return NA
    h, lo, c = b["spot_h"], b["spot_l"], b["spot_c"]
    lvl = np.max(h[t - 1 - lb : t - 1]) if up else np.min(lo[t - 1 - lb : t - 1])
    broke = c[t - 1] > lvl if up else c[t - 1] < lvl
    if not broke:
        return NA
    return G if (c[t] > lvl if up else c[t] < lvl) else R


def _k17(d: Day, t: int, up: bool) -> str:
    n = int(CHK["K17_MIN"])
    if t < n:
        return NA
    ch = chain(d)
    cw, pw = d.base["cm_call_wall"][t], d.base["cm_put_wall"][t]
    if cw not in ch or pw not in ch:
        return NA
    c_oi, p_oi = ch[cw]["ce_oi"], ch[pw]["pe_oi"]
    if np.isnan([c_oi[t], c_oi[t - n], p_oi[t], p_oi[t - n]]).any():
        return NA
    if up:
        return G if c_oi[t] < c_oi[t - n] and p_oi[t] > p_oi[t - n] else R
    return G if p_oi[t] < p_oi[t - n] and c_oi[t] > c_oi[t - n] else R


def _k29(d: Day, f: dict[str, F64], t: int, up: bool) -> str:
    """LEVEL_BREAK: the P1 bar crossed PDH / ORH / ROUND / U1 (PE: PDL / ORL / ROUND / D1) within this bar."""
    lv = levels(d, f, t)
    o, c = d.base["spot_o"][t], d.base["spot_c"][t]
    step = float(FIX["ROUND_STEP"])
    names = ("PDH", "ORH", "U1") if up else ("PDL", "ORL", "D1")
    cand = [lv[x] for x in names if x in lv and not math.isnan(lv[x])]
    cand.append(math.floor(c / step) * step if up else math.ceil(c / step) * step)
    hit = any(o < x < c for x in cand) if up else any(c < x < o for x in cand)
    return G if hit else NA


def score(ck: dict[str, Any]) -> dict[str, Any]:
    """§10.1 scorecard: NA = 0; a group adds at most GROUP_CAP points; pass = every group >= 1 GREEN,
    >= MIN_GREENS GREENs, score >= MIN_SCORE."""
    total, greens, every = 0, 0, True
    for ids in GROUPS.values():
        pts = sum(int(SCORE[x]) for x in ids if ck.get(x) == G)
        g = sum(1 for x in ids if ck.get(x) == G)
        every &= g >= 1
        greens += g
        total += min(pts, int(SCORE["GROUP_CAP"]))
    ok = every and greens >= int(SCORE["MIN_GREENS"]) and total >= int(SCORE["MIN_SCORE"])
    return {"score": total, "checks_green": greens, "score_pass": ok}
