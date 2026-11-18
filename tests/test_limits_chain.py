"""MISSION V19 RULES K1 / K3 (from V11 T06): one source of risk limits, the chain, fixed rupees across the balance
band, LIVE_POSSIBLE, lot size only from the instrument file, and the banned old limit name."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from bot.limits import ABS_MAX_LOTS, InvalidLimits, derive_day_limits, load_limits

ROOT = Path(__file__).resolve().parents[1]
LIMITS = ROOT / "limits.toml"
BANNED_NAME = "LOSS_" + "FLOOR"  # the V10 name meant an amount in some places and an equity level in others


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout  # noqa: S607
    return [p for p in out.splitlines() if (ROOT / p).is_file()]


def with_value(tmp: Path, name: str, value: int) -> Path:
    text = LIMITS.read_text(encoding="utf-8")
    block = re.compile(rf"(\[{name}\]\nvalue = )\d+")
    assert block.search(text), name
    path = tmp / "limits.toml"
    path.write_text(block.sub(rf"\g<1>{value}", text, count=1), encoding="utf-8")
    return path


def test_the_chain_holds_on_the_real_file() -> None:
    lim = load_limits()
    assert 2 * lim.max_trade_loss_rs <= lim.max_drawdown_rs <= lim.max_total_loss_rs <= lim.capital_rs
    assert lim.equity_floor_rs == lim.capital_rs - lim.max_total_loss_rs
    assert lim.max_trade_loss_rs <= lim.daily_loss_lock_rs <= lim.weekly_loss_lock_rs <= lim.monthly_loss_lock_rs
    assert lim.monthly_loss_lock_rs <= lim.max_total_loss_rs
    assert lim.lots_cap == min(lim.max_lots, ABS_MAX_LOTS) == 1
    assert lim.cooloff_min >= 15
    if not lim.live_possible:
        assert lim.min_live_balance_rs is None and lim.max_balance_rs is None


def test_equity_floor_that_is_not_capital_minus_total_loss_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidLimits, match="EQUITY_FLOOR_RS"):
        load_limits(with_value(tmp_path, "EQUITY_FLOOR_RS", 10_000))


def test_a_trade_loss_above_half_the_drawdown_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidLimits):
        load_limits(with_value(tmp_path, "MAX_TRADE_LOSS_RS", load_limits().max_drawdown_rs))


def test_every_rupee_limit_is_fixed_across_five_balances() -> None:
    lim = load_limits()
    top = lim.max_balance_rs or 200_000
    low = lim.min_live_balance_rs or lim.max_total_loss_rs
    seen = set()
    for b in (low + (top - low) * k // 4 for k in range(5)):
        day = derive_day_limits(lim, b)
        assert day.equity_floor_rs == b - day.max_total_loss_rs
        seen.add(
            (day.max_trade_loss_rs, day.max_drawdown_rs, day.max_total_loss_rs, day.daily_loss_lock_rs,
             day.weekly_loss_lock_rs, day.monthly_loss_lock_rs)
        )  # fmt: skip
    assert len(seen) == 1, "a larger balance must never scale a rupee limit"


def test_a_balance_below_the_total_loss_is_refused() -> None:
    lim = load_limits()
    with pytest.raises(InvalidLimits):
        derive_day_limits(lim, lim.max_total_loss_rs - 1)


def test_live_possible_needs_a_band_and_false_forbids_one(tmp_path: Path) -> None:
    text = LIMITS.read_text(encoding="utf-8")
    flipped = tmp_path / "flip.toml"
    flipped.write_text(re.sub(r"(\[LIVE_POSSIBLE\]\nvalue = )\w+", r"\g<1>true", text, count=1), encoding="utf-8")
    band = tmp_path / "band.toml"
    band.write_text(re.sub(r"(\[LIVE_POSSIBLE\]\nvalue = )\w+", r"\g<1>false", text, count=1)
                    + "\n[MIN_LIVE_BALANCE_RS]\nvalue = 200000\n", encoding="utf-8")  # fmt: skip
    for path in (flipped, band) if not load_limits().live_possible else (band,):
        with pytest.raises(InvalidLimits, match="LIVE_POSSIBLE"):
            load_limits(path)


def test_a_cooloff_below_15_minutes_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidLimits, match="COOLOFF_MIN"):
        load_limits(with_value(tmp_path, "COOLOFF_MIN", 10))


def test_risk_limits_have_one_source() -> None:
    names = [k for k in tomllib.loads(LIMITS.read_text(encoding="utf-8")) if k.isupper()]
    assign = re.compile(rf"\b({'|'.join(names)})\s*[:=]\s*[-0-9]")
    offenders = []
    for rel in tracked_files():
        if rel == "limits.toml" or not rel.endswith((".py", ".toml", ".go")) or rel.startswith(("archive/", "docs/")):
            continue
        for n, line in enumerate((ROOT / rel).read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if assign.search(line):
                offenders.append(f"{rel}:{n}")
    assert offenders == [], "a second source of a risk limit (only ABS_MAX_LOTS is exempt, by name)"
    hard = [str(p) for p in (ROOT / "src").rglob("*.py") if re.search(r"Limits\(\s*\d", p.read_text(encoding="utf-8"))]
    assert hard == [], "every bot module (the entry point included) takes its limits from limits.toml"


def test_lot_size_never_comes_from_code() -> None:
    offenders = []
    for rel in tracked_files():
        if rel.startswith("src/") and rel.endswith(".py"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            offenders += [f"{rel}:{m.start()}" for m in re.finditer(r"\.lot\b(?!_)", text)]
    assert offenders == []


def test_the_banned_limit_name_appears_nowhere() -> None:
    hits = [
        rel
        for rel in tracked_files()
        if not rel.startswith("archive/")
        and rel not in ("MISSION.md", "MISSION_V19.md")  # the mission inputs that state the ban
        and not rel.startswith("docs/00_input/")
        and BANNED_NAME in (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    ]
    assert hits == []
