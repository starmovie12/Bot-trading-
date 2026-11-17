"""Read-only loader of the owner's data repo (MISSION V19 Phase 1): BANKNIFTY only, per day and per table.

Layout: <repo>/week_*/store/{dev|holdout}/<table>/underlying=<U>/trading_date=<D>/part-*.parquet.
Times are IST candle STARTS (`ts_open`); a bar is known one minute later (`known_at`). Options = opt_1m + opt_wide_1m.
"""

import datetime as dt
import functools
import re
from collections import defaultdict
from functools import cache
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

UNDERLYING = "BANKNIFTY"
VIX = "INDIAVIX"
BANK_STOCKS: tuple[str, ...] = (
    "AUBANK",
    "AXISBANK",
    "BANKBARODA",
    "CANBK",
    "FEDERALBNK",
    "HDFCBANK",
    "ICICIBANK",
    "IDFCFIRSTB",
)
BANK_STOCKS += ("INDUSINDBK", "KOTAKBANK", "PNB", "SBIN")
OPTION_TABLES = ("opt_1m", "opt_wide_1m")
PART = re.compile(r"store/[^/]+/(?P<table>[^/]+)/underlying=(?P<u>[^/]+)/trading_date=(?P<d>\d{4}-\d{2}-\d{2})/")
KEY = ("instrument_key", "ts_open")
BAR = dt.timedelta(minutes=1)


class DataConflict(ValueError):
    """Two different rows for one (instrument_key, ts_open): never silently merged."""


@cache
def partitions(root: Path) -> dict[tuple[str, str, dt.date], tuple[Path, ...]]:
    """(table, underlying, day) -> part files over every week folder (folders ordered by their dates, never by NN)."""
    out: dict[tuple[str, str, dt.date], list[Path]] = defaultdict(list)
    for f in sorted(root.glob("week_*/store/*/*/underlying=*/trading_date=*/*.parquet")):
        m = PART.search(f.as_posix())
        if m:
            out[(m["table"], m["u"], dt.date.fromisoformat(m["d"]))].append(f)
    return {k: tuple(v) for k, v in out.items()}


def days(root: Path, table: str, underlying: str = UNDERLYING) -> list[dt.date]:
    return sorted(d for (t, u, d) in partitions(root) if t == table and u == underlying)


def dedupe(tb: pa.Table) -> pa.Table:
    """Keep one row per (instrument_key, ts_open); raise DataConflict when two rows for one key differ."""
    if tb.num_rows == 0:
        return tb
    tb = tb.sort_by([(k, "ascending") for k in KEY])
    same_key = pc.and_(
        pc.equal(tb["instrument_key"][1:], tb["instrument_key"][:-1]), pc.equal(tb["ts_open"][1:], tb["ts_open"][:-1])
    )
    if not pc.any(same_key).as_py():
        return tb
    cols = [c for c in ("o", "h", "l", "c", "v", "oi") if c in tb.column_names]
    differs = functools.reduce(pc.or_, [_differs(tb[c][1:], tb[c][:-1]) for c in cols])
    if pc.any(pc.and_(same_key, differs)).as_py():
        raise DataConflict("two different rows for one (instrument_key, ts_open)")
    keep = pa.chunked_array([pa.array([True]), *pc.invert(same_key).chunks])
    return tb.filter(keep)


def _differs(a: pa.Array, b: pa.Array) -> pa.Array:
    """True where two values differ; null equals null."""
    return pc.or_(pc.fill_null(pc.not_equal(a, b), False), pc.xor(pc.is_null(a), pc.is_null(b)))


def read_day(
    root: Path, table: str, day: dt.date, underlying: str = UNDERLYING, columns: list[str] | None = None
) -> pa.Table:
    """One table, one day, de-duplicated; rows of any other underlying are never read (R1)."""
    tables = [
        pq.read_table(f, columns=columns)
        for t in _tables(table)
        for f in partitions(root).get((t, underlying, day), ())
    ]
    if not tables:
        return pa.table({})
    tb = pa.concat_tables(tables, promote_options="permissive")
    if "underlying" in tb.column_names and pc.any(pc.not_equal(tb["underlying"], underlying)).as_py():
        tb = tb.filter(pc.equal(tb["underlying"], underlying))
    return dedupe(tb) if all(k in tb.column_names for k in KEY) else tb


def _tables(table: str) -> tuple[str, ...]:
    return OPTION_TABLES if table == "options" else (table,)


def known_at(tb: pa.Table) -> pa.Array:
    """The time a bar is known: its start plus one minute."""
    return pc.add(tb["ts_open"], pa.scalar(BAR, pa.duration("us")))


def visible(tb: pa.Table, now: dt.datetime) -> pa.Table:
    """Only bars already closed at `now` (no look-ahead); `now` must be tz-aware."""
    if now.tzinfo is None:
        raise ValueError("now must be tz-aware (IST)")
    return tb.filter(pc.less_equal(known_at(tb), pa.scalar(now, tb.schema.field("ts_open").type)))
