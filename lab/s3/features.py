"""S3 features and the entry signal (§4.3, §4.4, §7.3). Index t = bar t (ts_open); a value at t uses bars <= t only,
so it is known at decision_ts = t + 1 min."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

from lab.s3.data import F64, Day, N, load
from lab.s3.registry import FIX, Cfg

NAN = float("nan")


def ema(x: F64, n: int) -> F64:
    a = 2.0 / (n + 1)
    out = np.empty_like(x)
    m = NAN
    for i, v in enumerate(x):
        if not np.isnan(v):
            m = v if np.isnan(m) else m + a * (v - m)
        out[i] = m
    return out


def lagged_mean(x: F64, n: int, nmin: int) -> F64:
    """Mean of x[t-n .. t-1] (today's bars only); NaN when fewer than nmin known values."""
    out = np.full(x.size, NAN)
    for t in range(x.size):
        w = x[max(0, t - n) : t]
        w = w[~np.isnan(w)]
        if w.size >= nmin:
            out[t] = float(w.mean())
    return out


def shift(x: F64, k: int) -> F64:
    out = np.full(x.size, NAN)
    if k < x.size:
        out[k:] = x[: x.size - k]
    return out


@dataclass
class Feats:
    a: dict[str, F64]


@lru_cache(maxsize=64)
def _cached(day: Any) -> Day:
    return load(day)


def base_feats(d: Day) -> dict[str, F64]:
    b, p = d.base, d.prev
    out: dict[str, F64] = {}
    two = np.concatenate([p["spot_c"], b["spot_c"]])
    out["ema9"] = ema(two, int(FIX["EMA_FAST"]))[N:]
    out["ema21"] = ema(two, int(FIX["EMA_SLOW"]))[N:]
    tp = (b["fut_h"] + b["fut_l"] + b["fut_c"]) / 3.0
    v = np.nan_to_num(b["fut_v"], nan=0.0)
    tpv = np.nan_to_num(tp, nan=0.0)
    cv = np.cumsum(v)
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = np.cumsum(tpv * v) / cv
        var = np.cumsum(tpv * tpv * v) / cv - vwap * vwap
    vwap[cv <= 0] = NAN
    out["vwap"] = vwap
    out["sigma"] = np.sqrt(np.clip(var, 0.0, None))
    out["basis"] = b["fut_c"] - b["spot_c"]
    nmin = int(FIX["EARLY_MIN_BARS"])
    out["atr10"] = lagged_mean(b["spot_h"] - b["spot_l"], int(FIX["ATR_SPOT_N"]), nmin)
    out["fatr10"] = lagged_mean(b["fut_h"] - b["fut_l"], int(FIX["ATR_SPOT_N"]), nmin)
    out["fvol_avg"] = lagged_mean(b["fut_v"], int(FIX["FUT_VOL_SMA"]), nmin)
    return out


@dataclass(frozen=True)
class SigParams:
    src: str
    lookback: int
    body_p1: float
    range_max: float
    hw_bars: int
    vol_mult: float

    @staticmethod
    def of(cfg: Cfg) -> SigParams:
        return SigParams(
            str(cfg["SIGNAL_SRC"]),
            int(cfg["BREAKOUT_LOOKBACK"]),
            float(cfg["BODY_MIN_P1"]),
            float(cfg["RANGE_MAX_ATR"]),
            int(cfg["HW_RET_BARS"]),
            float(cfg["FUT_VOL_MULT"]),
        )


@dataclass
class Sig:
    """Per-bar booleans for each side: a (trend + heavyweights), p1, p2, c (volume); pattern 1/2/0."""

    a_ce: np.ndarray[Any, np.dtype[np.bool_]]
    a_pe: np.ndarray[Any, np.dtype[np.bool_]]
    p1_ce: np.ndarray[Any, np.dtype[np.bool_]]
    p1_pe: np.ndarray[Any, np.dtype[np.bool_]]
    p2_ce: np.ndarray[Any, np.dtype[np.bool_]]
    p2_pe: np.ndarray[Any, np.dtype[np.bool_]]
    c_ok: np.ndarray[Any, np.dtype[np.bool_]]
    f: dict[str, F64]

    @property
    def ce(self) -> np.ndarray[Any, np.dtype[np.bool_]]:
        return self.a_ce & (self.p1_ce | self.p2_ce) & self.c_ok

    @property
    def pe(self) -> np.ndarray[Any, np.dtype[np.bool_]]:
        return self.a_pe & (self.p1_pe | self.p2_pe) & self.c_ok


def _gt(a: F64, b: F64) -> np.ndarray[Any, np.dtype[np.bool_]]:
    with np.errstate(invalid="ignore"):
        return np.asarray(np.nan_to_num(a, nan=-np.inf) > np.nan_to_num(b, nan=np.inf))


def signals(d: Day, sp: SigParams, f: dict[str, F64] | None = None) -> Sig:
    f = f if f is not None else base_feats(d)
    b = d.base
    pre = "fut" if sp.src == "FUT" else "spot"
    o, hi, lo, c = (b[f"{pre}_{k}"] for k in ("o", "h", "l", "c"))
    atr = f["fatr10"] if sp.src == "FUT" else f["atr10"]
    fc, vwap = b["fut_c"], f["vwap"]
    r = {}
    for s in ("HDFCBANK", "ICICIBANK"):
        x = b[f"stk_{s}"]
        r[s] = x / shift(x, sp.hw_bars) - 1.0
    zero = np.zeros(N)
    a_ce = _gt(fc, vwap) & _gt(b["spot_c"], f["ema9"]) & _gt(r["HDFCBANK"], zero) & _gt(r["ICICIBANK"], zero)
    a_pe = _gt(vwap, fc) & _gt(f["ema9"], b["spot_c"]) & _gt(zero, r["HDFCBANK"]) & _gt(zero, r["ICICIBANK"])
    rng = hi - lo
    body = np.abs(c - o)
    hi_l = np.full(N, NAN)
    lo_l = np.full(N, NAN)
    for t in range(sp.lookback, N):
        hi_l[t] = np.max(hi[t - sp.lookback : t])
        lo_l[t] = np.min(lo[t - sp.lookback : t])
    z1 = float(FIX["CLOSE_ZONE_P1"])
    with np.errstate(invalid="ignore"):
        rng_ok = (rng >= float(FIX["RANGE_MIN_ATR"]) * atr) & (rng <= sp.range_max * atr) & (rng > 0)
        body_ok = body >= sp.body_p1 * rng
        p1_ce = _gt(c, hi_l) & body_ok & (c - lo >= (1 - z1) * rng) & rng_ok
        p1_pe = _gt(lo_l, c) & body_ok & (hi - c >= (1 - z1) * rng) & rng_ok
    p2_ce, p2_pe = _p2((o, hi, lo, c), atr, f, fc, vwap)
    nmin_atr = float(FIX["VOL_FALLBACK_ATR"])
    fv, fa = b["fut_v"], f["fvol_avg"]
    vol_known = ~np.isnan(fv) & ~np.isnan(fa) & (np.nan_to_num(fa) > 0)
    with np.errstate(invalid="ignore"):
        c_ok = np.where(vol_known, fv >= sp.vol_mult * fa, rng >= nmin_atr * atr)
    c_ok = np.asarray(np.nan_to_num(c_ok, nan=0).astype(bool))
    return Sig(a_ce, a_pe, p1_ce, p1_pe, p2_ce, p2_pe, c_ok, f)


def _p2(
    ohlc: tuple[F64, F64, F64, F64], atr: F64, f: dict[str, F64], fc: F64, vwap: F64
) -> tuple[np.ndarray[Any, np.dtype[np.bool_]], np.ndarray[Any, np.dtype[np.bool_]]]:
    """P2 pullback bounce (§7.3 b): dip bars t-3..t-1, EMA9 at t-1, ATR10 at t (bars t-10..t-1)."""
    o, hi, lo, c = ohlc
    k = int(FIX["P2_MAX_BARS"])
    lo_a, hi_a, vw_a = float(FIX["P2_LOW_ATR"]), float(FIX["P2_HIGH_ATR"]), float(FIX["P2_VWAP_ATR"])
    bmin, zone = float(FIX["BODY_MIN_P2"]), float(FIX["CLOSE_ZONE_P2"])
    ce = np.zeros(N, dtype=bool)
    pe = np.zeros(N, dtype=bool)
    ema9 = f["ema9"]
    vwap_spot = vwap - f["basis"]
    for t in range(k + 1, N):
        a = atr[t]
        if not a > 0:
            continue
        rng = hi[t] - lo[t]
        if not rng > 0:
            continue
        w = range(t - k, t)
        e = ema9[t - 1]
        body = abs(c[t] - o[t])
        if (
            any(lo[j] < lo[j - 1] for j in w)
            and (
                e - lo_a * a <= min(lo[j] for j in w) <= e + hi_a * a
                or abs(min(lo[j] for j in w) - vwap_spot[t - 1]) <= vw_a * a
            )
            and all(fc[j] >= vwap[j] for j in w)
            and c[t] > hi[t - 1]
            and c[t] > o[t]
            and body >= bmin * rng
            and c[t] - lo[t] >= (1 - zone) * rng
        ):
            ce[t] = True
        if (
            any(hi[j] > hi[j - 1] for j in w)
            and (
                e - hi_a * a <= max(hi[j] for j in w) <= e + lo_a * a
                or abs(max(hi[j] for j in w) - vwap_spot[t - 1]) <= vw_a * a
            )
            and all(fc[j] <= vwap[j] for j in w)
            and c[t] < lo[t - 1]
            and c[t] < o[t]
            and body >= bmin * rng
            and hi[t] - c[t] >= (1 - zone) * rng
        ):
            pe[t] = True
    return ce, pe
