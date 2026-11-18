"""Owner order 5 R25 (PLAN.md §PREREG-R25): long ATM straddle when realised vol beats implied. RESEARCH ONLY.

python -m lab.straddle_r25 -> data/lab/matrix_r25.npz, trials.jsonl (15 lines), results/r25_board.md
"""

import datetime as dt
import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from lab import nested_r17 as nr
from lab import portfolio_r14 as pf
from lab import shrink_r19 as sh
from lab import universe as uv
from tools import bn_economics as be
from tools import engine_of_record as eor
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
ROWS = 61


def day_rows(d: eor.Day, base: int, spot: np.ndarray, c: dict[str, Any]) -> dict[str, list[dict[str, float]]]:
    out: dict[str, list[dict[str, float]]] = {"SX1": [], "SX2": []}
    costs = eor.StressedCosts()
    for j in range(ROWS):
        t, s0 = 15 + 5 * j, float(spot[j])
        if math.isnan(s0):
            continue
        atm = float(round(s0 / 100) * 100)
        ce, pe = d.opts.get((atm, "CE")), d.opts.get((atm, "PE"))
        if ce is None or pe is None:
            continue
        e = next(
            (m for m in range(t, min(t + 3, eor.FORCE_FLAT)) if all(a["live"][m] and a["o"][m] > 0 for a in (ce, pe))),
            -1,
        )
        if e < 0:
            continue
        deb = ce["o"][e] + pe["o"][e]
        for ex in ("SX1", "SX2"):
            x, val, stale = eor.FORCE_FLAT, math.nan, False
            if ex == "SX2":
                for m in range(e, eor.FORCE_FLAT + 1):
                    lo = ce["l"][m] + pe["l"][m]
                    if not math.isnan(lo) and lo <= 0.70 * deb:
                        x, val = m, lo
                        break
            if math.isnan(val):
                cl = [
                    next((a["c"][k] for k in range(x, e - 1, -1) if not math.isnan(a["c"][k])), math.nan)
                    for a in (ce, pe)
                ]
                if any(math.isnan(v) for v in cl):
                    continue
                val = cl[0] + cl[1]
                stale = not (ce["live"][x] and pe["live"][x])
            share = val / deb  # split the exit value across the legs by their entry weights (charges only)
            ch = sum(
                float(be.round_trip(Decimal(str(a["o"][e])), Decimal(str(a["o"][e] * share)), d.lot, d.day, c))
                for a in (ce, pe)
            )
            fill = float(costs.fill_stressed(2, d.lot, (e, x), d.expiry == d.day, stale))
            gross = (val - deb) * d.lot
            out[ex].append(
                {
                    "row": base + j,
                    "dir": 1,
                    "t": t,
                    "entry_m": e,
                    "exit_m": x,
                    "gross": gross,
                    "charges": ch,
                    "fill": fill,
                    "net": gross - 1.5 * ch - fill,
                    "max_loss": deb * d.lot + 1.5 * ch + fill,
                }
            )
    return out


def build() -> dict[str, le.Trades]:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    f = pf.matrix("data/lab/matrix_r11.npz")[0]
    spot = f["spot"].reshape(-1, ROWS)
    c = be.consts()
    rows: dict[str, list[dict[str, float]]] = {"SX1": [], "SX2": []}
    for i, ds in enumerate(days):
        d = eor.load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(ds), lots)
        for k, v in day_rows(d, i * ROWS, spot[i], c).items():
            rows[k] += v
    arrays: dict[str, Any] = {
        f"O_{k}|STRADDLE_{col}": np.array([r[col] for r in v], dtype=float) for k, v in rows.items() for col in v[0]
    }
    np.savez_compressed(ROOT / "data/lab/matrix_r25.npz", **arrays)
    out = {}
    for k, v in rows.items():
        a = {col: np.array([r[col] for r in v], dtype=float) for col in v[0]}
        row = a["row"].astype(int)
        out[k] = le.Trades(
            row,
            row // ROWS,
            a["t"].astype(int),
            a["dir"].astype(int),
            a["entry_m"].astype(int),
            a["exit_m"].astype(int),
            a["gross"],
            a["charges"],
            a["fill"],
            a["net"],
            a["gross"] - a["charges"],
            a["max_loss"],
            np.zeros(len(row)),
            f["vix"][row],
        )
    return out


def main() -> int:
    trs = build()
    f = pf.matrix("data/lab/matrix_r11.npz")[0]
    t = f["t"]
    win = (t >= 45) & (t <= 255)
    masks = {f"R25-1-{x}": win & (np.nan_to_num(f["rv_iv"]) >= x) for x in (1.0, 1.2, 1.4)}
    masks |= {f"R25-2-{x}": win & (np.nan_to_num(f["rv5"]) >= x * f["rv30"]) for x in (1.5, 2.0, 2.5)}
    masks["R25-3-every-day"] = t == 45
    side = np.ones(len(t), dtype=int)
    setups = []
    z = np.load(ROOT / "data/lab/pbo_matrix.npz")
    names, mat = list(z["names"]), z["m"]
    for mid, m in masks.items():
        for ex, tr in trs.items():
            s = uv.Setup(
                f"{mid}-{ex}",
                None,
                "data/lab/matrix_r25.npz",
                f"{ex}|STRADDLE",
                tr,
                le.select(tr, m, side),
                m,
                side,
                (45, 255),
                True,
                2,
            )
            setups.append(s)
            col = uv.alone_daily(s)
            names.append(s.id)
            mat = np.column_stack([mat, col])
            tk = le.sequence(tr, s.cand)
            le.append_trial(
                {
                    "id": s.id,
                    "cycle": 1,
                    "idea": f"long ATM straddle (research only): {mid}, exit {ex}",
                    "params": {"setup": mid, "exit": ex},
                    "design_net_stressed": round(float(col.sum()), 2),
                    "p_screen": None,
                    "source": f"owner order 5 R25 DESIGN alone ({len(tk)} trades)",
                }
            )
            print(
                s.id,
                len(tk),
                round(float(tr.net_stressed[tk].mean()), 1) if len(tk) else None,
                round(float(tr.gross[tk].mean()), 1) if len(tk) else None,
            )
    np.savez_compressed(ROOT / "data/lab/pbo_matrix.npz", names=np.array(names), m=mat)
    from lab import meta_r18 as mr  # noqa: PLC0415

    parts = []
    for b in range(1, 5):
        test = nr.block(b)
        members = mr.select_mb(setups, np.arange(0, test[0] - 1))
        parts.append(sh.trade_lots(members, [1] * len(members), test))
    res = {"R25-n": sh.concat(parts)}
    meta = {"R25-n": {"idea": "nested portfolio of the long-straddle setups (research only)", "params": {"lots": 1}}}
    return sh.finish(res, meta, "R25", "long straddle when realised vol beats implied (research only)")


if __name__ == "__main__":
    raise SystemExit(main())
