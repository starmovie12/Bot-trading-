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
from lab.s3.registry import FIX, RAW, Cfg, minute

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


def pick_strike(d: Day, t: int, side: str, cfg: Cfg) -> tuple[int, str]:
    """§7.4: premium band nearest PREMIUM_TARGET at signal-bar close; DTE 0: |Delta| band nearest the target.
    T1-RAW: nothing found -> ITM1. Returns (k, how) with k = -1 when nothing fits."""
    sel = (d.cp == side) & ~d.stale[:, t]
    if d.dte == 0:
        lo_d, hi_d = (float(x) for x in FIX["EXPIRY_DELTA"])
        dl = np.abs(d.opt["delta"][:, t])
        ok = sel & (dl >= lo_d) & (dl <= hi_d)
        if np.any(ok):
            idx = np.flatnonzero(ok)
            return int(idx[np.argmin(np.abs(dl[idx] - float(FIX["EXPIRY_DELTA_TARGET"])))]), "DELTA"
    else:
        px = d.opt["c"][:, t]
        ok = sel & (px >= float(FIX["PREMIUM_MIN"])) & (px <= float(FIX["PREMIUM_MAX"]))
        if np.any(ok):
            idx = np.flatnonzero(ok)
            dist = np.abs(px[idx] - float(FIX["PREMIUM_TARGET"]))
            spot = d.base["spot_c"][t]
            order = np.lexsort((np.abs(d.strikes[idx] - spot), dist))
            return int(idx[order[0]]), "BAND"
    if cfg.var("strike_itm1"):
        step = strike_step(d, t)
        k = d.k(atm(d, t) + (-step if side == "CE" else step), side)
        if k >= 0 and not d.stale[k, t]:
            return k, "ITM1"
    return -1, "NONE"


# ---------- gates ----------


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
    shock: np.ndarray[Any, np.dtype[np.bool_]],
    run: Mode = BARCLOSE,
) -> TradePath:
    """One trade from its entry bar e (fill F at e's open) to exit, per §6.2 / §6.4 / §7.6."""
    mode, px = run.intrabar, run.px
    o, h, lo, c = (d.opt[x][k].tolist() for x in ("o", "h", "l", "c"))
    st = d.stale[k].tolist()
    rng = [h[j] - lo[j] for j in range(N)]
    lot = d.lot
    qty = n * lot
    ff = float(f)
    bep = float(be_pts(f, qty, d.day, px))
    atr_e = opt_atr5(rng, st, e - 1)
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
    sl = max(ff - sl_pts, ff * (1 - float(FIX["SL_MAX_PCT"])))
    why = "SL_G0"
    tgt = ff + float(FIX["TARGET_XB_PTS"]) if cfg["EXIT_MODE"] == "X-B" else math.inf
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

    def lift(
        sl: float, why: str, gear: int, pk: float, step: float, close_o: tuple[float, float] | None
    ) -> tuple[float, str, int]:
        cands: list[tuple[float, str]] = []
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
        return TradePath(
            k,
            e,
            f,
            n,
            lot,
            sl0,
            be_level,
            g1,
            bar,
            level,
            reason,
            stale,
            peak,
            peak_bar,
            max_gear,
            peak - ff,
            mae,
            step,
        )

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
        if o[b] <= sl:
            return done(b, o[b], "GAP_SL", False)
        green = c[b] > o[b]
        if (mode == "BARCLOSE" or (mode == "PATH" and green)) and lo[b] <= sl:
            return done(b, sl, why, False)
        if mode == "BARCLOSE" and h[b] >= tgt:
            return done(b, tgt, "TARGET30", False)
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
        if h[b] > peak:
            peak, peak_bar = h[b], b
        step = clamp(smult * opt_atr5(rng, st, b), step_lo, step_hi)
        sl, why, gear = lift(sl, why, gear, peak, step, (c[b], o[b]))
        max_gear = max(max_gear, gear)
        if sl >= c[b] and pending is None:
            pending = why
        last_ns = b
    raise AssertionError(f"{d.day} trade open after the last bar")


def sl_points(cfg: Cfg, atr_e: float) -> float:
    if cfg.flag("FLAG_N2"):
        lo_c, hi_c = (float(x) for x in FIX["N2_CLAMP"])
        return clamp(float(cfg["N2_K"]) * atr_e, lo_c, hi_c)
    return float(cfg["SL_INIT_PTS"])


def fills(d: Day, p: TradePath, px: Px) -> tuple[Decimal, Decimal]:
    """Entry and exit fill of a path under one cost series (§6.1, §6.5; stale exit: spread and slip x 2)."""
    fe = costs.buy_fill(dec(d.opt["o"][p.k, p.e]), px.hs, px.slip)
    m = Decimal(str(FIX["STALE_SPREAD_MULT"])) if p.stale_forced else Decimal(1)
    fx = costs.sell_fill(dec(p.exit_level), px.hs * m, px.slip * m)
    return fe, fx


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
    reentry: Event | None = None
    taken = 0
    n_mode = int(FIX["S3_MAX_LOTS"])
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
        why = _skip_reason(d, cfg, win, blocked, st, ev, n_mode)
        k, how, f, n, lots_reason = -1, "", Decimal(0), 0, ""
        if why is None:
            if ev.pattern == "REENTRY":
                k, how = ev.k, "SAME"
            else:
                k, how = pick_strike(d, t, ev.side, cfg)
                if k < 0:
                    why = "NO_STRIKE_IN_BAND"
        if why is None:
            e = t + 1
            if d.stale[k, e]:
                why = "NO_FILL_STALE"
            else:
                f = costs.buy_fill(dec(d.opt["o"][k, e]), px.hs, px.slip)
                if (
                    ev.pattern == "REENTRY"
                    and float(d.opt["o"][k, e]) > ev.peak + float(FIX["REENTRY_ABOVE_PEAK"]) + ev.step
                ):
                    why = "REENTRY_CHASE"
                elif how == "BAND" and not cfg.var("strike_itm1") and f > Decimal(FIX["PREMIUM_MAX"]):
                    why = "NO_FILL_BAND"
        sl_pts = 0.0
        if why is None:
            sl_pts = sl_points(cfg, opt_atr5((d.opt["h"][k] - d.opt["l"][k]).tolist(), d.stale[k].tolist(), t))
            sl_eff = min(sl_pts, float(f) * float(FIX["SL_MAX_PCT"]))
            n, lots_reason = size_at_fill(f, d.lot, d.day, dec(sl_eff), (st.net, st.floor()), cfg, n_mode, px)
            if n == 0:
                why = lots_reason
        if why is None and cfg.var("gate_k03") and k03_ok(d) is False:
            why = "GATE_IVP"
        if (
            why is None
            and cfg.var("gate_k05")
            and k05_ok(d, t, ev.side, k, min(sl_pts, float(f) * float(FIX["SL_MAX_PCT"]))) is False
        ):
            why = "GATE_OI_WALL"
        row: dict[str, Any] = {"date": d.day.isoformat(), "t": t, "side": ev.side, "pattern": ev.pattern, "k": k}
        if why is not None:
            if record:
                res.signals.append(row | {"decision": why})
            continue
        p = simulate(d, k, t + 1, f, n, cfg, trig, run)
        nb = net(*fills(d, p, px), n * d.lot, d.day)
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


def _skip_reason(d: Day, cfg: Cfg, win: Any, blocked: Any, st: DayState, ev: Event, n_mode: int) -> str | None:
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
    return None
