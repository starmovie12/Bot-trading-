#!/usr/bin/env python3
"""Owner-question confirmation codes (MISSION V11 §3.1).

code = first 4 hex of sha256("<id>|<question text>|<proposed value>").

  qcode.py <id> <question text> <proposed value>   print the code
  qcode.py --check OWNER_QUESTIONS.md              recompute every entry's code; exit 1 on a mismatch

An entry in OWNER_QUESTIONS.md is a block that starts with
"## <id> | code <4hex> | ..." and holds a "SAWAL: <question text>" line and a
"PROPOSED: <proposed value>" line.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HEADER = re.compile(r"^## (F-[A-Z0-9-]+) \| code ([0-9a-f]{4}) \|")


def code(qid: str, question: str, proposed: str) -> str:
    return hashlib.sha256(f"{qid}|{question}|{proposed}".encode()).hexdigest()[:4]


def parse(text: str) -> list[tuple[str, str, str, str]]:
    """(id, stated code, question, proposed) for every entry, in file order."""
    entries: list[tuple[str, str, str, str]] = []
    current: list[str] | None = None
    for line in [*text.splitlines(), "## END"]:
        if line.startswith("## "):
            if current is not None:
                qid, stated = current[0], current[1]
                question = next((x[len("SAWAL: ") :] for x in current[2:] if x.startswith("SAWAL: ")), "")
                proposed = next((x[len("PROPOSED: ") :] for x in current[2:] if x.startswith("PROPOSED: ")), "")
                entries.append((qid, stated, question, proposed))
            m = HEADER.match(line)
            current = [m.group(1), m.group(2)] if m else None
        elif current is not None:
            current.append(line)
    return entries


def check(path: Path) -> int:
    bad = 0
    seen: set[str] = set()
    for qid, stated, question, proposed in parse(path.read_text(encoding="utf-8")):
        if qid in seen:
            print(f"{qid}: id used twice")
            bad += 1
        seen.add(qid)
        if not question or not proposed:
            print(f"{qid}: SAWAL or PROPOSED line missing")
            bad += 1
        elif code(qid, question, proposed) != stated:
            print(f"{qid}: stated code does not match its question and proposed value")
            bad += 1
    print(f"checked {len(seen)} question(s), {bad} problem(s)")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--check":
        return check(Path(argv[1]))
    if len(argv) == 3:
        print(code(*argv))
        return 0
    print(__doc__, file=sys.stderr)
    return 64


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
