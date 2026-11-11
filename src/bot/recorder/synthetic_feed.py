"""Synthetic LIGHT-scope feed (MISSION V11 §10): machinery tests only, never evidence of an edge (tag SIM).

LIGHT scope: NIFTY, BANKNIFTY and SENSEX spot + near future + ATM ± 5 strikes CE and PE = 72 instruments,
one normalised message per instrument per minute, 09:15-15:30 IST, deterministic for a seed.
"""

from __future__ import annotations

import datetime as dt
import random
from collections.abc import Iterator
from typing import Any

from bot.recorder.snapshot import NS, SESSION_MINUTES

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")


def light_keys() -> list[str]:
    keys = []
    for idx in INDEXES:
        keys += [f"{idx}|SPOT", f"{idx}|FUT"]
        keys += [f"{idx}|ATM{k:+d}|{t}" for k in range(-5, 6) for t in ("CE", "PE")]
    return keys


def session_open_ns(day: dt.date) -> int:
    return int(dt.datetime(day.year, day.month, day.day, 9, 15, tzinfo=IST).timestamp()) * NS


def synthetic_day(
    day: dt.date,
    seed: int,
    keys: list[str],
    *,
    skip_minutes: frozenset[int] = frozenset(),
    extra: dict[int, dict[str, Any]] | None = None,
) -> Iterator[tuple[int, dict[str, Any]]]:
    """(local_ns, message) in time order. `skip_minutes` drops whole minutes (a feed gap); `extra` merges
    fields into the message with that running index (to inject unknown fields or bad values)."""
    rng = random.Random(seed)  # noqa: S311 (simulation, not security)
    price = {k: 20_000 + 500 * i for i, k in enumerate(keys)}
    start = session_open_ns(day)
    n = 0
    for m in range(SESSION_MINUTES):
        if m in skip_minutes:
            continue
        for k in keys:
            price[k] = max(5, price[k] + rng.randint(-40, 40))
            exch = start + m * 60 * NS + rng.randrange(1, 59) * NS
            msg: dict[str, Any] = {
                "key": k,
                "exch_ts_ns": exch,
                "ltp_paise": price[k],
                "bid_paise": price[k] - 5,
                "ask_paise": price[k] + 5,
                "vol": rng.randint(0, 5_000),
                "oi": rng.randint(0, 100_000),
                "iv_bp": rng.randint(900, 2_500),
                "iv_src": "computed",
            }
            if extra and n in extra:
                msg.update(extra[n])
            n += 1
            yield exch + 50_000_000, msg
