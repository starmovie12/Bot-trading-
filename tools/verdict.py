#!/usr/bin/env python3
"""`make verdict` (MISSION V19 RULES V1, V3): the static verdict after 3e and again after Phase 6.

  verdict.py [--root DIR] [--write]   print `LABEL(CODE, ...)`; --write saves results/verdict.json; exit 0
Inputs (all files of the repo): results/stage1_card.md / docs/DATA_REPORT.md (DATA_GRADE), results/loss_first_rank.json
(the 3c battery), results/holdout.json (3e), results/review.json (Phase 6; absent = NOT_REVIEWED), DATA_REQUEST.md
(MUST items with fallback_ok = no), DECISIONS.md (an owner stop at STOP-1), limits.toml (LIVE_POSSIBLE).
Every row is evaluated; the label is the worst matching one; the first code in table order is the headline.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TEXT = {"PAPER_READY": "PAPER PAR CHALAO (asli paisa nahi)", "NOT_YET": "ABHI NAHI",
        "STOP": "RUKO: is data mein raasta nahi mila"}  # fmt: skip
RANK = {"PAPER_READY": 0, "NOT_YET": 1, "STOP": 2}
CLASS = {
    **dict.fromkeys(("NO_DATA", "MISSING_DATA", "OPEN_FINDINGS", "NOT_REVIEWED", "HOLDOUT_FAIL", "FORWARD_FAIL",
                     "FORWARD_DEGRADED", "AGREEMENT_FAIL", "OWNER_STOPPED_AT_STOP1"), "BLOCK"),
    "NO_EDGE_IN_TESTED_SET": "STOP",
    **dict.fromkeys(("MODELLED_PREMIUM", "NO_LIVE_BALANCE_UP_TO_2L", "MIN_ABOVE_OWNER_CEILING", "UNDERPOWERED"),
                    "LIMIT"),
    **dict.fromkeys(("FORWARD_PENDING", "FORWARD_UNDERPOWERED", "FORWARD_SHORT", "AGREEMENT_PARTIAL",
                     "FORWARD_CONSISTENT"), "INFO"),
}  # fmt: skip


def jload(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def grade(root: Path) -> str:
    for rel in ("results/stage1_card.md", "docs/DATA_REPORT.md"):
        p = root / rel
        m = re.search(r"DATA_GRADE\W+([A-Z]+)", p.read_text(encoding="utf-8")) if p.is_file() else None
        if m:
            return m.group(1)
    return "NONE"


def decide(root: Path = ROOT) -> dict[str, Any]:
    g, rank = grade(root), jload(root / "results/loss_first_rank.json")
    hold, review = jload(root / "results/holdout.json"), jload(root / "results/review.json")
    short = bool(rank.get("short_mode")) or bool(rank.get("underpowered_only"))
    rows: list[tuple[int | str, str, str]] = []
    if g == "NONE":
        rows.append((1, "NOT_YET", "NO_DATA"))
    if g != "NONE" and not short and not rank.get("passed_battery"):
        rows.append((2, "STOP", "NO_EDGE_IN_TESTED_SET"))
    if g != "NONE" and short:
        rows.append(("2b", "PAPER_READY", "UNDERPOWERED"))
    if not review:
        rows.append((3, "NOT_YET", "NOT_REVIEWED"))
    elif review.get("open_sev12") or review.get("open_rule10") or review.get("e2_red"):
        rows.append((3, "NOT_YET", "OPEN_FINDINGS"))
    if g != "NONE" and not hold.get("pass", False):
        rows.append((4, "NOT_YET", "HOLDOUT_FAIL"))
    must = (root / "DATA_REQUEST.md").read_text(encoding="utf-8") if (root / "DATA_REQUEST.md").is_file() else ""
    if re.search(r"MUST\b.*fallback_ok = no", must) and "status: CLOSED" not in must:
        rows.append((5, "NOT_YET", "MISSING_DATA"))
    dec = (root / "DECISIONS.md").read_text(encoding="utf-8") if (root / "DECISIONS.md").is_file() else ""
    if re.search(r"^- OWNER: (continue )?stop-here", dec, flags=re.M):
        rows.append((6, "NOT_YET", "OWNER_STOPPED_AT_STOP1"))
    if not rows:
        rows.append((7, "PAPER_READY", ""))
    label = max((r[1] for r in rows), key=RANK.__getitem__)
    codes = [r[2] for r in rows if r[2]]
    lim = tomllib.loads((root / "limits.toml").read_text(encoding="utf-8")) if (root / "limits.toml").is_file() else {}
    if not lim.get("LIVE_POSSIBLE", {}).get("value", False):
        ceiling = jload(root / "results/limits_derivation.json").get("code") == "MIN_ABOVE_OWNER_CEILING"
        codes.append("MIN_ABOVE_OWNER_CEILING" if ceiling else "NO_LIVE_BALANCE_UP_TO_2L")
    codes = list(dict.fromkeys(codes))
    return {"label": label, "label_text": TEXT[label], "headline": codes[0] if codes else None,
            "codes": [{"code": c, "class": CLASS[c]} for c in codes], "rows": [str(r[0]) for r in rows],
            "inputs": {"data_grade": g, "short_mode": short, "passed_battery": rank.get("passed_battery", []),
                       "holdout_pass": hold.get("pass"), "reviewed": bool(review)},
            "paper_only": True, "date": str(dt.date.today())}  # fmt: skip


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    v = decide(root)
    if "--write" in argv:
        (root / "results/verdict.json").write_text(json.dumps(v, indent=1) + "\n", encoding="utf-8")
    print(f"{v['label']}({', '.join(c['code'] for c in v['codes'])}) {v['label_text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
