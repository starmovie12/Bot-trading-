"""T09 delivery (MISSION V11 §10 item 3): data pack round trip, restore drill, alert dry-run. SIM data only."""

from __future__ import annotations

import datetime as dt
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from bot.recorder.notify import DryRunNotifier
from bot.recorder.snapshot import RecorderConfig, SnapshotRecorder, verify_day
from bot.recorder.synthetic_feed import light_keys, synthetic_day

ROOT = Path(__file__).resolve().parents[1]
DAY = dt.date(2026, 11, 12)


def record_days(data: Path, n: int) -> None:
    rec = SnapshotRecorder(RecorderConfig(data_dir=data, size_cap_bytes=10**9))
    for i in range(n):
        for local, msg in synthetic_day(DAY + dt.timedelta(days=i), 20 + i, light_keys()[:4]):
            rec.on_message(msg, local)
        rec.end_day()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)  # noqa: S603


def test_data_pack_round_trip_checksums_match(tmp_path: Path) -> None:
    data = tmp_path / "data"
    record_days(data, 2)
    out = run(str(ROOT / "tools/pack_data.py"), "--data", str(data), "--out", str(tmp_path))
    pack = Path(out.stdout.strip())
    assert out.returncode == 0 and pack.name == "datapack_2026-11-12_2026-11-13.zip"
    back = run(str(ROOT / "tools/pack_data.py"), "--verify", str(pack), "--into", str(tmp_path / "agent"))
    assert back.returncode == 0 and back.stdout.startswith("OK")
    for gz in sorted((tmp_path / "agent").glob("*.jsonl.gz")):
        assert verify_day(gz)
        assert gz.read_bytes() == (data / gz.name).read_bytes()


def test_a_tampered_or_padded_pack_is_refused(tmp_path: Path) -> None:
    data = tmp_path / "data"
    record_days(data, 1)
    pack = Path(run(str(ROOT / "tools/pack_data.py"), "--data", str(data), "--out", str(tmp_path)).stdout.strip())
    with zipfile.ZipFile(pack, "a") as z:
        z.writestr("notes.txt", "a file that does not belong in a pack")
    assert run(str(ROOT / "tools/pack_data.py"), "--verify", str(pack)).returncode == 1


def test_restore_drill_passes_and_a_damaged_copy_fails(tmp_path: Path) -> None:
    data = tmp_path / "data"
    record_days(data, 2)
    backup = tmp_path / "backup"
    shutil.copytree(data, backup)
    shutil.rmtree(data)
    restored = tmp_path / "restored"
    shutil.copytree(backup, restored)
    assert run(str(ROOT / "tools/backup_verify.py"), str(restored)).returncode == 0
    victim = sorted(restored.glob("*.jsonl.gz"))[0]
    raw = bytearray(victim.read_bytes())
    raw[-10] ^= 0xFF
    victim.write_bytes(bytes(raw))
    assert run(str(ROOT / "tools/backup_verify.py"), str(restored)).returncode == 1


def test_alert_dry_run_writes_a_message_file_and_sends_nothing(tmp_path: Path) -> None:
    n = DryRunNotifier(tmp_path / "outbox")
    when = dt.datetime(2026, 11, 12, 9, 15, tzinfo=dt.UTC)
    a = n.send("gap", "minutes missing", when)
    h = n.heartbeat(when)
    assert a.read_text().startswith("[DRY-RUN, not sent] gap:")
    assert h.read_text().startswith("[DRY-RUN, not sent] heartbeat:")
