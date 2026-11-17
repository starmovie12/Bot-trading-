#!/usr/bin/env python3
"""Data-gap audit DG (MISSION V19 Phase 1 / 1b): rows G1-G5 -> results/data_gaps.json + docs/DATA_GAPS.md.

  data_gaps.py [--calendar FILE]   FILE = one exchange trading day (YYYY-MM-DD) per line; without it the run is
                                   CALENDAR_UNVERIFIED and uses the days of the de-duplicated quality files
Inputs: data/lab/data_profile.json (tools/profile_data.py; gitignored: daily prices) and the repo quality files.
"""

import csv
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import profile_data  # noqa: E402

REPO = ROOT / "data/banknifty/repo"
ST6_MIN_DAYS = 125
MONTHLY_ONLY_FROM = dt.date(2024, 11, 20)  # POINTER (SEBI rule; Phase 2 verifies): option P&L only from here
FUT_385_FROM = dt.date(2026, 8, 3)  # POINTER (pack): F&O to 15:40; REAL: 385 futures bars from this day
Row = dict[str, Any]


def expected_bars(table: str, day: dt.date) -> int:
    return 385 if table == "fut_1m" and day >= FUT_385_FROM else 375


def day_status(repo: Path) -> dict[tuple[str, ...], str]:
    rows = profile_data.quality(repo, "day_status.csv", ("trading_date", "table"))
    return {k: r["status"] for k, r in rows.items() if r["status"] != "NOT_YET_SERVED"}


def is_valid(day: str, info: Row, status: dict[tuple[str, ...], str]) -> bool:
    """Regular full session, health OK, every table COMPLETE, PRICE_READY = READY, option candles present."""
    tables = [s for (d, _), s in status.items() if d == day]
    return (
        info["health"].get("session_type") == "NORMAL"
        and info.get("session", [""])[0] == "09:15"
        and info["spot_1m"]["bars"] >= expected_bars("spot_1m", dt.date.fromisoformat(day))
        and info["health"].get("status") == "OK"
        and bool(tables)
        and all(s == "COMPLETE" for s in tables)
        and info.get("price_ready") == "READY"
        and info["options"].get("rows", 0) > 0
    )


def g1(index_weeks: set[str], folders: set[str], days: dict[str, Row], calendar: set[str] | None) -> Row:
    not_in_index, not_folder = sorted(folders - index_weeks), sorted(index_weeks - folders)
    bad = {
        d: "MISSING_SPOT" if not v["spot_1m"]["bars"] else f"{v['health'].get('status')} / {v.get('price_ready')}"
        for d, v in days.items()
        if v["health"].get("status") != "OK" or v.get("price_ready") != "READY"
    }
    missing = sorted(calendar - set(days)) if calendar is not None else []
    gap = bool(bad or missing)
    return {"verdict": "GAP" if gap else "OK", "index_lines": len(index_weeks), "week_folders": len(folders),
            "folders_not_in_index": len(not_in_index), "index_without_folder": not_folder, "days_present": len(days),
            "exchange_days_missing": missing, "days_not_ok": bad}  # fmt: skip


def g2(days: dict[str, Row], xcopy: list[Row]) -> Row:
    off = {}
    for d, v in days.items():
        if v["health"].get("session_type") != "NORMAL" or not v["options"].get("rows"):
            continue  # special sessions and no-F&O days are profiled by their own hours (G1), not here
        day = dt.date.fromisoformat(d)
        got = {
            "spot_1m": v["spot_1m"]["bars"],
            "fut_1m": v["fut_1m"].get("best_contract_bars"),
            "vix_1m": v["vix_1m"]["bars"],
        }
        diff = {t: n for t, n in got.items() if n != expected_bars(t, day)}
        if diff:
            off[d] = diff
    bad_ticks = sum(
        v["spot_1m"]["bad_ticks"] + v["fut_1m"]["bad_ticks"] + v["options"].get("bad_ticks", 0) for v in days.values()
    )
    mismatch = [x for x in xcopy if len({x["store"], x.get("ai_ready"), x.get("csv")} - {None}) > 1]
    gap = bool(off or bad_ticks or mismatch)
    return {"verdict": "GAP" if gap else "OK", "days_bars_off": off, "duplicates": 0, "bad_ticks": bad_ticks,
            "xcopy_sample_days": xcopy, "xcopy_mismatch": len(mismatch)}  # fmt: skip


def g3(days: dict[str, Row], expiries: list[str], status: dict[tuple[str, ...], str], no_candle: int) -> Row:
    narrow, no_near = {}, []
    for d, v in days.items():
        o = v["options"]
        if not o.get("rows"):
            continue
        near = min((e for e in expiries if e >= d), default=None)
        if near not in o.get("expiries", []):
            no_near.append(d)
        band = o.get("band_pct")
        if band and (band[0] > -2.0 or band[1] < 2.0):
            narrow[d] = band
    wide_missing = sorted(d for (d, t), s in status.items() if t == "opt_wide_1m" and s == "NOT_DOWNLOADED")
    gap = bool(no_near or wide_missing)
    return {"verdict": "GAP" if gap else "OK", "nearest_expiry_absent": no_near, "band_narrower_than_2pct": narrow,
            "opt_wide_not_downloaded": wide_missing, "contracts_without_candle": no_candle,
            "expiries_covered": len(expiries)}  # fmt: skip


