"""F6 (owner order 2; not a trial): break-even in index points by strike type and hold time. DESIGN only.

  python -m lab.f6_table -> results/f6_breakeven.md
For every DESIGN day at 10:00, 11:30 and 13:00 and both sides: strike ITM2 (200 points in the money), ITM1, ATM,
CAP15 (nearest-ATM strike with premium x lot <= ₹15,000, walking OTM). Empirical delta = slope of the option change on
the signed index change over 30 / 60 min (least squares through the origin after removing the mean); decay = the
option change per hour when the index is unchanged (the regression intercept). Stressed cost per unit = (stressed
charges + fill) / lot as the engine applies it. Break-even = (cost per unit + decay x hold) / delta.
"""

import datetime as dt
import json
import math
from decimal import Decimal
from pathlib import Path

import numpy as np

from lab import build_r2 as b2
from tools import bn_economics as be
from tools import engine_of_record as eor

ROOT = Path(__file__).resolve().parent.parent
TIMES, HOLDS = (45, 135, 225), (30, 60)


def main() -> int:
    days = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))["design"]
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    costs, c = eor.StressedCosts(), be.consts()
    rec: dict[tuple[str, int], list[tuple[float, float, float, float]]] = {}
    for ds in days[::3]:  # every third DESIGN day keeps the run short; a table, not a test
        d = eor.load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(ds), lots)
        ic = [b.c for b in d.index]
        for t in TIMES:
            s0 = ic[t - 1]
            if math.isnan(s0):
                continue
            atm = round(s0 / 100) * 100
            for side, typ in ((1, "CE"), (-1, "PE")):
                strikes = {"ITM2": atm - side * 200, "ITM1": atm - side * 100, "ATM": atm}
                for k in range(11):
                    a = d.opts.get((float(atm + side * 100 * k), typ))
                    if a and a["o"][t] > 0 and a["o"][t] * d.lot <= b2.CAP_RS:
                        strikes["CAP15"] = atm + side * 100 * k
                        break
                for name, kk in strikes.items():
                    a = d.opts.get((float(kk), typ))
                    if not a or not a["o"][t] > 0:
                        continue
                    p0 = a["o"][t]
                    ch = float(Decimal("1.5") * be.round_trip(Decimal(str(p0)), Decimal(str(p0)), d.lot, d.day, c))
                    cost_u = (ch + float(costs.fill_stressed(1, d.lot, (t, t + 60), d.expiry == d.day, False))) / d.lot
                    for h in HOLDS:
                        p1, s1 = a["c"][t + h], ic[t + h]
                        if not math.isnan(p1) and not math.isnan(s1):
                            rec.setdefault((name, h), []).append((side * (s1 - s0), p1 - p0, cost_u, p0))
    lines = [
        "# F6 BREAK-EVEN TABLE (owner order 2; not a trial; DESIGN, every 3rd day, 10:00 / 11:30 / 13:00, both sides)",
        "",
        "Index points the trade must move in its favour to cover stressed costs and the option's decay over the "
        "hold. [BACKTEST·in-sample, empirical]",
        "",
        "| strike | hold | samples | premium (median pts) | delta | decay pts / hour | cost pts / unit "
        "| break-even index pts |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for (name, h), v in sorted(rec.items(), key=lambda x: (x[0][1], ["ITM2", "ITM1", "ATM", "CAP15"].index(x[0][0]))):
        arr = np.array(v)
        x, y = arr[:, 0], arr[:, 1]
        delta = float(np.polyfit(x, y, 1)[0])
        decay = float(np.polyfit(x, y, 1)[1]) * 60 / h
        cost = float(np.median(arr[:, 2]))
        be_pts = (cost - min(decay, 0) * h / 60) / delta if delta > 0 else float("nan")
        lines.append(
            f"| {name} | {h} min | {len(arr)} | {np.median(arr[:, 3]):.0f} | {delta:.2f} | {decay:.1f} | {cost:.2f} | "
            f"{be_pts:.1f} |"
        )
    lines += [
        "",
        "Reading: the lower the break-even, the smaller the index move each trade needs. Choose the strike per",
        "signal by this table only inside a pre-registered round (each choice is then a trial).",
    ]
    (ROOT / "results/f6_breakeven.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
