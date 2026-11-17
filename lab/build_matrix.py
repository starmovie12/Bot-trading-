"""Phase 3a matrix (MISSION V19 LAB): FEATURES per 5-minute decision bar and OUTCOMES per pre-registered exit preset.

Runs ONCE on DESIGN days (data/lab/split.json) and caches data/lab/matrix.npz (gitignored). Research only, never the
bot runtime. Decision at minute t (minutes after 09:15) reads bars [0, t) only; entry at the NEXT non-stale option bar
(open of minute >= t with v > 0 and not stale, within 2 bars, else NO_FILL_STALE); exits by the RISK SHELL of the preset
with the pessimistic intrabar rule (a bar touching stop and target exits at the stop). Gross ₹ uses candle prices;
charges are stored unstressed and per component so stress, kill-side and delay runs are arithmetic (ST7).
"""

import datetime as dt
import json
from dataclasses import dataclass
from math import isnan
from pathlib import Path
from typing import Any

import numpy as np

from lab import data

ROOT = Path(__file__).resolve().parent.parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
N = 385  # minutes 09:15 .. 15:39 (F&O to 15:40 from 2026-08-03; the index stops 15:29)
DECISIONS = np.arange(15, 316, 5)  # 09:30 .. 14:30 (the shell's entry window)
FORCE_FLAT = 355  # 15:10 IST: before the stressed MIS cutoff 15:15 (D-17)
STRIKE = 100
SPREAD_WIDTH = 2  # short leg 2 strikes OTM
NAN = float("nan")
F = dict[str, np.ndarray]


@dataclass(frozen=True)
class Preset:
    """Exit preset (fixed in PLAN.md §PREREG-0 before any OUTCOME was computed)."""

    name: str
    stop_frac: float  # stop = entry value x (1 - stop_frac); R = stop_frac x entry value
    target_r: float  # target = entry value + target_r x R
    scratch_min: int  # no progress after this many minutes -> exit
    time_stop_min: int


PRESETS = {
    "EXIT0": Preset("EXIT0", 0.30, 2.0, 30, 120),
    "C1": Preset("C1", 0.30, 2.0, 20, 120),
    "C2": Preset("C2", 0.30, 2.0, 45, 120),
    "C3": Preset("C3", 0.30, 2.0, 30, 60),
    "C4": Preset("C4", 0.30, 3.0, 30, 120),
}
SPREAD_STOP_FRAC = 0.40  # a debit spread's stop at -40% of the debit (same R logic)


def minute_index(ts: list[dt.datetime]) -> np.ndarray:
    return np.array([(t.hour - 9) * 60 + t.minute - 15 for t in ts], dtype=np.int64)


def grid(tb: Any, cols: tuple[str, ...]) -> F:
    out = {c: np.full(N, NAN) for c in cols}
    if tb.num_rows == 0:
        return out
    m = minute_index(tb["ts_open"].to_pylist())
    ok = (m >= 0) & (m < N)
    for c in cols:
        vals = np.array(tb[c].to_pylist(), dtype=float)
        out[c][m[ok]] = vals[ok]
    return out


def load_day(repo: Path, day: dt.date) -> dict[str, Any]:
    """Minute arrays of one day: index, near futures, VIX, two bank stocks, options of the nearest expiry."""
    spot = grid(data.read_day(repo, "spot_1m", day, columns=["ts_open", "o", "h", "l", "c"]), ("o", "h", "l", "c"))
    fut_tb = data.read_day(
        repo, "fut_1m", day, columns=["instrument_key", "expiry_date", "ts_open", "o", "h", "l", "c", "v"]
    )
    near = min(e for e in set(fut_tb["expiry_date"].to_pylist()) if e >= day)
    fut = grid(fut_tb.filter(np.array([e == near for e in fut_tb["expiry_date"].to_pylist()])), ("c", "v"))
    vix = grid(data.read_day(repo, "vix_1m", day, underlying=data.VIX, columns=["ts_open", "c"]), ("c",))
    stocks = {
        s: grid(data.read_day(repo, "stock_1m", day, underlying=s, columns=["ts_open", "c"]), ("c",))
        for s in ("HDFCBANK", "ICICIBANK")
    }
    opt_tb = data.read_day(
        repo,
        "options",
        day,
        columns=["expiry_date", "strike", "option_type", "ts_open", "o", "h", "l", "c", "v", "is_stale"],
    )
    expiry = min(e for e in set(opt_tb["expiry_date"].to_pylist()) if e >= day)
    rows = [r for r in opt_tb.to_pylist() if r["expiry_date"] == expiry]
    opts: dict[tuple[float, str], F] = {}
    for r in rows:
        k = (r["strike"], r["option_type"])
        if k not in opts:
            opts[k] = {c: np.full(N, NAN) for c in ("o", "h", "l", "c")} | {"live": np.zeros(N, dtype=bool)}
        m = (r["ts_open"].hour - 9) * 60 + r["ts_open"].minute - 15
        if 0 <= m < N:
            for c in ("o", "h", "l", "c"):
                opts[k][c][m] = r[c]
            opts[k]["live"][m] = bool(r["v"]) and not r["is_stale"]
    return {"day": day, "spot": spot, "fut": fut, "vix": vix, "stocks": stocks, "opts": opts, "expiry": expiry}


