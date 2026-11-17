"""Index contracts ki jaankari (dekha 11 Nov 2026, sources strategy/STRATEGY_v2.md mein).

- Nifty 50: lot 65, weekly expiry Tuesday (1 Sep 2025 se), monthly = mahine ka aakhri Tuesday.
- Sensex: lot 20, weekly expiry Thursday, monthly = aakhri Thursday.
- Bank Nifty: lot 30, weekly NOV 2024 SE BAND; sirf monthly (aakhri Tuesday).
Chhutti par expiry pichhle kaam ke din chali jaati hai: woh list abhi nahi jaanchi (verify nahi hua),
isliye `is_expiry_day` chhutti nahi samajhta. Bot ko roz subah broker ki instrument list se pakka karna hai.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final


@dataclass(frozen=True, slots=True)
class IndexSpec:
    name: str
    label: str
    exchange: str
    lot_crosscheck: int  # NEVER used for sizing: only a test cross-checks the instrument file (S6)
    strike_step: int
    expiry_weekday: int  # 0 = Somvaar ... 3 = Guruvaar
    weekly: bool
    tradable: bool  # False = sirf signal/breadth ke liye (jaise Bank Nifty: ₹15k mein lot nahi aata)


SPECS: Final[dict[str, IndexSpec]] = {
    "Nifty50": IndexSpec("Nifty50", "Nifty 50", "NSE", 65, 50, 1, True, True),
    "Sensex": IndexSpec("Sensex", "Sensex", "BSE", 20, 100, 3, True, True),
    "BankNifty": IndexSpec("BankNifty", "Bank Nifty", "NSE", 30, 100, 1, False, False),
}


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    last = date(year, month, calendar.monthrange(year, month)[1])
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def next_expiry(name: str, today: date) -> date:
    """Aaj ya aage ki pehli expiry (chhutti ka shift nahi samajhta)."""
    s = SPECS[name]
    if s.weekly:
        return today + timedelta(days=(s.expiry_weekday - today.weekday()) % 7)
    exp = _last_weekday_of_month(today.year, today.month, s.expiry_weekday)
    if exp < today:
        y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        exp = _last_weekday_of_month(y, m, s.expiry_weekday)
    return exp


def is_expiry_day(name: str, today: date) -> bool:
    return next_expiry(name, today) == today


def days_to_expiry(name: str, today: date) -> int:
    return (next_expiry(name, today) - today).days


def expiry_rules_apply(name: str, today: date, known_expiries: frozenset[date] | None = None) -> bool:
    """Expiry-din ke sakht niyam aaj lagu hon ya nahi.

    `known_expiries` broker ki instrument list se (pakka). Na mile toh SURAKSHIT andaza: ganit wali expiry
    ka din AUR uska pichla kaam ka din bhi (chhutti par expiry ek din pehle khisakti hai; verify nahi hua).
    """
    if known_expiries is not None:
        return today in known_expiries
    exp = next_expiry(name, today)
    if exp == today:
        return True
    prev = exp - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev == today