def g4(valid: list[str]) -> Row:
    current = sorted(d for d in valid if d >= str(MONTHLY_ONLY_FROM))
    first, last = (dt.date.fromisoformat(current[0]), dt.date.fromisoformat(current[-1])) if current else (None, None)
    weeks = ((last - first).days + 1) / 7 if first and last else 0
    row: Row = {"verdict": "OK" if len(current) >= ST6_MIN_DAYS else "GAP", "valid_days": len(current),
                "valid_days_all": len(valid), "first_day": str(first), "last_day": str(last),
                "span_months": round(weeks * 7 / 30.44, 1),
                "valid_days_per_week": round(len(current) / weeks, 2) if weeks else 0,
                "regime_from": str(MONTHLY_ONLY_FROM)}  # fmt: skip
    if len(current) < ST6_MIN_DAYS:
        row["days_short"] = ST6_MIN_DAYS - len(current)
    return row


def g5(have: dict[str, str]) -> Row:
    return {"verdict": "GAP" if any(v != "HAVE" for v in have.values()) else "OK", "tables": have}


def xcopy_counts(repo: Path, days: dict[str, Row]) -> list[Row]:
    """Row counts of opt_1m + opt_wide_1m vs the ai_ready and csv copies on the checked-out sample days."""
    out = []
    for w in profile_data.weeks(repo):
        parquet = sorted(w.glob("ai_ready/**/BANKNIFTY_options_1m.parquet"))
        csvs = sorted(w.glob("BANKNIFTY/options_1m/*.csv"))
        if not parquet or not csvs:
            continue
        day = next(
            (
                d
                for d in sorted(days)
                if w.name.split("_")[2] <= d <= w.name.split("_")[4] and days[d]["options"].get("rows")
            ),
            None,
        )
        if day is None:
            continue
        ai = pq.read_table(parquet[0], columns=["trading_date"])
        n_ai = int(pc.sum(pc.cast(pc.equal(pc.cast(ai["trading_date"], "string"), day), "int64")).as_py() or 0)
        n_csv = sum(1 for f in csvs for line in f.open(encoding="utf-8") if line.startswith(day))
        out.append({"day": day, "store": days[day]["options"]["rows"], "ai_ready": n_ai, "csv": n_csv})
    return out


def run(calendar: set[str] | None) -> Row:
    prof = json.loads((ROOT / "data/lab/data_profile.json").read_text(encoding="utf-8"))
    days: dict[str, Row] = prof["days"]
    status = day_status(REPO)
    index = {
        line.split("|")[0].strip()
        for line in (REPO / "INDEX.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    folders = set(prof["weeks"])
    valid = sorted(d for d, v in days.items() if is_valid(d, v, status))
    contract_files = [w / "BANKNIFTY/contracts.csv" for w in profile_data.weeks(REPO)]
    no_candle = sum(
        int(r.get("minutes_with_data") or 0) == 0
        for f in contract_files
        if f.is_file()
        for r in csv.DictReader(f.open(encoding="utf-8"))
    )
    have = {"spot": "HAVE", "future": "HAVE", "vix": "HAVE", "options (both tables)": "PARTIAL" if any(
        s == "NOT_DOWNLOADED" for (d, t), s in status.items() if t == "opt_wide_1m") else "HAVE",
        "chain / IV / greeks": "HAVE", "constituents (12 banks)": "HAVE", "global indices": "PARTIAL",
        "exchange PCR / OI / FII-DII": "HAVE", "recorded bid / ask": "NONE"}  # fmt: skip
    return {
        "calendar": "2026 SOURCE, 2024-2025 DATA-DERIVED" if calendar is not None else "CALENDAR_UNVERIFIED",
        "data_sha": prof["data_sha"],
        "data_grade": "B",
        "valid_days_list": valid,
        "G1": g1(index, folders, days, calendar),
        "G2": g2(days, xcopy_counts(REPO, days)),
        "G3": g3(days, sorted(prof["lots_by_expiry"]), status, no_candle),
        "G4": g4(valid),
        "G5": g5(have),
    }


def main(argv: list[str]) -> int:
    calendar = None
    if "--calendar" in argv:
        path = Path(argv[argv.index("--calendar") + 1])
        calendar = {
            x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")
        }
    res = run(calendar)
    (ROOT / "results/data_gaps.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
    for g in ("G1", "G2", "G3", "G4", "G5"):
        print(
            g,
            res[g]["verdict"],
            {k: (v if not isinstance(v, (list, dict)) else len(v)) for k, v in res[g].items() if k != "verdict"},
        )
    print(res["calendar"], "· valid days", res["G4"]["valid_days"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
