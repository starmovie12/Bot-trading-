#!/usr/bin/env python3
"""BANKNIFTY economics (MISSION V19 Phase 2c): charges, lot cost, break-even, by-construction loss, feasibility.

  bn_economics.py   REAL premiums from the data at 10:00 IST -> results/feasibility.json, results/feasibility_card.md,
                    docs/BALANCE_LADDER.md (skeleton; 3e fills the Monte Carlo columns)
Money is Decimal rounded to paise (I12). Charges are the dated SOURCE rows of constants.toml. Spread and slippage are an
ESTIMATE stressed x 2 (no measured spread yet); MODEL / ESTIMATE inputs are stressed on the PASS side (C4).
"""

import datetime as dt
import json
import statistics
import sys
import tomllib
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lab import data  # noqa: E402

PAISA = Decimal("0.01")
LADDER = (10_000, 15_000, 20_000, 25_000, 30_000, 40_000, 50_000, 75_000, 100_000, 150_000, 200_000)
SIDE_FILL_PER_UNIT = Decimal("0.70")  # ESTIMATE: half of a ₹1.00 ATM bid-ask + ₹0.20 slippage, per unit per side
STRESS = Decimal(2)
MARGIN_LEG2_SHARE = Decimal("0.09")  # ESTIMATE, UNVERIFIED: naked short index option ≈ 9% of notional, no hedge benefit
FIXED_PM_STRESSED = Decimal(1500)  # ₹ a month: the R5 cap (server price UNVERIFIED; HISTORY $12 → ₹1,324.96)
STRIKE = 100
BUCKETS = ((0, 2), (3, 7), (8, 15), (16, 40))
Row = dict[str, Any]


def money(x: Decimal | float | int | str) -> Decimal:
    return Decimal(str(x)).quantize(PAISA, ROUND_HALF_UP)


def consts(root: Path = ROOT) -> dict[str, Any]:
    return tomllib.loads((root / "constants.toml").read_text(encoding="utf-8"))


def dated(rows: Any, on: dt.date) -> Decimal:
    """Value of a constants row; for a dated series the last row whose valid_from <= on."""
    if isinstance(rows, dict):
        return Decimal(str(rows["value"]))
    live = [r for r in rows if dt.date.fromisoformat(r["valid_from"]) <= on]
    return Decimal(str(max(live, key=lambda r: r["valid_from"])["value"]))


def side_charges(turnover: Decimal, side: str, on: dt.date, c: dict[str, Any]) -> Decimal:
    """Statutory + broker charges of one executed order (one leg, one side); GST also on the SEBI fee (stress)."""
    pct = Decimal(100)
    brokerage = dated(c["brokerage_option_per_order"], on)
    exchange = turnover * dated(c["nse_txn_option"], on) / pct
    ipft = turnover * dated(c["ipft_option"], on) / pct
    sebi = turnover * dated(c["sebi_fee"], on) / pct
    stamp = turnover * dated(c["stamp_option_buy"], on) / pct if side == "BUY" else Decimal(0)
    stt = turnover * dated(c["stt_option_sell"], on) / pct if side == "SELL" else Decimal(0)
    gst = (brokerage + exchange + ipft + sebi) * dated(c["gst"], on) / pct
    return money(brokerage + exchange + ipft + sebi + stamp + stt + gst)


def round_trip(entry: Decimal, exit_: Decimal, lot: int, on: dt.date, c: dict[str, Any], long: bool = True) -> Decimal:
    """Charges of opening and closing one leg (a long leg buys first; a short leg sells first)."""
    first, last = ("BUY", "SELL") if long else ("SELL", "BUY")
    return money(side_charges(entry * lot, first, on, c) + side_charges(exit_ * lot, last, on, c))


def fill_cost(lot: int, legs: int, stressed: bool, per_unit: Decimal = SIDE_FILL_PER_UNIT) -> Decimal:
    """Spread + slippage in ₹: points per unit per leg x LOT x legs x 2 sides (C4 units), x 2 when stressed."""
    return money(per_unit * lot * legs * 2 * (STRESS if stressed else 1))


