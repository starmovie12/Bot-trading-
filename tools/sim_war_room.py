#!/usr/bin/env python3
"""SIM war room (MISSION V11 §9 SIM stage, T11): machinery only, tag SIM. SIM can neither kill nor crown a
family, so this file never writes a NEGATIVE.md row.

  sim_war_room.py               run the SIM checks for every family alive after T08 and write
                                EVIDENCE/T11/sim.json, docs/SIM_WAR_ROOM.md and the SIM.* keys of EVIDENCE/numbers.json
  sim_war_room.py --check FILE  check a SIM result file: every family row tagged SIM, both controls behaved, a
                                result (candidates or NONE) recorded; exit 1 on any problem

Per family: a profile (trades a month, option legs per trade: ASSUMPTION, see PROFILES and DECISIONS D-039) and,
from EVIDENCE/T04/g0.json with their own tags, the per-leg charges and fill cost at the fitting Nifty premium, the
S0 MANUAL hurdle per trade (the cheapest stage) and the credible edge per trade. SIM trades are Gaussian around a
planted net edge per trade with sigma = the kindest value of the G0 table. Through the unchanged T10 harness
(tools/truth_tests.py):
  null control     gross edge 0 (net = minus costs): the full harness must FAIL
  planted control  a large net edge, over enough months for min_trades: the full harness must PASS
  power            share of SIM runs over MONTHS whose stressed 95% day-block CI lower bound clears the hurdle
                   (the binding T10 criterion; the stress formula of truth_tests.evaluate), at
                     kind        net edge = hurdle + credible edge (it clears the hurdle by the whole credible edge)
                     kind_fill0  the same net edge with every fill cost at ₹0 (the most favourable fill)
                     needed      the net edge for TARGET_POWER, from SE = sigma / sqrt(N) (a calibration check)
A family is a forward-test candidate iff its power at kind_fill0 reaches TARGET_POWER; none → NONE.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import random
import sys
import tomllib
from pathlib import Path
from statistics import NormalDist, fmean
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import truth_tests as tt  # noqa: E402

Trade = dict[str, Any]
Profile = tuple[int, int]  # (trades a month, option legs per trade)

# Profiles [ASSUMPTION, D-039]: the trade rate is a key of the G0 hurdle table. Family h has no cost row
# (equity / ETF charges are not in constants.toml; T03 needs the web), so it is not run.
PROFILES: dict[str, Profile | None] = {
    "a": (8, 1),
    "b": (4, 2),
    "c": (12, 1),
    "d": (4, 1),
    "e": (20, 1),
    "f": (4, 2),
    "g": (20, 1),
    "h": None,
    "i": (8, 2),
}
MONTHS = 24  # the longest window of the G0 validation table
DAYS_PER_MONTH = 21  # trading days a month [ASSUMPTION]
SIGMA = 500.0  # ₹ per trade: the kindest sigma of the G0 validation table [ESTIMATE]
RUNS = 50
N_BOOT = 200
NULL_RUNS = 1000
TARGET_POWER = 0.8
PLANTED_SE = 6.0  # the planted control's edge above the stressed hurdle, in standard errors
SEED = 2026


def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def gate_values(gates: dict[str, Any]) -> dict[str, Any]:
    return {k: v["value"] for k, v in gates.items() if isinstance(v, dict) and "value" in v}


def make_trades(
    net_mean: float, prof: Profile, costs: tuple[float, float], months: int, seed: int, sigma: float = SIGMA
) -> list[Trade]:
    """SIM trades, one a day at most, spread evenly over the months; costs = (charges, fill) per leg."""
    per_month, legs = prof
    rng = random.Random(seed)  # noqa: S311 (simulation, not security)
    start = dt.date(2027, 1, 1)
    return [
        {
            "day": str(start + dt.timedelta(days=int(k * DAYS_PER_MONTH / per_month))),
            "net_rs": rng.gauss(net_mean, sigma),
            "charges_rs": costs[0] * legs,
            "slippage_rs": costs[1] * legs,
        }
        for k in range(per_month * months)
    ]


def stress_cut(g: dict[str, Any], prof: Profile, costs: tuple[float, float]) -> float:
    """What truth_tests.evaluate subtracts from each trade's net before the CI (charges and fill stress)."""
    legs = prof[1]
    charges_cut = (float(g["cost_stress_charges_mult"]) - 1) * costs[0] * legs
    fill_cut = (float(g["cost_stress_slippage_mult"]) - 1) * costs[1] * legs
    return charges_cut + fill_cut