def features_at(d: dict[str, Any], t: int, prev_close: float) -> dict[str, float]:
    """Features known at decision minute t: only bars [0, t) are read (prefix-safe)."""
    c = d["spot"]["c"][:t]
    o0 = d["spot"]["o"][0]
    px = c[~np.isnan(c)]
    if len(px) < 15:
        return {}
    last = px[-1]
    rets = np.diff(np.log(px))
    fc, fv = d["fut"]["c"][:t], d["fut"]["v"][:t]
    ok = ~np.isnan(fc) & ~np.isnan(fv)
    vwap = float(np.sum(fc[ok] * fv[ok]) / np.sum(fv[ok])) if ok.any() and np.sum(fv[ok]) > 0 else NAN
    fut_last = fc[ok][-1] if ok.any() else NAN
    vx = d["vix"]["c"][:t]
    vx = vx[~np.isnan(vx)]
    hd, ic = d["stocks"]["HDFCBANK"]["c"][:t], d["stocks"]["ICICIBANK"]["c"][:t]

    def r15(a: np.ndarray) -> float:
        a = a[~np.isnan(a)]
        return float(a[-1] / a[-16] - 1) if len(a) >= 16 else NAN

    path = float(np.sum(np.abs(np.diff(px))))
    return {
        "t": float(t),
        "spot": float(last),
        "gap": float(o0 / prev_close - 1) if not isnan(prev_close) else NAN,
        "or15_hi": float(np.nanmax(d["spot"]["h"][:15])),
        "or15_lo": float(np.nanmin(d["spot"]["l"][:15])),
        "or30_hi": float(np.nanmax(d["spot"]["h"][:30])) if t >= 30 else NAN,
        "or30_lo": float(np.nanmin(d["spot"]["l"][:30])) if t >= 30 else NAN,
        "day_hi": float(np.nanmax(d["spot"]["h"][:t])),
        "day_lo": float(np.nanmin(d["spot"]["l"][:t])),
        "ret15": float(last / px[-16] - 1) if len(px) >= 16 else NAN,
        "ret30": float(last / px[-31] - 1) if len(px) >= 31 else NAN,
        "ret_open": float(last / o0 - 1),
        "eff": float(abs(last - o0) / path) if path > 0 else 0.0,
        "rv5": float(np.std(rets[-5:])) if len(rets) >= 5 else NAN,
        "rv15": float(np.std(rets[-15:])) if len(rets) >= 15 else NAN,
        "rv30": float(np.std(rets[-30:])) if len(rets) >= 30 else NAN,
        "vwap_dist": float((fut_last - vwap) / vwap) if not isnan(vwap) else NAN,
        "basis": float(fut_last / last - 1) if not isnan(fut_last) else NAN,
        "vix": float(vx[-1]) if len(vx) else NAN,
        "vix_chg": float(vx[-1] - vx[0]) if len(vx) else NAN,
        "hdfc15": r15(hd),
        "icici15": r15(ic),
        "dte": float((d["expiry"] - d["day"]).days),
    }


def entry_minute(live: np.ndarray, t: int) -> int:
    for m in range(t, min(t + 3, FORCE_FLAT)):
        if live[m]:
            return m
    return -1


def simulate(val: F, live: np.ndarray, e: int, p: Preset, stop_frac: float) -> dict[str, float]:
    """One trade of a long position in `val` (an option or a debit spread's net value) from entry minute e."""
    entry = val["o"][e]
    risk = stop_frac * entry
    stop, target = entry - risk, entry + p.target_r * risk
    trail_on = False
    mae = mfe = 0.0
    for m in range(e, FORCE_FLAT + 1):
        lo, hi, cl = val["l"][m], val["h"][m], val["c"][m]
        if isnan(lo) or isnan(hi) or isnan(cl):
            continue
        mae, mfe = min(mae, lo - entry), max(mfe, hi - entry)
        cur_stop = entry if trail_on else stop
        hit_stop, hit_target = lo <= cur_stop, hi >= target
        if hit_stop:  # pessimistic: a bar touching both exits at the stop (gap through: the worse open)
            return {
                "exit_m": m,
                "exit": min(cur_stop, val["o"][m]),
                "reason": 1 + trail_on,
                "mae": mae,
                "mfe": mfe,
                "stale": not live[m],
            }
        if hit_target:
            return {"exit_m": m, "exit": target, "reason": 3, "mae": mae, "mfe": mfe, "stale": not live[m]}
        if hi >= entry + risk:
            trail_on = True
        held = m - e + 1
        if (held >= p.scratch_min and cl <= entry and not trail_on) or held >= p.time_stop_min or m == FORCE_FLAT:
            reason = 4 if held >= p.scratch_min and cl <= entry and not trail_on else (5 if m != FORCE_FLAT else 6)
            return {"exit_m": m, "exit": cl, "reason": reason, "mae": mae, "mfe": mfe, "stale": not live[m]}
    return {"exit_m": FORCE_FLAT, "exit": entry, "reason": 7, "mae": mae, "mfe": mfe, "stale": True}


