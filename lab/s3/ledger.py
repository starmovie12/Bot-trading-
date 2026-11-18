"""S3 trial ledger (§13.2): the runner writes every fit itself: one trials.jsonl row + one result file per call."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TRIALS = ROOT / "trials.jsonl"
RUNS = ROOT / "wip/s3_runs"
CALLS = ROOT / "wip/s3_runner_calls.json"


def s3_rows(trials: Path = TRIALS) -> list[dict[str, Any]]:
    if not trials.exists():
        return []
    rows = [json.loads(x) for x in trials.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if str(r.get("id", "")).startswith("S3-")]


@dataclass
class Ledger:
    trials: Path = TRIALS
    runs: Path = RUNS
    calls: Path = CALLS

    def next_id(self) -> str:
        return f"S3-{len(s3_rows(self.trials)):04d}"

    def record(self, row: dict[str, Any], result: dict[str, Any]) -> str:
        tid = self.next_id()
        n = json.loads(self.calls.read_text())["calls"] if self.calls.exists() else 0
        self.calls.parent.mkdir(parents=True, exist_ok=True)
        self.calls.write_text(json.dumps({"calls": n + 1}))
        self.runs.mkdir(parents=True, exist_ok=True)
        (self.runs / f"{tid}.json").write_text(json.dumps({"id": tid, **row, **result}, sort_keys=True, default=str))
        line = {"id": tid, "program": "S3", "ts": dt.datetime.now(dt.UTC).isoformat(), **st1_fields(row, result), **row}
        with self.trials.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, sort_keys=True, default=str) + "\n")
        return tid

    def counts(self) -> tuple[int, int, int]:
        calls = json.loads(self.calls.read_text())["calls"] if self.calls.exists() else 0
        files = len(list(self.runs.glob("S3-*.json"))) if self.runs.exists() else 0
        return len(s3_rows(self.trials)), calls, files


def st1_fields(row: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """The repo ledger's common fields (tools/accept.py ST1_FIELDS) for an S3 fit."""
    return {
        "cycle": "S3",
        "idea": f"{row.get('round')} {row.get('variant')} {row.get('role')}",
        "params": {
            "overrides": row.get("overrides", {}),
            "flags": row.get("flags", {}),
            "checks": row.get("checks", []),
        },
        "design_net_stressed": result.get("net_stress"),
        "p_screen": None,
        "source": f"owner order 6 S3 {row.get('round')} (nested walk-forward fit)",
    }
