"""S3 engine: Adaptive Sniper (§6, §7). One open trade at a time; every number from the registry (Cfg / FIX).

Trade path decisions use the BASE series; net_stress / net_proxy reprice the same path (entry and exit fills).
Intrabar modes: BARCLOSE (the rule, SL moves only at bar close), PATH and WORST (sensitivity only, §6.3).
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from functools import lru_cache
from typing import Any

import numpy as np

from lab.s3 import costs
from lab.s3.data import Day, N
from lab.s3.features import Sig
from lab.s3.registry import CHK, FIX, RAW, SCORE, Cfg, hhmm, minute

TICK = Decimal(str(FIX["TICK"]))
M_FF = minute(str(FIX["FORCE_FLAT"]))
M_EXP = minute(str(FIX["EXPIRY_EXIT"]))
M_EXP_LAST = minute(str(FIX["EXPIRY_LAST_DECISION"]))
REASONS_SKIP = (
    "WINDOW",
    "EXPIRY_AFTER_1259",
    "EARLY_BARS",
    "CALL_PUT_TAKRAAV",
    "IN_TRADE",
    "DAY_STOP_2LOSS",
    "PROFIT_FLOOR",
    "MAX_TRADES",
    "SHOCK",
    "COOLDOWN",
    "NO_STRIKE_IN_BAND",
    "NO_FILL_STALE",
    "NO_FILL_BAND",
    "MAX_LOSS_CAP",
    "DAY_LOSS_ROOM",
    "RISK_TOO_BIG",
    "GATE_IVP",
    "GATE_OI_WALL",
    "REENTRY_CHASE",
)


def dec(x: float) -> Decimal:
    return Decimal(repr(round(float(x), 6)))


@dataclass(frozen=True)
class Px:
    """Half spread and slippage of one cost series (rupees per unit, per side)."""

    hs: Decimal
    slip: Decimal


BASE = Px(costs.base().half_spread, costs.base().slip)


@dataclass(frozen=True)
class Mode:
    """How a run fills and moves the stop: intrabar BARCLOSE / PATH / WORST, and the cost series."""

    intrabar: str = "BARCLOSE"
    px: Px = BASE
    dd_cut: bool = False  # §10.2 cut: equity 5% below its peak (set per day by the runner)


BARCLOSE = Mode()


def windows(cfg: Cfg, dte: int) -> np.ndarray[Any, np.dtype[np.bool_]]:
    m = np.arange(N)
    w = ((m >= minute(cfg["DECISION_START"])) & (m <= minute(cfg["MORNING_END"]))) | (
        (m >= minute(cfg["AFTERNOON_START"])) & (m <= minute(cfg["LAST_ENTRY"]))
    )
    if dte == 0:
        w &= m <= M_EXP_LAST
    return np.asarray(w)


def in_any_window(cfg: Cfg, t: int) -> bool:
    return bool(windows(cfg, 1)[t])


# ---------- money ----------


@lru_cache(maxsize=1 << 16)
def rt_total(entry: Decimal, exit_: Decimal, qty: int, day: dt.date) -> Decimal:
    return costs.round_trip(entry, exit_, qty, day)["total"]


def net(entry: Decimal, exit_: Decimal, qty: int, day: dt.date) -> Decimal:
    return (exit_ - entry) * qty - rt_total(entry, exit_, qty, day)


@lru_cache(maxsize=1 << 16)
def be_pts(f: Decimal, qty: int, day: dt.date, px: Px = BASE) -> Decimal:
    """Smallest x on the tick grid with net_base >= 0 when the exit level is F + x (§7.6)."""
    x = Decimal(0)
    while net(f, costs.sell_fill(f + x, px.hs, px.slip), qty, day) < 0:
        x += TICK
    return x


def risk(n: int, lot: int, f: Decimal, sl_pts: Decimal, day: dt.date, px: Px = BASE) -> Decimal:
    """§10.2 risk(n): n x lot x (SL + half spread + slip) + round-trip charges at that SL fill."""
    q = n * lot
    exit_fill = f - sl_pts - px.hs - px.slip
    return q * (sl_pts + px.hs + px.slip) + rt_total(f, exit_fill, q, day)


def cap_ok(n: int, lot: int, f: Decimal, day: dt.date) -> bool:
    """§2 #12: F x qty + round-trip charges (worst-case sell at 0) within MAX_TRADE_LOSS_RS and CAPITAL_RS."""
    q = n * lot
    outlay = f * q + rt_total(f, Decimal(0), q, day)
    return outlay <= Decimal(FIX["MAX_TRADE_LOSS_RS"]) and outlay <= Decimal(FIX["CAPITAL_RS"])


def size_at_fill(
    f: Decimal,
    lot: int,
    day: dt.date,
    sl_pts: Decimal,
    room_now: tuple[Decimal, Decimal | None],
    cfg: Cfg,
    n0: int,
    px: Px = BASE,
) -> tuple[int, str]:
    """§7.5: mode lots -> cap -> day room (-DAY_MAX_LOSS) -> profit floor. Returns (n, lots_reason or skip)."""
    day_net, floor = room_now
    n, why = min(n0, int(FIX["S3_MAX_LOTS"])), "MODE"
    while n > 0 and not cap_ok(n, lot, f, day):
        n, why = n - 1, "CAP"
    if n == 0:
        return 0, "MAX_LOSS_CAP"
    room = -Decimal(str(cfg["DAY_LOSS_SU"])) * Decimal(str(cfg["RISK_PER_TRADE_RS"]))
    while n > 0 and day_net - risk(n, lot, f, sl_pts, day, px) < room:
        n, why = n - 1, "DAY"
    if n == 0:
        return 0, "DAY_LOSS_ROOM"
    if floor is not None:
        while n > 0 and day_net - risk(n, lot, f, sl_pts, day, px) < floor:
            n, why = n - 1, "DAY"
        if n == 0:
            return 0, "PROFIT_FLOOR"
    return n, why


