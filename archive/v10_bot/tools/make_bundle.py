#!/usr/bin/env python3
"""`make bundle` (MISSION V11 §10 item 3, T09): dist/recorder_bundle_<YYYYMMDD>.zip for the owner's machine.

Contents: the read-only Recorder package (no strategy code, no order code), recorder.toml, OWNER_START.md,
RUNBOOK.md, tools/pack_data.py, tools/backup_verify.py, a locked dependency list (standard library only) and
the bundle's own SHA256SUMS. Every file is secret-scanned first (names + content patterns of
tools/secret_patterns.txt); one hit means no bundle. dist/ is gitignored: a bundle is never committed.

  make_bundle.py [--date YYYYMMDD]
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.redact import load_rules, scan_text, secret_named  # noqa: E402

FILES = {
    "bot/__init__.py": "src/bot/__init__.py",
    "bot/recorder/__init__.py": "src/bot/recorder/__init__.py",
    "bot/recorder/__main__.py": "src/bot/recorder/__main__.py",
    "bot/recorder/clock.py": "src/bot/recorder/clock.py",
    "bot/recorder/journal.py": "src/bot/recorder/journal.py",
    "bot/recorder/notify.py": "src/bot/recorder/notify.py",
    "bot/recorder/snapshot.py": "src/bot/recorder/snapshot.py",
    "bot/recorder/synthetic_feed.py": "src/bot/recorder/synthetic_feed.py",
    "recorder.toml": "recorder.toml",
    "OWNER_START.md": "docs/OWNER_START.md",
    "RUNBOOK.md": "docs/RUNBOOK.md",
    "tools/pack_data.py": "tools/pack_data.py",
    "tools/backup_verify.py": "tools/backup_verify.py",
}
LOCK = "# Recorder bundle: standard library only, no third-party packages (MISSION V11 T09)\n"
FORBIDDEN_IMPORT = re.compile(r"\bbot\.(strategy|haath|dimaag|backtest|login)\b|\bgateway\b")


def main(argv: list[str]) -> int:
    day = argv[argv.index("--date") + 1] if "--date" in argv else dt.datetime.now().strftime("%Y%m%d")
    rules = load_rules()
    contents: dict[str, bytes] = {"requirements-recorder.lock": LOCK.encode()}
    problems: list[str] = []
    for inside, source in FILES.items():
        path = ROOT / source
        if not path.is_file():
            problems.append(f"{source}: missing")
            continue
        if secret_named(source, rules) is not None:
            problems.append(f"{source}: secret-named file")
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        problems += scan_text(source, text, rules, ("content", "entropy"))
        if inside.endswith(".py") and FORBIDDEN_IMPORT.search(text):
            problems.append(f"{source}: imports strategy, order or login code (not allowed in the Recorder bundle)")
        contents[inside] = path.read_bytes()
    if problems:
        for p in problems:
            print(f"REFUSED {p}")
        print("make bundle: refused; no bundle written")
        return 1
    sums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(contents.items()))
    contents["SHA256SUMS"] = sums.encode()
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"recorder_bundle_{day}.zip"
    folder = f"recorder_bundle_{day}"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(contents.items()):
            z.writestr(f"{folder}/{name}", data)
    print(f"bundle: {out.relative_to(ROOT)} ({len(contents)} files, secret scan clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
