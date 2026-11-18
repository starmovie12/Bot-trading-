"""P3R STEP 0 (owner order D-40): why A1+b1 lost. DESIGN data only (the old holdout stays closed).

  python -m lab.diagnose -> results/diagnosis.md, data/lab/diagnosis.json
Descriptive, in-sample numbers: seeds for hypotheses, never evidence (every later test is a pre-registered trial).
"""

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from lab import ideas
from tools import bn_economics as be
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
TIME = (("09:45-10:29", 30, 74), ("10:30-11:59", 75, 164), ("12:00-13:29", 165, 254), ("13:30-14:30", 255, 315))
DTE = (("0-2", 0, 2), ("3-7", 3, 7), ("8-15", 8, 15), ("16+", 16, 99))


def cost_parts(t: dict[str, Any], c: dict[str, Any]) -> dict[str, float]:
    on, lot, pct = dt.date.fromisoformat(t["day"]), t["lot"], Decimal(100)
    buy, sell = Decimal(str(t["entry"])) * lot, Decimal(str(t["exit"])) * lot
    turn = buy + sell
    brok = 2 * be.dated(c["brokerage_option_per_order"], on)
    exch = (
        turn * (be.dated(c["nse_txn_option"], on) + be.dated(c["ipft_option"], on) + be.dated(c["sebi_fee"], on)) / pct
    )
    gst = (brok + exch) * be.dated(c["gst"], on) / pct
    stt, stamp = sell * be.dated(c["stt_option_sell"], on) / pct, buy * be.dated(c["stamp_option_buy"], on) / pct
    slip = 0.20 * 2 * 2 * lot  # ₹0.20 per unit per side, stressed x 2
    return {
        "spread": t["fill"] - slip,
        "spread_base": 1.0 * lot,
        "slippage": slip,
        "slippage_base": 0.4 * lot,
        "stt": 1.5 * float(stt),
        "brokerage": 1.5 * float(brok),
        "exchange_sebi_ipft": 1.5 * float(exch),
        "gst": 1.5 * float(gst),
        "stamp": 1.5 * float(stamp),
    }


def bucket_rows(f: le.A, tr: le.Trades, days: list[str]) -> list[dict[str, Any]]:
    """Every decision row, EXIT0 long ATM, both sides: momentum = the side of the day's move so far; fade = other."""
    mom = tr.dir == np.where(f["ret_open"][tr.row] >= 0, 1, -1)
    cost = le.STRESS_CHARGES * tr.charges + tr.fill_stressed
    row = tr.row
    t, dte, vix, eff, gap = f["t"][row], f["dte"][row], f["vix"][row], f["eff"][row], np.abs(f["gap"][row])
    v1, v2 = np.nanpercentile(f["vix"], [33.3, 66.7])
    groups: list[tuple[str, str, np.ndarray]] = [("time", n, (t >= a) & (t <= b)) for n, a, b in TIME]
    groups += [("DTE", n, (dte >= a) & (dte <= b)) for n, a, b in DTE]
    groups += [
        ("VIX", f"low < {v1:.1f}", vix < v1),
        ("VIX", "mid", (vix >= v1) & (vix < v2)),
        ("VIX", f"high >= {v2:.1f}", vix >= v2),
    ]
    groups += [("day", "trend (eff >= 0.35)", eff >= 0.35), ("day", "range (eff <= 0.20)", eff <= 0.20)]
    groups += [("day", "gap |gap| >= 0.5%", gap >= 0.005), ("day", "no gap", gap < 0.005)]
    out = []
    for g, name, m in groups:
        mm, mf = m & mom, m & ~mom
        best = max(float(tr.gross[mm].mean()) if mm.any() else -1e9, float(tr.gross[mf].mean()) if mf.any() else -1e9)
        out.append(
            {
                "group": g,
                "bucket": name,
                "n": int(mm.sum()),
                "gross_momentum": round(float(tr.gross[mm].mean()), 1),
                "gross_fade": round(float(tr.gross[mf].mean()), 1),
                "cost": round(float(cost[m].mean()), 1),
                "seed": best > float(cost[m].mean()),
            }
        )
    return out


