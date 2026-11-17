"""tools/data_gaps.py: G1-G5 verdicts on small synthetic inputs (MISSION V19 Phase 1 DG)."""

import datetime as dt
from typing import Any

from tools import data_gaps as dg


def _day(
    spot: int = 375, fut: int = 375, status: str = "OK", ready: str = "READY", rows: int = 30000
) -> dict[str, Any]:
    return {
        "spot_1m": {"bars": spot, "bad_ticks": 0},
        "fut_1m": {"bars": 2 * fut, "best_contract_bars": fut, "bad_ticks": 0},
        "vix_1m": {"bars": 375},
        "session": ["09:15", "15:29"],
        "options": {"rows": rows, "expiries": ["2026-11-23"], "band_pct": [-4.0, 4.0], "bad_ticks": 0},
        "health": {"status": status, "session_type": "NORMAL"},
        "price_ready": ready,
    }


def test_futures_have_385_bars_from_the_dated_session_change() -> None:
    assert dg.expected_bars("fut_1m", dt.date(2026, 8, 2)) == 375
    assert dg.expected_bars("fut_1m", dt.date(2026, 8, 3)) == 385
    assert dg.expected_bars("spot_1m", dt.date(2026, 8, 3)) == 375


def test_a_valid_day_needs_ok_complete_ready_and_options() -> None:
    status: dict[tuple[str, ...], str] = {("2026-11-12", "spot_1m"): "COMPLETE", ("2026-11-12", "opt_1m"): "COMPLETE"}
    assert dg.is_valid("2026-11-12", _day(), status)
    assert not dg.is_valid("2026-11-12", _day(status="NOT OK"), status)
    assert not dg.is_valid("2026-11-12", _day(ready="PARTIAL"), status)
    assert not dg.is_valid("2026-11-12", _day(rows=0), status)
    assert not dg.is_valid("2026-11-12", _day(), {**status, ("2026-11-12", "opt_1m"): "NOT_DOWNLOADED"})


def test_g1_names_folders_missing_from_the_index_and_bad_days() -> None:
    row = dg.g1({"week_01"}, {"week_01", "week_02"}, {"2026-11-12": _day(spot=0, status="NOT OK")}, None)
    assert row["verdict"] == "GAP" and row["folders_not_in_index"] == 1
    assert row["days_not_ok"] == {"2026-11-12": "MISSING_SPOT"}
    assert dg.g1({"w"}, {"w"}, {"2026-11-12": _day()}, {"2026-11-12"})["verdict"] == "OK"


def test_g2_flags_bar_counts_and_cross_copy_mismatches() -> None:
    ok = {"day": "2026-11-12", "store": 5, "ai_ready": 5, "csv": 5}
    assert dg.g2({"2026-11-12": _day(fut=385)}, [ok])["verdict"] == "OK"  # futures: 385 bars from 2026-08-03
    assert dg.g2({"2026-11-12": _day(fut=380)}, [])["verdict"] == "GAP"
    assert dg.g2({"2026-11-12": _day()}, [{"day": "x", "store": 5, "ai_ready": 4, "csv": 5}])["xcopy_mismatch"] == 1


def test_g3_flags_an_absent_nearest_expiry() -> None:
    days = {"2026-11-12": _day()}
    assert dg.g3(days, ["2026-11-23"], {}, 0)["verdict"] == "OK"
    assert dg.g3(days, ["2026-11-16", "2026-11-23"], {}, 0)["nearest_expiry_absent"] == ["2026-11-12"]


def test_g4_counts_only_the_current_regime_and_reports_the_shortfall() -> None:
    short = dg.g4(["2024-11-01", "2026-11-12"])
    assert short["valid_days"] == 1 and short["days_short"] == dg.ST6_MIN_DAYS - 1 and short["verdict"] == "GAP"
    days = [str(dt.date(2025, 1, 1) + dt.timedelta(days=i)) for i in range(dg.ST6_MIN_DAYS)]
    assert dg.g4(days)["verdict"] == "OK" and "days_short" not in dg.g4(days)


def test_g5_is_a_gap_while_any_table_is_not_had() -> None:
    assert dg.g5({"spot": "HAVE"})["verdict"] == "OK"
    assert dg.g5({"spot": "HAVE", "recorded bid / ask": "NONE"})["verdict"] == "GAP"