def long_option(premium: Decimal, lot: int, on: dt.date, c: dict[str, Any], fill: Decimal = SIDE_FILL_PER_UNIT) -> Row:
    charges = round_trip(premium, premium, lot, on, c)
    stressed = money(charges + fill_cost(lot, 1, True, fill))
    max_loss = money(premium * lot + stressed)
    be = breakeven(stressed, Decimal("0.5"), lot)
    return {"cash_needed_rs": money(premium * lot), "max_loss_rs": max_loss, "round_trip_rs": charges,
            "round_trip_stressed_rs": stressed, "breakeven_points": be}  # fmt: skip


def debit_spread(
    long_p: Decimal,
    short_p: Decimal,
    lot: int,
    spot: Decimal,
    on: dt.date,
    c: dict[str, Any],
    fill: Decimal = SIDE_FILL_PER_UNIT,
) -> Row:
    charges = round_trip(long_p, long_p, lot, on, c) + round_trip(short_p, short_p, lot, on, c, long=False)
    stressed = money(charges + fill_cost(lot, 2, True, fill))
    margin = money(MARGIN_LEG2_SHARE * spot * lot)
    return {"net_debit_rs": money((long_p - short_p) * lot), "max_loss_rs": money((long_p - short_p) * lot + stressed),
            "round_trip_stressed_rs": stressed, "margin_leg2_estimate_rs": margin,
            "cash_needed_stressed_rs": money(long_p * lot + margin * Decimal("1.25")),
            "cash_needed_favourable_rs": money(long_p * lot)}  # fmt: skip


def breakeven(cost: Decimal, delta: Decimal, lot: int) -> Decimal:
    """Index points the underlying must move to pay the round trip: cost / (delta x lot)."""
    return money(cost / (delta * lot))


def chain_floor(max_loss: Decimal) -> Decimal:
    """Smallest balance the K1 chain allows for this structure: 2 x its by-construction max loss."""
    return money(2 * max_loss)


def ceil_to(x: Decimal, step: int) -> Decimal:
    return (x / step).to_integral_value(ROUND_CEILING) * step


def real_premiums(repo: Path, days: list[str]) -> dict[str, Any]:
    """Median option close (last non-stale bar 09:50-09:59, known by 10:00) by days to expiry and strikes OTM."""
    samples: dict[str, list[float]] = {}
    spots = []
    for d in days:
        day = dt.date.fromisoformat(d)
        spot_tb = data.read_day(repo, "spot_1m", day, columns=["instrument_key", "ts_open", "c"])
        ten = dt.datetime.combine(day, dt.time(10, 0), dt.timezone(dt.timedelta(hours=5, minutes=30)))
        spot_v = data.visible(spot_tb, ten)
        opt = data.read_day(
            repo,
            "options",
            day,
            columns=["instrument_key", "ts_open", "expiry_date", "strike", "option_type", "c", "is_stale"],
        )
        if spot_v.num_rows == 0 or opt.num_rows == 0:
            continue
        spot = float(spot_v["c"][-1].as_py())
        spots.append(spot)
        rows = [
            r for r in data.visible(opt, ten).to_pylist() if not r["is_stale"] and r["ts_open"].time() >= dt.time(9, 50)
        ]
        if not rows:
            continue
        expiry = min(r["expiry_date"] for r in rows if r["expiry_date"] >= day)
        last: dict[tuple[float, str], float] = {}
        for r in sorted(rows, key=lambda r: r["ts_open"]):
            if r["expiry_date"] == expiry:
                last[(r["strike"], r["option_type"])] = r["c"]
        atm = round(spot / STRIKE) * STRIKE
        dte = (expiry - day).days
        bucket = next(f"{a}-{b}" for a, b in BUCKETS if a <= dte <= b) if dte <= BUCKETS[-1][1] else None
        if bucket is None:
            continue
        for k in range(4):
            for side, strike in (("CE", atm + k * STRIKE), ("PE", atm - k * STRIKE)):
                if (strike, side) in last:
                    samples.setdefault(f"{bucket}|{side}|{k}", []).append(last[(strike, side)])
    return {"tag": "REAL", "days": len(spots), "spot_median": round(statistics.median(spots), 2) if spots else None,
            "median": {k: round(statistics.median(v), 2) for k, v in sorted(samples.items())},
            "count": {k: len(v) for k, v in sorted(samples.items())}}  # fmt: skip


