"""Finalist columns of the scoreboard (MISSION V19 ST4b, ST4c, ST7 entry delay, ST11, DESIGN drawdown).

  python -m lab.finalists -> results/finalists.json + a "Finalists" section at the end of results/scoreboard.md
No candidate became a finalist (3c), so the section carries the pick carried as EXPERIMENTAL (3d). The ST4b, ST4c,
ST11 and drawdown values are the lab row (AGREE 24 of 24 with the engine); the delay test runs the engine of record.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from bot.strategy.orb_vix import OrbVix
from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
MIN_HALF = 15  # MIN_TRADES_PER_HALF (ST4b, ASSUMPTION)


def delayed_mean(days: list[str], bars: int) -> tuple[float, int]:
    eor.DELAY = bars
    try:
        net = [float(t.net_stressed_rs) for t in eor.run(days, OrbVix())]
    finally:
        eor.DELAY = 0
    return (round(float(np.mean(net)), 2) if net else 0.0), len(net)


def row(pick: str, days: list[str]) -> dict[str, Any]:
    board = {r["id"]: r for r in json.loads((ROOT / "results/scoreboard.json").read_text(encoding="utf-8"))}
    rank = json.loads((ROOT / "results/loss_first_rank.json").read_text(encoding="utf-8"))
    r = board[pick]
    d1, d2 = delayed_mean(days, 1), delayed_mean(days, 2)
    hi, lo = (r["net_mean_high_vix"], r["n_high_vix"]), (r["net_mean_low_vix"], r["n_low_vix"])
    return {
        "id": pick,
        "status": rank["flag"],
        "st4b_high_vix": {"net_mean": hi[0], "trades": hi[1], "thin": hi[1] < MIN_HALF},
        "st4b_low_vix": {"net_mean": lo[0], "trades": lo[1], "thin": lo[1] < MIN_HALF},
        "st4b_pass": all(n >= MIN_HALF and (m or 0) > 0 for m, n in (hi, lo)),
        "st4c_net_mean_wo_best5": r["net_mean_wo_best5"],
        "st4c_pass": (r["net_mean_wo_best5"] or 0) > 0,
        "st7_delay_1": {"net_mean": d1[0], "trades": d1[1]},
        "st7_delay_2": {"net_mean": d2[0], "trades": d2[1]},
        "st7_delay_pass": d1[0] > 0 and d2[0] > 0,
        "st11_per_day": r["per_day"],
        "st11_pass": r["per_day"] >= 0.5,
        "design_max_dd_rs": r["max_dd"],
        "design_dd95_mtm_rs": rank["pick_dd95_rs"],
        "profit_factor": r["profit_factor"],
        "losing_streak": r["losing_streak"],
        "best5_share": r["best5_share"],
    }


def section(rows: list[dict[str, Any]]) -> list[str]:
    head = (
        "| id | status | ST4b high VIX (n) | ST4b low VIX (n) | ST4c w/o best 5 | ST7 delay +1 bar (n) | "
        "ST7 delay +2 bars (n) | ST11 per day | DESIGN max DD ₹ | DESIGN DD95 MTM ₹ | profit factor | losing streak |"
    )
    out = ["", "## Finalists (ST4b, ST4c, ST7-delay, ST11, DESIGN-drawdown)", "",
           "No candidate passed the 3c battery; the row is the pick carried as EXPERIMENTAL (3d).",
           "Stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample].", "", head, "|" + "---|" * 12]  # fmt: skip
    for r in rows:
        h, lo, d1, d2 = r["st4b_high_vix"], r["st4b_low_vix"], r["st7_delay_1"], r["st7_delay_2"]
        out.append(
            f"| {r['id']} | {r['status']} | {h['net_mean']} ({h['trades']}{', thin' if h['thin'] else ''}) | "
            f"{lo['net_mean']} ({lo['trades']}{', thin' if lo['thin'] else ''}) | {r['st4c_net_mean_wo_best5']} | "
            f"{d1['net_mean']} ({d1['trades']}) | {d2['net_mean']} ({d2['trades']}) | {r['st11_per_day']}"
            f"{' RARE' if not r['st11_pass'] else ''} | {r['design_max_dd_rs']} | {r['design_dd95_mtm_rs']} | "
            f"{r['profit_factor']} | {r['losing_streak']} |"
        )
    return out


def main() -> int:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    rows = [row(json.loads((ROOT / "results/loss_first_rank.json").read_text(encoding="utf-8"))["pick"], days)]
    (ROOT / "results/finalists.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    md = ROOT / "results/scoreboard.md"
    text = md.read_text(encoding="utf-8").split("\n## Finalists")[0].rstrip("\n")
    md.write_text(text + "\n" + "\n".join(section(rows)) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