def ci_lower_stressed(trades: list[Trade], g: dict[str, Any], n_boot: int) -> float:
    """The same stressed day-block CI lower bound as truth_tests.evaluate (checked equal in the tests)."""
    stressed = [
        {
            **t,
            "net_rs": float(t["net_rs"])
            - (g["cost_stress_charges_mult"] - 1) * float(t["charges_rs"])
            - (g["cost_stress_slippage_mult"] - 1) * float(t.get("slippage_rs", 0)),
        }
        for t in trades
    ]
    lo, _ = tt.block_ci(stressed, g["ci_level"], n_boot=n_boot)
    return lo


def ci_pass(trades: list[Trade], g: dict[str, Any], hurdle: float, n_boot: int = N_BOOT) -> bool:
    if len(trades) < g["min_trades"] or len(tt.by_day(trades)) < g["min_trading_days"]:
        return False
    return ci_lower_stressed(trades, g, n_boot) > hurdle


def power(net_mean: float, prof: Profile, costs: tuple[float, float], hurdle: float, g: dict[str, Any]) -> float:
    wins = sum(ci_pass(make_trades(net_mean, prof, costs, MONTHS, SEED + r), g, hurdle) for r in range(RUNS))
    return wins / RUNS


def null_mean(prof: Profile, costs: tuple[float, float]) -> float:
    return -(costs[0] + costs[1]) * prof[1]


def harness(
    net_mean: float,
    prof: Profile,
    costs: tuple[float, float],
    hurdle: float,
    gates: dict[str, Any],
    months: int,
    null_totals: list[float],
) -> dict[str, Any]:
    """The full T10 harness on one SIM trade list (walk-forward and stability inputs are SIM too)."""
    g = gate_values(gates)
    trades = make_trades(net_mean, prof, costs, months, SEED + 1)
    days = sorted({str(t["day"]) for t in trades})
    wf = []
    for _, test in tt.walk_forward_folds(days, int(g["wf_folds"])):
        window = set(test)
        wf.append(fmean(float(t["net_rs"]) for t in trades if t["day"] in window))
    perturbed = [
        fmean(float(t["net_rs"]) for t in make_trades(net_mean * (0.8 + 0.04 * k), prof, costs, months, SEED + 50 + k))
        for k in range(11)
    ]
    return tt.evaluate(
        trades,
        gates,
        hurdle_per_trade=hurdle,
        null_totals=null_totals,
        wf_fold_expectancies=wf,
        perturbed_expectancies=perturbed,
    )


def tagged(value: Any, tag: str) -> dict[str, Any]:
    return {"value": value, "tag": tag}


