#!/usr/bin/env python3
"""Pin check (MISSION V19 C3, RULES K0): the pinned files must match config/PINS.sha256.

check_pins.py          verify; exit 1 on any mismatch
check_pins.py --write  rewrite config/PINS.sha256 from the files as they are (a PIN BUMP: log it, RULES K0)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINNED = ("gates.toml", "limits.toml", "tools/secret_patterns.txt", "tools/secret_allow.txt")


def sha(root: Path, rel: str) -> str:
    return hashlib.sha256((root / rel).read_bytes()).hexdigest()


def read_pins(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (root / "config" / "PINS.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            digest, rel = line.split(None, 1)
            out[rel.strip()] = digest
    return out


def problems(root: Path = ROOT) -> list[str]:
    if not (root / "config" / "PINS.sha256").is_file():
        return ["config/PINS.sha256 missing"]
    pins = read_pins(root)
    out = []
    for rel in PINNED:
        if rel not in pins:
            out.append(f"{rel}: not pinned")
        elif not (root / rel).is_file():
            out.append(f"{rel}: missing")
        elif sha(root, rel) != pins[rel]:
            out.append(f"{rel}: sha256 differs from config/PINS.sha256")
    return out + [f"{rel}: pinned but not in the pinned list" for rel in pins if rel not in PINNED]


def write(root: Path = ROOT) -> None:
    (root / "config" / "PINS.sha256").write_text("".join(f"{sha(root, r)}  {r}\n" for r in PINNED), encoding="utf-8")


def main(argv: list[str]) -> int:
    if argv == ["--write"]:
        write()
        print("pins written (PIN BUMP: add a results/pin_log.md line)")
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 64
    bad = problems()
    for b in bad:
        print(f"FAIL {b}")
    print("pins OK" if not bad else f"pins: {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
