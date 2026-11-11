"""Recorder MVP (MISSION V11 §10, T05): read-only market data -> 1-minute snapshots in a hash-chained journal.

Read-only: no order, no broker write. The adapter for the Upstox V3 feed (WebSocket + protobuf) is NOT built:
that schema is UNVERIFIED (docs/REGULATORY.md, row `market_feed`). This module records NORMALISED messages
(plain dicts, schema below) that a future adapter will produce; `synthetic_feed.py` produces the same shape.

Money is integer paise (I12); IV is integer basis points. Each record keeps the exchange AND the local
timestamp (I11). Feed-side guards: stale feed or a gap or a schema problem -> `entries_allowed()` is False
(I4, I13); exits are never blocked by the recorder. Storage: one append-only journal per IST day, gzip at the
day's end with a sha256 sidecar; a size cap with an alert at `alert_pct`; on a full disk the recorder stops and
alerts; nothing is ever deleted silently.
"""

from __future__ import annotations

import datetime as dt
import errno
import hashlib
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from bot.recorder.clock import IST_OFFSET_NS, ist_minute
from bot.recorder.journal import JournalCorrupt, JournalWriter, compress_day, read_journal

NS = 1_000_000_000
OPEN_MINUTE = 9 * 60 + 15  # 09:15 IST
SESSION_MINUTES = 375  # 09:15-15:30 IST
SCHEMA: dict[str, tuple[type, bool]] = {
    "key": (str, True),
    "exch_ts_ns": (int, True),
    "ltp_paise": (int, True),
    "vol": (int, True),
    "bid_paise": (int, False),
    "ask_paise": (int, False),
    "oi": (int, False),
    "iv_bp": (int, False),
    "iv_src": (str, False),
}
IV_SOURCES = ("feed", "computed")


class SchemaError(ValueError):
    """Unknown shape, wrong type or unknown enum: the feed is not trusted until it is fixed (I13)."""


