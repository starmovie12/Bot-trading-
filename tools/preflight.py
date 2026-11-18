"""Preflight for every S3 run (BANKNIFTY_STRATEGY_V3.md §13.1). Any failure -> PreflightError -> abort.

1. The round grid is in PLAN.md as committed (no uncommitted PLAN.md change), in a block
   `<!-- S3-GRID R<n> -->` + fenced json list of {variant, overrides, flags}; the PLAN.md commit is older
   than the round's first trial row.
2. trials.jsonl S3 rows == runner calls == result files.
3. Every existing S3 row of the round has a config_hash from the grid and the round's series_id.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ.pop("UPSTOX_RO_TOKEN", None)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab.s3.ledger import Ledger, s3_rows  # noqa: E402
from lab.s3.registry import Cfg  # noqa: E402

GRID = re.compile(r"<!-- S3-GRID (?P<round>R\d+) -->\s*```json\s*(?P<body>.*?)```", re.S)


class PreflightError(RuntimeError):
    pass


def grid(plan_text: str, rnd: str) -> list[Cfg]:
    for m in GRID.finditer(plan_text):
        if m["round"] == rnd:
            return [
                Cfg(
                    variant=c["variant"],
                    overrides=c.get("overrides", {}),
                    flags=c.get("flags", {}),
                    intrabar=c.get("intrabar", "BARCLOSE"),
                )
                for c in json.loads(m["body"])
            ]
    raise PreflightError(f"no committed grid for {rnd} in PLAN.md")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout  # noqa: S603, S607


def plan_commit_time(plan: Path) -> datetime:
    if _git("status", "--porcelain", "--", str(plan)).strip():
        raise PreflightError("PLAN.md has uncommitted changes: commit the grid before the run")
    ts = _git("log", "-1", "--format=%ct", "--", str(plan)).strip()
    if not ts:
        raise PreflightError("PLAN.md is not committed")
    return datetime.fromtimestamp(int(ts), UTC)


def check(
    rnd: str,
    series_id: str,
    plan: Path = ROOT / "PLAN.md",
    ledger: Ledger | None = None,
    commit_time: Callable[[Path], datetime] = plan_commit_time,
) -> dict[str, Any]:
    led = ledger or Ledger()
    cfgs = grid(plan.read_text(encoding="utf-8"), rnd)
    t_plan = commit_time(plan)
    rows, calls, files = led.counts()
    if not rows == calls == files:
        raise PreflightError(f"trials rows {rows} / runner calls {calls} / result files {files} differ")
    hashes = {c.config_hash() for c in cfgs}
    mine = [r for r in s3_rows(led.trials) if r.get("round") == rnd]
    for r in mine:
        if datetime.fromisoformat(r["ts"]) < t_plan:
            raise PreflightError(f"{r['id']} ran before the PLAN.md commit of {rnd}")
        if r.get("config_hash") not in hashes and not r.get("nested_choice"):
            raise PreflightError(f"{r['id']} config_hash not in the committed {rnd} grid")
        if r.get("series_id") != series_id:
            raise PreflightError(f"{r['id']} series_id {r.get('series_id')} != {series_id}")
    return {"round": rnd, "configs": len(cfgs), "rows": rows, "plan_commit": t_plan.isoformat()}


if __name__ == "__main__":
    from lab.s3.costs import base

    try:
        print(json.dumps(check(sys.argv[1], base().series_id)))
    except PreflightError as e:
        print(f"PREFLIGHT ABORT: {e}")
        sys.exit(1)
