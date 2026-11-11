#!/usr/bin/env python3
"""CORE canaries (MISSION V11 §5.5): build each violation at runtime in a temp copy of the repo
(${TMPDIR:-/tmp}/mission-v11-canary-*) and require tools/mission_check.py to turn the named check RED.
Nothing violating is ever written to the real repository. Exit 0 only when the clean copy is GREEN
and every canary is caught. Fake secrets are assembled from fragments and never stored whole.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TMP = Path(tempfile.gettempdir())  # ${TMPDIR:-/tmp}
IGNORE = shutil.ignore_patterns(
    ".venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", ".hypothesis", "data", "dist", ".cache"
)


def run_check(copy: Path) -> str:
    r = subprocess.run(  # noqa: S603
        [sys.executable, str(copy / "tools/mission_check.py"), "--root", str(copy)],
        cwd=copy,
        capture_output=True,
        check=False,
    )
    return r.stdout.decode("utf-8", "replace")


def red(output: str, check: str) -> bool:
    return re.search(rf"^#{check} [^\n]*: RED", output, re.MULTILINE) is not None


def make_copy() -> Path:
    dst = Path(tempfile.mkdtemp(prefix="mission-v11-canary-", dir=TMP))
    shutil.copytree(ROOT, dst, dirs_exist_ok=True, ignore=IGNORE, symlinks=True)
    if not (dst / "EVIDENCE/seal_log.jsonl").read_text().strip():
        subprocess.run(  # noqa: S603
            [sys.executable, str(dst / "tools/seal.py"), "CANARY", "--no-commit"],
            cwd=dst,
            capture_output=True,
            check=True,
        )
        subprocess.run(  # noqa: S603
            [sys.executable, str(dst / "tools/make_report.py")], cwd=dst, capture_output=True, check=True
        )
    tasks = json.loads((dst / "TASKS.json").read_text())
    for t in tasks:  # no owner task in progress inside the copy
        if t["status"] == "IN_PROGRESS":
            t["status"] = "TODO"
    (dst / "TASKS.json").write_text(json.dumps(tasks, indent=1) + "\n")
    subprocess.run([sys.executable, str(dst / "tools/make_report.py")], cwd=dst, capture_output=True, check=True)  # noqa: S603
    return dst


def append(path: Path, text: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def untagged_number(c: Path) -> None:
    append(c / "DECISIONS.md", "\n## D-999 | canary | 2026-11-11\nOLD → NEW: a limit of ₹123 with no tag\n")


def fake_secret(c: Path) -> None:
    token = "ey" + "J" + "x" * 12 + "Q2" * 8 + "abc"
    (c / "canary_note.md").write_text("Authorization: " + "Bear" + "er " + token + "\n", encoding="utf-8")


def skipped_test(c: Path) -> None:
    marker = "@pytest.mark." + "skip"
    (c / "tests/test_canary_skip.py").write_text(f"import pytest\n\n\n{marker}\ndef test_x() -> None:\n    pass\n")


def protected_change(c: Path) -> None:
    append(c / "tools/preflight.sh", "# canary: unapproved change\n")


def fake_approval(c: Path) -> None:
    append(
        c / "OWNER_APPROVALS.md",
        "\n## A-901 | session 1 | received 2026-11-11 10:00 IST | question F-MAXLOSS (code 0000)\n"
        "OWNER COMMAND (verbatim line): haan F-MAXLOSS 0000\nEFFECT: none\n",
    )


def digit_in_fields(c: Path) -> None:
    fields = json.loads((c / "report_fields.json").read_text())
    fields["seedhi_baat"] = "munafa " + str(7 * 6) + " pakka"
    (c / "report_fields.json").write_text(json.dumps(fields, ensure_ascii=False))


def constants_missing_extract(c: Path) -> None:
    (c / "EVIDENCE/T03").mkdir(parents=True, exist_ok=True)
    (c / "EVIDENCE/T03/src_canary_rate.txt").write_text("the rate is 0.5 percent\n")
    append(
        c / "constants.toml",
        '\n[canary_rate]\nvalue = 0.7\nunit = "pct"\ntag = "SOURCE"\nsource_url = "https://example.invalid/x"\n'
        'fetched = "2026-11-11"\nttl_days = 30\nstatus = "VERIFIED"\nextract = "EVIDENCE/T03/src_canary_rate.txt"\n',
    )


def fullb_pass_gate_closed(c: Path) -> None:
    tasks = json.loads((c / "TASKS.json").read_text())
    for t in tasks:
        if t["id"] == "T13a":
            t["status"] = "PASS"
    (c / "TASKS.json").write_text(json.dumps(tasks, indent=1) + "\n")


CANARIES: list[tuple[str, str, Callable[[Path], None]]] = [
    ("untagged number", "1", untagged_number),
    ("fake secret (from fragments)", "6", fake_secret),
    ("skipped test", "5", skipped_test),
    ("protected change without approval", "3", protected_change),
    ("fake approval with a wrong code", "17", fake_approval),
    ("digit in report_fields.json", "2", digit_in_fields),
    ("constants value missing from its extract", "18", constants_missing_extract),
    ("FULL-B task PASS while the gate is CLOSED", "19", fullb_pass_gate_closed),
]


def main() -> int:
    failures = 0
    clean = make_copy()
    try:
        out = run_check(clean)
        ok = "mission_check: GREEN" in out
        print(f"{'PASS' if ok else 'FAIL'} clean copy is GREEN")
        if not ok:
            print(out)
            failures += 1
    finally:
        shutil.rmtree(clean, ignore_errors=True)
    for name, check, mutate in CANARIES:
        copy = make_copy()
        try:
            mutate(copy)
            caught = red(run_check(copy), check)
            print(f"{'PASS' if caught else 'FAIL'} canary '{name}' → #{check} RED")
            failures += 0 if caught else 1
        finally:
            shutil.rmtree(copy, ignore_errors=True)
    left = sorted(TMP.glob("mission-v11-canary-*"))
    if left:
        print("FAIL canary temp dirs left behind")
        failures += 1
    print(f"canaries: {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
