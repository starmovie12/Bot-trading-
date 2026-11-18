"""Owner order 4 R16 (PLAN.md §PREREG-R16): cost-aware filter on R15-a. DESIGN only.

python -m lab.filter_r16 -> trials.jsonl (3 lines), results/r16_board.md, data/lab/r16_rows.json
"""

import json
from pathlib import Path

import numpy as np

from lab import portfolio_r14 as pf
from lab import sizing_r15 as sz
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
BE = {0: (14.9, 12.5, 11.7), 1: (17.0, 14.0, 13.0), 2: (14.0, 11.8, 11.1)}  # ATM, CAP15, ITM2 x 1 / 2 / 3 lots


def keeper(x: float) -> sz.Keep:
    md = pf.matrix("data/lab/matrix_r11.npz")[0]["md"]

    def keep(tr: le.Trades, ex: dict[str, np.ndarray]) -> np.ndarray:
        n = np.array([sz.lots_for(int(r), float(m)) for r, m in zip(ex["rank"], tr.max_loss, strict=True)])
        be_pts = np.array([BE[int(s)][k - 1] for s, k in zip(ex["struct"], n, strict=True)])
        move = md[tr.row] * np.sqrt(np.maximum(0.0, 355 - tr.entry_m) / 375)
        return np.asarray(np.nan_to_num(move) >= x * be_pts)

    return keep


def main() -> int:
    rows = [sz.run("a", keeper(x), f"R16-x{x}") for x in (2, 4, 6)]
    for r, x in zip(rows, (2, 4, 6), strict=True):
        r["x"] = x
    for i, r in enumerate(rows):
        r["gates"]["neighbours"] = all(rows[j]["net_mean"] > 0 for j in (i - 1, i + 1) if 0 <= j < len(rows))
        le.append_trial(
            {
                "id": r["id"],
                "cycle": 1,
                "idea": f"R15-a + cost-aware filter: expected move >= {r['x']} x break-even",
                "params": {"x": r["x"]},
                "design_net_stressed": r["net_total"],
                "p_screen": r["p"],
                "source": "owner order 4 R16 EXPLORE (cost filter)",
            }
        )
    (ROOT / "data/lab/r16_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    out = pf.board(
        "# R16 BOARD (owner order 4: cost-aware filter on R15-a; DESIGN; stressed ₹ per TRADE, PRE-TAX, "
        "[BACKTEST·in-sample, selection-biased])",
        rows,
    )
    (ROOT / "results/r16_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
