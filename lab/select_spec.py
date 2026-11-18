"""Phase 3d (MISSION V19 LAB): LOSS-FIRST rank on engine-of-record trades and the edge decomposition.

  python -m lab.select_spec   -> results/loss_first_rank.json, results/edge_decomposition.md, data/lab/eor_design.json
DD95 = 95th percentile of the 12-month maximum peak-to-trough fall, marked at the worst 1-minute mark of every open
trade (TradeRecord.mae_rs), day-block bootstrap (5-day blocks, 2,000 paths, SEED); stressed costs.
"""

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from bot.strategy.orb_vix import OrbVix
from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261116


def day_marks(trades: list[dict[str, Any]], days: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Per day: net ₹ and the lowest mark-to-market point relative to the day's start (<= 0)."""
    net, low = np.zeros(len(days)), np.zeros(len(days))
    idx = {d: i for i, d in enumerate(days)}
    for t in sorted(trades, key=lambda t: (t["day"], t["entry_m"])):
        i = idx[t["day"]]
        costs = t["gross"] - t["net"]
        low[i] = min(low[i], net[i] + t["mae"] - costs, net[i] + t["net"])
        net[i] += t["net"]
    return net, low


def dd95(net: np.ndarray, low: np.ndarray, block: int = 5, paths: int = 2000, days: int = 250) -> float:
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(paths):
        starts = rng.integers(0, len(net) - block + 1, size=days // block + 1)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:days]
        end = np.cumsum(net[idx])
        start = end - net[idx]
        worst = start + low[idx]
        peak = np.maximum.accumulate(np.maximum(np.concatenate([[0.0], end[:-1]]), 0))
        out.append(float(np.max(np.maximum(peak, np.maximum.accumulate(end)) - np.minimum(worst, end))))
    return float(np.percentile(out, 95))


def as_dict(t: Any) -> dict[str, Any]:
    return {
        "day": str(t.day),
        "strike": t.legs[0].strike,
        "type": t.legs[0].opt_type,
        "entry_m": t.entry_minute,
        "exit_m": t.exit_minute,
        "reason": t.exit_reason,
        "lot": t.lot,
        "entry": t.entry_value,
        "exit": t.exit_value,
        "gross": float(t.gross_rs),
        "charges": float(t.charges_rs),
        "fill": float(t.fill_cost_stressed_rs),
        "net": float(t.net_stressed_rs),
        "mae": float(t.mae_rs),
    }


def edge_md(tr: list[dict[str, Any]]) -> list[str]:
    n = len(tr)
    g = sum(t["gross"] for t in tr) / n
    ch = sum(1.5 * t["charges"] for t in tr) / n
    fl = sum(t["fill"] for t in tr) / n
    pts = sum((t["exit"] - t["entry"]) for t in tr) / n
    return [
        "# EDGE DECOMPOSITION (MISSION V19 3d; carried candidate A1+b1, EXPERIMENTAL: paper only)",
        "",
        f"Engine of record, DESIGN 362 days, {n} trades [BACKTEST·in-sample], ₹ per trade, PRE-TAX, stressed costs:",
        "",
        "| component | ₹ per trade |",
        "|---|---|",
        f"| gross option points captured (mean {pts:.2f} points x lot) | {g:.2f} |",
        f"| spread + slippage (stressed ESTIMATE, ST7) | -{fl:.2f} |",
        f"| charges x 1.5 (SOURCE rows by date) | -{ch:.2f} |",
        "| theta | inside the gross (the option price path already pays it; not separable without a pricing model) |",
        f"| **net** | **{g - ch - fl:.2f}** |",
        "",
        "Reading: the stressed costs are about "
        f"{(ch + fl) / abs(g) * 100:.0f}% of the gross per trade; the gross alone does not clear them."
        if g != 0
        else "Reading: no gross edge.",
    ]


def main() -> int:
    split = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))
    days = split["design"]
    trades = [as_dict(t) for t in eor.run(days, OrbVix())]
    (ROOT / "data/lab/eor_design.json").write_text(json.dumps(trades) + "\n", encoding="utf-8")
    net, low = day_marks(trades, days)
    carried = round(dd95(net, low), 0)
    screen = json.loads((ROOT / "data/lab/dd95_screen.json").read_text(encoding="utf-8"))
    rank = {
        "passed_battery": [],
        "result": "NO EDGE FOUND IN THE TESTED SET",
        "pick": "A1+b1",
        "flag": "EXPERIMENTAL: paper only",
        "pick_dd95_rs": carried,
        "pick_dd95_source": "engine of record, MTM marks, 5-day blocks, 2,000 paths, 12 months",
        "pick_net_per_month_rs": round(float(net.sum()) / len(days) * 21, 0),
        "pick_trades": len(trades),
        "passed_over": {
            "id": "A2+b1",
            "dd95_rs": screen["A2+b1"]["dd95"],
            "net_per_month_rs": screen["A2+b1"]["net_pm"],
            "source": "lab screen (closed trades), data/lab/dd95_screen.json",
        },
        "screen_dd95_rs": {k: v["dd95"] for k, v in screen.items()},
        "seed": SEED,
        "date": str(dt.date.today()),
    }
    (ROOT / "results/loss_first_rank.json").write_text(json.dumps(rank, indent=1) + "\n", encoding="utf-8")
    (ROOT / "results/edge_decomposition.md").write_text("\n".join(edge_md(trades)) + "\n", encoding="utf-8")
    print({k: rank[k] for k in ("pick", "pick_dd95_rs", "pick_net_per_month_rs", "pick_trades")}, Decimal(0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
