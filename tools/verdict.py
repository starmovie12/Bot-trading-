#!/usr/bin/env python3
"""`make verdict DATA=<path>` (MISSION V11 §16, T10): the decision rule of PREREGISTER_v2.md.

Order of permission: GO_PAPER > NOT_YET > STOP. NOT_YET is the default; STOP needs its own rule.
  verdict.py [--data DIR] [--g0 FILE]     print the verdict with its reason codes; exit 0

- STOP(G0_FAIL_ARITH / G0_FAIL_CREDIBILITY): every universe member of G0 is FAIL_* (G0 itself only fails on
  SOURCE facts and OWNER / approved limits).
- NOT_YET(NO_DATA): no REAL market data (DATA missing, or `kind.txt` in it is not REAL), or fewer trading days
  than gates.toml `min_trading_days`; G0_CONDITIONAL and DATA_RIGHTS_OPEN are added when they hold.
- NOT_YET(BLOCKED_INPUT): enough REAL days, but the engine is not wired to the harness yet (T14, FULL-B).
- GO_PAPER only through the full harness on stressed trades from REAL data (T14); never from this script alone.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def decide(data: Path | None, g0_file: Path) -> tuple[str, list[str]]:
    g0 = json.loads(g0_file.read_text()) if g0_file.is_file() else {}
    outcomes = [m.get("outcome", "") for m in g0.get("members", {}).values()]
    if outcomes and all(o.startswith("FAIL") for o in outcomes):
        cred = all(o == "FAIL_CREDIBILITY" for o in outcomes)
        return "STOP", ["G0_FAIL_CREDIBILITY" if cred else "G0_FAIL_ARITH"]
    reasons = []
    gates = tomllib.loads((ROOT / "gates.toml").read_text())
    kind = (data / "kind.txt").read_text().strip() if data is not None and (data / "kind.txt").is_file() else ""
    days = len(list(data.glob("*.jsonl.gz"))) if data is not None and kind == "REAL" else 0
    if days < int(gates["min_trading_days"]["value"]):
        reasons.append("NO_DATA")
    if g0.get("g0") == "CONDITIONAL":
        reasons.append("G0_CONDITIONAL")
    rights = tomllib.loads((ROOT / "constants.toml").read_text()).get("data_rights", {}).get("value")
    if rights != "OK":
        reasons.append("DATA_RIGHTS_OPEN")
    if "NO_DATA" not in reasons:
        reasons.append("BLOCKED_INPUT")  # the engine is wired to the harness only in T14 (FULL-B)
    return "NOT_YET", reasons


def main(argv: list[str]) -> int:
    data = Path(argv[argv.index("--data") + 1]) if "--data" in argv else None
    g0_file = Path(argv[argv.index("--g0") + 1]) if "--g0" in argv else ROOT / "EVIDENCE/T04/g0.json"
    label, reasons = decide(data, g0_file)
    print(f"{label}({', '.join(reasons)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
