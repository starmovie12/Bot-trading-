"""I11 time (MISSION V11 §7): IST-aware minutes, exchange and local timestamps both stored, clock drift checked.

The NSE / BSE holiday calendar from an official page is UNVERIFIED (no web in sessions 1-3); see
docs/RECORDER_SPEC.md. Expiry shifts on holidays come from the broker's instrument master (T05/T09 runtime).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from bot.recorder.snapshot import NS, RecorderConfig, SnapshotRecorder, ist_date, replay
from bot.recorder.synthetic_feed import light_keys, session_open_ns, synthetic_day
from bot.recorder.ticks import ist_minute

DAY = dt.date(2026, 11, 12)


def test_session_open_is_0915_ist_on_the_right_date() -> None:
    t = session_open_ns(DAY)
    assert ist_minute(t) == 9 * 60 + 15
    assert ist_date(t) == DAY
    assert ist_date(t - 10 * 3600 * NS) == DAY - dt.timedelta(days=1)


def test_every_snapshot_keeps_exchange_and_local_time(tmp_path: Path) -> None:
    rec = SnapshotRecorder(RecorderConfig(data_dir=tmp_path / "data", size_cap_bytes=10**9))
    for local, msg in synthetic_day(DAY, 3, light_keys()[:2]):
        rec.on_message(msg, local)
    gz = rec.end_day()
    assert gz is not None
    rows = replay(gz)
    assert rows and all(isinstance(r["exch_ts_ns"], int) and isinstance(r["local_ts_ns"], int) for r in rows)


def test_clock_drift_raises_an_alert_and_blocks_entries(tmp_path: Path) -> None:
    rec = SnapshotRecorder(RecorderConfig(data_dir=tmp_path / "data", size_cap_bytes=10**9, max_drift_s=2))
    local, msg = next(synthetic_day(DAY, 4, light_keys()[:1]))
    rec.on_message(msg, msg["exch_ts_ns"] + 5 * NS)
    assert [a.kind for a in rec.alerts] == ["clock_drift"]
    assert not rec.guard.entries_allowed(msg["exch_ts_ns"] + 6 * NS)
    assert local > 0