def feasibility(prem: dict[str, Any], lot: int, on: dt.date, c: dict[str, Any], favourable: bool = False) -> Row:
    """PASS side: stressed fills and the margin ESTIMATE; kill side (favourable): fills at ₹0, no Leg 2 margin (C4)."""
    fill = Decimal(0) if favourable else SIDE_FILL_PER_UNIT
    med = prem["median"]
    spot = Decimal(str(prem["spot_median"]))
    structures: dict[str, Row] = {}
    for bucket in (f"{a}-{b}" for a, b in BUCKETS):
        for k in (0, 1, 2):
            p = [med[f"{bucket}|{s}|{k}"] for s in ("CE", "PE") if f"{bucket}|{s}|{k}" in med]
            if p:
                structures[f"long dte {bucket} {'ATM' if k == 0 else f'{k} OTM'}"] = long_option(
                    money(statistics.mean(p)), lot, on, c
                )
        if f"{bucket}|CE|0" in med and f"{bucket}|CE|2" in med:
            structures[f"debit CE dte {bucket} ATM / 2 OTM"] = debit_spread(
                money(med[f"{bucket}|CE|0"]), money(med[f"{bucket}|CE|2"]), lot, spot, on, c, fill
            )
    ladder = []
    for bal in LADDER:
        row: Row = {"balance_rs": bal, "fixed_cost_pct_pm": float(money(FIXED_PM_STRESSED * 100 / bal)),
                    "fd_baseline_rs_pm": money(Decimal(bal) * dated(c["fd_rate_1y"], on) / 100 / 12)}  # fmt: skip
        for name, s in structures.items():
            key = "cash_needed_favourable_rs" if favourable else "cash_needed_stressed_rs"
            need = s[key] if key in s else s["cash_needed_rs"]
            row[name] = {"fits": bool(need <= bal), "max_loss_pct": float(money(s["max_loss_rs"] * 100 / bal)),
                         "chain_ok": bool(chain_floor(s["max_loss_rs"]) <= bal)}  # fmt: skip
        ladder.append(row)
    floors = {n: chain_floor(s["max_loss_rs"]) for n, s in structures.items()}
    fits = [
        r["balance_rs"] for r in ladder if any(v["fits"] and v["chain_ok"] for k, v in r.items() if isinstance(v, dict))
    ]
    return {"lot": lot, "on": str(on), "structures": structures, "chain_floor_rs": floors, "ladder": ladder,
            "smallest_row": min(fits) if fits else None}  # fmt: skip


def _plain(x: Any) -> Any:
    if isinstance(x, Decimal):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_plain(v) for v in x]
    return x


def rs(x: Decimal | int) -> str:
    """Indian grouping, no paise: 12345 -> 12,345."""
    n = int(Decimal(x).to_integral_value(ROUND_HALF_UP))
    s = str(n)
    head, tail = s[:-3], s[-3:]
    while len(head) > 2:
        tail = head[-2:] + "," + tail
        head = head[:-2]
    return (head + "," + tail) if head else tail


