#!/usr/bin/env python3
"""Engine of record (MISSION V19 C10, ST9): bars -> strategy.decide -> next-bar fill -> RISK SHELL exits, bar by bar.
Shares with the lab only the contracts, the clock, the data reader and the cost model (never its vectorized code);
every verdict number comes from here (lab/replay_agree.py checks AGREE, RULES K5)."""

import datetime as dt
import json
import math
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
from bot.contracts import Bar, Intent, MarketState, Strategy, TradeRecord  # noqa: E402
from tools import bn_economics as be  # noqa: E402

N, FIRST, LAST, STEP, FORCE_FLAT = 385, 15, 315, 5, 355  # minutes after 09:15; FORCE_FLAT = 15:10 IST
MAX_ENTRIES, COOLOFF = 2, 30
HALF_SPREAD, SLIP = Decimal("0.50"), Decimal("0.20")  # ₹ per unit per side, ESTIMATE (D-21); stressed below (ST7)
Arr = dict[str, list[float]]


@dataclass(frozen=True)
class Day:
    day: dt.date
    expiry: dt.date
    lot: int
    index: tuple[Bar, ...]
    vix: list[float]
    opts: dict[tuple[float, str], Arr]


class StressedCosts:
    """CostModel (bot.contracts): SOURCE charges by date, x 1.5; ST7 spread and slippage stress."""

    def __init__(self) -> None:
        self.c = be.consts()

    def charges(self, prices: tuple[tuple[float, float], ...], lot: int, day: dt.date) -> Decimal:
        out = Decimal(0)
        for i, (entry, exit_) in enumerate(prices):
            out += be.round_trip(Decimal(str(entry)), Decimal(str(exit_)), lot, day, self.c, long=i == 0)
        return out

    def fill_stressed(self, legs: int, lot: int, minutes: tuple[int, int], expiry_day: bool, stale: bool) -> Decimal:
        def mult(m: int) -> Decimal:
            return Decimal(4) if m < 10 or 330 <= m <= 355 else Decimal(3) if expiry_day else Decimal(2)

        m_in, m_out = mult(minutes[0]), mult(minutes[1]) * (2 if stale else 1)
        return be.money(lot * legs * ((HALF_SPREAD * m_in + 2 * SLIP) + (HALF_SPREAD * m_out + 2 * SLIP)))


def value_path(day: Day, intent: Intent) -> tuple[Arr, list[bool]] | None:
    """Price path of the structure: one option, or a debit spread (long - short, pessimistic low)."""
    keys = [(leg.strike, leg.opt_type) for leg in intent.legs]
    if any(k not in day.opts for k in keys):
        return None
    a = day.opts[keys[0]]
    if len(keys) == 1:
        return {k: a[k] for k in ("o", "h", "l", "c")}, [bool(x) for x in a["live"]]
    b = day.opts[keys[1]]
    net = {
        "o": [x - y for x, y in zip(a["o"], b["o"], strict=True)],
        "c": [x - y for x, y in zip(a["c"], b["c"], strict=True)],
        "l": [x - y for x, y in zip(a["l"], b["h"], strict=True)],
    }
    net["h"] = list(net["c"])
    return net, [bool(x and y) for x, y in zip(a["live"], b["live"], strict=True)]


def manage(v: Arr, live: list[bool], e: int, it: Intent) -> tuple[int, float, str, bool, float]:
    """Exit minute, exit value, reason, stale exit: the RISK SHELL rules with the pessimistic intrabar rule."""
    entry = v["o"][e]
    risk = it.stop_frac * entry
    stop, target, trail, mae = entry - risk, entry + it.target_r * risk, False, 0.0
    for m in range(e, FORCE_FLAT + 1):
        lo, hi, cl = v["l"][m], v["h"][m], v["c"][m]
        if math.isnan(lo) or math.isnan(hi) or math.isnan(cl):
            continue
        cur = entry if trail else stop
        mae = min(mae, max(lo, min(cur, v["o"][m])) - entry)
        if lo <= cur:
            return m, min(cur, v["o"][m]), "breakeven" if trail else "stop", not live[m], mae
        if hi >= target:
            return m, target, "target", not live[m], mae
        trail = trail or hi >= entry + risk
        held = m - e + 1
        if held >= it.scratch_min and cl <= entry and not trail:
            return m, cl, "scratch", not live[m], mae
        if held >= it.time_stop_min or m == FORCE_FLAT:
            return m, cl, "time" if held >= it.time_stop_min else "force_flat", not live[m], mae
    return FORCE_FLAT, entry, "no_bar", True, 0.0