def validate(msg: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """(clean message, warnings). An unknown field is logged and dropped; anything else wrong raises."""
    if not isinstance(msg, dict):
        raise SchemaError("message is not an object")
    clean: dict[str, Any] = {}
    for name, (kind, required) in SCHEMA.items():
        if name not in msg or msg[name] is None:
            if required:
                raise SchemaError(f"missing field {name}")
            continue
        value = msg[name]
        if isinstance(value, bool) or not isinstance(value, kind):
            raise SchemaError(f"field {name} has the wrong type")
        clean[name] = value
    if "iv_src" in clean and clean["iv_src"] not in IV_SOURCES:
        raise SchemaError("unknown iv_src value")
    warnings = [f"unknown field {k} dropped" for k in sorted(set(msg) - set(SCHEMA))]
    return clean, warnings


@dataclass(frozen=True, slots=True)
class Alert:
    kind: str
    detail: str
    ts_ns: int


@dataclass(frozen=True, slots=True)
class RecorderConfig:
    data_dir: Path
    size_cap_bytes: int
    scope: str = "LIGHT"
    alert_pct: int = 80
    max_stale_s: int = 120
    max_drift_s: int = 2

    @classmethod
    def load(cls, path: Path, root: Path) -> RecorderConfig:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        return cls(
            data_dir=root / str(raw["data_dir"]),
            size_cap_bytes=int(raw["size_cap_mb"]) * 1024 * 1024,
            scope=str(raw.get("scope", "LIGHT")),
            alert_pct=int(raw.get("alert_pct", 80)),
            max_stale_s=int(raw.get("max_stale_s", 120)),
            max_drift_s=int(raw.get("max_drift_s", 2)),
        )


class Writer(Protocol):
    def write(self, kind: str, ts_ns: int, data: dict[str, Any]) -> int: ...

    def close(self) -> None: ...


@dataclass
class FeedGuard:
    """Feed-side invariants: I4 (stale / gap -> no new entries), I11 (clock drift), I13 (schema)."""

    max_stale_s: int
    max_drift_s: int
    last_local_ns: int = 0
    schema_ok: bool = True
    drift_ok: bool = True
    gap_open: bool = False

    def seen(self, local_ns: int, exch_ns: int) -> None:
        self.last_local_ns = max(self.last_local_ns, local_ns)
        self.drift_ok = abs(local_ns - exch_ns) <= self.max_drift_s * NS

    def stale(self, now_ns: int) -> bool:
        return self.last_local_ns == 0 or now_ns - self.last_local_ns > self.max_stale_s * NS

    def entries_allowed(self, now_ns: int) -> bool:
        return self.schema_ok and self.drift_ok and not self.gap_open and not self.stale(now_ns)


def ist_date(ts_ns: int) -> dt.date:
    return dt.datetime.fromtimestamp((ts_ns + IST_OFFSET_NS) // NS, tz=dt.UTC).date()


def dir_bytes(folder: Path) -> int:
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else 0


@dataclass
class SnapshotRecorder:
    """Keeps the latest message per instrument in the current minute and writes one snapshot each."""

    cfg: RecorderConfig
    dry_run: bool = False
    alert_sink: Callable[[Alert], None] | None = None
    writer_factory: Callable[[Path], Writer] = JournalWriter
    alerts: list[Alert] = field(default_factory=list)
    stopped: str = ""
    messages: int = 0
    written: int = 0
    late: int = 0
    _minute: int = -1
    _day: dt.date | None = None
    _buffer: dict[str, dict[str, Any]] = field(default_factory=dict)
    _writer: Writer | None = None
    _cap_alerted: bool = False
    guard: FeedGuard = field(init=False)

    def __post_init__(self) -> None:
        self.guard = FeedGuard(self.cfg.max_stale_s, self.cfg.max_drift_s)

    def _alert(self, kind: str, detail: str, ts_ns: int) -> None:
        a = Alert(kind, detail, ts_ns)
        self.alerts.append(a)
        if self.alert_sink is not None:
            self.alert_sink(a)

    def day_path(self, day: dt.date) -> Path:
        return self.cfg.data_dir / f"{day.isoformat()}.jsonl"

    def on_message(self, msg: dict[str, Any], local_ns: int) -> None:
        if self.stopped:
            return
        self.messages += 1
        try:
            clean, warnings = validate(msg)
        except SchemaError as e:
            self.guard.schema_ok = False
            self._alert("schema", str(e), local_ns)
            return
        for w in warnings:
            self._alert("schema_warning", w, local_ns)
        exch = int(clean["exch_ts_ns"])
        self.guard.seen(local_ns, exch)
        if not self.guard.drift_ok:
            # T07 bug A: a message with an untrustworthy exchange time is never recorded (it once split a day)
            self._alert("clock_drift", f"exchange vs local more than {self.cfg.max_drift_s} s: not recorded", local_ns)
            return
        day, minute = ist_date(exch), ist_minute(exch)
        if self._day == day and self._minute != -1 and minute < self._minute:
            self.late += 1  # a late message for a minute already written: never rewrite history
            return
        if self._day is not None and day != self._day:
            self.end_day()
        if self._minute not in (-1, minute):
            self.flush()
            if minute > self._last_flushed + 1 and self._last_flushed >= 0:
                self.guard.gap_open = True
                self._alert("gap", f"no data for minutes {self._last_flushed + 1}..{minute - 1}", local_ns)
            else:
                self.guard.gap_open = False
        self._day, self._minute = day, minute
        clean["local_ts_ns"] = local_ns
        self._buffer[str(clean["key"])] = clean

    _last_flushed: int = -1

    def flush(self) -> None:
        if not self._buffer or self._day is None or self.stopped:
            return
        rows = [self._buffer[k] for k in sorted(self._buffer)]
        self._buffer = {}
        self._last_flushed = self._minute
        if self.dry_run:
            return
        used = dir_bytes(self.cfg.data_dir)
        ts = int(rows[-1]["local_ts_ns"])
        if used >= self.cfg.size_cap_bytes:
            self.stopped = "size_cap"
            self._alert("size_cap_full", "size cap reached: recording stopped, nothing deleted", ts)
            return
        if used >= self.cfg.size_cap_bytes * self.cfg.alert_pct // 100 and not self._cap_alerted:
            self._cap_alerted = True
            self._alert("size_cap_80", f"{self.cfg.alert_pct}% of the size cap used", ts)
        if self._writer is None:
            path = self.day_path(self._day)
            if path.with_name(path.name + ".gz").exists():
                self._alert("day_already_sealed", f"{self._day} is sealed: late rows not written", ts)
                return
            self._writer = self.writer_factory(path)
        try:
            for row in rows:
                self._writer.write("snap", int(row["exch_ts_ns"]), row)
                self.written += 1
        except OSError as e:
            if e.errno != errno.ENOSPC:
                raise
            self.stopped = "disk_full"
            self._alert("disk_full", "disk full: recording stopped; the journal stays readable", ts)

    def end_day(self) -> Path | None:
        """Flush, close and seal (gzip + sha256 sidecar) the current day's journal."""
        self.flush()
        path = self.day_path(self._day) if self._day is not None else None
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        self._minute, self._last_flushed, self._day = -1, -1, None
        if path is None or self.dry_run or not path.is_file():
            return None
        if self.stopped == "disk_full":
            return path  # no space to gzip; the plain journal stays readable
        return seal_day(path)


def seal_day(path: Path) -> Path:
    target = path.with_name(path.name + ".gz")
    if target.exists():  # T07 bug A: never overwrite a sealed day
        raise FileExistsError(f"{target.name} already sealed")
    gz = compress_day(path)
    gz.with_name(gz.name + ".sha256").write_text(f"{hashlib.sha256(gz.read_bytes()).hexdigest()}  {gz.name}\n")
    return gz


def verify_day(gz: Path) -> bool:
    """True only when the sidecar checksum matches and the hash chain reads end to end."""
    side = gz.with_name(gz.name + ".sha256")
    if not side.is_file() or side.read_text().split()[0] != hashlib.sha256(gz.read_bytes()).hexdigest():
        return False
    try:
        sum(1 for _ in read_journal(gz))
    except (JournalCorrupt, OSError, EOFError):
        return False
    return True


def replay(path: Path) -> list[dict[str, Any]]:
    return [r.data for r in read_journal(path) if r.kind == "snap"]


def health(path: Path, keys: list[str], coverage_min: float = 0.99) -> dict[str, Any]:
    """One-line daily health: OK when >= 99% of the expected 1-minute snapshots exist and none repeats."""
    seen: dict[tuple[str, int], int] = {}
    for row in replay(path):
        m = ist_minute(int(row["exch_ts_ns"]))
        if OPEN_MINUTE <= m < OPEN_MINUTE + SESSION_MINUTES:
            seen[(str(row["key"]), m)] = seen.get((str(row["key"]), m), 0) + 1
    expected = len(keys) * SESSION_MINUTES
    present = sum(1 for k in keys for m in range(OPEN_MINUTE, OPEN_MINUTE + SESSION_MINUTES) if (k, m) in seen)
    duplicates = sum(1 for n in seen.values() if n > 1)
    coverage = present / expected if expected else 0.0
    ok = coverage >= coverage_min and duplicates == 0
    return {"ok": ok, "coverage": coverage, "missing": expected - present, "duplicates": duplicates}
