#!/usr/bin/env python3
"""Secret redactor and scanner (MISSION V11 §5.3).

The one pattern list is tools/secret_patterns.txt (shared with the pre-commit hook,
tools/safe_add.sh and tools/mission_check.py).

Modes:
  redact.py                   stdin -> stdout; every content / pii / entropy hit -> [REDACTED:<name>]
  redact.py --scan PATH...    print "path:line: kind/name" per content, pii or entropy hit (never the text)
  redact.py --guard PATH...   name + content check of worktree files (safe_add.sh); exit 1 on a hit
  redact.py --names PATH...   print paths whose base name is secret-named; exit 1 on a hit
  redact.py --staged          name + content check of the git index (pre-commit hook); exit 1 on a hit

Hash context is kept: 40-hex git SHAs and 64-hex digests never match a pattern, and the entropy
rule needs upper case, lower case and digits together, which a hex digest never has.
Every mode except plain redaction exits 1 when it finds something. A matched value is never
printed, and a secret-named file is never opened.
"""

from __future__ import annotations

import fnmatch
import itertools
import math
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS_FILE = ROOT / "tools" / "secret_patterns.txt"
KINDS = ("name", "content", "pii", "exempt", "entropy")
TOKEN = re.compile(r"[A-Za-z0-9+/=_-]{16,}")


@dataclass(frozen=True)
class Rule:
    kind: str
    name: str
    pattern: str


def load_rules(path: Path = PATTERNS_FILE) -> list[Rule]:
    rules: list[Rule] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) != 3 or parts[0] not in KINDS:
            raise ValueError(f"{path.name}:{number}: bad pattern line")
        rules.append(Rule(parts[0], parts[1], parts[2]))
    return rules


def _compiled(rules: list[Rule], kinds: tuple[str, ...]) -> list[tuple[Rule, re.Pattern[str]]]:
    return [(r, re.compile(r.pattern)) for r in rules if r.kind in kinds and r.kind != "entropy"]


def shannon(s: str) -> float:
    counts = Counter(s)
    return -sum(c / len(s) * math.log2(c / len(s)) for c in counts.values())


def switch_ratio(token: str) -> float:
    classes = ["u" if c.isupper() else "l" if c.islower() else "d" for c in token if c.isalnum()]
    switches = sum(1 for a, b in itertools.pairwise(classes) if a != b)
    return switches / max(1, len(classes) - 1)


def high_entropy(token: str, rule: Rule) -> bool:
    min_len, min_bits, min_switch = rule.pattern.split()
    return (
        len(token) >= int(min_len)
        and any(c.isupper() for c in token)
        and any(c.islower() for c in token)
        and any(c.isdigit() for c in token)
        and shannon(token) >= float(min_bits)
        and switch_ratio(token) >= float(min_switch)
    )


def secret_named(path: str, rules: list[Rule]) -> str | None:
    """Name of the first name-rule matching the base name, else None. Looks at the path only."""
    base = Path(path).name.lower()
    if any(r.kind == "exempt" and fnmatch.fnmatchcase(base, r.pattern.lower()) for r in rules):
        return None
    for r in rules:
        if r.kind == "name" and fnmatch.fnmatchcase(base, r.pattern.lower()):
            return r.name
    return None


def _entropy_replacer(rule: Rule) -> Callable[[re.Match[str]], str]:
    def replace(m: re.Match[str]) -> str:
        return f"[REDACTED:{rule.name}]" if high_entropy(m.group(0), rule) else m.group(0)

    return replace


def redact_text(text: str, rules: list[Rule]) -> str:
    compiled = _compiled(rules, ("content", "pii"))
    entropy = [r for r in rules if r.kind == "entropy"]
    out_lines = []
    for raw in text.split("\n"):
        line = raw
        for rule, rx in compiled:
            line = rx.sub(f"[REDACTED:{rule.name}]", line)
        for rule in entropy:
            line = TOKEN.sub(_entropy_replacer(rule), line)
        out_lines.append(line)
    return "\n".join(out_lines)


def scan_text(label: str, text: str, rules: list[Rule], kinds: tuple[str, ...]) -> list[str]:
    compiled = _compiled(rules, kinds)
    entropy = [r for r in rules if r.kind == "entropy" and "entropy" in kinds]
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        for rule, rx in compiled:
            if rx.search(line):
                hits.append(f"{label}:{number}: {rule.kind}/{rule.name}")
        for rule in entropy:
            if any(high_entropy(m.group(0), rule) for m in TOKEN.finditer(line)):
                hits.append(f"{label}:{number}: entropy/{rule.name}")
    return hits


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True, cwd=ROOT).stdout  # noqa: S603, S607


def staged_paths() -> list[str]:
    raw = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    return [p for p in raw.decode("utf-8", "replace").split("\0") if p]


def _guard(paths: list[str], rules: list[Rule], read: bool, from_index: bool) -> list[str]:
    hits: list[str] = []
    for p in paths:
        if (n := secret_named(p, rules)) is not None:
            hits.append(f"{p}: name/{n} (not opened)")
            continue
        if not read:
            continue
        data = _git("show", f":{p}") if from_index else Path(p).read_bytes()
        hits += scan_text(p, data.decode("utf-8", "replace"), rules, ("content",))
    return hits


def main(argv: list[str]) -> int:
    rules = load_rules()
    if not argv:
        data = sys.stdin.buffer.read().decode("utf-8", "replace")
        sys.stdout.write(redact_text(data, rules))
        return 0
    mode, paths = argv[0], argv[1:]
    if mode == "--names":
        hits = _guard(paths, rules, read=False, from_index=False)
    elif mode == "--guard":
        hits = _guard(paths, rules, read=True, from_index=False)
    elif mode == "--staged":
        hits = _guard(staged_paths(), rules, read=True, from_index=True)
    elif mode == "--scan":
        hits = []
        for p in paths:
            if (n := secret_named(p, rules)) is not None:
                hits.append(f"{p}: name/{n} (not opened)")
                continue
            text = Path(p).read_bytes().decode("utf-8", "replace")
            hits += scan_text(p, text, rules, ("content", "pii", "entropy"))
    else:
        print(__doc__, file=sys.stderr)
        return 64
    for h in hits:
        print(h)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
