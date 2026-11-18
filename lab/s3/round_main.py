# ruff: noqa: E501 (card lines)
"""Driver for S3 rounds R1-R12 (§13.3). `python -m lab.s3.round_main plan R1` prints the PLAN.md grid block;
`python -m lab.s3.round_main run R1` runs the round after preflight (grid committed first)."""

from __future__ import annotations

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)

import json
import sys
from collections import Counter
from typing import Any

from lab.s3 import report as rp
from lab.s3.registry import Cfg
from lab.s3.rounds import (
    Round,
    apply,
    commit_round,
    evaluate,
    finish,
    log,
    preflight_or_die,
    run_round,
    test_trades,
    to_json,
)

T1P = Cfg("T1-P")


def r1(b: Cfg, k: int) -> list[Cfg]:
    g = [
        apply(b, {"G1_TRIGGER_PTS": g1, "SL_INIT_PTS": sl, "EXIT_MODE": x})
        for g1 in (5, 8, 12)
        for sl in (12, 18)
        for x in ("X-A", "X-B")
    ]
    return [*g, apply(b, fl={"FLAG_N13": True})]


def r2(b: Cfg, k: int) -> list[Cfg]:
    return [apply(b, {"STRIKE_MODE": m}) for m in ("DELTA_BAND", "N6", "N15")]


def r3(b: Cfg, k: int) -> list[Cfg]:
    return [
        apply(b, {"EXIT_MODE": "X-C"}),
        apply(b, {"EXIT_MODE": "X-D"}),
        apply(b, {"N2_K": 1.0}, {"FLAG_N2": True}),
        apply(b, {"N2_K": 1.5}, {"FLAG_N2": True}),
        apply(b, fl={"FLAG_N7": True}),
        apply(b, fl={"FLAG_N12": True}),
        apply(b, fl={"FLAG_N14": True}),
    ]


R4_FLAGS = ("FLAG_K25", "FLAG_K26", "FLAG_K27", "FLAG_K28")


def r4(b: Cfg, k: int) -> list[Cfg]:
    return [apply(b, fl={f: True}) for f in R4_FLAGS]


def r4_pair(b: Cfg, k: int, scored: list[tuple[Cfg, float]]) -> list[Cfg]:
    singles = [(c, s) for c, s in scored if sum(c.flag(f) for f in R4_FLAGS) - sum(b.flag(f) for f in R4_FLAGS) == 1]
    top = sorted(singles, key=lambda x: -x[1])[:2]
    if len(top) < 2:
        return []
    fl = {f: True for c, _ in top for f in R4_FLAGS if c.flag(f) and not b.flag(f)}
    return [apply(b, fl=fl)]


def r5(b: Cfg, k: int) -> list[Cfg]:
    return [
        apply(b, {"ENTRY_ENGINE": "STEP"}),
        apply(b, {"ENTRY_ENGINE": "TRAIL_BUY"}),
        apply(b, checks=("K12",)),
        apply(b, {"DECISION_START": "09:30"}),
        apply(b, {"SIGNAL_SRC": "FUT"}),
    ]


def r6(b: Cfg, k: int) -> list[Cfg]:
    return [apply(b, {"P3_MODE": m}, {"FLAG_P3": True}) for m in ("ALL", "CHOP", "PM")]


def r8(b: Cfg, k: int) -> list[Cfg]:
    return [apply(b, {"LOT_MODE": m}) for m in ("L1", "L2", "L3", "RISK", "RISK+L2")]


def r9(b: Cfg, k: int) -> list[Cfg]:
    grid = [apply(b, {"MAX_TRADES_DAY": m, "LOSS_COOLDOWN_MIN": c}) for m in (4, 6, 10, 15) for c in (10, 20)]
    slots: dict[str, float] = {}
    for t in evaluate(b).trades:
        if t["wf_window"] <= k:
            slots[t["slot"]] = slots.get(t["slot"], 0.0) + t["net_base"]
    neg = tuple(sorted(s for s, v in slots.items() if v < 0))
    out = list(grid)
    if neg:
        out.append(apply(b, slots=neg))
        out.append(apply(b, slots=(min(slots, key=lambda s: slots[s]),)))
    return out