def risk_lots(f: Decimal, lot: int, sl_pts: Decimal, budget: Decimal, day: dt.date) -> tuple[int, str]:
    """N17 (§10.2): largest n <= 3 with risk(n) <= budget; none -> RISK_TOO_BIG."""
    for n in range(int(FIX["S3_MAX_LOTS"]), 0, -1):
        if risk(n, lot, f, sl_pts, day) <= budget:
            return n, "RISK"
    return 0, "RISK_TOO_BIG"


# ---------- strike ----------


def atm(d: Day, t: int) -> float:
    s = d.base["spot_c"][t]
    ks = np.unique(d.strikes)
    return float(ks[np.argmin(np.abs(ks - s))])


def strike_step(d: Day, t: int) -> float:
    """STRIKE_STEP: distance from the ATM strike to its nearest listed neighbour (§7.1)."""
    ks = np.unique(d.strikes)
    a = atm(d, t)
    other = np.abs(ks[ks != a] - a)
    if other.size == 0:
        raise ValueError(f"{d.day}: one strike only, no STRIKE_STEP")
    return float(np.min(other))


def _delta_pick(d: Day, t: int, sel: Any, band: Any, target: float) -> int:
    lo_d, hi_d = (float(x) for x in band)
    dl = np.abs(d.opt["delta"][:, t])
    ok = sel & (dl >= lo_d) & (dl <= hi_d)
    if not np.any(ok):
        return -1
    idx = np.flatnonzero(ok)
    return int(idx[np.argmin(np.abs(dl[idx] - target))])


def pick_strike(d: Day, t: int, side: str, cfg: Cfg) -> tuple[int, str]:
    """§7.4 / R2: at signal-bar close. PREMIUM_BAND (T1): premium band nearest PREMIUM_TARGET. DELTA_BAND: |Delta| in
    DELTA_BAND nearest its middle. N6: band strike, but |Delta| < DELTA_FLOOR -> N6_STRIKES_IN strike(s) in-the-money
    if its premium <= N6_PREMIUM_CAP, else skip. N15: CE by CE_DELTA_BAND (nearest its middle), PE by the band.
    DTE 0 (every mode): |Delta| EXPIRY_DELTA nearest EXPIRY_DELTA_TARGET. T1-RAW: nothing found -> ITM1."""
    sel = (d.cp == side) & ~d.stale[:, t]
    mode = str(cfg["STRIKE_MODE"])
    if d.dte == 0:
        k = _delta_pick(d, t, sel, FIX["EXPIRY_DELTA"], float(FIX["EXPIRY_DELTA_TARGET"]))
        if k >= 0:
            return k, "DELTA"
    elif mode == "DELTA_BAND" or (mode == "N15" and side == "CE"):
        band = FIX["DELTA_BAND"] if mode == "DELTA_BAND" else FIX["CE_DELTA_BAND"]
        k = _delta_pick(d, t, sel, band, float(np.mean([float(x) for x in band])))
        if k >= 0:
            return k, "DELTA"
    else:
        px = d.opt["c"][:, t]
        ok = sel & (px >= float(FIX["PREMIUM_MIN"])) & (px <= float(FIX["PREMIUM_MAX"]))
        if np.any(ok):
            idx = np.flatnonzero(ok)
            dist = np.abs(px[idx] - float(FIX["PREMIUM_TARGET"]))
            spot = d.base["spot_c"][t]
            k = int(idx[np.lexsort((np.abs(d.strikes[idx] - spot), dist))[0]])
            if mode != "N6" or abs(d.opt["delta"][k, t]) >= float(cfg["DELTA_FLOOR"]):
                return k, "BAND"
            step = strike_step(d, t) * int(FIX["N6_STRIKES_IN"])
            k2 = d.k(float(d.strikes[k]) + (-step if side == "CE" else step), side)
            if k2 >= 0 and not d.stale[k2, t] and d.opt["c"][k2, t] <= float(FIX["N6_PREMIUM_CAP"]):
                return k2, "N6"
            return -1, "N6_FAIL"
    if cfg.var("strike_itm1"):
        step = strike_step(d, t)
        k = d.k(atm(d, t) + (-step if side == "CE" else step), side)
        if k >= 0 and not d.stale[k, t]:
            return k, "ITM1"
    return -1, "NONE"


# ---------- gates ----------


def k03_on(cfg: Cfg) -> bool:
    """FIX-10: K03 is a switch (K03_SWITCH ON / OFF) inside the variants that carry the gate."""
    return bool(cfg.var("gate_k03")) and cfg["K03_SWITCH"] == "ON"


def k03_ok(d: Day) -> bool | None:
    """IVP <= IVP_MAX on INTRADAY_PREV_CLOSE; status not OK -> NA (None)."""
    if not d.meta.get("ivp_ok") or math.isnan(float(d.meta["ivp"])):
        return None
    return float(d.meta["ivp"]) <= float(FIX["IVP_MAX"])


def k05_ok(d: Day, t: int, side: str, k: int, sl_pts: float) -> bool | None:
    """Next OI wall >= K05_MULT x index risk away (index risk = SL / |Delta|), or the wall's OI fell over 5 min."""
    delta = d.opt["delta"][k, t]
    if not abs(delta) > 0:
        return None
    irisk = sl_pts / abs(delta)
    spot = d.base["spot_c"][t]
    wall = d.base["cm_call_wall" if side == "CE" else "cm_put_wall"][t]
    if math.isnan(wall) or math.isnan(spot):
        return None
    dist = (wall - spot) if side == "CE" else (spot - wall)
    if dist <= 0 or dist >= float(FIX["K05_MULT"]) * irisk:
        return True
    return wall_oi_fell(d, t, side, wall)


def wall_oi_fell(d: Day, t: int, side: str, wall: float) -> bool:
    k = d.k(wall, side)
    n = int(FIX["K05_OI_MIN"])
    if k < 0 or t < n:
        return False
    oi = d.opt["oi"][k]
    return bool(oi[t] < oi[t - n])


# ---------- trade ----------


@dataclass
class Leg:
    bar: int
    level: float
    stale: bool  # stale fill: last non-stale min(low, close) - 2 x (hs + slip)


