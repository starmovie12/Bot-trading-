"""Phase 3e (MISSION V19 LAB): holdout opened ONCE, Monte Carlo x 4, K1 limits, K2 ladder (python -m lab.holdout_mc).

Writes holdout_log.jsonl (the one open record), data/lab/eor_holdout.json, results/holdout.json,
results/monte_carlo.json, results/limits_derivation.json, docs/BALANCE_LADDER.md and limits.toml (a PIN BUMP).
Every number comes from engine-of-record trades (C10), stressed costs, PRE-TAX.
"""

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np

from bot.strategy.orb_vix import OrbVix
from lab.select_spec import SEED, as_dict, day_marks
from tools import bn_economics as be
from tools import engine_of_record as eor
from tools.truth_tests import Holdout

ROOT = Path(__file__).resolve().parent.parent
ON = dt.date(2026, 11, 18)  # the cycle date: lot and charge rows in force for the limits
PATHS, YEAR, KILL_P = 10_000, 250, 0.05  # 12 months = 250 trading days (ASSUMPTION)
LADDER = (10_000, 15_000, 20_000, 25_000, 30_000, 40_000, 50_000, 75_000, 100_000, 150_000, 200_000)
SPREAD_COL = "debit CE dte 16-40 ATM / 2 OTM"  # the 2c skeleton cell for the nearest monthly expiry


def holdout_trades(days: list[str]) -> list[dict[str, Any]]:
    cache, log = ROOT / "data/lab/eor_holdout.json", Holdout(ROOT / "holdout_log.jsonl")
    if not log.opened():
        log.open(date=str(ON), strategy="A1+b1 (bot.strategy.orb_vix)", days=len(days), engine="engine_of_record")
    elif cache.is_file():
        return list(json.loads(cache.read_text(encoding="utf-8")))
    trades = [as_dict(t) for t in eor.run(days, OrbVix())]
    cache.write_text(json.dumps(trades) + "\n", encoding="utf-8")
    return trades