def move_table(f: le.A, cost_pts: float) -> list[dict[str, Any]]:
    """p90 of the |index move| over the next 30 / 60 / 120 minutes vs the break-even index move (ATM delta 0.5)."""
    out = []
    spot = f["spot"].reshape(-1, 61)  # 61 decision rows a day (09:30 .. 14:30, 5-minute steps)
    t = f["t"].reshape(-1, 61)[0]
    for name, a, b in TIME:
        cols = np.nonzero((t >= a) & (t <= b))[0]
        row: dict[str, Any] = {"window": name, "break_even_pts": round(cost_pts, 1)}
        for h in (30, 60, 120):
            k = h // 5
            c = cols[cols + k < 61]
            mv = np.abs(spot[:, c + k] - spot[:, c]).ravel()
            row[f"p90_{h}m"] = round(float(np.nanpercentile(mv, 90)), 1)
        out.append(row)
    return out


def mae_mfe(f: le.A, o: le.A, tr: le.Trades) -> dict[str, Any]:
    """A1+b1 as the lab selects it (AGREE 24 of 24 with the engine): excursions in R (R = 30% of the premium)."""
    idea = next(i for i in ideas.BRACKET if i.id == "A1")
    mask, direction = idea.rule(f, idea.params)
    taken = le.sequence(tr, le.select(tr, np.nan_to_num(mask & (f["vix_chg"] < 0)).astype(bool), direction))
    r = 0.30 * o["entry"][taken]
    mfe, mae = o["mfe"][taken] / r, o["mae"][taken] / r
    net = tr.net_stressed[taken]
    reasons = {str(k): int(v) for k, v in zip(*np.unique(o["reason"][taken], return_counts=True), strict=True)}
    return {
        "trades": len(taken),
        "mfe_r_median": round(float(np.median(mfe)), 2),
        "mae_r_median": round(float(np.median(mae)), 2),
        "mfe_ge_half_r_then_loss": int(((mfe >= 0.5) & (net < 0)).sum()),
        "mfe_ge_1r_then_loss": int(((mfe >= 1.0) & (net < 0)).sum()),
        "reached_2r": int((mfe >= 2.0).sum()),
        "hit_stop": int((mae <= -1.0).sum()),
        "reasons": reasons,
        "hold_min_median": float(np.median(o["exit_m"][taken] - o["entry_m"][taken])),
    }


def max_loss(trades: list[dict[str, Any]], f: le.A) -> dict[str, Any]:
    t = max(trades, key=lambda x: x["entry"])
    prem = f["atm_prem"].reshape(-1, 61)[:, 3]  # ATM premium at 09:45 (row t = 30) per DESIGN day
    dte = f["dte"].reshape(-1, 61)[:, 3]
    by_dte = {n: round(float(np.nanmedian(prem[(dte >= a) & (dte <= b)])), 1) for n, a, b in DTE}
    return {
        "day": t["day"],
        "strike": t["strike"],
        "type": t["type"],
        "entry_pts": t["entry"],
        "lot": t["lot"],
        "premium_x_lot30": round(t["entry"] * 30, 0),
        "stop_loss_at_30pct_x_lot30": round(0.3 * t["entry"] * 30, 0),
        "median_entry_pts": float(np.median([x["entry"] for x in trades])),
        "atm_premium_median_by_dte": by_dte,
    }


def main() -> int:
    f, outs, days = le.load()
    o = outs["EXIT0|LONG"]
    tr = le.trades(f, o, days)
    eor = json.loads((ROOT / "data/lab/eor_design.json").read_text(encoding="utf-8"))
    c = be.consts()
    parts = [cost_parts(t, c) for t in eor]
    mean = {k: round(float(np.mean([p[k] for p in parts])), 2) for k in parts[0]}
    gross = round(float(np.mean([t["gross"] for t in eor])), 2)
    stress_extra = round(
        mean["spread"]
        - mean["spread_base"]
        + mean["slippage"]
        - mean["slippage_base"]
        + (mean["stt"] + mean["brokerage"] + mean["exchange_sebi_ipft"] + mean["gst"] + mean["stamp"]) / 3,
        2,
    )
    cost_pts = float(np.mean(le.STRESS_CHARGES * tr.charges + tr.fill_stressed) / np.mean(f["lot"][tr.row])) / 0.5
    res = {
        "a1b1_cost_parts_rs": mean,
        "a1b1_gross_rs": gross,
        "stress_extra_rs": stress_extra,
        "buckets": bucket_rows(f, tr, days),
        "moves": move_table(f, cost_pts),
        "mae_mfe": mae_mfe(f, o, tr),
        "max_loss": max_loss(eor, f),
        "days": len(days),
        "seed": le.SEED,
    }
    (ROOT / "data/lab/diagnosis.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
