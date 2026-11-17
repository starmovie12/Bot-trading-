"""T05 Recorder MVP (MISSION V11 §10): journal + replay, 5-day soak, kill -9, full disk, size cap, checksum.

Synthetic feed only (tag SIM): this proves machinery, never an edge.
"""

from __future__ import annotations

import datetime as dt
import errno
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from bot.recorder.journal import JournalWriter, read_journal
from bot.recorder.snapshot import RecorderConfig, SnapshotRecorder, Writer, health, replay, verify_day
from bot.recorder.synthetic_feed import light_keys, synthetic_day
from bot.recorder.ticks import ist_minute

DAY = dt.date(2026, 11, 12)
SRC = str(Path(__file__).resolve().parents[1] / "src")


def config(tmp: Path, cap: int = 500 * 1024 * 1024) -> RecorderConfig:
    return RecorderConfig(data_dir=tmp / "data", size_cap_bytes=cap)


def record_day(rec: SnapshotRecorder, day: dt.date, seed: int, keys: list[str]) -> Path | None:
    for local, msg in synthetic_day(day, seed, keys):
        rec.on_message(msg, local)
    return rec.end_day()


def expected_snapshots(day: dt.date, seed: int, keys: list[str]) -> list[dict[str, Any]]:
    last: dict[tuple[int, str], dict[str, Any]] = {}
    for local, msg in synthetic_day(day, seed, keys):
        last[(ist_minute(msg["exch_ts_ns"]), msg["key"])] = {**msg, "local_ts_ns": local}
    return [last[k] for k in sorted(last)]


def test_one_synthetic_day_journals_and_replays_identically(tmp_path: Path) -> None:
    keys = light_keys()
    assert len(keys) == 72
    gz = record_day(SnapshotRecorder(config(tmp_path)), DAY, 1, keys)
    assert gz is not None and gz.name.endswith(".jsonl.gz")
    assert verify_day(gz)
    assert replay(gz) == expected_snapshots(DAY, 1, keys)
    assert health(gz, keys) == {"ok": True, "coverage": 1.0, "missing": 0, "duplicates": 0}


def test_five_simulated_days_soak_without_gaps(tmp_path: Path) -> None:
    keys = light_keys()
    rec = SnapshotRecorder(config(tmp_path))
    for i in range(5):
        gz = record_day(rec, DAY + dt.timedelta(days=i), 10 + i, keys)
        assert gz is not None and verify_day(gz)
        h = health(gz, keys)
        assert h["ok"] and h["missing"] == 0 and h["duplicates"] == 0
    assert rec.alerts == []
    assert rec.written == 5 * 72 * 375


def test_kill_9_mid_write_leaves_a_recoverable_journal(tmp_path: Path) -> None:
    data = tmp_path / "data"
    script = (
        "import datetime as dt, time\n"
        "from pathlib import Path\n"
        "from bot.recorder.snapshot import RecorderConfig, SnapshotRecorder\n"
        "from bot.recorder.synthetic_feed import light_keys, synthetic_day\n"
        f"rec = SnapshotRecorder(RecorderConfig(data_dir=Path({str(data)!r}), size_cap_bytes=10**9))\n"
        "for i, (local, msg) in enumerate(synthetic_day(dt.date(2026, 11, 12), 3, light_keys())):\n"
        "    rec.on_message(msg, local)\n"
        "    if i % 500 == 0:\n"
        "        time.sleep(0.01)\n"
    )
    env = dict(os.environ, PYTHONPATH=SRC)
    proc = subprocess.Popen([sys.executable, "-c", script], env=env)  # noqa: S603
    path = data / "2026-11-12.jsonl"
    deadline = time.time() + 30
    while time.time() < deadline and (not path.exists() or path.stat().st_size < 300_000):
        time.sleep(0.005)
    proc.send_signal(signal.SIGKILL)
    proc.wait()
    assert proc.returncode == -signal.SIGKILL, "the writer finished before the kill: no mid-write test"
    with JournalWriter(path) as w:  # reopening cuts a partial last line and continues the chain
        before = sum(1 for _ in read_journal(path))
        w.write("snap", 1, {"key": "probe"})
    records = list(read_journal(path))
    assert before > 0 and len(records) == before + 1
    assert [r.seq for r in records] == list(range(len(records)))


class FullDisk:
    """A writer that runs out of space after `left` records."""

    def __init__(self, path: Path, left: int) -> None:
        self.inner = JournalWriter(path)
        self.left = left

    def write(self, kind: str, ts_ns: int, data: dict[str, Any]) -> int:
        if self.left <= 0:
            raise OSError(errno.ENOSPC, "No space left on device")
        self.left -= 1
        return self.inner.write(kind, ts_ns, data)

    def close(self) -> None:
        self.inner.close()


def test_full_disk_stops_cleanly_and_the_journal_stays_readable(tmp_path: Path) -> None:
    def factory(p: Path) -> Writer:
        return FullDisk(p, 1000)

    rec = SnapshotRecorder(config(tmp_path), writer_factory=factory)
    out = record_day(rec, DAY, 4, light_keys())
    assert rec.stopped == "disk_full"
    assert [a.kind for a in rec.alerts] == ["disk_full"]
    assert out is not None and out.suffix == ".jsonl"
    assert len(replay(out)) == 1000


def test_size_cap_alert_fires_then_recording_stops_without_deleting(tmp_path: Path) -> None:
    seen: list[str] = []
    rec = SnapshotRecorder(config(tmp_path, cap=600_000), alert_sink=lambda a: seen.append(a.kind))
    for local, msg in synthetic_day(DAY, 5, light_keys()):
        rec.on_message(msg, local)
    assert "size_cap_80" in seen and "size_cap_full" in seen
    assert seen.index("size_cap_80") < seen.index("size_cap_full")
    assert rec.stopped == "size_cap"
    journal = tmp_path / "data" / "2026-11-12.jsonl"
    assert journal.exists() and len(replay(journal)) > 0


def test_a_corrupted_day_file_is_detected(tmp_path: Path) -> None:
    gz = record_day(SnapshotRecorder(config(tmp_path)), DAY, 6, light_keys()[:6])
    assert gz is not None and verify_day(gz)
    raw = bytearray(gz.read_bytes())
    raw[len(raw) // 2] ^= 0xFF
    gz.write_bytes(bytes(raw))
    assert not verify_day(gz)


def test_dry_run_connects_and_logs_but_saves_nothing(tmp_path: Path) -> None:
    rec = SnapshotRecorder(config(tmp_path), dry_run=True)
    assert record_day(rec, DAY, 7, light_keys()[:4]) is None
    assert rec.messages == 4 * 375 and rec.written == 0
    assert not (tmp_path / "data").exists()


def test_late_messages_never_rewrite_a_written_minute(tmp_path: Path) -> None:
    keys = light_keys()[:2]
    rec = SnapshotRecorder(config(tmp_path))
    msgs = list(synthetic_day(DAY, 8, keys))
    for local, msg in msgs[:10]:
        rec.on_message(msg, local)
    rec.on_message(msgs[0][1], msgs[0][0])  # minute 0 again, after minute 4 started
    assert rec.late == 1