@dataclass
class TradePath:
    k: int
    e: int
    f: Decimal
    n: int
    lot: int
    sl_init: float
    be_level: float
    g1_trig: float
    exit_bar: int
    exit_level: float
    exit_reason: str
    stale_forced: bool
    peak: float
    peak_bar: int
    max_gear: int
    mfe: float
    mae: float
    step_at_exit: float
    entry_level: float = math.nan  # STEP / TRAIL_BUY intrabar entry level (NaN: the entry bar's open)
    book_bar: int = -1  # N3 runner: bar where one lot was sold at book_level
    book_level: float = math.nan
    book_lots: int = 0


@dataclass
class TradeCtx:
    """Per-trade inputs beyond the option path: shock bars, side, N7 structure level, signals (N12/N14)."""

    shock: np.ndarray[Any, np.dtype[np.bool_]]
    side: str = "CE"
    struct: float = math.nan
    sig: Sig | None = None
    entry_level: float = math.nan
    ref: str = "spot_c"  # N7 structure level is in this series (fut_c when SIGNAL_SRC = FUT)


def opt_atr5(rng: list[float], stale: list[bool], upto: int) -> float:
    vals = [rng[j] for j in range(upto, -1, -1) if not stale[j]][: int(FIX["ATR_OPT_N"])]
    return sum(vals) / len(vals) if vals else math.nan


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if math.isnan(x) else max(lo, min(hi, x))


def simulate(
    d: Day,
    k: int,
    e: int,
    f: Decimal,
    n: int,
    cfg: Cfg,
    ctx: TradeCtx | np.ndarray[Any, np.dtype[np.bool_]],
    run: Mode = BARCLOSE,
) -> TradePath:
    """One trade from its entry bar e (fill F at e's open, or intrabar at ctx.entry_level) to exit,
    per §6.2 / §6.4 / §7.6, plus the exit modules of §11 when their flag / EXIT_MODE is on."""
    c_ = ctx if isinstance(ctx, TradeCtx) else TradeCtx(ctx)
    if str(cfg["EXIT_MODE"]) in ("X-T0", "X-T"):
        return _simulate_xt(d, k, e, f, n, cfg, c_)
    shock = c_.shock
    mode, px = run.intrabar, run.px
    o, h, lo, c = (d.opt[x][k].tolist() for x in ("o", "h", "l", "c"))
    st = d.stale[k].tolist()
    rng = [h[j] - lo[j] for j in range(N)]
    lot = d.lot
    qty = n * lot
    ff = float(f)
    bep = float(be_pts(f, qty, d.day, px))
    atr_e = opt_atr5(rng, st, e - 1)
    xmode = str(cfg["EXIT_MODE"])
    if cfg.var("lock_raw"):
        be_level, g1 = ff + float(RAW["raw"]["LOCK_PTS"]), ff + float(RAW["raw"]["TRIGGER_PTS"])
    else:
        be_level = ff + bep + float(FIX["BE_BUFFER_PTS"])
        g1 = ff + max(float(cfg["G1_TRIGGER_PTS"]), bep + float(FIX["G1_EXTRA_PTS"]))
    g2s, g3s = float(cfg["G2_START"]), float(cfg["G3_START"])
    if cfg.flag("FLAG_N13"):
        g1 = ff + max(bep + float(FIX["G1_EXTRA_PTS"]), float(FIX["N13_G1_ATR"]) * atr_e)
        g2s = clamp(float(FIX["N13_G2_ATR"]) * atr_e, *map(float, FIX["N13_G2_CLAMP"]))
        g3s = clamp(float(FIX["N13_G3_ATR"]) * atr_e, *map(float, FIX["N13_G3_CLAMP"]))
    sl_pts = sl_points(cfg, atr_e)
    floor_sl = ff * (1 - float(FIX["SL_MAX_PCT"]))
    sl = max(ff - sl_pts, floor_sl)
    tgt = math.inf
    if xmode == "X-B":
        tgt = ff + float(FIX["TARGET_XB_PTS"])
    elif xmode == "X-D":
        sl = max(ff * (1 - float(FIX["XD_SL_PCT"])), floor_sl)
        tgt = ff * (1 + float(FIX["XD_TARGET_PCT"]))
    book = ff + float(cfg["RUNNER_BOOK_PTS"]) if xmode == "X-C" and n >= int(FIX["N3_MIN_LOTS"]) else math.inf
    booked: tuple[int, float] | None = None
    why = "SL_G0"
    step_lo, step_hi = (float(x) for x in FIX["STEP_CLAMP"])
    smult, g3m = float(cfg["STEP_MULT"]), float(cfg["G3_MULT"])
    climax, cgap = float(cfg["CLIMAX_PTS"]), float(FIX["CLIMAX_GAP"])
    ts_bars = int(cfg["TIME_STOP_BARS"])
    stale_max = int(FIX["STALE_EXIT_BARS"])
    clock_bar = M_EXP if d.dte == 0 else M_FF
    clock_why = "EXPIRY_1330" if d.dte == 0 else "FORCE_FLAT_1510"
    peak, peak_bar, gear, max_gear, mae = -math.inf, e, 0, 0, 0.0
    step = clamp(smult * atr_e, step_lo, step_hi)
    pending: str | None = None
    stale_run = 0
    last_ns = e
    sgn = 1 if c_.side == "CE" else -1
    spot = d.base[c_.ref]
    n12 = cfg.flag("FLAG_N12") and c_.sig is not None
    n14 = cfg.flag("FLAG_N14") and c_.sig is not None
    rev = c_.sig.f["rev_ce" if c_.side == "CE" else "rev_pe"] if c_.sig is not None else None
    xd_be, xd_tr = ff * (1 + float(FIX["XD_BE_PCT"])), ff * (1 + float(FIX["XD_TRAIL_START_PCT"]))

    def lift(
        sl: float, why: str, gear: int, pk: float, step: float, close_o: tuple[float, float] | None
    ) -> tuple[float, str, int]:
        cands: list[tuple[float, str]] = []
        if xmode == "X-D":
            if pk >= xd_be:
                cands.append((be_level, "SL_G1_LOCK"))
                gear = max(gear, 1)
            if pk >= xd_tr:
                cands.append((pk - float(FIX["XD_TRAIL_RS"]), "TRAIL_G2"))
                gear = max(gear, 2)
        else:
            if pk >= g1:
                cands.append((be_level, "SL_G1_LOCK"))
                gear = max(gear, 1)
            gain = pk - ff
            if gain >= g2s:
                cands.append((pk - step, "TRAIL_G2"))
                gear = max(gear, 2)
            if gain >= g3s:
                cands.append((pk - g3m * step, "TRAIL_G3"))
                gear = 3
            if close_o is not None and close_o[0] - close_o[1] >= climax:
                cands.append((close_o[0] - cgap, "CLIMAX_LOCK"))
        for v, r in cands:
            if v > sl:
                sl, why = v, r
        return sl, why, gear

    sl0 = sl

    def done(bar: int, level: float, reason: str, stale: bool) -> TradePath:
        bb, bl = booked if booked is not None else (-1, math.nan)
        return TradePath(
            k, e, f, n, lot, sl0, be_level, g1, bar, level, reason, stale, peak, peak_bar, max_gear, peak - ff,
            mae, step, c_.entry_level, bb, bl, 1 if booked is not None else 0,
        )  # fmt: skip

    for b in range(e, N):
        ns = not st[b]
        if b >= clock_bar and pending is None:
            pending = clock_why
        if pending is not None:
            if ns:
                return done(b, o[b], pending, False)
            if pending in (clock_why, "SHOCK", "ILLIQUID_EXIT", "FORCE_FLAT_1510", "EXPIRY_1330"):
                return done(b, min(lo[last_ns], c[last_ns]), pending, True)
        if not ns:
            stale_run += 1
            if stale_run >= stale_max and pending is None:
                pending = "ILLIQUID_EXIT"
            if b - e + 1 >= ts_bars and max_gear < 2 and pending is None:
                pending = "TIME_STOP"
            if shock[b] and pending is None:
                pending = "SHOCK"
            continue
        stale_run = 0
        intrabar_entry = b == e and not math.isnan(c_.entry_level)
        if not intrabar_entry:
            if o[b] <= sl:
                return done(b, o[b], "GAP_SL", False)
            green = c[b] > o[b]
            if (mode == "BARCLOSE" or (mode == "PATH" and green)) and lo[b] <= sl:
                return done(b, sl, why, False)
            if h[b] >= tgt:
                return done(b, tgt, "TARGET30", False)
            if booked is None and h[b] >= book:
                booked = (b, book)
            if mode != "BARCLOSE":
                pk = max(peak, h[b])
                sl, why, gear = lift(sl, why, gear, pk, step, None)
                max_gear = max(max_gear, gear)
                if mode == "WORST" or not green:
                    if lo[b] <= sl:
                        peak, peak_bar = (pk, b) if h[b] > peak else (peak, peak_bar)
                        return done(b, sl, why, False)
                elif c[b] <= sl:
                    peak, peak_bar = (pk, b) if h[b] > peak else (peak, peak_bar)
                    return done(b, sl, why, False)
        mae = min(mae, lo[b] - ff)
        if b - e + 1 >= ts_bars and max_gear < 2:
            pending = "TIME_STOP"
        if shock[b] and pending is None:
            pending = "SHOCK"
        if pending is None and not math.isnan(c_.struct) and sgn * (spot[b] - c_.struct) < 0:
            pending = "STRUCTURE_STOP"
        if pending is None and n12 and rev is not None and max_gear <= 1 and b >= 1 and rev[b] and rev[b - 1]:
            pending = "REASON_REVERSAL"
        if h[b] > peak:
            peak, peak_bar = h[b], b
        step = clamp(smult * opt_atr5(rng, st, b), step_lo, step_hi)
        sl, why, gear = lift(sl, why, gear, peak, step, (c[b], o[b]))
        if (
            n14
            and gear == 2
            and c_.sig is not None
            and _near_level(d, c_.sig, b, c_.side, float(cfg["LEVEL_NEAR_ATR"]))
        ):
            v = peak - g3m * step
            if v > sl:
                sl, why = v, "TRAIL_G3"
            gear = 3
        max_gear = max(max_gear, gear)
        if sl >= c[b] and pending is None:
            pending = why
        last_ns = b
    raise AssertionError(f"{d.day} trade open after the last bar")


