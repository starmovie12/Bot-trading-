"""Owner order 4 R15 (PLAN.md §PREREG-R15): tiers, scale-out, pyramiding only in profit on R14-P3-e3. DESIGN only.

python -m lab.sizing_r15 -> trials.jsonl (3 lines), results/r15_board.md, data/lab/r15_rows.json
"""

import datetime as dt
import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from lab import portfolio_r14 as pf
from tools import bn_economics as be
from tools import engine_of_record as eor
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
TIERS = ((6, 3), (14, 2), (99, 1))  # priority rank (1-based) up to -> lots


def base() -> tuple[le.Trades, np.ndarray, dict[str, np.ndarray], list[str]]:
    allm = json.loads((ROOT / "results/r14_members.json").read_text(encoding="utf-8"))
    ids = [m for m in allm if pf.member(m)[1].size >= 20]
    extra: dict[str, list[np.ndarray]] = {"entry": [], "exit": [], "strike": [], "rank": []}
    for rank, mid in enumerate(ids, start=1):
        tr, cand, path, f, key = pf.member(mid)
        o = pf.matrix(path)[1][key]
        extra["entry"].append(o["entry"][cand])
        extra["exit"].append(o["exit"][cand])
        strike = o["strike"][cand] if "strike" in o else np.round(f["spot"][tr.row[cand]] / 100) * 100
        extra["strike"].append(np.asarray(strike, dtype=float))
        extra["rank"].append(np.full(len(cand), rank))
    tr, prio = pf.union(ids)
    taken = pf.sequence(tr, prio, 3)
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    return tr, taken, {k: np.concatenate(v)[taken] for k, v in extra.items()}, days


def charges(orders: list[tuple[float, int, str]], day: dt.date, c: dict[str, Any]) -> float:
    return float(sum(be.side_charges(Decimal(str(p)) * q, side, day, c) for p, q, side in orders))


def run(variant: str) -> dict[str, Any]:
    tr, taken, ex, days = base()
    lots_map = json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"]
    lots = {e: int(v) for e, v in lots_map.items()}
    c = be.consts()
    lot_of = pf.matrix("data/lab/matrix.npz")[0]["lot"]
    out: dict[str, list[float]] = {k: [] for k in ("gross", "charges", "fill", "net", "max_loss")}
    cache: dict[int, eor.Day] = {}
    for j, i in enumerate(taken):
        d_i, e, x = int(tr.day[i]), int(tr.entry_m[i]), int(tr.exit_m[i])
        day = dt.date.fromisoformat(days[d_i])
        lot = int(lot_of[int(tr.row[i])])
        en, xp, rank = float(ex["entry"][j]), float(ex["exit"][j]), int(ex["rank"][j])
        tier = next(n for r, n in TIERS if rank <= r)
        per_lot = float(tr.max_loss[i])
        n = max(1, min(tier, int(pf.CAP // per_lot))) if per_lot <= pf.CAP else 1
        f1 = float(tr.fill_stressed[i])
        orders = [(en, lot * n, "BUY"), (xp, lot * n, "SELL")]
        gross, fill, mloss = (xp - en) * lot * n, f1 * n, per_lot * n
        if variant in ("b", "c") and (n >= 2 or variant == "c"):
            if d_i not in cache:
                cache.clear()
                cache[d_i] = eor.load_day(ROOT / "data/banknifty/repo", day, lots)
            a = cache[d_i].opts.get((float(ex["strike"][j]), "CE" if tr.dir[i] > 0 else "PE"))
            if a is not None and variant == "b":
                hit = next((m for m in range(e + 1, x) if a["h"][m] > 1.3 * en), -1)
                if hit >= 0:
                    gross = 0.3 * en * lot + (xp - en) * lot * (n - 1)
                    orders = [(en, lot * n, "BUY"), (1.3 * en, lot, "SELL"), (xp, lot * (n - 1), "SELL")]
            if a is not None and variant == "c":
                n, orders, gross, fill, mloss = 1, [(en, lot, "BUY"), (xp, lot, "SELL")], (xp - en) * lot, f1, per_lot
                k = next((m for m in range(e + 1, x - 1) if not math.isnan(a["c"][m]) and a["c"][m] >= 1.3 * en), -1)
                add_px = a["o"][k + 1] if k >= 0 and a["live"][k + 1] and a["o"][k + 1] > 0 else math.nan
                if not math.isnan(add_px):
                    room = int((pf.CAP / lot - en - 10) // add_px)  # whole position premium (+ ~₹300 costs) <= the cap
                    add = max(0, min(tier - 1, room))
                    if add:
                        s = max(en, (add * add_px + 0.7 * en) / (add + 1))
                        out_px = xp
                        for m in range(k + 2, x + 1):
                            if not math.isnan(a["l"][m]) and a["l"][m] <= s:
                                out_px = min(s, a["o"][m]) if not math.isnan(a["o"][m]) else s
                                break
                        gross = (out_px - en) * lot + (out_px - add_px) * lot * add
                        orders = [(en, lot, "BUY"), (add_px, lot * add, "BUY"), (out_px, lot * (1 + add), "SELL")]
                        fill, mloss = f1 * (1 + add), (en + add * add_px) * lot + 300.0
                        n = 1 + add
        ch = charges(orders, day, c)
        out["gross"].append(gross)
        out["charges"].append(ch)
        out["fill"].append(fill)
        out["net"].append(gross - 1.5 * ch - fill)
        out["max_loss"].append(mloss)
    k = len(taken)
    arr = {key: np.array(v) for key, v in out.items()}
    t2 = le.Trades(
        np.arange(k),
        tr.day[taken],
        tr.t[taken],
        tr.dir[taken],
        tr.entry_m[taken],
        tr.exit_m[taken],
        arr["gross"],
        arr["charges"],
        arr["fill"],
        arr["net"],
        arr["gross"] - arr["charges"],
        arr["max_loss"],
        np.zeros(k),
        tr.vix[taken],
    )
    return pf.evaluate(f"R15-{variant}", t2, np.arange(k))


def main() -> int:
    rows = [run(v) for v in ("a", "b", "c")]
    for r in rows:
        r["gates"]["neighbours"] = True  # no grid neighbour in R15: the tiers are one pre-registered rule
        le.append_trial(
            {
                "id": r["id"],
                "cycle": 1,
                "idea": f"R14-P3-e3 + sizing variant {r['id'][-1]}",
                "params": {"variant": r["id"][-1], "tiers": TIERS},
                "design_net_stressed": r["net_total"],
                "p_screen": r["p"],
                "source": "owner order 4 R15 EXPLORE (sizing)",
            }
        )
    (ROOT / "data/lab/r15_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    out = pf.board(
        "# R15 BOARD (owner order 4: sizing on R14-P3-e3; DESIGN; stressed ₹ per TRADE (all lots), PRE-TAX, "
        "[BACKTEST·in-sample, selection-biased])",
        rows,
    )
    (ROOT / "results/r15_board.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
