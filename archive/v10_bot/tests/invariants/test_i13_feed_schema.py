"""I13 feed side (MISSION V11 §7): schema-validate every feed message; an unknown field is logged; an unknown
enum or shape means no new entries plus an alert. Contract tests on redacted real responses follow once the
owner supplies recordings (the Upstox V3 feed schema is UNVERIFIED this session)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bot.recorder.snapshot import RecorderConfig, SchemaError, SnapshotRecorder, replay, validate
from bot.recorder.synthetic_feed import light_keys, synthetic_day

DAY = dt.date(2026, 11, 12)


def recorder(tmp: Path) -> SnapshotRecorder:
    return SnapshotRecorder(RecorderConfig(data_dir=tmp / "data", size_cap_bytes=10**9))


def test_unknown_field_is_logged_and_dropped(tmp_path: Path) -> None:
    rec = recorder(tmp_path)
    for local, msg in synthetic_day(DAY, 5, light_keys()[:1], extra={0: {"surprise": 1}}):
        rec.on_message(msg, local)
    gz = rec.end_day()
    assert gz is not None
    assert [a.kind for a in rec.alerts] == ["schema_warning"]
    assert all("surprise" not in r for r in replay(gz))


def test_unknown_enum_blocks_entries_and_is_not_recorded(tmp_path: Path) -> None:
    rec = recorder(tmp_path)
    local, msg = next(synthetic_day(DAY, 6, light_keys()[:1], extra={0: {"iv_src": "bogus"}}))
    rec.on_message(msg, local)
    assert [a.kind for a in rec.alerts] == ["schema"]
    assert not rec.guard.entries_allowed(local)
    assert rec.written == 0


@pytest.mark.parametrize(
    "bad",
    [
        {"key": "X", "exch_ts_ns": 1, "ltp_paise": 10.5, "vol": 1},
        {"key": "X", "exch_ts_ns": 1, "vol": 1},
        {"key": "X", "exch_ts_ns": True, "ltp_paise": 1, "vol": 1},
    ],
)
def test_wrong_type_missing_field_or_bool_is_a_schema_error(bad: dict[str, object]) -> None:
    with pytest.raises(SchemaError):
        validate(bad)