def _simulate_xt(d: Day, k: int, e: int, f: Decimal, n: int, cfg: Cfg, c_: TradeCtx) -> TradePath:
    """§V3.1 exits. X-T0: no stop, exit at the open of bar e + XT_H. X-T: HARD_SL intrabar (gap -> open);
    runner once a bar CLOSE - F >= XT_RUNNER_ATR x OptATR5; then TRAIL = highest CLOSE - XT_TRAIL_ATR x OptATR5,
    CLOSE <= TRAIL -> next open; no runner by bar e + XT_H -> next open. PEAK = highest CLOSE (FIX-9).
    Clock (15:10 / 13:30), shock and stale rules as §6.4. Intrabar mode has no effect (only HARD_SL is intrabar)."""
    o, h, lo, c = (d.opt[x][k].tolist() for x in ("o", "h", "l", "c"))
    st = d.stale[k].tolist()
    rng = [h[j] - lo[j] for j in range(N)]
    ff = float(f)
    atr_e = opt_atr5(rng, st, e - 1)
    xt = str(cfg["EXIT_MODE"]) == "X-T"
    hard = max(ff - sl_points(cfg, atr_e), ff * (1 - float(FIX["SL_MAX_PCT"]))) if xt else -math.inf
    hz = int(cfg["XT_H"])
    run_k, trail_k = float(FIX["XT_RUNNER_ATR"]), float(FIX["XT_TRAIL_ATR"])
    clock_bar = M_EXP if d.dte == 0 else M_FF
    clock_why = "EXPIRY_1330" if d.dte == 0 else "FORCE_FLAT_1510"
    peak, peak_bar, mae, runner = -math.inf, e, 0.0, False
    pending: str | None = None
    stale_run, last_ns = 0, e

    def done(bar: int, level: float, reason: str, stale: bool) -> TradePath:
        return TradePath(
            k, e, f, n, d.lot, hard, math.nan, math.nan, bar, level, reason, stale, peak, peak_bar,
            2 if runner else 0, peak - ff, mae, math.nan, c_.entry_level,
        )  # fmt: skip

    for b in range(e, N):
        ns = not st[b]
        if pending is None and b >= clock_bar:
            pending = clock_why
        if pending is None and not runner and b >= e + hz:
            pending = "TIME_H"
        if pending is not None:
            if ns:
                return done(b, o[b], pending, False)
            if pending in (clock_why, "SHOCK", "ILLIQUID_EXIT"):
                return done(b, min(lo[last_ns], c[last_ns]), pending, True)
        if not ns:
            stale_run += 1
            if stale_run >= int(FIX["STALE_EXIT_BARS"]) and pending is None:
                pending = "ILLIQUID_EXIT"
            if c_.shock[b] and pending is None:
                pending = "SHOCK"
            continue
        stale_run = 0
        if b > e or math.isnan(c_.entry_level):
            if o[b] <= hard:
                return done(b, o[b], "GAP_SL", False)
            if lo[b] <= hard:
                return done(b, hard, "HARD_SL", False)
        mae = min(mae, lo[b] - ff)
        if c[b] > peak:
            peak, peak_bar = c[b], b
        atr = opt_atr5(rng, st, b)
        if xt and not runner and c[b] - ff >= run_k * atr:
            runner = True
        if runner and c[b] <= peak - trail_k * atr and pending is None:
            pending = "TRAIL_RUNNER"
        if c_.shock[b] and pending is None:
            pending = "SHOCK"
        last_ns = b
    raise AssertionError(f"{d.day} trade open after the last bar")


