#!/usr/bin/env python3
"""G0 FEASIBILITY (MISSION V11 §8.1, T04). Deterministic: the same inputs give byte-identical output.

  economics.py                 build inputs from limits.toml, constants.toml, OWNER_APPROVALS.md and the
                               ESTIMATE / ASSUMPTION parameters below; write EVIDENCE/T04/g0.json,
                               EVIDENCE/T04/g0_report.md and the G0 keys of EVIDENCE/numbers.json
  economics.py --inputs FILE   compute from an inputs JSON instead; print the result JSON (no writes)
  economics.py --dump-inputs   print the inputs JSON built from the repo

Money is Decimal, rounded to paise (I12). Every output number carries a tag CODE(<weakest input tag>).
Outcome rules (§8.1): a FAIL rests only on SOURCE facts and OWNER / approved limits, else CONDITIONAL;
an ESTIMATE ceiling never gives FAIL_CREDIBILITY and enters the FEASIBLE test at 0.5x; ESTIMATE /
ASSUMPTION small costs count 2x in the FEASIBLE test and 0 in FAIL tests; tax is applied once, after
the decision quantities, and never changes them.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import power  # noqa: E402

PAISE = Decimal("0.01")
TICK = Decimal("0.05")
STRENGTH = ["SOURCE", "REAL", "BACKTEST", "SHADOW", "SIM", "HISTORY", "POINTER", "ESTIMATE", "ASSUMPTION"]
RANK = {"SOURCE": 0, "REAL": 0, "BACKTEST": 1, "SHADOW": 1, "SIM": 2, "HISTORY": 3, "POINTER": 4, "ESTIMATE": 5}
RANK["ASSUMPTION"] = 6
GATE_FACT = ("SOURCE", "REAL")
ORDER = {"FEASIBLE": 3, "CONDITIONAL": 2, "FAIL_CREDIBILITY": 1, "FAIL_ARITH": 0}

FACTS = [
    "brokerage_fo_per_order",
    "stt_option_sell",
    "nse_txn_charge_composite",
    "bse_txn_charge",
    "sebi_fee",
    "stamp_duty_buy",
    "gst",
    "lot_nifty_crosscheck",
    "lot_banknifty_crosscheck",
    "lot_sensex_crosscheck",
    "lightsail_small_usd_pm",
    "lightsail_1gb_usd_pm",
    "lightsail_bundle_usd_pm",
    "usd_inr",
    "aws_india_gst",
    "fd_rate",
]
LIMITS = ["CAPITAL_RS", "MAX_TOTAL_LOSS_RS", "MAX_DRAWDOWN_RS", "MAX_TRADE_LOSS_RS", "H2_MONTHLY_RS"]
# ESTIMATE / ASSUMPTION parameters (value, tag, why). Placeholders are marked "verify nahi hua".
PARAMS: dict[str, tuple[Any, str, str]] = {
    "slippage_per_unit_side_rs": (
        "0.50",
        "ESTIMATE",
        "fill cost incl. half-spread per unit per side; Recorder measures it",
    ),
    "charges_stress": ("1.5", "OWNER", "MISSION §8.2 cost stress: charges x1.5"),
    "slippage_stress": ("2", "OWNER", "MISSION §8.2 cost stress: slippage x2"),
    "trades_pm_grid": (["4", "8", "12", "20"], "ESTIMATE", "MISSION §8.1 sensitivity rows; REAL rate unknown"),
    "internet_share_rs_pm": (
        "100",
        "ASSUMPTION",
        "placeholder, verify nahi hua: the bot's share of the owner's internet",
    ),
    "electricity_rs_pm": ("100", "ASSUMPTION", "placeholder, verify nahi hua: a PC or phone on in market hours"),
    "ca_fee_rs_pm": ("250", "ASSUMPTION", "placeholder, verify nahi hua: a yearly CA / ITR fee spread over months"),
    "ai_share_rs_pm": ("0", "ASSUMPTION", "bot share of an AI subscription the owner already pays; build cost is sunk"),
    "tax_slab_pct": ("30", "ASSUMPTION", "placeholder until a CA confirms the regime (F&O as business income)"),
    "credible_ceiling_pct_pm": (
        "2",
        "ESTIMATE",
        "no SEBI figure with a capital denominator; judgment, sensitivity 1/2/5",
    ),
    "sigma_per_trade_rs": (
        ["500", "1000", "1500"],
        "ESTIMATE",
        "sd of net P&L per trade, about the max loss per trade",
    ),
    "premium_grid": (["10", "25", "50", "100", "200", "300", "450"], "ASSUMPTION", "illustrative premium per unit"),
    "band_pct": ("20", "ASSUMPTION", "U5 price band for the by-construction loss of a cash position, verify nahi hua"),
    "strike_step_nifty": ("50", "ASSUMPTION", "U3 width = one strike step, verify nahi hua"),
    "strike_step_sensex": ("100", "ASSUMPTION", "U3 width = one strike step, verify nahi hua"),
    "u3_hedged_margin_rs": ("unknown", "ASSUMPTION", "no source in the repo"),
}
INDEXES = {"NIFTY": ("lot_nifty_crosscheck", "NSE"), "BANKNIFTY": ("lot_banknifty_crosscheck", "NSE")}
INDEXES["SENSEX"] = ("lot_sensex_crosscheck", "BSE")


def D(x: Any) -> Decimal:
    return Decimal(str(x))


def money(x: Decimal) -> Decimal:
    return x.quantize(PAISE, rounding=ROUND_HALF_UP)


def weakest(tags: list[str]) -> str:
    inner = [t[5:-1].replace("·stressed", "") if t.startswith("CODE(") else t for t in tags]
    real = [t for t in inner if t != "OWNER"]
    if not real:
        return "CODE(OWNER)"
    return f"CODE({max(real, key=lambda t: RANK.get(t, 6))})"


def tv(value: Decimal | int | str, *tags: str) -> dict[str, str]:
    v = str(money(value)) if isinstance(value, Decimal) else str(value)
    return {"value": v, "tag": weakest(list(tags))}


def approved_ids(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        parts = line.split("OWNER COMMAND (verbatim line): ")
        if len(parts) == 2:
            words = parts[1].split()
            if len(words) >= 3 and words[0].lower() in ("haan", "ha", "haa", "han", "yes", "set"):
                out.add(words[1].upper())
    return out


def build_inputs(root: Path = ROOT) -> dict[str, Any]:
    consts = tomllib.loads((root / "constants.toml").read_text(encoding="utf-8"))
    limits = tomllib.loads((root / "limits.toml").read_text(encoding="utf-8"))
    approvals = approved_ids((root / "OWNER_APPROVALS.md").read_text(encoding="utf-8"))
    facts = {}
    for name in FACTS:
        row = consts.get(name, {"value": "unknown", "tag": "ASSUMPTION"})
        facts[name] = {"value": str(row["value"]), "tag": str(row["tag"])}
    lims = {}
    for name in LIMITS:
        row = limits[name]
        q = str(row.get("question", ""))
        lims[name] = {"value": str(row["value"]), "tag": str(row["tag"]), "approved": bool(q and q in approvals)}
    params = {k: {"value": v, "tag": t, "why": w} for k, (v, t, w) in PARAMS.items()}
    return {"facts": facts, "limits": lims, "params": params}


class Model:
    def __init__(self, inputs: dict[str, Any]) -> None:
        self.i = inputs

    def f(self, name: str) -> Decimal:
        return D(self.i["facts"][name]["value"])

    def ftag(self, name: str) -> str:
        return str(self.i["facts"][name]["tag"])

    def lim(self, name: str) -> Decimal:
        return D(self.i["limits"][name]["value"])

    def ltag(self, name: str) -> str:
        row = self.i["limits"][name]
        if row["approved"] or row["tag"] == "OWNER":
            return "OWNER"
        tag = str(row["tag"])
        return tag[5:-1] if tag.startswith("CODE(") else tag

    def limit_ok(self, name: str) -> bool:
        row = self.i["limits"][name]
        return bool(row["approved"]) or row["tag"] == "OWNER"

    def p(self, name: str) -> Any:
        return self.i["params"][name]["value"]

    def ptag(self, name: str) -> str:
        return str(self.i["params"][name]["tag"])

    # ---------------------------------------------------------------- charges (round trip)

    def charges(self, buy: Decimal, sell: Decimal, orders: int, exchange: str) -> Decimal:
        rate = self.f("nse_txn_charge_composite" if exchange == "NSE" else "bse_txn_charge")
        brokerage = money(orders * self.f("brokerage_fo_per_order"))
        stt = money(sell * self.f("stt_option_sell") / 100)
        exch = money((buy + sell) * rate / 100)
        sebi = money((buy + sell) * self.f("sebi_fee") / Decimal(10**7))
        stamp = money(buy * self.f("stamp_duty_buy") / 100)
        gst = money((brokerage + exch + sebi) * self.f("gst") / 100)
        return brokerage + stt + exch + sebi + stamp + gst

    def charge_tags(self, exchange: str) -> list[str]:
        names = ["brokerage_fo_per_order", "stt_option_sell", "sebi_fee", "stamp_duty_buy", "gst"]
        names.append("nse_txn_charge_composite" if exchange == "NSE" else "bse_txn_charge")
        return [self.ftag(n) for n in names]

    def max_fit_premium(self, lot: Decimal, exchange: str, legs: int, limit: Decimal) -> Decimal:
        p = (limit / lot / TICK).to_integral_value(rounding=ROUND_FLOOR) * TICK
        while p > 0:
            value = p * lot * legs
            if p * lot + self.charges(value, value, 2 * legs, exchange) <= limit:
                return p
            p -= TICK
        return Decimal(0)

    # ---------------------------------------------------------------- fixed costs

    def small_costs(self) -> Decimal:
        return sum(
            (D(self.p(k)) for k in ("internet_share_rs_pm", "electricity_rs_pm", "ca_fee_rs_pm", "ai_share_rs_pm")),
            Decimal(0),
        )

    def server(self, fact: str) -> Decimal:
        return money(self.f(fact) * self.f("usd_inr") * (1 + self.f("aws_india_gst") / 100))

    def fd_known(self) -> bool:
        return str(self.i["facts"]["fd_rate"]["value"]) != "unknown"

    def baseline(self) -> Decimal:
        return money(self.lim("CAPITAL_RS") * self.f("fd_rate") / 100 / 12) if self.fd_known() else Decimal(0)

    def run(self) -> dict[str, Any]:
        cap, mtl = self.lim("CAPITAL_RS"), self.lim("MAX_TRADE_LOSS_RS")
        captag, mtltag = self.ltag("CAPITAL_RS"), self.ltag("MAX_TRADE_LOSS_RS")
        srv_tags = [self.ftag(n) for n in ("lightsail_small_usd_pm", "usd_inr", "aws_india_gst")]
        small = self.small_costs()
        small_tag = "ASSUMPTION"
        stages: dict[str, Any] = {}
        for stage, server in (("S0_MANUAL", Decimal(0)), ("S1_API", self.server("lightsail_small_usd_pm"))):
            tags = [] if stage == "S0_MANUAL" else srv_tags
            base = self.baseline()
            fixed_fail, fixed_mid, fixed_feas = server, server + small, server + 2 * small
            stages[stage] = {
                "server_rs_pm": tv(server, *(tags or ["OWNER"])),
                "fixed_fail_test_rs_pm": tv(fixed_fail, *(tags or ["OWNER"])),
                "fixed_indicative_rs_pm": tv(fixed_mid, *tags, small_tag),
                "fixed_feasible_test_rs_pm": tv(fixed_feas, *tags, small_tag),
                "baseline_rs_pm": tv(base, self.ftag("fd_rate")) if self.fd_known() else tv(Decimal(0), "ASSUMPTION"),
                "hurdle_pct_pm": tv((fixed_mid + base) / cap * 100, *tags, small_tag, captag),
                "required_net_edge_pct_pm_fail_test": tv((fixed_fail + base) / cap * 100, *(tags or ["OWNER"]), captag),
                "required_net_edge_pct_pm_feasible_test": tv((fixed_feas + base) / cap * 100, *tags, small_tag, captag),
                "cost_hurdle_per_trade_rs": {
                    t: tv((fixed_mid + base) / D(t), *tags, small_tag, self.ptag("trades_pm_grid"))
                    for t in self.p("trades_pm_grid")
                },
            }
        plans = {}
        for fact in ("lightsail_small_usd_pm", "lightsail_1gb_usd_pm", "lightsail_bundle_usd_pm"):
            rs = self.server(fact)
            plans[fact] = {
                "rs_pm": tv(rs, self.ftag(fact), self.ftag("usd_inr"), self.ftag("aws_india_gst")),
                "pct_of_capital_pm": tv(rs / cap * 100, self.ftag(fact), self.ftag("usd_inr"), captag),
                "within_h2": rs <= self.lim("H2_MONTHLY_RS"),
            }
        # ---------------------------------------------------------- members
        members: dict[str, Any] = {}
        lf_rows = []
        for idx, (lotname, exch) in INDEXES.items():
            lot, ltag = self.f(lotname), self.ftag(lotname)
            tags = [ltag, *self.charge_tags(exch)]
            fit1 = self.max_fit_premium(lot, exch, 1, mtl)
            for prem in [str(fit1), *self.p("premium_grid")]:
                p = D(prem)
                value = p * lot
                loss = value + self.charges(value, value, 2, exch)
                lf_rows.append(
                    {
                        "member": "U1",
                        "index": idx,
                        "premium_per_unit_rs": tv(p, self.ptag("premium_grid")),
                        "max_trade_loss_needed_rs": tv(loss, *tags),
                        "f_maxloss_needed_default_rule_rs": tv(4 * loss, *tags),
                        "f_maxloss_needed_loosest_rs": tv(2 * loss, *tags),
                        "fits_current_limit": loss <= mtl,
                        "possible_under_h1": 2 * loss <= cap,
                    }
                )
            min_value = TICK * lot
            min_ch = self.charges(min_value, min_value, 2, exch)
            members.setdefault("U1", {"rows": {}})["rows"][idx] = {
                "lot": tv(lot, ltag),
                "max_fit_premium_per_unit_rs": tv(fit1, *tags, mtltag),
                "min_round_trip_charges_rs": tv(min_ch, *self.charge_tags(exch)),
                "round_trip_charges_at_fit_rs": tv(self.charges(fit1 * lot, fit1 * lot, 2, exch), *tags),
                "fill_cost_at_fit_rs": tv(2 * lot * D(self.p("slippage_per_unit_side_rs")), ltag, "ESTIMATE"),
                "_impossible": min_ch > mtl or min_value > cap,
                "_tags": tags,
            }
            if idx != "BANKNIFTY":
                fit2 = self.max_fit_premium(lot, exch, 2, mtl)
                min4 = self.charges(min_value * 2, min_value, 4, exch)
                members.setdefault("U2", {"rows": {}})["rows"][idx] = {
                    "max_fit_net_debit_per_unit_rs": tv(fit2, *tags, mtltag, "ASSUMPTION"),
                    "min_round_trip_charges_rs": tv(min4, *self.charge_tags(exch)),
                    "_impossible": min4 > mtl,
                    "_tags": tags,
                }
                step = D(self.p(f"strike_step_{idx.lower()}"))
                need_credit = step - (mtl - min4) / lot
                members.setdefault("U3", {"rows": {}})["rows"][idx] = {
                    "width_one_step_rs": tv(step, "ASSUMPTION"),
                    "min_credit_per_unit_to_fit_rs": tv(max(need_credit, Decimal(0)), *tags, mtltag, "ASSUMPTION"),
                    "hedged_margin": "unknown",
                    "_impossible": min4 > mtl,
                    "_tags": [*tags, "ASSUMPTION"],
                }
        band = D(self.p("band_pct"))
        min_eq = money(2 * self.f("brokerage_fo_per_order") * (1 + self.f("gst") / 100))
        members["U4"] = {
            "rows": {"note": "F-S16 default: stock list for signals only, no U4 trading"},
            "_owner_off": True,
        }
        members["U5"] = {
            "rows": {
                "max_notional_by_construction_rs": tv((mtl - min_eq) / band * 100, mtltag, "ASSUMPTION"),
                "note": "equity intraday charges are not in constants.toml (placeholder: F&O brokerage)",
            },
            "_impossible_any": min_eq > mtl,
            "_tags": ["ASSUMPTION"],
        }
        members["U6"] = {
            "rows": {
                "max_notional_by_construction_rs": tv(mtl - min_eq, mtltag, "ASSUMPTION"),
                "note": "ETF delivery charges are not in constants.toml (placeholder: F&O brokerage)",
            },
            "_impossible_any": min_eq > mtl,
            "_tags": ["ASSUMPTION"],
        }
        # ---------------------------------------------------------- outcomes
        ceiling = D(self.p("credible_ceiling_pct_pm"))
        ceil_tag = self.ptag("credible_ceiling_pct_pm")
        ceiling_feasible = ceiling if ceil_tag == "SOURCE" else ceiling / 2
        best_fail = stages["S0_MANUAL"]["required_net_edge_pct_pm_fail_test"]
        req_fail = D(best_fail["value"])
        req_feas = D(stages["S0_MANUAL"]["required_net_edge_pct_pm_feasible_test"]["value"])
        decisive_extra = [self.ftag("fd_rate")]  # best lever: S0 MANUAL, so no static-IP price is decisive
        for m in members.values():
            rows = m["rows"]
            reasons: list[str] = []
            if m.get("_owner_off"):
                reasons.append("owner choice F-S16 keeps U4 to signals only (default)")
            tags = m.get("_tags") or [t for r in rows.values() if isinstance(r, dict) for t in r.get("_tags", [])]
            non_gate = sorted({t for t in [*tags, *decisive_extra] if t not in (*GATE_FACT, "OWNER")})
            if non_gate:
                reasons.append("decisive inputs not SOURCE / REAL: " + ", ".join(non_gate))
            if not self.limit_ok("MAX_TOTAL_LOSS_RS"):
                reasons.append("F-MAXLOSS default not approved")
            impossible = bool(m.get("_impossible_any")) or (
                bool(rows)
                and all(r.get("_impossible") for r in rows.values() if isinstance(r, dict) and "_impossible" in r)
                and any(isinstance(r, dict) and "_impossible" in r for r in rows.values())
            )
            fact_ok = all(t in GATE_FACT for t in tags if t != "OWNER")
            limit_ok = self.limit_ok("MAX_TOTAL_LOSS_RS") and self.limit_ok("CAPITAL_RS")
            if impossible and fact_ok and limit_ok:
                outcome = "FAIL_ARITH"
            elif impossible:
                outcome = "CONDITIONAL"
                reasons.insert(0, "structural impossibility rests on a non-SOURCE fact or an unapproved limit")
            elif ceil_tag == "SOURCE" and fact_ok and req_fail > ceiling:
                outcome = "FAIL_CREDIBILITY"
            elif not m.get("_owner_off") and not non_gate and limit_ok and req_feas <= ceiling_feasible:
                outcome = "FEASIBLE"  # does not mean profitable (§8.1)
            else:
                outcome = "CONDITIONAL"
            m["outcome"] = outcome
            m["reasons"] = reasons
            for r in rows.values():
                if isinstance(r, dict):
                    r.pop("_impossible", None)
                    r.pop("_tags", None)
            for k in ("_impossible_any", "_tags", "_owner_off"):
                m.pop(k, None)
        g0 = max((m["outcome"] for m in members.values()), key=lambda o: ORDER[o])
        track = "SHORT" if all(m["outcome"].startswith("FAIL") for m in members.values()) else "FULL"
        # ---------------------------------------------------------- tax (applied once, shown only)
        tax = D(self.p("tax_slab_pct"))
        s0 = stages["S0_MANUAL"]
        fixed_mid = D(s0["fixed_indicative_rs_pm"]["value"])
        example_result = 2 * (fixed_mid + D(s0["baseline_rs_pm"]["value"]))
        pre_tax = 12 * (example_result - fixed_mid)
        tax_block = {
            "example_monthly_trading_result_rs": tv(example_result, "ASSUMPTION"),
            "annual_pre_tax_net_rs": tv(pre_tax, "ASSUMPTION"),
            "tax_rs": tv(max(pre_tax, Decimal(0)) * tax / 100, "ASSUMPTION"),
            "annual_post_tax_net_rs": tv(pre_tax - max(pre_tax, Decimal(0)) * tax / 100, "ASSUMPTION"),
        }
        # ---------------------------------------------------------- validation feasibility (power)
        val = {}
        for t in self.p("trades_pm_grid"):
            n24 = 24 * int(t)
            credible_per_trade = cap * ceiling / 100 / D(t)
            row: dict[str, Any] = {
                "months_to_150_trades": tv(D(150) / D(t), "ESTIMATE"),
                "credible_edge_per_trade_rs": tv(credible_per_trade, ceil_tag, "ESTIMATE", captag),
            }
            for s in self.p("sigma_per_trade_rs"):
                row[f"mde_rs_sigma{s}_n150"] = tv(D(f"{power.mde(float(s), 150):.2f}"), "ESTIMATE")
                row[f"mde_rs_sigma{s}_24months"] = tv(D(f"{power.mde(float(s), n24):.2f}"), "ESTIMATE")
            mid = self.p("sigma_per_trade_rs")[1]
            row["validation_infeasible"] = D(row[f"mde_rs_sigma{mid}_24months"]["value"]) > credible_per_trade
            val[t] = row
        out = {
            "g0": g0,
            "track": track,
            "ceiling_pct_pm": tv(ceiling, ceil_tag),
            "ceiling_feasible_test_pct_pm": tv(ceiling_feasible, ceil_tag),
            "stages": stages,
            "server_plans": plans,
            "members": members,
            "limit_feasibility": lf_rows,
            "tax": tax_block,
            "validation": val,
            "power_factor": f"{power.factor():.3f}",
            "baseline_per_1pct_fd_rs_pm": tv(cap / 100 / 12, captag),
            "sensitivity": {
                "U1": "becomes FEASIBLE-eligible only when charges, lot size and the static-IP price are SOURCE, "
                "F-MAXLOSS is answered, and REAL data gives slippage, spread and trades per month",
                "U2": "same as U1; the debit-spread width decides how much premium fits the limit",
                "U3": "hedged margin (unknown) decides first; then the credit needed per unit for a one-step spread",
                "U4": "the owner's F-S16 answer decides whether U4 is traded at all; D12 bans the expiry week",
                "U5": "equity intraday charges (not in constants) and the price band decide the notional",
                "U6": "ETF delivery charges (not in constants); by-construction loss = notional caps size",
            },
        }
        return out


def inputs_hash(inputs: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def compute(inputs: dict[str, Any]) -> dict[str, Any]:
    result = Model(inputs).run()
    result["inputs_sha256"] = inputs_hash(inputs)
    return result


def fmt(x: dict[str, str], unit: str = "") -> str:
    v = x["value"]
    return f"{'₹' if unit == 'rs' else ''}{v}{'%' if unit == 'pct' else ''} [{x['tag']}]"


def report_md(r: dict[str, Any]) -> str:
    s0, s1 = r["stages"]["S0_MANUAL"], r["stages"]["S1_API"]
    lines = [
        f"G0 = **{r['g0']}** · TRACK = **{r['track']}** · source: EVIDENCE/T04/g0.json (inputs sha256 "
        f"{r['inputs_sha256'][:16]}) · every input is UNVERIFIED this session (INCIDENT #1, no web)",
        "",
        "| member | outcome | main reason |",
        "|---|---|---|",
    ]
    for name, m in r["members"].items():
        lines.append(f"| {name} | {m['outcome']} | {m['reasons'][0]} |")
    lines += [
        "",
        "Fixed cost and hurdle per month (EVIDENCE/T04/g0.json):",
        f"- S0 MANUAL (no server): fixed {fmt(s0['fixed_indicative_rs_pm'], 'rs')}, "
        f"hurdle {fmt(s0['hurdle_pct_pm'], 'pct')} of capital",
        f"- S1 API (cheapest static-IP route in the research): server {fmt(s1['server_rs_pm'], 'rs')}, "
        f"fixed {fmt(s1['fixed_indicative_rs_pm'], 'rs')}, hurdle {fmt(s1['hurdle_pct_pm'], 'pct')} of capital",
    ]
    for plan, p in r["server_plans"].items():
        lines.append(f"- server plan {plan}: {fmt(p['rs_pm'], 'rs')} = {fmt(p['pct_of_capital_pm'], 'pct')} of capital")
    lines += ["", "Cost hurdle per trade at TRADES_PM (S1 API / S0 MANUAL), EVIDENCE/T04/g0.json:"]
    for t, v in s1["cost_hurdle_per_trade_rs"].items():
        lines.append(f"- {t} trades a month: S1 {fmt(v, 'rs')} · S0 {fmt(s0['cost_hurdle_per_trade_rs'][t], 'rs')}")
    lines += ["", "U1 long option, one lot, by construction (I7), EVIDENCE/T04/g0.json:"]
    for idx, row in r["members"]["U1"]["rows"].items():
        lines.append(
            f"- {idx}: max premium per unit that fits the current limit "
            f"{fmt(row['max_fit_premium_per_unit_rs'], 'rs')}; "
            f"charges at that premium {fmt(row['round_trip_charges_at_fit_rs'], 'rs')}; "
            f"fill cost {fmt(row['fill_cost_at_fit_rs'], 'rs')}"
        )
    lines += [
        "",
        "Limit feasibility (U1, one lot; F-MAXLOSS needed under the default 50% [ASSUMPTION] drawdown rule), "
        "EVIDENCE/T04/g0.json:",
    ]
    for row in r["limit_feasibility"]:
        lines.append(
            f"- {row['index']} premium {fmt(row['premium_per_unit_rs'], 'rs')}: needs F-MAXLOSS "
            f"{fmt(row['f_maxloss_needed_default_rule_rs'], 'rs')} "
            f"(loosest {fmt(row['f_maxloss_needed_loosest_rs'], 'rs')}); "
            f"fits now: {'yes' if row['fits_current_limit'] else 'no'}; possible under H1: "
            f"{'yes' if row['possible_under_h1'] else 'no'}"
        )
    lines += ["", f"Validation (power factor {r['power_factor']} at TRIALS_MAX 50), EVIDENCE/T04/g0.json:"]
    for t, v in r["validation"].items():
        lines.append(
            f"- {t} trades a month: months to 150 trades {fmt(v['months_to_150_trades'])}; MDE after 24 months "
            f"{fmt(v['mde_rs_sigma1000_24months'], 'rs')} vs credible edge "
            f"{fmt(v['credible_edge_per_trade_rs'], 'rs')} per trade: "
            f"{'VALIDATION_INFEASIBLE' if v['validation_infeasible'] else 'ok'}"
        )
    return "\n".join(lines) + "\n"


NUMBER_KEYS = {
    "G0.s1_server_rs_pm": (("stages", "S1_API", "server_rs_pm"), "INR/month"),
    "G0.s1_hurdle_pct": (("stages", "S1_API", "hurdle_pct_pm"), "pct"),
    "G0.s0_fixed_rs_pm": (("stages", "S0_MANUAL", "fixed_indicative_rs_pm"), "INR/month"),
    "G0.s0_hurdle_pct": (("stages", "S0_MANUAL", "hurdle_pct_pm"), "pct"),
    "G0.s1_cost_hurdle_12_rs": (("stages", "S1_API", "cost_hurdle_per_trade_rs", "12"), "INR"),
    "G0.s1_server_pct": (("server_plans", "lightsail_small_usd_pm", "pct_of_capital_pm"), "pct"),
    "G0.plan12_rs_pm": (("server_plans", "lightsail_bundle_usd_pm", "rs_pm"), "INR/month"),
    "G0.plan12_pct": (("server_plans", "lightsail_bundle_usd_pm", "pct_of_capital_pm"), "pct"),
    "G0.nifty_fit_premium_rs": (("members", "U1", "rows", "NIFTY", "max_fit_premium_per_unit_rs"), "INR"),
    "G0.sensex_fit_premium_rs": (("members", "U1", "rows", "SENSEX", "max_fit_premium_per_unit_rs"), "INR"),
    "G0.nifty_charges_at_fit_rs": (("members", "U1", "rows", "NIFTY", "round_trip_charges_at_fit_rs"), "INR"),
    "G0.mde_24m_12_rs": (("validation", "12", "mde_rs_sigma1000_24months"), "INR"),
    "G0.credible_edge_12_rs": (("validation", "12", "credible_edge_per_trade_rs"), "INR"),
    "G0.months_to_150_at_12": (("validation", "12", "months_to_150_trades"), "months"),
}


def write_outputs(result: dict[str, Any]) -> None:
    out_dir = ROOT / "EVIDENCE/T04"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "g0.json").write_text(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    (out_dir / "g0_report.md").write_text(report_md(result), encoding="utf-8")
    numbers_path = ROOT / "EVIDENCE/numbers.json"
    numbers = json.loads(numbers_path.read_text()) if numbers_path.is_file() else {}
    numbers = {k: v for k, v in numbers.items() if not k.startswith("G0.")}
    for key, (path, unit) in NUMBER_KEYS.items():
        node: Any = result
        for part in path:
            node = node[part]
        value = D(node["value"])
        numbers[key] = {
            "value": float(value) if unit != "count" else int(value),
            "unit": unit,
            "tag": node["tag"],
            "evidence": "EVIDENCE/T04/g0.json",
        }
    numbers_path.write_text(json.dumps(dict(sorted(numbers.items())), indent=1, ensure_ascii=False) + "\n")


def main(argv: list[str]) -> int:
    if argv[:1] == ["--dump-inputs"]:
        print(json.dumps(build_inputs(), indent=1, sort_keys=True, ensure_ascii=False))
        return 0
    if argv[:1] == ["--inputs"] and len(argv) == 2:
        inputs = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        print(json.dumps(compute(inputs), indent=1, sort_keys=True, ensure_ascii=False))
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 64
    result = compute(build_inputs())
    write_outputs(result)
    print(f"G0 {result['g0']} · TRACK {result['track']} · inputs sha256 {result['inputs_sha256']}")
    for name, m in result["members"].items():
        print(f"{name}: {m['outcome']} · {m['reasons'][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