def spread_values(long_: F, short: F) -> tuple[F, np.ndarray]:
    """Net value of long - short with a pessimistic low (long low - short high) and a conservative high (close)."""
    val = {"o": long_["o"] - short["o"], "c": long_["c"] - short["c"], "l": long_["l"] - short["h"]}
    val["h"] = val["c"].copy()
    return val, long_["live"] & short["live"]


EXIT_REASONS = {1: "stop", 2: "breakeven", 3: "target", 4: "scratch", 5: "time", 6: "force_flat", 7: "no_bar"}


def outcomes_at(
    d: dict[str, Any], t: int, spot: float, direction: int, structure: str, p: Preset
) -> dict[str, float] | None:
    side = "CE" if direction > 0 else "PE"
    atm = round(spot / STRIKE) * STRIKE
    long_k = (float(atm), side)
    if long_k not in d["opts"]:
        return None
    leg = d["opts"][long_k]
    if structure == "LONG":
        val, live, stop_frac, legs = {k: leg[k] for k in ("o", "h", "l", "c")}, leg["live"], p.stop_frac, 1
    else:
        short_k = (float(atm + direction * SPREAD_WIDTH * STRIKE), side)
        if short_k not in d["opts"]:
            return None
        val, live = spread_values(leg, d["opts"][short_k])
        stop_frac, legs = SPREAD_STOP_FRAC, 2
    e = entry_minute(live, t)
    if e < 0 or not val["o"][e] > 0:
        return None
    r = simulate(val, live, e, p, stop_frac)
    x = int(r["exit_m"])
    short = d["opts"].get((float(atm + direction * SPREAD_WIDTH * STRIKE), side)) if legs == 2 else None
    return {"t": t, "dir": direction, "entry_m": e, "entry": float(val["o"][e]), "exit": float(r["exit"]), "exit_m": x,
            "reason": r["reason"], "mae": r["mae"], "mfe": r["mfe"], "stale_exit": float(r["stale"]), "legs": legs,
            "long_in": float(leg["o"][e]), "long_out": float(leg["c"][x]),
            "short_in": float(short["o"][e]) if short else 0.0,
            "short_out": float(short["c"][x]) if short else 0.0}  # fmt: skip


HORIZONS = (15, 30, 60, 120)


def atm_premium(d: dict[str, Any], t: int, spot: float) -> float:
    atm = float(round(spot / STRIKE) * STRIKE)
    px = [d["opts"][(atm, s)]["c"][t - 1] for s in ("CE", "PE") if (atm, s) in d["opts"]]
    px = [x for x in px if not isnan(x)]
    return float(np.mean(px)) if px else NAN


def build(days: list[str], repo: Path, with_outcomes: bool) -> dict[str, Any]:
    """FEATURES (+ market-fact samples) always; OUTCOMES only after §PREREG-0 is committed (with_outcomes)."""
    profile = json.loads((ROOT / "data/lab/data_profile.json").read_text(encoding="utf-8"))
    lots = {e: int(v) for e, v in profile["lots_by_expiry"].items()}
    feats: list[dict[str, float]] = []
    facts: list[dict[str, float]] = []
    outs: dict[str, list[dict[str, float]]] = {f"{p}|{s}": [] for p in PRESETS for s in ("LONG", "SPREAD")}
    prev_close = NAN
    for di, ds in enumerate(days):
        d = load_day(repo, dt.date.fromisoformat(ds))
        lot = lots[str(d["expiry"])]
        c = d["spot"]["c"]
        for t in DECISIONS:
            f = features_at(d, int(t), prev_close)
            if not f:
                continue
            f |= {"day_i": float(di), "lot": float(lot), "atm_prem": atm_premium(d, int(t), f["spot"])}
            row = len(feats)
            feats.append(f)
            moves = {f"mv{h}": float(abs(c[min(int(t) + h, 374) - 1] - c[int(t) - 1])) for h in HORIZONS}
            facts.append({"t": float(t), "vix": f["vix"], "dte": f["dte"], "atm_prem": f["atm_prem"]} | moves)
            if not with_outcomes:
                continue
            for name, p in PRESETS.items():
                for st in ("LONG", "SPREAD"):
                    for direction in (1, -1):
                        o = outcomes_at(d, int(t), f["spot"], direction, st, p)
                        if o is not None:
                            outs[f"{name}|{st}"].append(o | {"row": float(row)})
        hi, lo = np.nanmax(d["spot"]["h"]), np.nanmin(d["spot"]["l"])
        facts.append({"day_range": float(hi - lo), "gap_abs": abs(feats[-1]["gap"]) if feats else NAN, "t": -1.0})
        prev_close = float(c[~np.isnan(c)][-1]) if (~np.isnan(c)).any() else prev_close
    return {"features": feats, "facts": facts, "outcomes": outs, "days": days}