def _near_level(d: Day, sig: Sig, b: int, side: str, near: float) -> bool:
    """N14: spot within LEVEL_NEAR_ATR x ATR10 of the next resistance (CE) / support (PE)."""
    from lab.s3.checks import next_level  # noqa: PLC0415

    atr = sig.f["atr10"][b]
    return bool(atr > 0 and next_level(d, sig.f, b, side) <= near * atr)


def sl_points(cfg: Cfg, atr_e: float) -> float:
    if cfg["EXIT_MODE"] == "X-T":
        lo_c, hi_c = (float(x) for x in FIX["XT_SL_CLAMP"])
        return clamp(float(cfg["SL_K"]) * atr_e, lo_c, hi_c)
    if cfg.flag("FLAG_N2"):
        lo_c, hi_c = (float(x) for x in FIX["N2_CLAMP"])
        return clamp(float(cfg["N2_K"]) * atr_e, lo_c, hi_c)
    return float(cfg["SL_INIT_PTS"])


def fills(d: Day, p: TradePath, px: Px) -> tuple[Decimal, Decimal]:
    """Entry and exit fill of a path under one cost series (§6.1, §6.5; stale exit: spread and slip x 2)."""
    lvl = d.opt["o"][p.k, p.e] if math.isnan(p.entry_level) else p.entry_level
    fe = costs.buy_fill(dec(lvl), px.hs, px.slip)
    m = Decimal(str(FIX["STALE_SPREAD_MULT"])) if p.stale_forced else Decimal(1)
    fx = costs.sell_fill(dec(p.exit_level), px.hs * m, px.slip * m)
    return fe, fx


def path_net(d: Day, p: TradePath, px: Px) -> tuple[Decimal, dict[str, Decimal], Decimal, Decimal]:
    """Net of a path (N3 runner: the booked lot is a separate sell order with its own brokerage + GST).
    Returns (net, charges, entry fill, qty-weighted exit fill)."""
    fe, fx = fills(d, p, px)
    q = p.n * p.lot
    if p.book_lots:
        qb = p.book_lots * p.lot
        fb = costs.sell_fill(dec(p.book_level), px.hs, px.slip)
        ch = costs.charges([(fe, q, "BUY"), (fb, qb, "SELL"), (fx, q - qb, "SELL")], d.day)
        gross = fb * qb + fx * (q - qb) - fe * q
        return gross - ch["total"], ch, fe, (fb * qb + fx * (q - qb)) / q
    ch = costs.round_trip(fe, fx, q, d.day)
    return (fx - fe) * q - ch["total"], ch, fe, fx


def proxy_px(d: Day, k: int, bar: int) -> Px:
    v = d.opt["hs_proxy"][k, bar]
    return Px(dec(v), BASE.slip) if v > 0 else BASE


@dataclass
class DayState:
    net: Decimal = Decimal(0)
    peak: Decimal = Decimal(0)
    trades: int = 0
    losses_in_row: int = 0
    stopped: bool = False
    locked: bool = False
    free_at: int = 0
    cool_until: int = 0

    def floor(self) -> Decimal | None:
        trig = Decimal(str(FIX["PROFIT_LOCK_TRIG"])) * Decimal(FIX["CAPITAL_RS"])
        return Decimal(str(FIX["PROFIT_LOCK_KEEP"])) * self.peak if self.peak >= trig else None


def shock_state(d: Day) -> tuple[np.ndarray[Any, np.dtype[np.bool_]], np.ndarray[Any, np.dtype[np.bool_]]]:
    """§7.9: trigger = spot 5-min move > 1% and VIX 5-min jump > 8%; block until VIX 5% below its peak for 10 min."""
    s, v = d.base["spot_c"], d.base["vix_c"]
    nb = int(FIX["SHOCK_BARS"])
    trig = np.zeros(N, dtype=bool)
    blocked = np.zeros(N, dtype=bool)
    on, pk, calm = False, 0.0, 0
    for t in range(N):
        if t >= nb and s[t - nb] > 0 and v[t - nb] > 0:
            trig[t] = bool(
                abs(s[t] / s[t - nb] - 1) > float(FIX["SHOCK_MOVE"]) and v[t] / v[t - nb] - 1 > float(FIX["SHOCK_VIX"])
            )
        if trig[t]:
            on, pk, calm = True, float(v[t]), 0
        elif on:
            pk = max(pk, float(v[t])) if not math.isnan(v[t]) else pk
            calm = calm + 1 if v[t] <= (1 - float(FIX["SHOCK_CLEAR_DROP"])) * pk else 0
            if calm >= int(FIX["SHOCK_CLEAR_MIN"]):
                on = False
        blocked[t] = on
    return trig, blocked


