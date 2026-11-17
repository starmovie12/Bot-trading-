"""tools/check_recording.py judges CONTENT (MISSION V19 R9, RECORDER_SPEC.md A.5)."""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from tools import check_recording as cr

SAMPLE = Path(__file__).resolve().parent / "fixtures" / "rec_sample_day.csv"
ONE_MINUTE = ["--session", "09:15-09:15"]


def _rows() -> list[dict[str, str]]:
    with SAMPLE.open() as f:
        return list(csv.DictReader(f))


def _write(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


def test_the_sample_day_passes() -> None:
    assert cr.main([str(SAMPLE), *ONE_MINUTE]) == 0


def test_missing_option_bid_ask_fails(tmp_path: Path) -> None:
    rows = _rows()
    for r in rows:
        if r["type"] in ("CE", "PE"):
            r["bid"] = r["ask"] = ""
    assert cr.main([str(_write(tmp_path / "rec.csv", rows)), *ONE_MINUTE]) == 1


def test_other_column_names_are_accepted(tmp_path: Path) -> None:
    rows = [
        {("timestamp" if k == "ts_recv" else "last_price" if k == "ltp" else k): v for k, v in r.items()}
        for r in _rows()
    ]
    assert cr.main([str(_write(tmp_path / "day1.csv", rows)), *ONE_MINUTE]) == 0


def test_a_timestamp_without_the_ist_offset_fails(tmp_path: Path) -> None:
    rows = _rows()
    rows[3]["ts_recv"] = rows[3]["ts_recv"].replace("+05:30", "")
    assert cr.main([str(_write(tmp_path / "rec.csv", rows)), *ONE_MINUTE]) == 1


def test_gaps_above_two_percent_of_the_session_fail(tmp_path: Path) -> None:
    late = [{**r, "ts_recv": r["ts_recv"].replace("09:15:00", "09:30:00")} for r in _rows()]
    path = _write(tmp_path / "rec.csv", _rows() + late)
    assert cr.main([str(path), "--session", "09:15-09:30"]) == 1


def test_a_zip_archive_is_read(tmp_path: Path) -> None:
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(SAMPLE, "rec_20261113.csv")
        z.writestr("rec_20261113.sha256", "0" * 64)
    assert cr.main([str(archive), *ONE_MINUTE]) == 0


def test_no_rows_fails(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("ts_recv,ltp\n")
    assert cr.main([str(empty)]) == 1
