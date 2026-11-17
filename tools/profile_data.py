#!/usr/bin/env python3
"""Profile the data repo snapshot (MISSION V19 Phase 1; DG re-runs it): per-day facts -> data/lab/data_profile.json.

  profile_data.py [REPO]   default data/banknifty/repo; prints a summary of at most 40 lines
Reads per day and per table (lab/data.py); BANKNIFTY only; other underlyings of a table are counted, never read.
"""

import collections
import csv
import datetime as dt
import itertools
import json
import statistics
import subprocess
import sys
from pathlib import Path

import pyarrow.compute as pc

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lab import data  # noqa: E402

COLS = ["instrument_key", "ts_open", "expiry_date", "strike", "option_type", "o", "h", "l", "c", "v", "oi", "is_stale"]


def bad_ticks(tb: object) -> int:
    """Rows with a non-positive price or a close / open outside [low, high]."""
    t = tb  # pyarrow Table
    bad = pc.or_(pc.less_equal(t["l"], 0), pc.greater(t["l"], t["h"]))  # type: ignore[index]
    bad = pc.or_(bad, pc.or_(pc.less(t["c"], t["l"]), pc.greater(t["c"], t["h"])))  # type: ignore[index]
    return int(pc.sum(pc.cast(bad, "int64")).as_py() or 0)


def weeks(repo: Path) -> list[Path]:
    """Week folders ordered by their first date (never by NN)."""
    return sorted(repo.glob("week_*"), key=lambda w: w.name.split("_")[2])


def quality(repo: Path, name: str, key: tuple[str, ...]) -> dict[tuple[str, ...], dict[str, str]]:
    """Cumulative quality file, de-duplicated on `key`; the newest folder's row wins."""
    out: dict[tuple[str, ...], dict[str, str]] = {}
    for w in weeks(repo):
        f = w / name
        if f.is_file():
            for r in csv.DictReader(f.open(encoding="utf-8")):
                if r.get("underlying", data.UNDERLYING) == data.UNDERLYING:
                    out[tuple(r[k] for k in key)] = r
    return out


def lots(repo: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    for w in weeks(repo):
        f = w / "BANKNIFTY" / "contracts.csv"
        if f.is_file():
            for r in csv.DictReader(f.open(encoding="utf-8")):
                out[r["expiry"]] = int(r["lot_size"])
    return out


def option_day(repo: Path, day: dt.date, spot_close: float | None) -> dict[str, object]:
    tb = data.read_day(repo, "options", day, columns=COLS)
    if tb.num_rows == 0:
        return {"rows": 0}
    expiries = sorted(set(tb["expiry_date"].to_pylist()))
    near = tb.filter(pc.equal(tb["expiry_date"], expiries[0]))
    strikes = sorted(set(near["strike"].to_pylist()))
    steps = [round(b - a, 2) for a, b in itertools.pairwise(strikes)]
    band = None
    if spot_close:
        band = [round(100 * (strikes[0] / spot_close - 1), 1), round(100 * (strikes[-1] / spot_close - 1), 1)]
    return {
        "rows": tb.num_rows,
        "contracts": len(set(tb["instrument_key"].to_pylist())),
        "expiries": [str(e) for e in expiries],
        "dte_near": (expiries[0] - day).days,
        "strike_step": statistics.mode(steps) if steps else None,
        "band_pct": band,
        "stale_share": round(float(pc.mean(pc.cast(tb["is_stale"], "int8")).as_py() or 0), 3),
        "bad_ticks": bad_ticks(tb),
    }


def profile(repo: Path) -> dict[str, object]:
    health = quality(repo, "health.csv", ("trading_date",))
    ready = quality(repo, "strategy_ready_days.csv", ("trading_date",))
    all_days = sorted({d for (t, u, d) in data.partitions(repo) if u == data.UNDERLYING})
    per_day = {}
    for day in all_days:
        row: dict[str, object] = {}
        for table in ("spot_1m", "fut_1m"):
            tb = data.read_day(repo, table, day, columns=["instrument_key", "ts_open", "o", "h", "l", "c", "v", "oi"])
            row[table] = {"bars": tb.num_rows, "bad_ticks": bad_ticks(tb) if tb.num_rows else 0}
            if tb.num_rows and table == "fut_1m":
                row[table]["contracts"] = len(set(tb["instrument_key"].to_pylist()))  # type: ignore[index]
                row[table]["best_contract_bars"] = max(collections.Counter(tb["instrument_key"].to_pylist()).values())  # type: ignore[index]
            if tb.num_rows and table == "spot_1m":
                ts = tb["ts_open"].to_pylist()
                row["session"] = [min(ts).strftime("%H:%M"), max(ts).strftime("%H:%M")]
                row["spot_close"] = tb["c"][-1].as_py()
        vix = data.read_day(repo, "vix_1m", day, underlying=data.VIX, columns=["instrument_key", "ts_open", "c"])
        row["vix_1m"] = {"bars": vix.num_rows}
        row["stocks"] = sum(bool(data.partitions(repo).get(("stock_1m", s, day))) for s in data.BANK_STOCKS)
        spot_close = row.get("spot_close")
        row["options"] = option_day(repo, day, spot_close if isinstance(spot_close, float) else None)
        h, r = health.get((str(day),), {}), ready.get((str(day),), {})
        row["health"] = {k: h.get(k) for k in ("status", "session_type", "bar_count", "expected_bars")}
        row["price_ready"] = r.get("PRICE_READY")
        per_day[str(day)] = row
    others = collections.Counter(
        u for (t, u, d) in data.partitions(repo) if t == "stock_1m" and u not in data.BANK_STOCKS
    )
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)  # noqa: S603, S607
    return {
        "data_sha": sha.stdout.strip(),
        "weeks": [w.name for w in weeks(repo)],
        "lots_by_expiry": lots(repo),
        "global_1m_underlyings": sorted({u for (t, u, d) in data.partitions(repo) if t == "global_1m"}),
        "non_bank_stock_days": dict(others),
        "days": per_day,
    }


def main(argv: list[str]) -> int:
    repo = Path(argv[0]) if argv else ROOT / "data/banknifty/repo"
    prof = profile(repo)
    out = ROOT / "data/lab/data_profile.json"
    out.write_text(json.dumps(prof, indent=1, default=str) + "\n", encoding="utf-8")
    days = prof["days"] if isinstance(prof["days"], dict) else {}
    n_weeks = len(prof["weeks"]) if isinstance(prof["weeks"], list) else 0
    print(f"DATA_SHA {prof['data_sha']} · weeks {n_weeks} · days {len(days)} ({min(days)}..{max(days)})")
    print(f"written {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
