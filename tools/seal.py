#!/usr/bin/env python3
"""Seal the protected set (MISSION V11 §5.2).

  seal.py <task>              write PROTECTED.toml from the files as they are, refresh REPORT.md,
                              append EVIDENCE/seal_log.jsonl, commit through tools/safe_add.sh and
                              tag seal/<task> (seal/<task>-2, -3 … for a re-seal)
  seal.py <task> --no-commit  write PROTECTED.toml and the seal-log line only (canary copies)
  seal.py <task> --trailer TEXT [--trailer TEXT]   add trailer lines to the seal commit message
  seal.py --compute           print the SEAL the current files would get; write nothing

SEAL = first 8 hex of sha256 over the sorted list of "<path>  <sha256>" lines.
Refuses (except with --no-commit) when a protected file has uncommitted changes: a seal must
describe committed content.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWS = ("T02a", "T02b", "T04", "T09", "T11", "T18")

# (glob, rule, owner_tasks). owner_tasks = the tasks that create or extend the file (§5.2, §12).
RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("MISSION.md", "exact", ()),
    ("tools/floors_baseline.toml", "exact", ("T10",)),
    ("tools/mission_check.py", "exact", ("T02a", "T02b")),
    ("tools/make_report.py", "exact", VIEWS),
    ("report_templates/*", "exact", VIEWS),
    ("tools/ev.sh", "exact", ("T01", "T02a")),
    ("tools/redact.py", "exact", ("T01", "T02a")),
    ("tools/secret_patterns.txt", "exact", ("T01", "T02a", "T03")),
    ("tools/preflight.sh", "exact", ("T01",)),
    ("tools/env_allowlist.txt", "exact", ("T01",)),
    ("tools/safe_add.sh", "exact", ("T01",)),
    ("tools/clock.sh", "exact", ("T01",)),
    ("tools/seal.py", "exact", ("T02a",)),
    ("tools/tag_scope.toml", "exact", ("T02a",)),
    ("tools/callsite_allowlist.toml", "exact", ("T02b",)),
    ("tools/economics.py", "exact", ("T04",)),
    ("tools/power.py", "exact", ("T04", "T10")),
    ("tools/truth_tests.py", "exact", ("T10", "T14")),
    ("tools/fullb_gate.py", "exact", ("T10",)),
    (".githooks/*", "exact", ("T01", "T02a", "T02b")),
    (".github/workflows/*", "exact", ("T02b",)),
    ("tools/verify/*.sh", "exact", ()),  # owner task = the script's own task id (file stem)
    ("tests/canary/*", "exact", ("T02a", "T02b")),
    ("limits.toml", "per_value", ("T01", "T06")),
    ("gates.toml", "per_value", ("T10", "T12")),
    ("constants.toml", "evidence", ("T03",)),
    ("OWNER_QUESTIONS.md", "append_only", ()),
    ("OWNER_APPROVALS.md", "append_only", ()),
    ("OWNER_CONFIG.md", "append_only", ()),
    ("tests/adversary/*", "append_only", ("T17-R1", "T17-R2", "T17-R3")),
]


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)  # noqa: S603, S607
    return r.stdout.decode().strip()


def entries() -> list[dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for pattern, rule, owners in RULES:
        for p in sorted(ROOT.glob(pattern)):
            rel = str(p.relative_to(ROOT))
            if not p.is_file() or rel in out or rel == "PROTECTED.toml" or "__pycache__" in rel:
                continue
            tasks = (p.stem,) if pattern == "tools/verify/*.sh" else owners
            out[rel] = {
                "path": rel,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "rule": rule,
                "owner_tasks": list(tasks),
            }
    return [out[k] for k in sorted(out)]


def seal_of(items: list[dict[str, object]]) -> str:
    canon = "\n".join(f"{e['path']}  {e['sha256']}" for e in sorted(items, key=lambda e: str(e["path"])))
    return hashlib.sha256(canon.encode()).hexdigest()[:8]


def write_protected(items: list[dict[str, object]], task: str, session: str, seal: str) -> None:
    lines = [
        "# PROTECTED.toml (MISSION V11 §5.2): written by tools/seal.py. Never edit by hand.",
        f'seal = "{seal}"',
        f'task = "{task}"',
        f'session = "{session}"',
        "",
    ]
    for e in items:
        owners = ", ".join(f'"{t}"' for t in e["owner_tasks"])  # type: ignore[attr-defined]
        lines += ["[[file]]", f'path = "{e["path"]}"', f'sha256 = "{e["sha256"]}"', f'rule = "{e["rule"]}"']
        lines += [f"owner_tasks = [{owners}]", ""]
    (ROOT / "PROTECTED.toml").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    items = entries()
    seal = seal_of(items)
    if argv == ["--compute"]:
        print(seal)
        return 0
    if not argv or not re.fullmatch(r"T[0-9]{2}[ab]?(-[RF][0-9])?|CANARY", argv[0]):
        print(__doc__, file=sys.stderr)
        return 64
    task, commit = argv[0], "--no-commit" not in argv
    if commit:
        dirty = git("status", "--porcelain", "--", *[str(e["path"]) for e in items])
        if dirty:
            print("seal: protected files have uncommitted changes; commit them first", file=sys.stderr)
            return 1
    state = (ROOT / "STATE.md").read_text(encoding="utf-8") if (ROOT / "STATE.md").is_file() else ""
    m = re.search(r"^SESSION_N: *(\d+)", state, re.MULTILINE)
    session = m.group(1) if m else "0"
    old = re.search(r'^seal = "([0-9a-f]{8})"', (ROOT / "PROTECTED.toml").read_text(encoding="utf-8"), re.MULTILINE)
    write_protected(items, task, session, seal)
    log = {
        "session": int(session),
        "task": task,
        "old_seal": old.group(1) if old else None,
        "new_seal": seal,
        "commit": git("rev-parse", "HEAD"),
        "protected_toml_sha256": hashlib.sha256((ROOT / "PROTECTED.toml").read_bytes()).hexdigest(),
        "files": len(items),
        "time": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with (ROOT / "EVIDENCE/seal_log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(log) + "\n")
    if not commit:
        print(seal)
        return 0
    subprocess.run([sys.executable, str(ROOT / "tools/make_report.py")], cwd=ROOT, check=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [str(ROOT / "tools/safe_add.sh"), "PROTECTED.toml", "EVIDENCE/seal_log.jsonl", "REPORT.md"],
        cwd=ROOT,
        check=True,
    )
    msg = f"{task}: seal {seal} ({len(items)} protected files)"
    trailers = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == "--trailer"]
    if trailers:
        msg += "\n\n" + "\n".join(trailers)
    subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=ROOT, input=msg.encode(), check=True)  # noqa: S607
    tag, n = f"seal/{task}", 1
    while git("tag", "--list", tag):
        n += 1
        tag = f"seal/{task}-{n}"
    git("tag", tag)
    print(f"SEAL {seal} · commit {git('rev-parse', '--short', 'HEAD')} · tag {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
