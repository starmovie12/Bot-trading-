"""Recorder ke tests. Saara data NAKLI."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from bot.backtest.engine import BtConfig, DayData, run_day
from bot.recorder.journal import JournalCorrupt, JournalWriter, compress_day, read_journal
from bot.recorder.ticks import RecordedBook, candles_from_ticks, ist_minute

IST = timedelta(hours=5, minutes=30)


def ns(hh: int, mm: int, ss: int = 0, day: date = date(2026, 11, 11)) -> int:
    return int((datetime(day.year, day.month, day.day, hh, mm, ss, tzinfo=UTC) - IST).timestamp() * 1e9)


def test_write_read_roundtrip_and_reopen(tmp_path: Path) -> None:
    f = tmp_path / "2026-11-11" / "feed.jsonl"
    with JournalWriter(f, fsync_every=2) as w:
        assert w.write("tick", ns(9, 15), {"key": "N", "ltp": 100.0}) == 0
        assert w.write("tick", ns(9, 15, 30), {"key": "N", "ltp": 101.5}) == 1
    with JournalWriter(f) as w:  # dobara khola: chain wahin se aage
        assert w.write("tick", ns(9, 16), {"key": "N", "ltp": 99.0}) == 2
    recs = list(read_journal(f))
    assert [r.seq for r in recs] == [0, 1, 2] and recs[1].data["ltp"] == 101.5


def test_crash_partial_line_is_dropped_and_writer_continues(tmp_path: Path) -> None:
    f = tmp_path / "feed.jsonl"
    with JournalWriter(f) as w:
        w.write("tick", ns(9, 15), {"key": "N", "ltp": 100.0})
        w.write("tick", ns(9, 16), {"key": "N", "ltp": 101.0})
    with f.open("a", encoding="utf-8") as fh:
        fh.write('{"seq":2,"ts":1,"k":"tick","d":{"key":"N","lt')  # bijli gayi: adhuri line
    assert len(list(read_journal(f))) == 2
    with JournalWriter(f) as w:
        assert w.write("tick", ns(9, 17), {"key": "N", "ltp": 102.0}) == 2
    assert [r.data["ltp"] for r in read_journal(f)] == [100.0, 101.0, 102.0]


def test_tampering_in_middle_is_caught(tmp_path: Path) -> None:
    f = tmp_path / "feed.jsonl"
    with JournalWriter(f) as w:
        for i in range(3):
            w.write("tick", ns(9, 15 + i), {"key": "N", "ltp": 100.0 + i})
    lines = f.read_text().splitlines(keepends=True)
    lines[1] = lines[1].replace("101.0", "151.0")  # kisi ne daam badla
    f.write_text("".join(lines))
    with pytest.raises(JournalCorrupt):
        list(read_journal(f))
    lines2 = f.read_text().splitlines(keepends=True)
    f.write_text(lines2[0] + lines2[2])  # beech ki line gayab
    with pytest.raises(JournalCorrupt):
        list(read_journal(f))


def test_compress_day(tmp_path: Path) -> None:
    f = tmp_path / "feed.jsonl"
    with JournalWriter(f) as w:
        for i in range(50):
            w.write("tick", ns(9, 15, i), {"key": "N", "ltp": 100.0 + i})
    gz = compress_day(f)
    assert gz.name == "feed.jsonl.gz" and not f.exists()
    assert len(list(read_journal(gz))) == 50


def test_candles_from_ticks(tmp_path: Path) -> None:
    f = tmp_path / "feed.jsonl"
    with JournalWriter(f) as w:
        w.write("tick", ns(9, 10), {"key": "N", "ltp": 90.0})  # session se pehle: chhodo
        for s, px in ((5, 100.0), (20, 103.0), (40, 98.0), (59, 101.0)):
            w.write("tick", ns(9, 15, s), {"key": "N", "ltp": px})
        w.write("tick", ns(9, 16, 1), {"key": "N", "ltp": 102.0})
        w.write("tick", ns(9, 15, 30), {"key": "X", "ltp": 5.0})  # doosra instrument
    cs = candles_from_ticks(read_journal(f), "N")
    assert ist_minute(ns(9, 15)) == 555
    assert [(c.t, c.o, c.h, c.l, c.c) for c in cs] == [
        (555, 100.0, 103.0, 98.0, 101.0),
        (556, 102.0, 102.0, 102.0, 102.0),
    ]


def test_recorded_book_has_no_lookahead(tmp_path: Path) -> None:
    f = tmp_path / "feed.jsonl"
    with JournalWriter(f) as w:
        w.write("tick", ns(9, 20, 10), {"key": "CE25000", "ltp": 110.0, "bid": 109.5, "ask": 110.5, "oi": 90000})
        w.write("tick", ns(9, 20, 50), {"key": "CE25000", "ltp": 111.0, "bid": 110.5, "ask": 111.5, "oi": 90000})
        w.write("tick", ns(9, 25, 0), {"key": "CE25000", "ltp": 120.0, "bid": 119.5, "ask": 120.5, "oi": 95000})
    book = RecordedBook(read_journal(f), {"CE25000": (25000, "CE")})
    assert book.quote(9 * 60 + 19, 25000, "CE") is None  # pehle koi quote nahi
    assert book.quote(9 * 60 + 20, 25000, "CE") == (110.5, 111.5)  # minute ka aakhri quote
    assert book.quote(9 * 60 + 24, 25000, "CE") == (110.5, 111.5)  # 9:25 ka daam 9:24 par nahi dikhta
    assert book.quote(9 * 60 + 25, 25000, "CE") == (119.5, 120.5)
    assert [q.oi for q in book.chain(9 * 60 + 25, 25000.0)] == [95000]


def test_journal_to_backtest_end_to_end(tmp_path: Path) -> None:
    """Nakli trend din ke ticks -> journal -> candles + book -> backtest: chalna chahiye, lookahead nahi."""
    import math

    from tests.test_backtest import Book, make_day

    c1 = make_day("trend", 5)
    nakli = Book(c1)
    f = tmp_path / "feed.jsonl"
    keymap = {}
    with JournalWriter(f, fsync_every=5000) as w:
        for c in c1:
            hh, mm = divmod(c.t, 60)
            for j, px in enumerate((c.o, c.h, c.l, c.c)):
                w.write("tick", ns(hh, mm, j * 15), {"key": "NIFTY", "ltp": px})
            for q in nakli.chain(c.t, c.c):
                key = f"{q.opt}{q.strike}"
                keymap[key] = (q.strike, q.opt)
                w.write("tick", ns(hh, mm, 59), {"key": key, "ltp": q.ask, "bid": q.bid, "ask": q.ask, "oi": q.oi})
    cs = candles_from_ticks(read_journal(f), "NIFTY")
    assert len(cs) == 375 and math.isclose(cs[10].c, c1[10].c)
    book = RecordedBook(read_journal(f), keymap)
    d = DayData(date(2026, 11, 11), "Nifty50", cs, cs[0].o - 5, 40.0, lambda _m: (8, 10), lambda _m: 0.5, book)
    trades = run_day(d, BtConfig(capital=15000, daily_loss_limit=1500, kul_jeb_limit=4000), 15000)
    assert trades, "poore raaste se kam se kam ek trade (warna test bekaar)"
    for t in trades:
        assert t.entry_t >= t.signal_t + 5
