"""Entry/exit ke niyam (pure functions). Samay IST mein. Saare number `Params` mein, code mein nahi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time


@dataclass(frozen=True, slots=True)
class Params:
    entry_windows: tuple[tuple[time, time], ...] = ((time(9, 30), time(11, 30)), (time(13, 30), time(14, 45)))
    expiry_day_last_entry: time = time(13, 30)  # expiry din dopahar baad naya entry nahi (theta/gamma jua)
    hard_exit: time = time(15, 15)
    max_entries: int = 2
    max_losses_in_row: int = 2
    time_stop_min: int = 15  # itne minute mein chaal na aaye toh nikal jao (theta)
    time_stop_min_gain_pct: float = 5.0
    sl_pct: float = 25.0
    breakeven_at_r: float = 1.0  # +1R par SL entry par
    trail_giveback_pct: float = 35.0  # sabse uchi kamai ka itna % wapas jaaye toh exit
    vix_spike_pct: float = 8.0  # India VIX din mein itna uchhle toh naya entry nahi
    loss_cooldown_min: int = 20  # niyam Loss_Cooldown_Samay: nuksan ke baad 20 min koi entry nahi (badla-trade nahi)


@dataclass(slots=True)
class DayState:
    entries: int = 0
    losses_in_row: int = 0
    realised: float = 0.0
    daily_loss_limit: float = 0.0  # rupaye; 0 = tay nahi -> entry band
    halted: bool = False
    last_loss_minute: int | None = None
    notes: list[str] = field(default_factory=list)


def can_enter(
    now: time, day: DayState, p: Params, *, expiry_day: bool, vix_change_pct: float, open_position: bool
) -> tuple[bool, str]:
    if day.halted:
        return False, "aaj ke liye band (halt)"
    if day.daily_loss_limit <= 0:
        return False, "din ki nuksan seema tay nahi (Settings)"
    if open_position:
        return False, "pehle se ek position khula (sirf 1 lot ek samay)"
    if day.entries >= p.max_entries:
        return False, f"aaj {p.max_entries} entry ho chuki"
    if day.losses_in_row >= p.max_losses_in_row:
        return False, f"lagatar {p.max_losses_in_row} haar: aaj band"
    if -day.realised >= day.daily_loss_limit:
        return False, "din ki nuksan seema poori"
    if vix_change_pct >= p.vix_spike_pct:
        return False, f"India VIX {vix_change_pct:.1f}% uchhla: dar ka mahaul"
    minute = now.hour * 60 + now.minute
    if day.last_loss_minute is not None and minute - day.last_loss_minute < p.loss_cooldown_min:
        return False, f"nuksan ke baad {p.loss_cooldown_min} min ruko (cooldown)"
    if expiry_day and now >= p.expiry_day_last_entry:
        return False, "expiry din dopahar baad naya entry nahi"
    if not any(a <= now < b for a, b in p.entry_windows):
        return False, "entry ka samay nahi"
    return True, "theek"


@dataclass(slots=True)
class OpenTrade:
    entry_price: float
    entry_minute: int  # din ke minute (IST)
    best_price: float
    sl_price: float


def on_tick(t: OpenTrade, price: float, minute: int, now: time, p: Params, *, structure_broken: bool) -> str | None:
    """Exit ki wajah lautata hai (ya None). SL hamesha broker par bhi laga rehta hai (Broker Stop)."""
    t.best_price = max(t.best_price, price)
    risk = t.entry_price - t.entry_price * (1 - p.sl_pct / 100)
    if now >= p.hard_exit:
        return "samay khatam (hard exit)"
    if price <= t.sl_price:
        return "stop-loss"
    if structure_broken:
        return "chart ka dhaancha toota (underlying SL)"
    if t.best_price - t.entry_price >= p.breakeven_at_r * risk:
        t.sl_price = max(t.sl_price, t.entry_price)  # ab nuksan nahi
        gain = t.best_price - t.entry_price
        if price <= t.best_price - gain * p.trail_giveback_pct / 100:
            return "trailing exit (munafa bachaya)"
    if (
        minute - t.entry_minute >= p.time_stop_min
        and (t.best_price - t.entry_price) / t.entry_price * 100 < p.time_stop_min_gain_pct
    ):
        return f"{p.time_stop_min} min mein chaal nahi (theta se bachav)"
    return None


def after_exit(day: DayState, pnl: float, *, minute: int | None = None) -> None:
    if pnl < 0 and minute is not None:
        day.last_loss_minute = minute
    day.entries += 1
    day.realised += pnl
    day.losses_in_row = day.losses_in_row + 1 if pnl < 0 else 0
    if day.daily_loss_limit > 0 and -day.realised >= day.daily_loss_limit:
        day.halted = True
        day.notes.append("din ki nuksan seema: halt")


def risk_per_trade(
    capital: float, daily_loss_limit: float, *, daily_share_pct: float = 60.0, capital_pct: float = 6.0
) -> float:
    """Ek trade ki max risk (rupaye): din ki seema ka 60% aur capital ka 6%, jo kam ho.

    Seema tay nahi = 0 (entry band).
    """
    if capital <= 0 or daily_loss_limit <= 0:
        return 0.0
    return round(min(daily_loss_limit * daily_share_pct / 100, capital * capital_pct / 100), 2)


def account_allows_trading(start_capital: float, equity: float, kul_jeb_limit: float) -> tuple[bool, str]:
    """Kul jeb seema ka taala (malik ka last-chance paisa bachane ke liye).

    Shuru ke capital se kul nuksan `kul_jeb_limit` tak pahunche toh bot HAMESHA ke liye band.
    Yeh din badalne par apne-aap nahi khulta; sirf malik khud seema badal kar khol sakta hai.
    Seema tay nahi (0) = koi trade nahi.
    """
    if kul_jeb_limit <= 0:
        return False, "Kul jeb nuksan seema tay nahi (website Settings): trade band"
    if kul_jeb_limit >= start_capital:
        return False, "Kul jeb seema poore capital ke barabar ya zyada: yeh taala nahi, galat seema"
    lost = start_capital - equity
    if lost >= kul_jeb_limit:
        return False, f"Kul nuksan ₹{lost:,.0f} seema ₹{kul_jeb_limit:,.0f} tak pahuncha: bot hamesha ke liye band"
    return True, f"₹{kul_jeb_limit - lost:,.0f} aur nuksan ki gunjaish"
