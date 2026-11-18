"""S3 report helpers: CSV writers, diagnosis tables, cost curve, intrabar, chart table, round card numbers."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from collections.abc import Callable, Iterable
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

TRADE_COLS = [
    "variant",
    "series_id",
    "config_hash",
    "code_commit",
    "trial_id",
    "date",
    "signal_ts",
    "pattern",
    "side",
    "expiry",
    "dte",
    "strike",
    "delta_at_entry",
    "premium_at_signal",
    "entry_ts",
    "entry_fill",
    "lots",
    "lots_reason",
    "lot_size",
    "qty",
    "sl_init",
    "be_level",
    "index_risk_pts",
    "room_pts",
    "peak",
    "peak_ts",
    "max_gear",
    "mfe_pts",
    "mae_pts",
    "bars_held",
    "exit_ts",
    "exit_level",
    "exit_fill",
    "exit_reason",
    "stale_forced",
    "gross_rs",
    "brokerage",
    "stt",
    "exchange",
    "gst",
    "sebi",
    "ipft",
    "stamp",
    "charges_total",
    "spread_slip_rs",
    "net_base",
    "net_stress",
    "net_proxy",
    "net_path",
    "net_worst",
    "score",
    "checks_green",
    "wf_window",
    "vix_half",
    "day_state",
    "vix_open",
    "strike_how",
]


def write_csv(path: Path, rows: list[dict[str, Any]], cols: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(cols) if cols is not None else sorted({k for r in rows for k in r})
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r.get(k, "")) for k in keys})


def _fmt(v: Any) -> Any:
    if isinstance(v, float):
        return "" if math.isnan(v) else round(v, 4)
    return v


def rs(x: float) -> str:
    return f"{'-' if x < 0 else ''}₹{abs(x):,.0f}"


def group(trades: list[dict[str, Any]], key: Callable[[dict[str, Any]], Any]) -> list[tuple[Any, int, float, float]]:
    g: dict[Any, list[float]] = defaultdict(list)
    for t in trades:
        g[key(t)].append(t["net_base"])
    return [(k, len(v), float(np.sum(v)), float(np.mean(v))) for k, v in sorted(g.items(), key=lambda x: str(x[0]))]


def table(title: str, rows: list[tuple[Any, int, float, float]]) -> list[str]:
    out = [f"**{title}**", "", "| bucket | trades | net_base | per trade |", "|---|---:|---:|---:|"]
    out += [f"| {k} | {n} | {rs(s)} | {rs(m)} |" for k, n, s, m in rows]
    return [*out, ""]


def dte_bucket(d: int) -> str:
    return "0-2" if d <= 2 else "3-7" if d <= 7 else "8-15" if d <= 15 else "16+"


def half_hour(t: dict[str, Any]) -> str:
    hh, mm = (int(x) for x in t["entry_ts"][-5:].split(":"))
    return f"{hh:02d}:{0 if mm < 30 else 30:02d}"


def pr(trades: list[dict[str, Any]]) -> dict[str, float]:
    nb = np.array([t["net_base"] for t in trades])
    w, lo = nb[nb > 0], nb[nb < 0]
    p = float(w.size / nb.size) if nb.size else math.nan
    r = float(w.mean() / -lo.mean()) if w.size and lo.size else math.nan
    return {
        "p": p,
        "R": r,
        "p_needed": math.nan if math.isnan(r) else 1 / (1 + r),
        "avg_win": float(w.mean()) if w.size else 0.0,
        "avg_loss": float(lo.mean()) if lo.size else 0.0,
    }


def zero_crossing(curve: list[tuple[float, float]]) -> str:
    for (s0, n0), (s1, n1) in pairwise(curve):
        if n0 >= 0 > n1:
            return f"₹{s0 + (s1 - s0) * n0 / (n0 - n1):.2f}"
    if curve and curve[0][1] < 0:
        return f"sabse kam spread (₹{curve[0][0]:.2f}) par bhi net zero se neeche: koi zero-crossing nahi"
    return f"₹{curve[-1][0]:.2f} tak net zero se upar"


def chart_pick(trades: list[dict[str, Any]], n: int = 5) -> list[dict[str, Any]]:
    """n wins and n losses, each from a different month, spread over the period (deterministic)."""
    used: set[str] = set()
    out: list[dict[str, Any]] = []
    for want in (True, False):
        pool = [t for t in trades if (t["net_base"] > 0) == want]
        months = sorted({t["date"][:7] for t in pool})
        free = [m for m in months if m not in used] or months
        pick_m = [free[round(i * (len(free) - 1) / max(1, n - 1))] for i in range(min(n, len(free)))]
        for m in dict.fromkeys(pick_m):
            c = [t for t in pool if t["date"][:7] == m]
            out.append(max(c, key=lambda t: abs(t["net_base"])))
            used.add(m)
    return out


def write_signals(folder: Path, rows: list[dict[str, Any]], variants: Iterable[str]) -> list[str]:
    """One signals CSV per variant (each under the 1 MB commit limit); numbers rounded to 2 decimals."""
    cols = ["variant", *sorted({k for r in rows for k in r} - {"variant"})]
    names = []
    for v in variants:
        name = f"s3_signals_{v}.csv"
        sub = [
            {k: (round(x, 2) if isinstance(x, float) and not math.isnan(x) else x) for k, x in r.items()}
            for r in rows
            if r.get("variant") == v
        ]
        write_csv(folder / name, sub, cols)
        names.append(name)
    return names
