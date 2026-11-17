#!/usr/bin/env python3
"""Read-only check of the owner's recording against RECORDER_SPEC.md (MISSION V19 R9): content, never file names.

  check_recording.py FILE... [--session HH:MM-HH:MM]   PASS / FAIL per MUST item per day; exit 1 when a day fails
Reads csv, csv.gz, jsonl, parquet (needs pyarrow) and zip archives of those; other column names via ALIASES.
"""

import csv
import datetime as dt
import gzip
import io
import itertools
import json
import statistics
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

Row = dict[str, Any]
IST = dt.timedelta(hours=5, minutes=30)
STEP_S, GAP_SHARE_MAX, ROW_SHARE_MIN, STRIKES_PER_SIDE = 60, 0.02, 0.95, 11
# alias=field pairs: other column names the checker accepts for the same field (RECORDER_SPEC.md A.1)
_ALIASES = (
    "timestamp=ts_recv ts=ts_recv time=ts_recv recv_ts=ts_recv ts_received=ts_recv instrument=instrument_key"
    " key=instrument_key symbol=instrument_key tradingsymbol=instrument_key option_type=type opt_type=type"
    " right=type instrument_type=type best_bid=bid bid_price=bid best_ask=ask ask_price=ask bid_quantity=bid_qty"
    " bq=bid_qty ask_quantity=ask_qty aq=ask_qty last_price=ltp last=ltp open_interest=oi vol=volume vtt=volume"
    " strike_price=strike expiry_date=expiry status=event event_type=event"
)
REVERSE = dict(pair.split("=") for pair in _ALIASES.split())
FIELDS = {
    "index": ("ltp",),
    "future": ("bid", "ask", "bid_qty", "ask_qty", "ltp", "volume", "oi"),
    "option": ("instrument_key", "strike", "expiry", "type", "bid", "ask", "bid_qty", "ask_qty", "ltp", "volume", "oi"),
    "vix": ("ltp",),
}
STATUS, CONNECTION = (
    {"open", "close", "pre-open", "preopen", "halt", "special"},
    {"connect", "disconnect", "reconnect", "error"},
)


def read_any(name: str, data: bytes) -> list[Row]:
    if name.endswith(".gz"):
        name, data = name[:-3], gzip.decompress(data)
    if name.endswith(".csv"):
        return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    if name.endswith(".jsonl"):
        return [json.loads(x) for x in data.decode("utf-8").splitlines() if x.strip()]
    if name.endswith(".parquet"):
        import pyarrow.parquet as pq  # type: ignore[import-not-found, import-untyped, unused-ignore]  # noqa: PLC0415

        return list(pq.read_table(io.BytesIO(data)).to_pylist())
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            return [r for m in z.namelist() for r in read_any(m, z.read(m))]
    return []  # sha256, manifest, master and gaps files are not rows


def normalize(raw: Row) -> Row:
    row = {REVERSE.get(str(k).strip().lower(), str(k).strip().lower()): v for k, v in raw.items()}
    t = row.get("ts_recv")
    try:
        row["_t"] = t if isinstance(t, dt.datetime) else dt.datetime.fromisoformat(str(t))
    except ValueError:
        row["_t"] = None
    return row


def kind(r: Row) -> str:
    key, typ = str(r.get("instrument_key") or "").upper(), str(r.get("type") or "").upper()
    if r.get("event"):
        return "event"
    if typ in ("CE", "PE") and r.get("strike") not in (None, ""):
        return "option"
    if "VIX" in key:
        return "vix"
    if typ == "FUT" or "FUT" in key:
        return "future"
    return "index" if "BANK" in key else "other"


def complete(rows: list[Row], fields: tuple[str, ...]) -> tuple[bool, str]:
    ok = sum(all(r.get(f) not in (None, "") for f in fields) for r in rows)
    return bool(rows) and ok / len(rows) >= ROW_SHARE_MIN, f"{ok}/{len(rows)} rows complete"


def check_day(day: dt.date, rows: list[Row], session: tuple[dt.time, dt.time]) -> list[tuple[str, bool, str]]:
    out: list[tuple[str, bool, str]] = []
    bad_ts = sum(r["_t"] is None or r["_t"].utcoffset() != IST for r in rows)
    out.append(("A.2 ts_recv is IST +05:30", bad_ts == 0, f"{bad_ts} bad timestamps"))
    snaps = sorted({r["_t"] for r in rows if r["_t"] is not None and r["_t"].utcoffset() == IST})
    tz = dt.timezone(IST)
    start, end = (dt.datetime.combine(day, t, tz) for t in session)
    pairs = [(start, snaps[0]), *itertools.pairwise(snaps), (snaps[-1], end)] if snaps else []
    gaps = sum(max(0.0, (b - a).total_seconds() - STEP_S) for a, b in pairs)
    share = gaps / max(60.0, (end - start).total_seconds())
    out.append(
        (
            "A.2/A.4 snapshots <= 60 s apart, gaps <= 2% of the session",
            bool(snaps) and share <= GAP_SHARE_MAX,
            f"gaps {share:.1%}, {len(snaps)} snapshots",
        )
    )
    by_kind: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        by_kind[kind(r)].append(r)
    for k, fields in FIELDS.items():
        ok, ev = complete(by_kind[k], fields)
        out.append((f"A.3 {k}: {', '.join(fields)}", ok, ev))
    per_snap: dict[tuple[Any, str], set[str]] = defaultdict(set)
    for r in by_kind["option"]:
        per_snap[(r["_t"], str(r["type"]).upper())].add(str(r["strike"]))
    width = statistics.median(len(s) for s in per_snap.values()) if per_snap else 0
    out.append(("A.3 options ATM +- 5 (11 strikes per CE / PE)", width >= STRIKES_PER_SIDE, f"median {width} strikes"))
    events = {str(r["event"]).strip().lower() for r in by_kind["event"]}
    out.append(("A.3 market-status events", bool(events & STATUS), ", ".join(sorted(events & STATUS)) or "none"))
    out.append(("A.3 connection events", bool(events & CONNECTION), ", ".join(sorted(events & CONNECTION)) or "none"))
    return out


def main(argv: list[str]) -> int:
    session = (dt.time(9, 15), dt.time(15, 30))
    if "--session" in argv:
        i = argv.index("--session")
        a, b = argv[i + 1].split("-")
        session = (dt.time.fromisoformat(a), dt.time.fromisoformat(b))
        argv = argv[:i] + argv[i + 2 :]
    if not argv:
        print(__doc__, file=sys.stderr)
        return 64
    rows = [normalize(r) for f in argv for r in read_any(f.lower(), Path(f).read_bytes())]
    days: dict[dt.date, list[Row]] = defaultdict(list)
    for r in rows:
        days[r["_t"].date() if r["_t"] is not None else dt.date.min].append(r)
    failed = 0 if days else 1
    for day, day_rows in sorted(days.items()):
        results = check_day(day, day_rows, session)
        for item, ok, ev in results:
            print(f"{'PASS' if ok else 'FAIL'} {day} {item} ({ev})")
        failed += not all(ok for _, ok, _ in results)
    print(f"{len(days)} day(s), {failed} failed" if days else "FAIL no rows found")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
