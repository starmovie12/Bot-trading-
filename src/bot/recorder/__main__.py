"""Recorder command line (MISSION V11 §10, T09). Read-only: it never places an order.

python3 -m bot.recorder --dry-run [--days N]     synthetic feed, LIGHT scope; nothing is saved
python3 -m bot.recorder --health FILE            one-line daily health of a recorded day file
python3 -m bot.recorder --alert-dry-run DIR      write a test alert and a heartbeat to DIR (nothing sent)
python3 -m bot.recorder --live                   refused: the live Upstox feed adapter is not built yet
"""

from __future__ import annotations

import datetime as dt
import sys
import tempfile
from pathlib import Path

from bot.recorder.notify import DryRunNotifier
from bot.recorder.snapshot import RecorderConfig, SnapshotRecorder, health
from bot.recorder.synthetic_feed import light_keys, synthetic_day


def dry_run(days: int) -> int:
    keys = light_keys()
    with tempfile.TemporaryDirectory(prefix="mission-v11-dryrun-") as d:
        rec = SnapshotRecorder(RecorderConfig(data_dir=Path(d) / "data", size_cap_bytes=10**9), dry_run=True)
        start = dt.date(2026, 11, 12)
        for i in range(days):
            for local, msg in synthetic_day(start + dt.timedelta(days=i), i + 1, keys):
                rec.on_message(msg, local)
            rec.end_day()
        saved = any((Path(d) / "data").glob("*")) if (Path(d) / "data").exists() else False
    status = "OK" if not rec.alerts and not saved else "NOT OK"
    print(
        f"DRY-RUN {status}: {len(keys)} instruments, {rec.messages} messages, {len(rec.alerts)} alerts, nothing saved"
    )
    return 0 if status == "OK" else 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["--dry-run"]:
        days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 1
        return dry_run(days)
    if argv[:1] == ["--health"] and len(argv) == 2:
        h = health(Path(argv[1]), light_keys())
        verdict = "OK" if h["ok"] else "NOT OK"
        print(f"{verdict}: coverage {h['coverage']:.1%}, missing {h['missing']}, duplicates {h['duplicates']}")
        return 0 if h["ok"] else 1
    if argv[:1] == ["--alert-dry-run"] and len(argv) == 2:
        n = DryRunNotifier(Path(argv[1]))
        now = dt.datetime.now(dt.UTC)
        print(n.send("test", "recorder alert dry-run", now))
        print(n.heartbeat(now))
        return 0
    if argv[:1] == ["--live"]:
        print("REFUSED: the live Upstox feed adapter is not built (feed schema UNVERIFIED; docs/RECORDER_SPEC.md)")
        return 2
    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
