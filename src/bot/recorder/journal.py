"""Append-only journal. Har line: JSON {seq, ts, k, d, h}. `h` = pichhli line ke hash + is line ka sha256 (16 hex).

- Crash par aakhri ADHURI line (newline nahi / JSON toota) chupchaap chhod di jaati hai: baaki data sahi.
- Beech mein koi line badli ya kati (hash chain toota) toh `JournalCorrupt`: aisa data backtest mein nahi jaayega.
- Din band hone ke baad `compress_day` gzip karta hai (disk ~10x kam); reader .gz bhi padhta hai.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

GENESIS = "0" * 16


class JournalCorrupt(RuntimeError):
    """Journal ke beech mein gadbad (hash chain toota)."""


@dataclass(frozen=True, slots=True)
class Record:
    seq: int
    ts_ns: int
    kind: str
    data: dict[str, Any]


def _payload(seq: int, ts_ns: int, kind: str, data: dict[str, Any]) -> str:
    return json.dumps(
        {"seq": seq, "ts": ts_ns, "k": kind, "d": data}, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _digest(prev: str, payload: str) -> str:
    return hashlib.sha256(f"{prev}\n{payload}".encode()).hexdigest()[:16]


def _open_text(path: Path) -> IO[str]:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def read_journal(path: Path) -> Iterator[Record]:
    """Line-by-line padhta hai (poori file memory mein nahi).

    Ek line aage dekh kar tay karta hai ki kharab line aakhri hai (crash) ya beech ki (gadbad).
    """
    prev = GENESIS
    expect = 0
    with _open_text(path) as fh:
        it = iter(fh)
        cur = next(it, None)
        no = 0
        while cur is not None:
            nxt = next(it, None)
            no += 1
            last = nxt is None
            if not cur.endswith("\n"):
                return  # crash wali adhuri aakhri line
            try:
                obj = json.loads(cur)
                rec = Record(int(obj["seq"]), int(obj["ts"]), str(obj["k"]), dict(obj["d"]))
                h = str(obj["h"])
            except (ValueError, KeyError, TypeError) as e:
                if last:
                    return  # aakhri line hi kharab: crash, chhod do
                raise JournalCorrupt(f"line {no}: padhi nahi ja saki") from e
            if rec.seq != expect or _digest(prev, _payload(rec.seq, rec.ts_ns, rec.kind, rec.data)) != h:
                raise JournalCorrupt(f"line {no}: hash/seq chain toota")
            prev, expect = h, expect + 1
            yield rec
            cur = nxt


class JournalWriter:
    def __init__(self, path: Path, *, fsync_every: int = 200) -> None:
        self.path = path
        self._fsync_every = max(1, fsync_every)
        self._prev = GENESIS
        self._seq = 0
        if path.exists():
            self._truncate_partial(path)
            for rec in read_journal(path):  # purani file: chain wahin se aage (gadbad ho toh JournalCorrupt)
                self._seq = rec.seq + 1
            self._prev = self._last_hash(path) if self._seq else GENESIS
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("a", encoding="utf-8")
        self._since_sync = 0

    @staticmethod
    def _tail(path: Path, size: int = 65536) -> bytes:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            end = fh.tell()
            fh.seek(max(0, end - size))
            return fh.read()

    @classmethod
    def _last_hash(cls, path: Path) -> str:
        lines = cls._tail(path).rstrip(b"\n").split(b"\n")
        return str(json.loads(lines[-1])["h"])

    @classmethod
    def _truncate_partial(cls, path: Path) -> None:
        """Crash ki adhuri aakhri line kaato (sirf file ka aakhri hissa padhta hai)."""
        tail = cls._tail(path)
        size = path.stat().st_size
        if not tail or tail.endswith(b"\n"):
            return
        cut = tail.rfind(b"\n") + 1
        with path.open("r+b") as fh:
            fh.truncate(size - len(tail) + cut)

    def write(self, kind: str, ts_ns: int, data: dict[str, Any]) -> int:
        payload = _payload(self._seq, ts_ns, kind, data)
        h = _digest(self._prev, payload)
        self._fh.write(payload[:-1] + f',"h":"{h}"}}\n')
        self._prev, seq = h, self._seq
        self._seq += 1
        self._since_sync += 1
        if self._since_sync >= self._fsync_every:
            self.sync()
        return seq

    def sync(self) -> None:
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._since_sync = 0

    def close(self) -> None:
        if not self._fh.closed:
            self.sync()
            self._fh.close()

    def __enter__(self) -> JournalWriter:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def compress_day(path: Path) -> Path:
    """Din band hone ke baad: file.jsonl -> file.jsonl.gz (pehle poori jaanch, phir purani file hatao)."""
    sum(1 for _ in read_journal(path))  # gadbad ho toh yahin ruk jao
    out = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as src, gzip.open(out, "wb", compresslevel=6) as dst:
        shutil.copyfileobj(src, dst)
    sum(1 for _ in read_journal(out))
    path.unlink()
    return out