def run_family(fam: dict[str, Any], r: dict[str, Any], gates: dict[str, Any], cache: dict[Any, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {"id": fam["id"], "name": fam["name"], "members": fam["members"], "kind": fam["kind"]}
    row["tag"] = "SIM"
    prof = PROFILES.get(fam["id"])
    if prof is None:
        row.update(
            status="NOT_RUN",
            candidate=False,
            why="no cost row: equity / ETF charges are not in constants.toml (T03 needs the web)",
        )
        return row
    g = gate_values(gates)
    per_month, legs = prof
    nifty = r["members"]["U1"]["rows"]["NIFTY"]
    charges_e, fill_e = nifty["round_trip_charges_at_fit_rs"], nifty["fill_cost_at_fit_rs"]
    hurdle_e = r["stages"]["S0_MANUAL"]["cost_hurdle_per_trade_rs"][str(per_month)]
    credible_e = r["validation"][str(per_month)]["credible_edge_per_trade_rs"]
    costs = (float(charges_e["value"]), float(fill_e["value"]))
    hurdle, credible = float(hurdle_e["value"]), float(credible_e["value"])
    row.update(
        status="RUN",
        per_month=tagged(per_month, "ASSUMPTION"),
        legs=tagged(legs, "ASSUMPTION"),
        charges_per_leg_rs=tagged(charges_e["value"], charges_e["tag"]),
        fill_per_leg_rs=tagged(fill_e["value"], fill_e["tag"]),
        hurdle_rs=tagged(hurdle_e["value"], hurdle_e["tag"]),
        credible_rs=tagged(credible_e["value"], credible_e["tag"]),
        stress_cut_rs=tagged(round(stress_cut(g, prof, costs), 2), "SIM"),
        stress_cut_fill0_rs=tagged(round(stress_cut(g, prof, (costs[0], 0.0)), 2), "SIM"),
    )
    n = per_month * MONTHS
    row["trades_in_window"] = tagged(n, "SIM")
    need_n = max(int(g["min_trades"]), int(g["min_trading_days"]))
    months_c = max(MONTHS, math.ceil(need_n / per_month))
    row["months_to_min_trades"] = tagged(round(int(g["min_trades"]) / per_month, 1), "SIM")

    key = (prof, costs, months_c)
    if key not in cache:
        nm = null_mean(prof, costs)
        cache[key] = [
            sum(float(t["net_rs"]) for t in make_trades(nm, prof, costs, months_c, SEED + 1000 + i))
            for i in range(NULL_RUNS)
        ]
    null_totals = cache[key]
    se_c = SIGMA / math.sqrt(per_month * months_c)
    planted = hurdle + stress_cut(g, prof, costs) + PLANTED_SE * se_c
    null_res = harness(null_mean(prof, costs), prof, costs, hurdle, gates, months_c, null_totals)
    planted_res = harness(planted, prof, costs, hurdle, gates, months_c, null_totals)
    row["null_control"] = {"months": months_c, "pass": bool(null_res["pass"]), "ok": not null_res["pass"]}
    row["planted_control"] = {
        "months": months_c,
        "net_rs": tagged(round(planted, 2), "SIM"),
        "pass": bool(planted_res["pass"]),
        "ok": bool(planted_res["pass"]),
    }

    kind = hurdle + credible
    row["kind_net_rs"] = tagged(round(kind, 2), "SIM")
    if n < int(g["min_trades"]) or n < int(g["min_trading_days"]):
        row.update(
            power_kind=tagged(0.0, "SIM"),
            power_kind_fill0=tagged(0.0, "SIM"),
            needed_net_rs=None,
            power_needed=None,
            needed_over_credible=None,
            judgeable_in_window=False,
            candidate=False,
            why=f"{MONTHS} months give {n} trades, below min_trades {g['min_trades']}: the harness cannot judge "
            f"it inside the window",
        )
        return row
    z = NormalDist().inv_cdf
    needed = (
        hurdle
        + stress_cut(g, prof, costs)
        + (z(1 - (1 - g["ci_level"]) / 2) + z(TARGET_POWER)) * (SIGMA / math.sqrt(n))
    )
    p_kind = power(kind, prof, costs, hurdle, g)
    p_fill0 = power(kind, prof, (costs[0], 0.0), hurdle, g)
    p_needed = power(needed, prof, costs, hurdle, g)
    cand = p_fill0 >= TARGET_POWER
    row.update(
        power_kind=tagged(p_kind, "SIM"),
        power_kind_fill0=tagged(p_fill0, "SIM"),
        needed_net_rs=tagged(round(needed, 2), "SIM"),
        power_needed=tagged(p_needed, "SIM"),
        needed_over_credible=tagged(round(needed / credible, 1), "SIM"),
        judgeable_in_window=True,
        candidate=cand,
        why="reaches the target power at the kind edge with fill ₹0"
        if cand
        else "even at the kind edge with every fill at ₹0 the harness passes too rarely",
    )
    return row


def decide(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cands = [x for x in rows if x.get("candidate")]
    cands.sort(key=lambda x: (x["needed_over_credible"]["value"], x["id"]))
    if not cands:
        return {
            "result": "NONE",
            "candidates": [],
            "line": f"NONE: no family reaches {TARGET_POWER:.0%} power in {MONTHS} months of SIM trades, even at "
            "the kind edge (hurdle + credible edge) with every fill at ₹0",
        }
    ids = [x["id"] for x in cands]
    return {
        "result": "CANDIDATES",
        "candidates": ids,
        "line": "forward-test candidates (SIM-ranked, by needed / credible): " + ", ".join(ids),
    }


def compute() -> dict[str, Any]:
    r = json.loads((ROOT / "EVIDENCE/T04/g0.json").read_text(encoding="utf-8"))
    fams = json.loads((ROOT / "EVIDENCE/T08/families.json").read_text(encoding="utf-8"))
    gates = tomllib.loads((ROOT / "gates.toml").read_text(encoding="utf-8"))
    alive = [f for f in fams if not f.get("killed")]
    cache: dict[Any, Any] = {}
    rows = [run_family(f, r, gates, cache) for f in alive]
    return {
        "inputs": {
            "EVIDENCE/T04/g0.json": sha("EVIDENCE/T04/g0.json"),
            "EVIDENCE/T08/families.json": sha("EVIDENCE/T08/families.json"),
            "gates.toml": sha("gates.toml"),
            "tools/truth_tests.py": sha("tools/truth_tests.py"),
        },
        "settings": {
            "months": tagged(MONTHS, "ASSUMPTION"),
            "days_per_month": tagged(DAYS_PER_MONTH, "ASSUMPTION"),
            "sigma_rs": tagged(SIGMA, "ESTIMATE"),
            "runs": RUNS,
            "n_boot": N_BOOT,
            "null_runs": NULL_RUNS,
            "target_power": TARGET_POWER,
            "seed": SEED,
        },
        "families": rows,
        **decide(rows),
    }


def check(res: dict[str, Any]) -> list[str]:
    problems = []
    rows = res.get("families") or []
    if len(rows) < 8:
        problems.append(f"only {len(rows)} families")
    for x in rows:
        if x.get("tag") != "SIM":
            problems.append(f"family {x.get('id')}: the row is not tagged SIM")
        if x.get("status") == "RUN":
            if not x.get("null_control", {}).get("ok"):
                problems.append(f"family {x.get('id')}: the null control passed the harness")
            if not x.get("planted_control", {}).get("ok"):
                problems.append(f"family {x.get('id')}: the planted control failed the harness")
            p = x.get("power_needed")
            if p is not None and not 0.6 <= float(p["value"]) <= 0.97:
                problems.append(f"family {x.get('id')}: power at the needed edge {p['value']} is off calibration")
        elif x.get("status") != "NOT_RUN" or not x.get("why"):
            problems.append(f"family {x.get('id')}: neither run nor NOT_RUN with a reason")
        if x.get("killed"):
            problems.append(f"family {x.get('id')}: SIM cannot kill a family")
    if res.get("result") not in ("NONE", "CANDIDATES") or not res.get("line"):
        problems.append("no result (candidates or NONE) recorded")
    if res.get("result") == "CANDIDATES" and not res.get("candidates"):
        problems.append("CANDIDATES without a candidate")
    return problems


def money(v: Any) -> str:
    return f"₹{float(v):,.2f}"


def cell(e: dict[str, Any] | None, fmt: str = "money") -> str:
    if e is None:
        return "n/a (not judgeable in the window)"
    if fmt == "money":
        v = money(e["value"])
    elif fmt == "share":
        v = f"{float(e['value']):.0%}"
    elif fmt == "x":
        v = f"{e['value']}x"
    else:
        v = str(e["value"])
    return f"{v} [{e['tag']}]"


def write(res: dict[str, Any]) -> None:
    out = ROOT / "EVIDENCE/T11"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sim.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    s = res["settings"]
    lines = [
        "# SIM WAR ROOM (T11, machinery only)",
        "",
        "Result file: EVIDENCE/T11/sim.json (inputs: EVIDENCE/T04/g0.json, EVIDENCE/T08/families.json, gates.toml; "
        "harness: tools/truth_tests.py unchanged). SIM proves the machinery only: it can neither kill nor crown a "
        "family (§9), so no NEGATIVE.md row comes from here and every T08 family stays ALIVE (conditional).",
        "",
        f"Settings: window {s['months']['value']} months [{s['months']['tag']}], {s['days_per_month']['value']} "
        f"trading days a month [{s['days_per_month']['tag']}], sigma {money(s['sigma_rs']['value'])} per trade "
        f"[{s['sigma_rs']['tag']}] (the kindest G0 value), {s['runs']} SIM runs per power figure, "
        f"{s['n_boot']} day-block resamples, seed {s['seed']}. Trade profiles are ASSUMPTION (DECISIONS D-039).",
        "",
        "| id | family | trades a month, legs | hurdle per trade | credible edge per trade | stress cut per trade | "
        "null control | planted control | power at kind edge | power at kind edge, fill ₹0 | net edge needed "
        "for 80% power | needed / credible | candidate |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for x in res["families"]:
        if x["status"] != "RUN":
            lines.append(f"| {x['id']} | {x['name']} | NOT_RUN [SIM]: {x['why']} | | | | | | | | | | no |")
            continue
        nc, pc = x["null_control"], x["planted_control"]
        lines.append(
            "| "
            + " | ".join(
                [
                    x["id"],
                    x["name"],
                    f"{cell(x['per_month'], 'plain')}, {cell(x['legs'], 'plain')}",
                    cell(x["hurdle_rs"]),
                    cell(x["credible_rs"]),
                    cell(x["stress_cut_rs"]),
                    f"{'PASS' if nc['pass'] else 'FAIL'} (must FAIL) [SIM]",
                    f"{'PASS' if pc['pass'] else 'FAIL'} (must PASS) [SIM]",
                    cell(x["power_kind"], "share"),
                    cell(x["power_kind_fill0"], "share"),
                    cell(x["needed_net_rs"]),
                    cell(x["needed_over_credible"], "x"),
                    "yes" if x["candidate"] else "no",
                ]
            )
            + " |"
        )
    lines += [
        "",
        f"RESULT: {res['line']}.",
        "",
        "Reading: the kind edge already clears the hurdle by the whole credible edge, yet the T10 stress floors "
        "(charges x1.5, fill x2: gates.toml) cut more than the credible edge from every trade, so the stressed "
        "lower bound stays under the hurdle. A family needs the 'net edge needed' column, several times the credible "
        "edge, before two years of data can show it. This is not a kill: SIM cannot kill, and REAL data (Recorder: "
        "spreads, fills, sigma per trade) can move every input of this table.",
        "",
        "Cheapest next path: REAL Recorder days (MANUAL, no server) to measure the fill cost and sigma per trade; then "
        "re-run this file with those inputs. A smaller REAL fill cost and sigma shrink the needed edge; nothing else "
        "here can.",
    ]
    (ROOT / "docs/SIM_WAR_ROOM.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    numbers_path = ROOT / "EVIDENCE/numbers.json"
    numbers = json.loads(numbers_path.read_text(encoding="utf-8")) if numbers_path.is_file() else {}
    numbers = {k: v for k, v in numbers.items() if not k.startswith("SIM.")}
    run = [x for x in res["families"] if x["status"] == "RUN"]
    judged = [x for x in run if x.get("judgeable_in_window")]
    best = max(max(float(x["power_kind"]["value"]), float(x["power_kind_fill0"]["value"])) for x in run)
    easiest = min(judged, key=lambda x: (float(x["needed_net_rs"]["value"]), x["id"]))
    ev = "EVIDENCE/T11/sim.json"
    numbers["SIM.families_run"] = {"value": len(run), "unit": "count", "tag": "SIM", "evidence": ev}
    numbers["SIM.power_best_pct"] = {"value": round(best * 100, 1), "unit": "pct", "tag": "SIM", "evidence": ev}
    numbers["SIM.needed_min_rs"] = {
        "value": float(easiest["needed_net_rs"]["value"]),
        "unit": "INR",
        "tag": "SIM",
        "evidence": ev,
    }
    numbers["SIM.needed_min_credible_rs"] = {
        "value": float(easiest["credible_rs"]["value"]),
        "unit": "INR",
        "tag": easiest["credible_rs"]["tag"],
        "evidence": ev,
    }
    numbers["SIM.window_months"] = {"value": MONTHS, "unit": "months", "tag": "ASSUMPTION", "evidence": ev}
    numbers_path.write_text(json.dumps(dict(sorted(numbers.items())), indent=1, ensure_ascii=False) + "\n")


def main(argv: list[str]) -> int:
    if argv[:1] == ["--check"] and len(argv) == 2:
        problems = check(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        for p in problems:
            print(f"PROBLEM {p}")
        print(f"sim war room check: {len(problems)} problem(s)")
        return 1 if problems else 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 64
    res = compute()
    problems = check(res)
    write(res)
    print(res["line"])
    for p in problems:
        print(f"PROBLEM {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
