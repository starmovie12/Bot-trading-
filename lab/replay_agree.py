"""AGREE between the lab and the engine of record (MISSION V19 RULES K5, ST9): python -m lab.replay_agree.

Writes results/replay_agreement.json (key vec_vs_eor), results/replay_mismatch.csv and data/lab/eor_trades.json.
"""

import json
import sys
from typing import Any

from tools import engine_of_record as eor
from tools.engine_of_record import ROOT


def agree(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> dict[str, Any]:
    """RULES K5: match on date, strike, type, expiry, entry minute and exit reason, |net difference| <= max(₹2, 1%)."""
    key = ("day", "strike", "type", "expiry", "entry_m", "reason")
    left = {tuple(x[k] for k in key): x for x in a}
    matched = [
        k
        for k, x in left.items()
        if any(
            tuple(y[k2] for k2 in key) == k and abs(y["net"] - x["net"]) <= max(2.0, 0.01 * abs(x["net"])) for y in b
        )
    ]
    union = len(a) + len(b) - len(matched)
    rate = len(matched) / union if union else 0.0
    mism = union - len(matched)
    ok = union > 0 and (rate >= 0.99 if union >= 100 else mism <= 1)
    return {
        "n_lab": len(a),
        "n_eor": len(b),
        "matched": len(matched),
        "union": union,
        "agreement": round(rate, 4),
        "pass": ok,
    }


REASONS = {1: "stop", 2: "breakeven", 3: "target", 4: "scratch", 5: "time", 6: "force_flat", 7: "no_bar"}


def lab_trades() -> list[dict[str, Any]]:
    """The carried candidate A1+b1 as the lab sees it (tools/lab_eval.py, lab/ideas.py)."""
    import numpy as np  # noqa: PLC0415

    from lab import ideas  # noqa: PLC0415
    from tools import lab_eval as le  # noqa: PLC0415

    feats, outs, days = le.load()
    idea = next(i for i in ideas.BRACKET if i.id == "A1")
    mask, direction = idea.rule(feats, idea.params)
    tr = le.trades(feats, outs["EXIT0|LONG"], days)
    taken = le.sequence(tr, le.select(tr, np.nan_to_num(mask & (feats["vix_chg"] < 0)).astype(bool), direction))
    expiries = sorted(json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"])
    out = []
    for i in taken:
        d = days[tr.day[i]]
        out.append(
            {
                "day": d,
                "strike": float(round(feats["spot"][tr.row[i]] / 100) * 100),
                "type": "CE" if tr.dir[i] > 0 else "PE",
                "expiry": min(e for e in expiries if e >= d),
                "entry_m": int(tr.entry_m[i]),
                "reason": REASONS[int(outs["EXIT0|LONG"]["reason"][i])],
                "net": round(float(tr.net_stressed[i]), 2),
            }
        )
    return out


def main(argv: list[str]) -> int:
    if argv:
        print(__doc__, file=sys.stderr)
        return 64
    from bot.strategy.orb_vix import OrbVix  # noqa: PLC0415

    days = json.loads((ROOT / "data/lab/split.json").read_text())["design"]
    trades = eor.run(days, OrbVix())
    b = [
        {
            "day": str(t.day),
            "strike": t.legs[0].strike,
            "type": t.legs[0].opt_type,
            "expiry": str(t.legs[0].expiry),
            "entry_m": t.entry_minute,
            "reason": t.exit_reason,
            "net": float(t.net_stressed_rs),
        }
        for t in trades
    ]
    a = lab_trades()
    res = agree(a, b) | {"slice": "DESIGN, carried candidate A1+b1 (EXIT0, LONG)"}
    path = ROOT / "results/replay_agreement.json"
    allres = json.loads(path.read_text()) if path.is_file() else {}
    path.write_text(json.dumps(allres | {"vec_vs_eor": res}, indent=1) + "\n")
    (ROOT / "data/lab/eor_trades.json").write_text(json.dumps(b, indent=0) + "\n")
    keys = ("day", "strike", "type", "expiry", "entry_m", "reason")
    seen_b = {tuple(y[k] for k in keys): y for y in b}
    rows = ["side,day,strike,type,expiry,entry_m,reason,net_lab,net_eor"]
    for x in a:
        y = seen_b.get(tuple(x[k] for k in keys))
        if y is None or abs(y["net"] - x["net"]) > max(2.0, 0.01 * abs(x["net"])):
            rows.append(
                f"lab,{x['day']},{x['strike']},{x['type']},{x['expiry']},{x['entry_m']},{x['reason']},{x['net']},"
                + (str(y["net"]) if y else "")
            )
    seen_a = {tuple(x[k] for k in keys) for x in a}
    rows += [
        f"eor,{y['day']},{y['strike']},{y['type']},{y['expiry']},{y['entry_m']},{y['reason']},,{y['net']}"
        for y in b
        if tuple(y[k] for k in keys) not in seen_a
    ]
    (ROOT / "results/replay_mismatch.csv").write_text("\n".join(rows) + "\n")
    print(res)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