R11_IDEAS: list[dict[str, Any]] = []  # filled from PLAN.md before R11 (pre-registered)
R12_IDEAS: list[dict[str, Any]] = []


def from_ideas(ideas: list[dict[str, Any]]) -> Any:
    def gen(b: Cfg, k: int) -> list[Cfg]:
        return [apply(b, i.get("overrides"), i.get("flags"), tuple(i.get("checks", ()))) for i in ideas]

    return gen


ROUNDS: dict[str, Round] = {
    "R1": Round("R1", r1),
    "R2": Round("R2", r2),
    "R3": Round("R3", r3),
    "R4": Round("R4", r4, stage2=r4_pair),
    "R5": Round("R5", r5),
    "R6": Round("R6", r6),
    "R7": Round("R7", lambda b, k: [], forward=True),
    "R8": Round("R8", r8),
    "R9": Round("R9", r9),
    "R10": Round("R10", lambda b, k: [], backward=True),
}
NEXT = {
    "R1": "R2 (strike: DELTA_BAND, N6, N15)",
    "R2": "R3 (exit: X-C, X-D, N2 k1.0/1.5, N7, N12, N14)",
    "R3": "R4 (filters K25-K28 akele + sabse achhe do ka jod)",
    "R4": "R5 (entry: STEP, TRAIL_BUY, K12, N10, N16)",
    "R5": "R6 (P3: sab / sirf CHOP / sirf 13:15 ke baad)",
    "R6": "R7 (checks ka forward selection, family se max 2, max 6 kadam)",
    "R7": "R8 (lots: L1, L2, L3, RISK, RISK+L2)",
    "R8": "R9 (MAX_TRADES x cool-off; N9 samay ke khaane)",
    "R9": "R10 (har training window mein R1-R9 ka chunaav dobara)",
    "R10": "R11 (agent ideas, 2-way params / do modules)",
    "R11": "R12 (agent ideas)",
    "R12": "FINAL card (§13.9)",
}


def plan_block(name: str) -> str:
    rnd = ROUNDS[name]
    cfgs = [T1P, *rnd.gen(T1P, 1)]
    if rnd.forward or rnd.backward:
        cfgs = [T1P]
    return f"<!-- S3-GRID {name} -->\n```json\n{json.dumps([to_json(c) for c in cfgs])}\n```"


def note(res: dict[str, Any]) -> str:
    before = sum(t["net_base"] for k, b in res["bases_before"].items() for t in test_trades(evaluate(b), k))
    now = sum(t["net_base"] for t in res["oos"])
    picks = Counter(h["chosen"] for h in res["history"].values()).most_common(1)[0]
    kept = sum(1 for k, c in res["chosen"].items() if c.config_hash() == res["bases_before"][k].config_hash())
    return f"training ne {4 - kept}/4 window mein badlaav chuna (sabse aam: {picks[0]}); OOS {rp.rs(before)} (pichhla base) → {rp.rs(now)}."


def main(argv: list[str]) -> int:
    act, name = argv[0], argv[1]
    if act == "plan":
        print(plan_block(name))
        return 0
    if name in ("R11", "R12"):
        ideas = preflight_or_die(name)
        ROUNDS[name] = Round(
            name, from_ideas([{"overrides": c.overrides, "flags": c.flags, "checks": c.checks} for c in ideas[1:]])
        )
    else:
        preflight_or_die(name)
    res = run_round(ROUNDS[name], preflight_or_die(name))
    log(name, f"fits {res['fits']}; nulls next")
    card = finish(name, res, (note(res), NEXT[name]))
    commit_round(name, res, card)
    print(card)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
