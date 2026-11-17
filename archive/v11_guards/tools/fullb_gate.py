#!/usr/bin/env python3
"""FULL-B gate (MISSION V11 §12, T10). The order engine track opens only when ALL hold:
G0 = FEASIBLE for the candidate's universe member, REAL market data covers enough trading days for that
member (gates.toml `fullb_min_real_trading_days`), and T12 recorded at least one candidate (STRATEGY.md).

  fullb_gate.py      print the gate state (one line) and its reasons; exit 0 either way
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def real_days(data_dir: Path) -> int:
    kind = data_dir / "kind.txt"
    if not kind.is_file() or kind.read_text().strip() != "REAL":
        return 0
    return len(list(data_dir.glob("*.jsonl.gz")))


def state(root: Path = ROOT) -> tuple[bool, list[str]]:
    reasons = []
    g0_file = root / "EVIDENCE/T04/g0.json"
    g0 = json.loads(g0_file.read_text()) if g0_file.is_file() else {}
    feasible = [m for m, v in g0.get("members", {}).items() if v.get("outcome") == "FEASIBLE"]
    if not feasible:
        reasons.append(f"G0 is {g0.get('g0', 'missing')}: no member is FEASIBLE")
    need = int(tomllib.loads((root / "gates.toml").read_text())["fullb_min_real_trading_days"]["value"])
    days = real_days(root / "data" / "recorder")
    if days < need:
        reasons.append(f"REAL data covers {days} trading days (needs {need})")
    strategy = root / "STRATEGY.md"
    if not strategy.is_file() or not re.search(r"^candidate: ", strategy.read_text(), re.MULTILINE):
        reasons.append("T12 recorded no candidate (STRATEGY.md)")
    return not reasons, reasons


def main() -> int:
    is_open, reasons = state()
    print("FULL-B gate: " + ("OPEN" if is_open else "CLOSED · " + " · ".join(reasons)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