@dataclass
class Event:
    t: int
    side: str
    pattern: str  # P1 / P2 / P3 / REENTRY / RANDOM / FLIP
    k: int = -1  # fixed strike (re-entry)
    peak: float = math.nan  # re-entry: PEAK of the closed trade
    step: float = math.nan


@dataclass
class DayResult:
    trades: list[dict[str, Any]] = field(default_factory=list)
    signals: list[dict[str, Any]] = field(default_factory=list)


def pattern_of(sig: Sig, t: int, side: str) -> str:
    p1 = sig.p1_ce[t] if side == "CE" else sig.p1_pe[t]
    return "P1" if p1 else "P2"


def regular_events(sig: Sig) -> list[Event]:
    out = []
    ce, pe = sig.ce, sig.pe
    for t in np.flatnonzero(ce | pe):
        ti = int(t)
        if ce[ti] and pe[ti]:
            out.append(Event(ti, "BOTH", "-"))
        else:
            side = "CE" if ce[ti] else "PE"
            out.append(Event(ti, side, pattern_of(sig, ti, side)))
    return out


Provider = Callable[[int, DayState], Event | None]


def run_day(
    d: Day,
    sig: Sig,
    cfg: Cfg,
    events: list[Event] | None = None,
    provider: Provider | None = None,
    run: Mode = BARCLOSE,
    record: bool = True,
    max_entries: int | None = None,
) -> DayResult:
    """The day loop (§7.2-§7.9). `events` (time-ordered) or an adaptive `provider` feed candidate entries."""
    px = run.px
    res = DayResult()
    win = windows(cfg, d.dte)
    trig, blocked = shock_state(d)
    st = DayState()
    queue = list(events if events is not None else ([] if provider else regular_events(sig)))
    if events is None and provider is None and cfg.flag("FLAG_P3"):
        queue = _with_p3(d, sig, cfg, queue)
    reentry: Event | None = None
    taken = 0
    cool = int(cfg["LOSS_COOLDOWN_MIN"])
    while True:
        if reentry is not None and (provider is not None or not queue or reentry.t <= queue[0].t):
            ev, reentry = reentry, None
        elif provider is not None:
            if max_entries is not None and taken >= max_entries:
                break
            nxt = provider(st.free_at, st)
            if nxt is None:
                break
            ev = nxt
        elif queue:
            ev = queue.pop(0)
        else:
            break
        t = ev.t
        why, ent = _entry(d, sig, cfg, ev, st, run, (win, blocked, trig))
        row: dict[str, Any] = {"date": d.day.isoformat(), "t": t, "side": ev.side, "pattern": ev.pattern}
        row["k"] = ent.k if ent is not None else -1
        if why is not None or ent is None:
            if record:
                res.signals.append(row | {"decision": why})
            continue
        k, how, f, n, lots_reason = ent.k, ent.how, ent.f, ent.n, ent.lots_reason
        p = simulate(d, k, ent.e, f, n, cfg, ent.ctx, run)
        nb = path_net(d, p, px)[0]
        taken += ev.pattern != "REENTRY"
        st.trades += 1
        st.net += nb
        st.peak = max(st.peak, st.net)
        st.free_at = p.exit_bar
        if nb < 0:
            st.losses_in_row += 1
            st.cool_until = p.exit_bar + cool
        else:
            st.losses_in_row = 0
        if st.losses_in_row >= int(FIX["CONSEC_LOSS_STOP"]):
            st.stopped = True
        fl = st.floor()
        if fl is not None and st.net <= fl:
            st.locked = True
        if record:
            res.signals.append(row | {"decision": "TAKEN"})
        res.trades.append({"path": p, "event": ev, "lots_reason": lots_reason, "net_base": nb, "how": how, "t": t})
        if p.exit_reason == "SL_G1_LOCK" and ev.pattern != "REENTRY" and cfg.flag("FLAG_REENTRY"):
            reentry = _reentry(d, sig, cfg, win, p, ev.side)
    return res


def _reentry(d: Day, sig: Sig, cfg: Cfg, win: Any, p: TradePath, side: str) -> Event | None:
    """§7.7: within REENTRY_BARS after the lock exit, strike high >= PEAK + 1 and (a), (c) true -> entry next open."""
    a = sig.a_ce if side == "CE" else sig.a_pe
    for j in range(p.exit_bar + 1, min(p.exit_bar + 1 + int(FIX["REENTRY_BARS"]), N - 1)):
        if d.stale[p.k, j] or not win[j]:
            continue
        if d.opt["h"][p.k, j] >= p.peak + float(FIX["REENTRY_ABOVE_PEAK"]) and a[j] and sig.c_ok[j]:
            return Event(j, side, "REENTRY", k=p.k, peak=p.peak, step=p.step_at_exit)
    return None


def _skip_reason(d: Day, cfg: Cfg, win: Any, blocked: Any, st: DayState, ev: Event) -> str | None:
    t = ev.t
    if not win[t]:
        return "EXPIRY_AFTER_1259" if d.dte == 0 and t > M_EXP_LAST else "WINDOW"
    if ev.side == "BOTH":
        return "CALL_PUT_TAKRAAV"
    if t < st.free_at:
        return "IN_TRADE"
    if st.stopped:
        return "DAY_STOP_2LOSS"
    if st.locked:
        return "PROFIT_FLOOR"
    if st.trades >= int(cfg["MAX_TRADES_DAY"]):
        return "MAX_TRADES"
    if blocked[t]:
        return "SHOCK"
    if t + 1 < st.cool_until:
        return "COOLDOWN"
    if cfg.slots_off and half_hour(t + 1) in cfg.slots_off:
        return "SLOT_OFF_N9"
    return None