def run_day(day: Day, strategy: Strategy, costs: StressedCosts, max_entries: int = MAX_ENTRIES) -> list[TradeRecord]:
    out: list[TradeRecord] = []
    free_after, cool_until, over = -1, -1, False
    for t in range(FIRST, LAST + 1, STEP):
        if over or len(out) >= max_entries or t <= free_after:
            continue
        vix = [x for x in day.vix[:t] if not math.isnan(x)]
        if not vix:
            continue
        res = strategy.decide(MarketState(day.day, t, day.expiry, vix[0], vix[-1]), day.index[:t])
        path = value_path(day, res) if isinstance(res, Intent) else None
        if not isinstance(res, Intent) or path is None:
            continue
        v, live = path
        e = next((m for m in range(t, min(t + 3, FORCE_FLAT)) if live[m] and v["o"][m] > 0), -1)
        if e < 0 or e <= free_after or e < cool_until:
            continue
        x, xval, reason, stale, mae = manage(v, live, e, res)
        legs = res.legs
        legs_px = tuple(
            (
                day.opts[(g.strike, g.opt_type)]["o"][e],
                day.opts[(g.strike, g.opt_type)]["c"][x] if len(legs) == 2 else xval,
            )
            for g in legs
        )
        charges = costs.charges(legs_px, day.lot, day.day)
        fill = costs.fill_stressed(len(legs), day.lot, (e, x), day.expiry == day.day, stale)
        gross = be.money(Decimal(str(xval - v["o"][e])) * day.lot)
        net = be.money(gross - Decimal("1.5") * charges - fill)
        out.append(
            TradeRecord(
                res.intent_id,
                day.day,
                legs,
                e,
                x,
                v["o"][e],
                xval,
                day.lot,
                gross,
                charges,
                fill,
                net,
                reason,
                be.money(Decimal(str(mae)) * day.lot),
            )
        )
        free_after = x
        if net < 0:
            cool_until = x + COOLOFF
        max_loss = Decimal(str(v["o"][e])) * day.lot + Decimal("1.5") * charges + fill
        over = net <= -max_loss / 2
    return out


def load_day(repo: Path, day: dt.date, lots: dict[str, int]) -> Day:
    from lab import data  # noqa: PLC0415 (data reader only)

    def minute(ts: dt.datetime) -> int:
        return (ts.hour - 9) * 60 + ts.minute - 15

    nan = math.nan
    start = dt.datetime.combine(day, dt.time(9, 15))
    grid = [Bar(start + dt.timedelta(minutes=m), nan, nan, nan, nan) for m in range(N)]
    for r in data.read_day(repo, "spot_1m", day, columns=["ts_open", "o", "h", "l", "c"]).to_pylist():
        if 0 <= minute(r["ts_open"]) < N:
            grid[minute(r["ts_open"])] = Bar(r["ts_open"], r["o"], r["h"], r["l"], r["c"])
    index = tuple(grid)  # one Bar per minute (NaN where the index has no bar), so index[:t] = minutes [0, t)
    vix = [nan] * N
    for r in data.read_day(repo, "vix_1m", day, underlying=data.VIX, columns=["ts_open", "c"]).to_pylist():
        if 0 <= minute(r["ts_open"]) < N:
            vix[minute(r["ts_open"])] = r["c"]
    rows = data.read_day(
        repo,
        "options",
        day,
        columns=["expiry_date", "strike", "option_type", "ts_open", "o", "h", "l", "c", "v", "is_stale"],
    ).to_pylist()
    expiry = min(r["expiry_date"] for r in rows if r["expiry_date"] >= day)
    opts: dict[tuple[float, str], Arr] = {}
    for r in rows:
        if r["expiry_date"] != expiry or not 0 <= minute(r["ts_open"]) < N:
            continue
        a = opts.setdefault(
            (r["strike"], r["option_type"]), {k: [math.nan] * N for k in ("o", "h", "l", "c")} | {"live": [0.0] * N}
        )
        m = minute(r["ts_open"])
        for k in ("o", "h", "l", "c"):
            a[k][m] = r[k]
        a["live"][m] = 1.0 if r["v"] and not r["is_stale"] else 0.0
    return Day(day, expiry, lots[str(expiry)], index, vix, opts)


def run(days: list[str], strategy: Strategy) -> list[TradeRecord]:
    lots = {
        e: int(v) for e, v in json.loads((ROOT / "data/lab/data_profile.json").read_text())["lots_by_expiry"].items()
    }
    costs = StressedCosts()
    out: list[TradeRecord] = []
    for d in days:
        out += run_day(load_day(ROOT / "data/banknifty/repo", dt.date.fromisoformat(d), lots), strategy, costs)
    return out
