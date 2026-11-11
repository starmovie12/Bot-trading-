#!/usr/bin/env python3
"""Arithmetic war room (MISSION V11 §9, T08): at least 8 candidate families mapped to U1-U6, at least 3
unconventional, ARITHMETIC kill only (deterministic: lot cost, margin, charges, by-construction loss).

  war_room.py                 write docs/WAR_ROOM.md and EVIDENCE/T08/families.json from EVIDENCE/T04/g0.json
  war_room.py --check FILE    check a families JSON: >= 8 families, >= 3 unconventional, every row has a
                              number with a tag, no kill rests on SIM, and no kill rests on a non-SOURCE fact or an
                              unapproved limit (§5.1); exit 1 on any problem

A kill is valid only on SOURCE facts and OWNER / approved limits (§5.1, §8.1). In a session without web
access every fact is HISTORY, so a family can only be "ALIVE (conditional)" with the condition that would
kill it written next to it. NEGATIVE.md receives a row only for a valid kill.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
KILL_OK_TAGS = {"SOURCE", "REAL", "OWNER", "CODE(SOURCE)", "CODE(REAL)", "CODE(OWNER)"}


def g0() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((ROOT / "EVIDENCE/T04/g0.json").read_text(encoding="utf-8"))
    return data


def families(r: dict[str, Any]) -> list[dict[str, Any]]:
    u1 = r["members"]["U1"]["rows"]
    u3 = r["members"]["U3"]["rows"]
    u5 = r["members"]["U5"]["rows"]
    u6 = r["members"]["U6"]["rows"]
    s0 = r["stages"]["S0_MANUAL"]["cost_hurdle_per_trade_rs"]
    nifty, sensex = u1["NIFTY"], u1["SENSEX"]

    def row(**kw: Any) -> dict[str, Any]:
        kw.setdefault("killed", False)
        return kw

    return [
        row(
            id="a",
            name="No-trade-heavy: only the best 5-12 setups a month, cash otherwise",
            members=["U1", "U2"],
            kind="unconventional",
            edge="COST: fewer round trips, so less of the fixed and per-trade cost",
            loser="nobody directly; it avoids paying the spread and charges on weak setups",
            numbers=[("cost hurdle per trade at 4 trades a month (S0 MANUAL)", s0["4"])],
            dies_if="the measured edge per trade stays below the hurdle per trade (REAL data)",
            falsify="Recorder data: count qualifying setups a month; if fewer than 4, the hurdle per trade explodes",
        ),
        row(
            id="b",
            name="Defined-risk premium selling (credit spread / condor)",
            members=["U3"],
            kind="conventional",
            edge="RISK PREMIUM: option sellers are paid for carrying crash risk",
            loser="buyers who overpay for options (volatility risk premium)",
            numbers=[
                (
                    "minimum credit per unit for a one-step Nifty spread to fit the trade-loss limit",
                    u3["NIFTY"]["min_credit_per_unit_to_fit_rs"],
                )
            ],
            dies_if="hedged margin (unknown) above capital, or the credit needed per unit is never offered (REAL "
            "chain)",
            falsify="one official margin figure for a one-step spread + one week of Recorder option chains",
        ),
        row(
            id="c",
            name="Option buying with IV-percentile, event and time-stop filters",
            members=["U1", "U2"],
            kind="conventional",
            edge="weak: direction ('where price goes'); the filters only avoid the worst trades",
            loser="unclear; buyers pay the volatility premium on average",
            numbers=[
                ("max Nifty premium per unit that fits the trade-loss limit", nifty["max_fit_premium_per_unit_rs"]),
                ("round-trip charges at that premium", nifty["round_trip_charges_at_fit_rs"]),
            ],
            dies_if="charges + fill cost exceed the average gain per trade (REAL data), or only far-OTM strikes fit",
            falsify="random-entry null on Recorder data with the same exits (T10 harness)",
        ),
        row(
            id="d",
            name="Expiry-day structure (gamma / pinning on the weekly expiry)",
            members=["U1", "U2", "U3"],
            kind="conventional",
            edge="STRUCTURAL in part: dealer hedging near the expiry strike",
            loser="late sellers / hedgers forced to adjust",
            numbers=[
                ("max Sensex premium per unit that fits the trade-loss limit", sensex["max_fit_premium_per_unit_rs"])
            ],
            dies_if="the D10 exercise-STT trap is not avoidable inside the session close; expiring contracts close "
            "15:30",
            falsify="replay the last expiry days from Recorder data; count setups and slippage near the close",
        ),
        row(
            id="e",
            name="Time of day (opening range, closing hour, lunch lull)",
            members=["U1"],
            kind="conventional",
            edge="weak: intraday seasonality, widely known",
            loser="unclear",
            numbers=[("Nifty fill cost per round trip at the fitting premium", nifty["fill_cost_at_fit_rs"])],
            dies_if="the fill cost alone is a large share of the premium paid (REAL spreads)",
            falsify="Recorder spreads by minute of day; the setup must clear spread + charges in the cheapest hour",
        ),
        row(
            id="f",
            name="Gap / event (IV crush before and after scheduled events)",
            members=["U1", "U3"],
            kind="conventional",
            edge="RISK PREMIUM: implied volatility drops after events",
            loser="event buyers who overpay for implied volatility",
            numbers=[
                (
                    "minimum credit per unit for a one-step Sensex spread to fit the trade-loss limit",
                    u3["SENSEX"]["min_credit_per_unit_to_fit_rs"],
                )
            ],
            dies_if="no official event calendar (UNVERIFIED) or the post-event move exceeds the defined width",
            falsify="an official event list + Recorder IV before / after the next 5 events",
        ),
        row(
            id="g",
            name="Breadth / heavyweight lead-lag (index heavyweights lead the index)",
            members=["U1"],
            kind="unconventional",
            edge="STRUCTURAL: index arbitrage and ETF flows lag the heavyweights by seconds",
            loser="slow index-option quotes, if any lag survives costs",
            numbers=[
                ("max Nifty premium per unit that fits the trade-loss limit", nifty["max_fit_premium_per_unit_rs"])
            ],
            dies_if="the lag is shorter than the order latency or smaller than the spread (latency is no edge at "
            "this size)",
            falsify="Recorder: heavyweight and index ticks with both timestamps; measure the lag distribution",
        ),
        row(
            id="h",
            name="Non-options: equity intraday (cash) and index ETF delivery",
            members=["U5", "U6"],
            kind="unconventional",
            edge="COST: no option spread, no theta; RISK PREMIUM for the ETF (equity premium)",
            loser="nobody; the ETF earns the market return",
            numbers=[
                ("U5 max notional by construction", u5["max_notional_by_construction_rs"]),
                ("U6 max notional by construction (max loss = notional)", u6["max_notional_by_construction_rs"]),
            ],
            dies_if="by-construction loss (notional × band, or the notional itself) caps the size so low that "
            "charges dominate",
            falsify="official equity / ETF charge rows (T03 with web) + the I7 bound at the owner's chosen limit",
        ),
        row(
            id="i",
            name="Own idea: MANUAL low-frequency debit spreads (no server, no static IP)",
            members=["U2"],
            kind="unconventional",
            edge="COST: MANUAL execution removes the static-IP server cost (lever 6)",
            loser="as family c, with a defined and smaller premium outlay",
            numbers=[("S0 MANUAL cost hurdle per trade at 8 trades a month", s0["8"])],
            dies_if="the owner cannot place orders within minutes of the signal, or REAL spreads on two legs eat the "
            "edge",
            falsify="Recorder two-leg spreads at signal time + a timed owner dry-run of placing the order by hand",
        ),
    ]


def check(fams: list[dict[str, Any]]) -> list[str]:
    problems = []
    if len(fams) < 8:
        problems.append(f"only {len(fams)} families (need 8)")
    if sum(1 for f in fams if f.get("kind") == "unconventional") < 3:
        problems.append("fewer than 3 unconventional families")
    for f in fams:
        nums = f.get("numbers") or []
        if not nums or not all(isinstance(v, dict) and v.get("value") and v.get("tag") for _, v in nums):
            problems.append(f"family {f.get('id')}: needs at least one number with a tag")
        if not set(f.get("members", [])) <= {"U1", "U2", "U3", "U4", "U5", "U6"} or not f.get("members"):
            problems.append(f"family {f.get('id')}: bad universe members")
        if f.get("killed"):
            tags = {v["tag"] for _, v in nums}
            if any("SIM" in t for t in tags):
                problems.append(f"family {f.get('id')}: a kill rests on SIM")
            elif not tags <= KILL_OK_TAGS:
                problems.append(f"family {f.get('id')}: a kill rests on a non-SOURCE fact or an unapproved limit")
    return problems


def write(fams: list[dict[str, Any]], r: dict[str, Any]) -> None:
    out = ROOT / "EVIDENCE/T08"
    out.mkdir(parents=True, exist_ok=True)
    (out / "families.json").write_text(json.dumps(fams, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# WAR ROOM (T08, arithmetic only)",
        "",
        f"Inputs: EVIDENCE/T04/g0.json (G0 {r['g0']}, inputs sha256 {r['inputs_sha256'][:16]}); families: "
        "EVIDENCE/T08/families.json. Every fact is HISTORY this session (no web: INCIDENT #1) and the trade-loss "
        "limit rests on unapproved defaults, so **no arithmetic kill is valid yet** (§5.1): each family is ALIVE "
        "(conditional) with the condition that would kill it. SIM is never used.",
        "",
        "| id | family | members | kind | source of edge | number [tag] | dies if | cheapest falsification |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f in fams:
        nums = "; ".join(f"{label}: ₹{v['value']} [{v['tag']}]" for label, v in f["numbers"])
        lines.append(
            f"| {f['id']} | {f['name']} | {', '.join(f['members'])} | {f['kind']} | {f['edge']} | {nums} | "
            f"{f['dies_if']} | {f['falsify']} |"
        )
    n_unc = sum(1 for f in fams if f["kind"] == "unconventional")
    lines += ["", f"Families: {len(fams)}; unconventional: {n_unc} (a, g, h, i); killed: 0 (no valid kill basis yet)."]
    (ROOT / "docs/WAR_ROOM.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    if argv[:1] == ["--check"] and len(argv) == 2:
        problems = check(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        for p in problems:
            print(f"PROBLEM {p}")
        print(f"war room check: {len(problems)} problem(s)")
        return 1 if problems else 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 64
    r = g0()
    fams = families(r)
    problems = check(fams)
    if problems:
        print("\n".join(problems))
        return 1
    write(fams, r)
    print(f"{len(fams)} families written (docs/WAR_ROOM.md, EVIDENCE/T08/families.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