def half_hour(m: int) -> str:
    """Half-hour slot of minute m (e.g. 10:30 for 10:30-10:59)."""
    hm = hhmm(m)
    return f"{hm[:3]}{'00' if int(hm[3:]) < minute('09:45') - minute('09:15') else '30'}"


@dataclass
class Entry:
    k: int
    how: str
    e: int
    f: Decimal
    n: int
    lots_reason: str
    ctx: TradeCtx


GATE_LABEL = {
    "K01": "GATE_MAUSAM_K01", "K02": "GAP_WAIT_K02", "K04": "GATE_IV_K04", "K06": "GATE_STRIKEVOL_K06",
    "K07": "GATE_FAKESPIKE_K07", "K08": "GATE_CHASE_K08", "K09": "GATE_WICK_K09", "K10": "GATE_PREMTEZI_K10",
    "K11": "GATE_VOLUCHHAL_K11", "K12": "GATE_TRAP_K12", "K13": "GATE_RANGEBO_K13", "K14": "GATE_TFMATCH_K14",
    "K16": "GATE_RSI_K16", "K17": "GATE_OISC_K17", "K18": "GATE_PCR_K18", "K19": "GATE_BREADTH_K19",
    "K20": "GATE_VIX_K20", "K21": "GATE_KHARCHA_K21", "K29": "GATE_LEVELBREAK_K29",
}  # fmt: skip
LEVEL_FILTERS = (("FLAG_K25", "K25", "STRETCH"), ("FLAG_K26", "K26", "NO_ROOM"), ("FLAG_K27", "K27", "CHOP"),
                 ("FLAG_K28", "K28", "DEAD"))  # fmt: skip


def _needs_checks(cfg: Cfg) -> bool:
    return bool(cfg.checks) or cfg["LOT_MODE"] != "L1" or any(cfg.flag(f) for f, _, _ in LEVEL_FILTERS)


def _entry(
    d: Day, sig: Sig, cfg: Cfg, ev: Event, st: DayState, run: Mode, day_arr: tuple[Any, Any, Any]
) -> tuple[str | None, Entry | None]:
    """All entry checks of §6.1 / §7.4 / §7.5 / §7.7 (+ module filters and lot modes) for one event."""
    win, blocked, trig = day_arr
    px, t = run.px, ev.t
    why = _skip_reason(d, cfg, win, blocked, st, ev)
    if why is not None:
        return why, None
    if ev.pattern == "REENTRY":
        k, how = ev.k, "SAME"
    else:
        k, how = pick_strike(d, t, ev.side, cfg)
        if k < 0:
            return ("NO_DELTA_FLOOR_N6" if how == "N6_FAIL" else "NO_STRIKE_IN_BAND"), None
    e, level = t + 1, math.nan
    if "K12" in cfg.checks and ev.pattern == "P1":
        # R5 / R7 K12 (trap check): the bar after the breakout must not close back inside the level; entry one bar later
        if e >= N - 1 or not win[t + 1]:
            return "WINDOW", None
        lvl = sig.f["hi_l"][t] if ev.side == "CE" else sig.f["lo_l"][t]
        ref = d.base["fut_c" if cfg["SIGNAL_SRC"] == "FUT" else "spot_c"][t + 1]
        if (ref <= lvl) if ev.side == "CE" else (ref >= lvl):
            return GATE_LABEL["K12"], None
        e = t + 2
    if d.stale[k, e]:
        return "NO_FILL_STALE", None
    eng = str(cfg["ENTRY_ENGINE"]) if ev.pattern != "REENTRY" else "INSTANT"
    if eng != "INSTANT":
        e, level = _engine_entry(d, k, t, eng)
        if e < 0:
            return f"NO_{eng}_TRIGGER", None
        if not win[e - 1]:
            return "WINDOW", None
    f = costs.buy_fill(dec(d.opt["o"][k, e] if math.isnan(level) else level), px.hs, px.slip)
    if ev.pattern == "REENTRY" and float(d.opt["o"][k, e]) > ev.peak + float(FIX["REENTRY_ABOVE_PEAK"]) + ev.step:
        return "REENTRY_CHASE", None
    if how == "BAND" and not cfg.var("strike_itm1") and f > Decimal(FIX["PREMIUM_MAX"]):
        return "NO_FILL_BAND", None
    sl_pts = sl_points(cfg, opt_atr5((d.opt["h"][k] - d.opt["l"][k]).tolist(), d.stale[k].tolist(), t))
    sl_eff = min(sl_pts, float(f) * float(FIX["SL_MAX_PCT"]))
    ck: dict[str, Any] = {}
    if _needs_checks(cfg):
        from lab.s3.checks import shadow  # noqa: PLC0415

        ck = shadow(d, sig, t, ev.side, k, sl_eff, ev.pattern, cfg)
    n0, why = _lot_mode(d, cfg, ck, f, sl_eff, run)
    if why is not None:
        return why, None
    n, lots_reason = size_at_fill(f, d.lot, d.day, dec(sl_eff), (st.net, st.floor()), cfg, n0, px)
    if n == 0:
        return lots_reason, None
    risk_sized = str(cfg["LOT_MODE"]).startswith("RISK") or cfg["EXIT_MODE"] == "X-T"
    if lots_reason == "MODE" and risk_sized and n0 < int(FIX["S3_MAX_LOTS"]):
        lots_reason = "RISK"
    if k03_on(cfg) and k03_ok(d) is False:
        return "GATE_IVP", None
    if cfg.var("gate_k05") and k05_ok(d, t, ev.side, k, sl_eff) is False:
        return "GATE_OI_WALL", None
    for flag, cid, label in LEVEL_FILTERS:
        if cfg.flag(flag) and ck.get(cid) == "RED":
            return label, None
    for cid in cfg.checks:
        if cid != "K12" and ck.get(cid) == "RED":
            return GATE_LABEL[cid], None
    struct, ref = _structure(d, sig, cfg, ev)
    return None, Entry(k, how, e, f, n, lots_reason, TradeCtx(trig, ev.side, struct, sig, level, ref))


