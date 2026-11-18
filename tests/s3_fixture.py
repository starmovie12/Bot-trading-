"""Small synthetic S3 days for tests T01-T25 (never real data)."""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
import pyarrow as pa

from lab.data import BANK_STOCKS
from lab.s3.data import Day, N

STRIKES = [49600.0 + 100 * i for i in range(9)]


def _bars(o: np.ndarray[Any, Any], h: Any, lo: Any, c: Any, width: int, offset: int) -> pa.Table:
    rows: dict[str, list[Any]] = {"avail_m": [], "o": [], "h": [], "l": [], "c": [], "is_partial": []}
    for s in range(0, N, width):
        e = min(s + width, N)
        rows["avail_m"].append(e + offset)
        rows["o"].append(float(o[s]))
        rows["h"].append(float(np.max(h[s:e])))
        rows["l"].append(float(np.min(lo[s:e])))
        rows["c"].append(float(c[e - 1]))
        rows["is_partial"].append(e - s < width)
    return pa.table(rows)


def make_day(
    day: dt.date = dt.date(2026, 5, 4),
    dte: int = 10,
    lot: int = 30,
    ivp: float = 40.0,
    seed: int = 1,
    walk: bool = False,
) -> Day:
    rng = np.random.default_rng(seed)
    spot_c = 50000 + (np.cumsum(rng.normal(0, 8, N)) if walk else np.zeros(N))
    spot_o = np.concatenate([[spot_c[0]], spot_c[:-1]])
    spot_h = np.maximum(spot_o, spot_c) + (rng.uniform(1, 10, N) if walk else 5)
    spot_l = np.minimum(spot_o, spot_c) - (rng.uniform(1, 10, N) if walk else 5)
    base: dict[str, Any] = {"spot_o": spot_o, "spot_h": spot_h, "spot_l": spot_l, "spot_c": spot_c}
    for k in ("o", "h", "l", "c"):
        base[f"fut_{k}"] = base[f"spot_{k}"] + 100
    base["fut_v"] = rng.uniform(800, 1200, N) if walk else np.full(N, 1000.0)
    for k in ("o", "h", "l", "c"):
        base[f"vix_{k}"] = np.full(N, 14.0)
    for s in BANK_STOCKS:
        base[f"stk_{s}"] = 1000 + (np.cumsum(rng.normal(0, 0.5, N)) if walk else np.zeros(N))
    base |= {
        "cm_call_wall": np.full(N, 52000.0),
        "cm_put_wall": np.full(N, 48000.0),
        "cm_pcr": np.full(N, 1.0),
        "cm_max_pain": np.full(N, 50000.0),
        "cm_gex": np.full(N, 1.0),
        "cm_gamma_flip": np.full(N, 49800.0),
        "cm_atm_iv": np.full(N, 0.15),
    }
    prev = {k: np.full(N, 50000.0) for k in ("spot_o", "spot_c")}
    prev |= {"spot_h": np.full(N, 50050.0), "spot_l": np.full(N, 49950.0)}
    keys = [(s, cp) for s in STRIKES for cp in ("CE", "PE")]
    kk = len(keys)
    opt: dict[str, Any] = {}
    prem = np.array([350.0 + (50000 - s) * (0.5 if cp == "CE" else -0.5) for s, cp in keys])
    noise = (np.cumsum(rng.normal(0, 1.5, (kk, N)), axis=1)) if walk else np.zeros((kk, N))
    opt["c"] = prem[:, None] + noise
    opt["o"] = np.concatenate([opt["c"][:, :1], opt["c"][:, :-1]], axis=1)
    opt["h"] = np.maximum(opt["o"], opt["c"]) + 2
    opt["l"] = np.minimum(opt["o"], opt["c"]) - 2
    opt["v"] = np.full((kk, N), 500.0)
    opt["oi"] = np.full((kk, N), 1e5)
    opt["delta"] = np.array([[0.5 if cp == "CE" else -0.5] * N for _, cp in keys])
    opt["iv"] = np.full((kk, N), 0.15)
    opt["hs_proxy"] = np.full((kk, N), 1.0)
    opt["vbase"] = np.full((kk, N), np.nan)
    stale = np.zeros((kk, N), dtype=bool)
    d = Day(
        day=day,
        meta={
            "dte": dte,
            "lot": lot,
            "ivp": ivp,
            "ivp_ok": True,
            "rv20": 0.12,
            "expiry": (day + dt.timedelta(days=dte)).isoformat(),
        },
        base=base,
        prev=prev,
        strikes=np.array([s for s, _ in keys]),
        cp=np.array([c for _, c in keys]),
        opt=opt,
        stale=stale,
        vbase_ok=np.zeros((kk, N), dtype=bool),
        chain=pa.table({"m": [], "strike": [], "ce_close": [], "ce_oi": [], "pe_close": [], "pe_oi": []}),
        b3=pa.table({}),
        b15=pa.table({}),
    )
    refresh(d)
    return d


def refresh(d: Day) -> None:
    """Rebuild the chain_1m and 3m/15m tables from the arrays (after a test edits them)."""
    b = d.base
    pb3 = _bars(d.prev["spot_o"], d.prev["spot_h"], d.prev["spot_l"], d.prev["spot_c"], 3, -1000)
    pb15 = _bars(d.prev["spot_o"], d.prev["spot_h"], d.prev["spot_l"], d.prev["spot_c"], 15, -1000)
    d.b3 = pa.concat_tables([pb3, _bars(b["spot_o"], b["spot_h"], b["spot_l"], b["spot_c"], 3, 0)])
    d.b15 = pa.concat_tables([pb15, _bars(b["spot_o"], b["spot_h"], b["spot_l"], b["spot_c"], 15, 0)])
    rows: dict[str, list[float]] = {"m": [], "strike": [], "ce_close": [], "ce_oi": [], "pe_close": [], "pe_oi": []}
    for s in STRIKES:
        ce, pe = d.k(s, "CE"), d.k(s, "PE")
        for m in range(N):
            rows["m"].append(m)
            rows["strike"].append(s)
            rows["ce_close"].append(float(d.opt["c"][ce, m]))
            rows["ce_oi"].append(float(d.opt["oi"][ce, m]))
            rows["pe_close"].append(float(d.opt["c"][pe, m]))
            rows["pe_oi"].append(float(d.opt["oi"][pe, m]))
    d.chain = pa.table(rows)
    d.extra.clear()


def set_path(d: Day, strike: float, cp: str, start: int, bars: list[tuple[float, float, float, float]]) -> int:
    """Write o/h/l/c bars for one strike from minute `start`; later bars stay flat at the last close."""
    k = d.k(strike, cp)
    bars = bars[: N - start]
    for i, (o, h, lo, c) in enumerate(bars):
        m = start + i
        d.opt["o"][k, m], d.opt["h"][k, m], d.opt["l"][k, m], d.opt["c"][k, m] = o, h, lo, c
    last = bars[-1][3]
    m0 = start + len(bars)
    d.opt["o"][k, m0:] = last
    d.opt["h"][k, m0:] = last + 0.5
    d.opt["l"][k, m0:] = last - 0.5
    d.opt["c"][k, m0:] = last
    return k
