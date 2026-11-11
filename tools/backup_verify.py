#!/usr/bin/env python3
"""Backup check (MISSION V11 §10, T09): run it on a RESTORED copy of the Recorder data folder.

  python3 tools/backup_verify.py DATA_DIR      OK / NOT OK per sealed day; exit 1 if any day is NOT OK

A day is OK when its sha256 sidecar matches and its hash chain reads from start to end.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # bundle root (bot/ lives there)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))  # repo layout

from bot.recorder.snapshot import verify_day


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 64
    days = sorted(Path(argv[0]).glob("*.jsonl.gz"))
    bad = 0
    for gz in days:
        ok = verify_day(gz)
        bad += 0 if ok else 1
        print(f"{gz.name}: {'OK' if ok else 'NOT OK'}")
    print(f"{len(days)} day(s), {bad} NOT OK")
    return 1 if bad or not days else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