def _lot_mode(d: Day, cfg: Cfg, ck: dict[str, Any], f: Decimal, sl_eff: float, run: Mode) -> tuple[int, str | None]:
    """§10.2 lot modes L1 / L2 / L3 / RISK / RISK+L2 and the cuts (K01 MIXED day, equity 5% below peak)."""
    mode, top = str(cfg["LOT_MODE"]), int(FIX["S3_MAX_LOTS"])
    if cfg["EXIT_MODE"] == "X-T":
        r, why = risk_lots(f, d.lot, dec(sl_eff), Decimal(str(cfg["RISK_PER_TRADE_RS"])), d.day)
        return (r, None) if r > 0 else (0, "SKIP_RISK")
    if mode == "L1":
        return top, None
    sc = int(ck.get("score", 0))
    l2 = top if sc >= int(SCORE["L2_HIGH"]) else top - 1 if sc >= int(SCORE["L2_MID"]) else 1
    if mode == "L3" and not ck.get("score_pass"):
        return 0, "GATE_SCORE_L3"
    n = l2
    if mode.startswith("RISK"):
        r, why = risk_lots(f, d.lot, dec(sl_eff), Decimal(str(cfg["RISK_PER_TRADE_RS"])), d.day)
        if r == 0:
            return 0, why
        n = r if mode == "RISK" else min(r, l2)
    adx = ck.get("K01_adx", math.nan)
    mixed = not math.isnan(adx) and CHK["K01_ADX_RED"] < adx < CHK["K01_ADX_GREEN"]
    for cut in (mixed, run.dd_cut):
        if cut:
            n = max(1, int(n * float(FIX["DD_CUT_FACTOR"])))
    return n, None


def _engine_entry(d: Day, k: int, t: int, eng: str) -> tuple[int, float]:
    """N4 entry engines. STEP: within STEP_BARS a high >= open(t+1) + STEP_PTS -> buy at that level.
    TRAIL_BUY: for TRAIL_BARS track the low; buy at low + TRAIL_REV when reached, or at open + FOMO_PTS."""
    o1 = float(d.opt["o"][k, t + 1])
    h, lo, stl = d.opt["h"][k], d.opt["l"][k], d.stale[k]
    if eng == "STEP":
        lvl = o1 + float(FIX["STEP_PTS"])
        for j in range(t + 1, min(N, t + 1 + int(FIX["STEP_BARS"]))):
            if not stl[j] and h[j] >= lvl:
                return j, lvl
        return -1, math.nan
    low = math.inf
    for j in range(t + 1, min(N, t + 1 + int(FIX["TRAIL_BARS"]))):
        if stl[j]:
            continue
        if h[j] >= o1 + float(FIX["FOMO_PTS"]):
            return j, o1 + float(FIX["FOMO_PTS"])
        low = min(low, float(lo[j]))
        if h[j] >= low + float(FIX["TRAIL_REV"]):
            return j, low + float(FIX["TRAIL_REV"])
    return -1, math.nan


def _structure(d: Day, sig: Sig, cfg: Cfg, ev: Event) -> tuple[float, str]:
    """N7 structure level (P1 breakout level, P2 pullback low, P3 trap high), offset by N7_OFFSET_ATR x ATR10."""
    if not (cfg.flag("FLAG_N7") or ev.pattern == "P3") or ev.pattern not in ("P1", "P2", "P3"):
        return math.nan, "spot_c"
    fut = cfg["SIGNAL_SRC"] == "FUT"
    pre, ref = ("fut", "fut_c") if fut else ("spot", "spot_c")
    t, up = ev.t, ev.side == "CE"
    atr = sig.f["fatr10" if fut else "atr10"][t]
    off = float(FIX["N7_OFFSET_ATR"]) * atr
    hi, lo = d.base[f"{pre}_h"], d.base[f"{pre}_l"]
    w = slice(t - int(FIX["P2_MAX_BARS"]), t)
    if ev.pattern == "P1":
        lvl = sig.f["hi_l"][t] - off if up else sig.f["lo_l"][t] + off
    elif ev.pattern == "P2":
        lvl = float(np.min(lo[w])) - off if up else float(np.max(hi[w])) + off
    else:
        w3 = slice(t - int(FIX["TRAP_BARS"]), t + 1)
        lvl = float(np.min(lo[w3])) - off if up else float(np.max(hi[w3])) + off
    return lvl, ref


def _with_p3(d: Day, sig: Sig, cfg: Cfg, queue: list[Event]) -> list[Event]:
    """R6: add P3 trap-reversal events (P3_MODE ALL / CHOP: only when K27 is RED at that bar / PM: from 13:15)."""
    from lab.s3.p3 import p3  # noqa: PLC0415

    pe3, ce3 = p3(d, sig, float(cfg["FUT_VOL_MULT"]), {"HDFCBANK": sig.f["r_hdfc"], "ICICIBANK": sig.f["r_icici"]})
    mode = str(cfg["P3_MODE"])
    have = {e.t: e for e in queue}
    nb = int(CHK["K27_BARS"])
    above = (d.base["fut_c"] > sig.f["vwap"]).astype(int)
    for t in np.flatnonzero(pe3 | ce3):
        ti = int(t)
        side = "PE" if pe3[ti] else "CE"
        if mode == "PM" and ti < minute(str(cfg["AFTERNOON_START"])):
            continue
        if mode == "CHOP":
            if ti + 1 <= minute(str(FIX["K27_START"])) or ti < nb:
                continue
            if int(np.sum(np.abs(np.diff(above[ti - nb : ti + 1])))) < float(cfg["CHOP_CROSSES"]):
                continue
        if ti in have:
            if have[ti].side not in (side, "BOTH"):
                have[ti] = Event(ti, "BOTH", "-")
            continue
        have[ti] = Event(ti, side, "P3")
    return [have[x] for x in sorted(have)]
