"""Shared contracts (MISSION V19 C10, N3): frozen types of the lab, engine of record, gateway and paper broker.

A change = one commit `CONTRACT: <why>` + the full suite. BANKNIFTY index options only (R1); 1 lot per leg (R2).
"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

Side = Literal["BUY", "SELL"]
OptType = Literal["CE", "PE"]
UNDERLYING = "BANKNIFTY"


@dataclass(frozen=True)
class Bar:
    """One 1-minute candle; `ts` is the IST candle START (known one minute later)."""

    ts: dt.datetime
    o: float
    h: float
    l: float  # noqa: E741 (the conventional OHLC name)
    c: float
    v: float = 0.0
    stale: bool = False


@dataclass(frozen=True)
class Quote:
    ts: dt.datetime
    instrument_key: str
    bid: float
    ask: float
    ltp: float


@dataclass(frozen=True)
class Leg:
    strike: float
    expiry: dt.date
    opt_type: OptType
    side: Side
    lots: int = 1
    underlying: str = UNDERLYING


@dataclass(frozen=True)
class Intent:
    """One structure: 1 leg (long option) or 2 legs (same-expiry DEBIT spread: legs[0] BUY first, legs[1] SELL)."""

    intent_id: str
    legs: tuple[Leg, ...]
    stop_frac: float  # stop at entry value x (1 - stop_frac); R = stop_frac x entry value
    target_r: float
    scratch_min: int
    time_stop_min: int
    reason: str = ""

    def __post_init__(self) -> None:
        sides = tuple(x.side for x in self.legs) in (("BUY",), ("BUY", "SELL"))
        same = len({(x.expiry, x.opt_type) for x in self.legs}) == 1
        lots = all(x.lots == 1 and x.underlying == UNDERLYING for x in self.legs)
        if not (sides and same and lots):
            raise ValueError("1 BUY leg, or a same-expiry, same-type BUY + SELL debit spread; 1 BANKNIFTY lot each")


@dataclass(frozen=True)
class NoTrade:
    reason: str


@dataclass(frozen=True)
class Fill:
    intent_id: str
    leg: int
    ts: dt.datetime
    price: float
    side: Side


@dataclass(frozen=True)
class TradeRecord:
    intent_id: str
    day: dt.date
    legs: tuple[Leg, ...]
    entry_minute: int
    exit_minute: int
    entry_value: float
    exit_value: float
    lot: int
    gross_rs: Decimal
    charges_rs: Decimal
    fill_cost_stressed_rs: Decimal
    net_stressed_rs: Decimal
    exit_reason: str
    mae_rs: Decimal = Decimal(0)  # worst mark-to-market of the structure during the trade (gross, <= 0)


@dataclass(frozen=True)
class MarketState:
    """What a strategy may read at decision minute `minute` (minutes after 09:15): nothing after it."""

    day: dt.date
    minute: int
    expiry: dt.date
    vix_open: float
    vix_last: float


class Strategy(Protocol):
    def decide(self, state: MarketState, bars: tuple[Bar, ...]) -> Intent | NoTrade: ...


class CostModel(Protocol):
    def charges(self, prices: tuple[tuple[float, float], ...], lot: int, day: dt.date) -> Decimal: ...
    def fill_stressed(
        self, legs: int, lot: int, minutes: tuple[int, int], expiry_day: bool, stale: bool
    ) -> Decimal: ...