def block_idx(rng: np.random.Generator, n_days: int, block: int, paths: int, length: int) -> np.ndarray:
    starts = rng.integers(0, n_days - block + 1, size=(paths, length // block + 1))
    return (starts[:, :, None] + np.arange(block)).reshape(paths, -1)[:, :length]


def hlo(trades: list[dict[str, Any]], days: list[str]) -> float:
    """Lower end of the two-sided 95% CI of the stressed mean net per trade (5-day blocks, 10,000 resamples)."""
    net, _ = day_marks(trades, days)
    cnt = np.zeros(len(days))
    for t in trades:
        cnt[days.index(t["day"])] += 1
    idx = block_idx(np.random.default_rng(SEED), len(days), 5, PATHS, len(days))
    n = cnt[idx].sum(axis=1)
    means = net[idx].sum(axis=1)[n > 0] / n[n > 0]
    return float(np.percentile(means, 2.5))


def ensemble(net: np.ndarray, low: np.ndarray, block: int, inject: float = 0.0) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(SEED)
    idx = block_idx(rng, len(net), block, PATHS, YEAR)
    n, lo = net[idx], low[idx]
    if inject:
        pos = np.argsort(rng.random((PATHS, YEAR)), axis=1)[:, :2]  # 2 distinct injected days per path
        rows = np.arange(PATHS)[:, None]
        n[rows, pos], lo[rows, pos] = -inject, -inject
    end = np.cumsum(n, axis=1)
    start = end - n
    trough = np.minimum(start + lo, end)  # the lowest mark-to-market point of each day
    return {
        "min_eq": np.minimum(trough.min(axis=1), 0.0),
        "dd": (np.maximum.accumulate(start, axis=1) - trough).max(axis=1),
        "final": end[:, -1],
    }


def trade_cap(trades: list[dict[str, Any]], c: dict[str, Any], lot: int) -> tuple[int, dict[str, Any]]:
    """K1: by-construction max loss of 1 ATM long option at the highest premium the strategy paid, + stressed costs."""
    prem = Decimal(str(max(t["entry"] for t in trades)))
    charges = be.round_trip(prem, Decimal(0), lot, ON, c, long=True)
    fill = eor.StressedCosts().fill_stressed(1, lot, (0, 330), True, True)  # worst buckets, stale exit
    raw = prem * lot + Decimal("1.5") * charges + fill
    cap = int(be.ceil_to(raw, 50))
    return cap, {
        "premium_pts": float(prem),
        "lot": lot,
        "charges_x1_5": float(Decimal("1.5") * charges),
        "fill": float(fill),
    }


def size(ens: dict[str, dict[str, np.ndarray]], cap: int) -> int:
    total = int(be.ceil_to(Decimal(2 * cap), 500))
    while max(float(np.mean(e["min_eq"] <= -total)) for e in ens.values()) > KILL_P:
        total += 500
    return total


def ladder(
    lim: dict[str, Any], prem_lot: float, fixed: float, base_pm: float, spread: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    fd = float(be.consts()["fd_rate_1y"]["value"])
    for b, sp in zip(LADDER, spread, strict=True):
        chain = 2 * lim["mtl"] <= lim["dd"] <= lim["total"] <= b
        cond = {
            "fits": prem_lot <= b,
            "max_loss_within_cap": True,  # the cap IS the by-construction max loss (K1)
            "chain": chain,
            "p_kill_ok": lim["p_kill"] <= KILL_P,
            "cost_ok": fixed <= 0.5 * base_pm,
        }
        rows.append({
            "balance_rs": b, "long": cond, "pass": all(cond.values()),
            "max_loss_pct": round(lim["mtl"] / b * 100, 1), "dd95_pct": round(lim["dd95"] / b * 100, 1),
            "fixed_pct": round(fixed / b * 100, 2), "fd_pm": round(b * fd / 1200), "spread": sp[SPREAD_COL],
        })  # fmt: skip
    return rows


def entry(name: str, value: Any, unit: str, tag: str, direction: str, note: str) -> list[str]:
    v = str(value).lower() if isinstance(value, bool) else value
    return [f"[{name}]", f"value = {v}", f'unit = "{unit}"', f'tag = "{tag}"', f'direction = "{direction}"',
            f'note = "{note}"', ""]  # fmt: skip


def limits_toml(lim: dict[str, Any], capital: int, live: dict[str, int] | None) -> str:
    t, lw, hi = "3E(ESTIMATE, PROVISIONAL until Phase 7)", "lower_is_tighter", "higher_is_tighter"
    out = [
        "# limits.toml: the ONE source of risk limits (MISSION V19 RULES K1). Derived in 3e by lab/holdout_mc.py",
        "# (results/limits_derivation.json); PROVISIONAL (ESTIMATE spreads) until Phase 7, which may only tighten.",
        "# Fixed rupees: every _RS limit is the same number at every balance; only EQUITY_FLOOR_RS follows the",
        "# effective balance (bot.limits.derive_day_limits). Chain: 2 x MAX_TRADE_LOSS_RS <= MAX_DRAWDOWN_RS <=",
        "# MAX_TOTAL_LOSS_RS <= effective balance; EQUITY_FLOOR_RS = effective balance - MAX_TOTAL_LOSS_RS.",
        "",
    ]
    out += entry(
        "LIVE_POSSIBLE",
        live is not None,
        "boolean",
        t,
        "exact",
        "false: no ladder row up to 2 lakh passes K2 (NO_LIVE_BALANCE_UP_TO_2L); MIN and MAX are omitted",
    )
    if live:
        out += entry("MIN_LIVE_BALANCE_RS", live["min"], "INR", t, hi, "K2")
        out += entry("MAX_BALANCE_RS", live["max"], "INR", t, lw, "K2, m = 2")
    cap_note = "MIN_LIVE_BALANCE_RS" if live else "paper reference balance: no live balance exists"
    out += entry("CAPITAL_RS", capital, "INR", t, "exact", f"{cap_note}; the limits are calibrated here")
    out += entry(
        "MAX_TRADE_LOSS_RS",
        lim["mtl"],
        "INR per trade",
        t,
        lw,
        "by-construction max loss: highest premium paid x lot + stressed round-trip costs, up to 50",
    )
    out += entry("MAX_DRAWDOWN_RS", lim["dd"], "INR", t, lw, "max(2 x MAX_TRADE_LOSS_RS, MAX_TOTAL_LOSS_RS / 2)")
    out += entry(
        "MAX_TOTAL_LOSS_RS",
        lim["total"],
        "INR",
        t,
        lw,
        "smallest 500 step with worst-of-four Monte Carlo P(HARD KILL in 12 months) <= 5%",
    )
    out += entry("EQUITY_FLOOR_RS", capital - lim["total"], "INR", t, hi, "CAPITAL_RS - MAX_TOTAL_LOSS_RS")
    for name, k in (("DAILY", 2), ("WEEKLY", 4), ("MONTHLY", 8)):
        v = min(k * lim["mtl"], lim["total"])
        out += entry(f"{name}_LOSS_LOCK_RS", v, "INR", t, lw, f"min({k} x MAX_TRADE_LOSS_RS, MAX_TOTAL_LOSS_RS)")
    out += entry("COOLOFF_MIN", 30, "minutes after a losing trade", t, hi, "the RISK SHELL value (PLAN.md PREREG-0)")
    out += entry("MAX_LOTS", 1, "lots per leg", "OWNER(R2)", lw, "the gateway also hard-codes ABS_MAX_LOTS = 1")
    out += entry("H2_MONTHLY_RS", 1500, "INR per month", "OWNER", lw, "H2: new spend the bot causes (R5 cap)")
    return "\n".join(out)


def ladder_md(rows: list[dict[str, Any]], lim: dict[str, Any], base_pm: float, live: Any) -> str:
    out = [
        "# BALANCE LADDER (MISSION V19 RULES K2; filled in 3e; PROVISIONAL until Phase 7)",
        "",
        f"Strategy A1+b1 (EXPERIMENTAL: paper only), 1 lot long ATM option. Per-trade cap ₹{lim['mtl']:,}, "
        f"MAX_TOTAL_LOSS ₹{lim['total']:,}, P(HARD KILL 12m) {lim['p_kill']:.3f} and DD p95 ₹{lim['dd95']:,.0f}: "
        "worst of four Monte Carlo ensembles, stressed, PRE-TAX [BACKTEST].",
        f"Base-case stressed net per month: ₹{base_pm:,.0f} [BACKTEST]; fixed monthly cost ₹1,500 [ESTIMATE].",
        "",
        "| balance | 1 lot fits | max loss % | chain | P(kill) <= 5% | fixed cost % / month | cost <= half net | "
        "FD ₹ / month | DD p95 % | spread (fits / max loss % / chain) | row passes |",
        "|" + "---|" * 11,
    ]
    for r in rows:
        c, sp = r["long"], r["spread"]
        yn = {True: "yes", False: "no"}
        out.append(
            f"| ₹{r['balance_rs']:,} | {yn[c['fits']]} | {r['max_loss_pct']}% | {yn[c['chain']]} | "
            f"{yn[c['p_kill_ok']]} | {r['fixed_pct']}% | {yn[c['cost_ok']]} | ₹{r['fd_pm']:,} | {r['dd95_pct']}% | "
            f"{'fits' if sp['fits'] else 'no'} / {sp['max_loss_pct']}% / {'OK' if sp['chain_ok'] else 'no'} | "
            f"{yn[r['pass']]} |"
        )
    out.append("")
    out.append(
        f"MIN_LIVE_BALANCE_RS = ₹{live['min']:,}, MAX_BALANCE_RS = ₹{live['max']:,}."
        if live
        else "No row up to ₹2,00,000 passes: LIVE_POSSIBLE = false (NO_LIVE_BALANCE_UP_TO_2L)."
        " The bot ships PAPER only."
    )
    return "\n".join(out) + "\n"


def main() -> int:
    split = json.loads((ROOT / "data/lab/split.json").read_text(encoding="utf-8"))
    design, hold = split["design"], split["holdout"]
    d_tr = json.loads((ROOT / "data/lab/eor_design.json").read_text(encoding="utf-8"))
    h_tr = holdout_trades(hold)
    h_lo = hlo(d_tr, design)
    h_mean = float(np.mean([t["net"] for t in h_tr])) if h_tr else 0.0
    h_pass = bool(h_tr) and h_mean > 0 and h_mean >= h_lo
    holdout = {
        "trades": len(h_tr),
        "days": len(hold),
        "mean_net_rs": round(h_mean, 2),
        "hlo_rs": round(h_lo, 2),
        "total_net_rs": round(sum(t["net"] for t in h_tr), 2),
        "pass": h_pass,
        "code": None if h_pass else "HOLDOUT_FAIL",
        "label": "BACKTEST(out-of-sample), stressed, PRE-TAX",
    }
    days, trades = design + hold, d_tr + h_tr
    net, low = day_marks(trades, days)
    c = be.consts()
    lot = int(be.dated(c["lot_size"], ON))
    cap, cap_info = trade_cap(trades, c, lot)
    inject = 2 * cap + 2 * cap_info["fill"]
    ens = {f"block{b}": ensemble(net, low, b) for b in (1, 5, 10)} | {"tail5": ensemble(net, low, 5, inject)}
    total = size(ens, cap)
    lim: dict[str, Any] = {"mtl": cap, "total": total, "dd": max(2 * cap, total // 2)}
    lim["p_kill"] = max(float(np.mean(e["min_eq"] <= -total)) for e in ens.values())
    lim["dd95"] = max(float(np.percentile(e["dd"], 95)) for e in ens.values())
    base_pm = float(net.sum()) / len(days) * 21
    fixed = float(be.FIXED_PM_STRESSED)
    spread = json.loads((ROOT / "results/feasibility.json").read_text(encoding="utf-8"))["feasibility"]["ladder"]
    rows = ladder(lim, cap_info["premium_pts"] * lot, fixed, base_pm, spread)
    passing = [r["balance_rs"] for r in rows if r["pass"]]
    live = None
    if passing:
        mx = max(r["balance_rs"] for r in rows if r["pass"] and r["balance_rs"] <= 2 * passing[0])
        live = {"min": passing[0], "max": mx}
    risk_ok = [r["balance_rs"] for r in rows if r["long"]["fits"] and r["long"]["chain"]]
    capital = live["min"] if live else (risk_ok[0] if risk_ok else int(be.ceil_to(Decimal(total), 5000)))
    mc = {
        k: {
            "p_kill": round(float(np.mean(e["min_eq"] <= -total)), 4),
            "dd95_rs": round(float(np.percentile(e["dd"], 95)), 0),
            "median_12m_rs": round(float(np.median(e["final"])), 0),
        }
        for k, e in ens.items()
    }
    deriv = {
        "cap": cap_info | {"max_trade_loss_rs": cap},
        "limits": lim,
        "inject_rs": inject,
        "monte_carlo": mc,
        "base_net_per_month_rs": round(base_pm, 2),
        "fixed_pm_rs": fixed,
        "live": live,
        "capital_rs": capital,
        "code": None if live else "NO_LIVE_BALANCE_UP_TO_2L",
        "ladder": rows,
        "days": len(days),
        "trades": len(trades),
        "seed": SEED,
        "paths": PATHS,
        "year_days": YEAR,
        "on": str(ON),
    }
    for name, obj in (("holdout", holdout), ("monte_carlo", mc), ("limits_derivation", deriv)):
        (ROOT / f"results/{name}.json").write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    (ROOT / "docs/BALANCE_LADDER.md").write_text(ladder_md(rows, lim, base_pm, live), encoding="utf-8")
    (ROOT / "limits.toml").write_text(limits_toml(lim, capital, live), encoding="utf-8")
    print(json.dumps({"holdout": holdout, "limits": lim, "mc": mc, "live": live, "capital": capital}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
