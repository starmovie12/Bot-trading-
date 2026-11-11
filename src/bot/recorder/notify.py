"""Alerts and heartbeat, dry-run only (MISSION V11 §10, T09). The owner adds a channel token later on his own
machine; until then every message is written to a local outbox file and nothing is ever sent."""

from __future__ import annotations

import datetime as dt
from pathlib import Path


class DryRunNotifier:
    def __init__(self, outbox: Path) -> None:
        self.outbox = outbox
        self.outbox.mkdir(parents=True, exist_ok=True)

    def send(self, kind: str, text: str, when: dt.datetime) -> Path:
        stamp = when.strftime("%Y%m%dT%H%M%S")
        path = self.outbox / f"{stamp}_{kind}.txt"
        path.write_text(f"[DRY-RUN, not sent] {kind}: {text}\n", encoding="utf-8")
        return path

    def heartbeat(self, when: dt.datetime) -> Path:
        return self.send("heartbeat", "recorder alive", when)