def to_arrays(rows: list[dict[str, float]]) -> F:
    keys = sorted({k for r in rows for k in r if not k.startswith("_")})
    return {k: np.array([r.get(k, NAN) for r in rows], dtype=float) for k in keys}


def market_facts(facts: list[dict[str, float]], n_days: int) -> list[str]:
    """Unconditional DESIGN distributions (no rule is evaluated): results/market_facts.md."""
    bar = [f for f in facts if f["t"] >= 0]
    vix_med = float(np.nanmedian([f["vix"] for f in bar]))
    buckets = (("09:30-10:30", 15, 75), ("10:30-13:30", 75, 255), ("13:30-14:30", 255, 316))

    def pct(xs: list[float]) -> str:
        a = np.array([x for x in xs if not isnan(x)])
        return "/".join(f"{np.percentile(a, q):.0f}" for q in (50, 75, 90)) if len(a) else "n/a"

    def pct2(xs: list[float]) -> str:
        a = np.array([x for x in xs if not isnan(x)])
        return "/".join(f"{np.percentile(a, q):.2f}" for q in (50, 75, 90)) if len(a) else "n/a"

    out = [
        f"# MARKET FACTS (MISSION V19 3a; DESIGN {n_days} days; unconditional; index points unless ₹) [REAL]",
        "",
        f"|index move| p50/p75/p90 by decision-time bucket and VIX state (DESIGN median VIX {vix_med:.2f}):",
        "",
        "| bucket | VIX | 15 min | 30 min | 60 min | 120 min |",
        "|---|---|---|---|---|---|",
    ]
    for name, a, b in buckets:
        for state in ("low", "high"):
            rows = [f for f in bar if a <= f["t"] < b and (f["vix"] <= vix_med) == (state == "low")]
            out.append(f"| {name} | {state} | " + " | ".join(pct([r[f"mv{h}"] for r in rows]) for h in HORIZONS) + " |")
    days = [f for f in facts if f["t"] < 0]
    out += ["", f"Daily range p50/p75/p90: {pct([f['day_range'] for f in days])} points; |gap| % p50/p75/p90: "
            f"{pct2([100 * f['gap_abs'] for f in days])}.", "",
            "ATM premium (mean of CE and PE, ₹ per unit) p50 at 09:30 / 12:00 / 14:30 by days to expiry:", "",
            "| DTE | 09:30 | 12:00 | 14:30 |", "|---|---|---|---|"]  # fmt: skip
    for lo, hi in ((0, 2), (3, 7), (8, 15), (16, 40)):
        cells = []
        for t in (15, 165, 315):
            xs = [f["atm_prem"] for f in bar if f["t"] == t and lo <= f["dte"] <= hi and not isnan(f["atm_prem"])]
            cells.append(f"{np.median(xs):.0f}" if xs else "n/a")
        out.append(f"| {lo}-{hi} | " + " | ".join(cells) + " |")
    out += ["", "Spread: not measured (DATA_GRADE B, no bid / ask in the data): ESTIMATE ₹1.00 ATM bid-ask (D-21)."]
    return out


def main(argv: list[str]) -> int:
    split = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))
    with_outcomes = argv == ["--outcomes"]
    res = build(split["design"], ROOT / "data/banknifty/repo", with_outcomes)
    out: dict[str, np.ndarray] = {f"F_{k}": v for k, v in to_arrays(res["features"]).items()}
    for key, rows in res["outcomes"].items():
        out |= {f"O_{key}_{k}": v for k, v in to_arrays(rows).items()}
    np.savez_compressed(ROOT / ("data/lab/matrix.npz" if with_outcomes else "data/lab/features.npz"), **out)  # type: ignore[arg-type]
    if not with_outcomes:
        (ROOT / "results/market_facts.md").write_text("\n".join(market_facts(res["facts"], len(res["days"]))) + "\n")
    n = len(res["features"])
    print(
        f"{len(res['days'])} DESIGN days, {n} decision rows; outcomes "
        + ", ".join(f"{k}: {len(v)}" for k, v in res["outcomes"].items())
    )
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