def card(f: Row, favourable_row: int | None) -> list[str]:
    st = f["structures"]
    atm, otm, spr = (
        st.get(k, {}) for k in ("long dte 8-15 ATM", "long dte 8-15 2 OTM", "debit CE dte 8-15 ATM / 2 OTM")
    )
    low = min(f["chain_floor_rs"].values())
    answer = f"1 LOT: kam se kam ₹{rs(f['smallest_row'])}" if f["smallest_row"] else "1 LOT: NAHI"
    if f["smallest_row"] != favourable_row:
        answer = "1 LOT: PATA NAHI"
    lad = f["ladder"]
    row: Row = next((r for r in lad if r["balance_rs"] == f["smallest_row"]), {})
    fit = [n for n, v in row.items() if isinstance(v, dict) and v["fits"] and v["chain_ok"]]
    cheapest = min(fit, key=lambda n: f["chain_floor_rs"][n]) if fit else "koi nahi"
    lines = [
        "FEASIBILITY · 1 lot = 30 · PRE-TAX · kharche stressed [CODE(SOURCE)]",
        f"ATM option 8-15 din: lot ₹{rs(atm['cash_needed_rs'])} [REAL] · max loss ₹{rs(atm['max_loss_rs'])}",
        f"2 OTM option 8-15 din: lot ₹{rs(otm['cash_needed_rs'])} [REAL] · max loss ₹{rs(otm['max_loss_rs'])}",
        f"Debit spread ATM/2OTM: max loss ₹{rs(spr['max_loss_rs'])} · cash ₹{rs(spr['cash_needed_stressed_rs'])}"
        " [ESTIMATE]",
        f"Ek leg round trip ₹{rs(atm['round_trip_stressed_rs'])} [ESTIMATE] · break-even"
        f" {atm['breakeven_points']} points",
        f"Chain floor (2 x max loss): sabse kam ₹{rs(low)} [CODE(REAL)]",
        f"Jo fit hua: {cheapest}"[:75],
        f"Fixed ₹1,500/mahina = {lad[1]['fixed_cost_pct_pm']}% of ₹15k, {lad[3]['fixed_cost_pct_pm']}% of ₹25k",
        f"FD 6.25%: ₹15k par ₹{rs(lad[1]['fd_baseline_rs_pm'])}/mahina [SOURCE]",
        "Ye sirf hisaab hai: fayda (edge) ka saboot nahi.",
        answer,
    ]
    return lines


def ladder_md(f: Row) -> str:
    names = list(f["structures"])
    keep = [n for n in names if "8-15" in n]
    head = "| balance | fixed cost % / month | FD ₹ / month | " + " | ".join(keep) + " | P(HARD KILL 12m) | DD p95 |"
    out = [
        "# BALANCE LADDER (MISSION V19 RULES K2): skeleton from Phase 2c; 3e fills the Monte Carlo columns",
        "",
        f"1 lot = {f['lot']} units; costs PRE-TAX and stressed; premiums = REAL medians at 10:00 IST"
        " (results/feasibility.json).",
        "Cell = fits / max loss % of balance / chain OK (2 x max loss <= balance)."
        " Spread cash uses the margin ESTIMATE.",
        "",
        head,
        "|" + "---|" * (len(keep) + 5),
    ]
    for r in f["ladder"]:
        cells = [
            f"{'fits' if r[n]['fits'] else 'no'} / {r[n]['max_loss_pct']}% / {'OK' if r[n]['chain_ok'] else 'no'}"
            for n in keep
        ]
        out.append(
            f"| ₹{rs(r['balance_rs'])} | {r['fixed_cost_pct_pm']}% | ₹{rs(r['fd_baseline_rs_pm'])} | "
            + " | ".join(cells)
            + " | 3e | 3e |"
        )
    out += ["", "MIN_LIVE_BALANCE_RS / MAX_BALANCE_RS: derived in 3e (K2), never from this skeleton alone."]
    return "\n".join(out) + "\n"


def main() -> int:
    gaps = json.loads((ROOT / "results/data_gaps.json").read_text(encoding="utf-8"))
    excluded = set(gaps["G3"]["band_narrower_than_2pct"])
    days = [d for d in gaps["valid_days_list"] if d >= gaps["G4"]["regime_from"] and d not in excluded]
    prem = real_premiums(ROOT / "data/banknifty/repo", days)
    c = consts()
    on = dt.date(2026, 11, 18)
    lot = int(dated(c["lot_size"], on))
    f = feasibility(prem, lot, on, c)
    favourable = feasibility(prem, lot, on, c, favourable=True)["smallest_row"]  # kill side: fill at ₹0 (C4)
    lines = card(f, favourable)
    assumptions = {
        "side_fill_per_unit_rs": str(SIDE_FILL_PER_UNIT),
        "stress": str(STRESS),
        "margin_leg2_share_of_notional": str(MARGIN_LEG2_SHARE),
        "fixed_pm_stressed_rs": str(FIXED_PM_STRESSED),
    }
    out = {
        "premiums": prem,
        "feasibility": _plain(f),
        "favourable_smallest_row": favourable,
        "assumptions": assumptions,
    }
    (ROOT / "results/feasibility.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    (ROOT / "results/feasibility_card.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "docs/BALANCE_LADDER.md").write_text(ladder_md(f), encoding="utf-8")
    print("\n".join(lines))
    print("days", prem["days"], "max line", max(len(x) for x in lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
