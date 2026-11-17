"""I4 feed side (MISSION V11 §7): a stale feed or a gap means no new entries; the recorder never blocks exits."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from bot.recorder.snapshot import NS, RecorderConfig, SnapshotRecorder
from bot.recorder.synthetic_feed import light_keys, synthetic_day

DAY = dt.date(2026, 11, 12)


def recorder(tmp: Path) -> SnapshotRecorder:
    return SnapshotRecorder(RecorderConfig(data_dir=tmp / "data", size_cap_bytes=10**9, max_stale_s=120))


def test_no_data_yet_means_no_entries(tmp_path: Path) -> None:
    assert not recorder(tmp_path).guard.entries_allowed(now_ns=10**18)


def test_a_stale_feed_blocks_entries_and_fresh_data_reopens(tmp_path: Path) -> None:
    rec = recorder(tmp_path)
    local, msg = next(synthetic_day(DAY, 1, light_keys()[:1]))
    rec.on_message(msg, local)
    assert rec.guard.entries_allowed(local + 60 * NS)
    assert not rec.guard.entries_allowed(local + 121 * NS)


def test_a_feed_gap_raises_an_alert_and_blocks_entries_until_data_is_contiguous(tmp_path: Path) -> None:
    rec = recorder(tmp_path)
    feed = list(synthetic_day(DAY, 2, light_keys()[:1], skip_minutes=frozenset({3, 4, 5})))
    for local, msg in feed[:4]:  # minutes 0, 1, 2 and then 6 (3-5 missing)
        rec.on_message(msg, local)
    assert [a.kind for a in rec.alerts] == ["gap"]
    assert not rec.guard.entries_allowed(feed[3][0])
    rec.on_message(feed[4][1], feed[4][0])  # minute 7 follows minute 6
    assert rec.guard.entries_allowed(feed[4][0])
