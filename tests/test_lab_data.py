"""lab/data.py: per-day reads, option union, de-duplication, no look-ahead (MISSION V19 Phase 1)."""

import datetime as dt
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from lab import data

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
DAY = dt.date(2026, 11, 12)


def _bars(key: str, minutes: int, start: int = 0, underlying: str = "BANKNIFTY", close: float = 100.0) -> pa.Table:
    ts = [dt.datetime(2026, 11, 12, 9, 15, tzinfo=IST) + dt.timedelta(minutes=start + i) for i in range(minutes)]
    n = len(ts)
    return pa.table(
        {
            "instrument_key": [key] * n,
            "underlying": [underlying] * n,
            "ts_open": pa.array(ts, pa.timestamp("us", tz="+05:30")),
            "o": [close] * n,
            "h": [close] * n,
            "l": [close] * n,
            "c": [close] * n,
            "v": [10] * n,
            "oi": [5] * n,
        }
    )


def _write(root: Path, week: str, table: str, day: dt.date, tb: pa.Table, part: str = "part-0") -> None:
    d = root / week / "store" / "dev" / table / "underlying=BANKNIFTY" / f"trading_date={day}"
    d.mkdir(parents=True, exist_ok=True)
    pq.write_table(tb, d / f"{part}.parquet")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    data.partitions.cache_clear()
    _write(tmp_path, "week_02_2026-11-07_to_2026-11-13", "spot_1m", DAY, _bars("IDX", 3))
    _write(tmp_path, "week_03_2026-10-31_to_2026-11-06", "spot_1m", dt.date(2026, 11, 6), _bars("IDX", 3))
    _write(tmp_path, "week_02_2026-11-07_to_2026-11-13", "opt_1m", DAY, _bars("OPT-A", 2))
    _write(tmp_path, "week_02_2026-11-07_to_2026-11-13", "opt_wide_1m", DAY, _bars("OPT-W", 2))
    return tmp_path


def test_days_span_every_week_folder_in_date_order(repo: Path) -> None:
    assert data.days(repo, "spot_1m") == [dt.date(2026, 11, 6), DAY]


def test_options_are_the_union_of_both_option_tables(repo: Path) -> None:
    keys = set(data.read_day(repo, "options", DAY)["instrument_key"].to_pylist())
    assert keys == {"OPT-A", "OPT-W"}


def test_identical_duplicates_are_kept_once(repo: Path) -> None:
    _write(repo, "week_02_2026-11-07_to_2026-11-13", "spot_1m", DAY, _bars("IDX", 3), part="part-1")
    data.partitions.cache_clear()
    assert data.read_day(repo, "spot_1m", DAY).num_rows == 3


def test_two_different_rows_for_one_key_raise(repo: Path) -> None:
    _write(repo, "week_02_2026-11-07_to_2026-11-13", "spot_1m", DAY, _bars("IDX", 1, close=101.0), part="part-1")
    data.partitions.cache_clear()
    with pytest.raises(data.DataConflict):
        data.read_day(repo, "spot_1m", DAY)


def test_rows_of_another_underlying_are_dropped(repo: Path) -> None:
    mixed = pa.concat_tables([_bars("IDX", 3), _bars("OTHER", 2, underlying="XIDX")])
    _write(repo, "week_02_2026-11-07_to_2026-11-13", "fut_1m", DAY, mixed)
    data.partitions.cache_clear()
    assert set(data.read_day(repo, "fut_1m", DAY)["underlying"].to_pylist()) == {"BANKNIFTY"}


def test_a_bar_is_visible_only_after_it_closed(repo: Path) -> None:
    tb = data.read_day(repo, "spot_1m", DAY)
    at_0916 = dt.datetime(2026, 11, 12, 9, 16, tzinfo=IST)
    assert data.visible(tb, at_0916).num_rows == 1
    assert data.visible(tb, at_0916 - dt.timedelta(seconds=1)).num_rows == 0
    with pytest.raises(ValueError, match="tz-aware"):
        data.visible(tb, at_0916.replace(tzinfo=None))
