"""T06 (MISSION V11 §5.4, S1, S6, S11): one source of risk limits, the chain, lot size only from the
instrument file, and the banned old limit name."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from bot.limits import ABS_MAX_LOTS, InvalidLimits, load_limits

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
    assert lim.lots_cap == min(lim.max_lots, ABS_MAX_LOTS) == 1


def test_equity_floor_that_is_not_capital_minus_total_loss_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidLimits, match="EQUITY_FLOOR_RS"):
        load_limits(with_value(tmp_path, "EQUITY_FLOOR_RS", 10_000))


def test_a_trade_loss_above_half_the_drawdown_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidLimits):
        load_limits(with_value(tmp_path, "MAX_TRADE_LOSS_RS", 2_000))


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
    entry = (ROOT / "src/bot/__main__.py").read_text(encoding="utf-8")
    assert re.search(r"Limits\(\s*\d", entry) is None, "the entry point must take its limits from limits.toml"


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
        and rel != "MISSION.md"
        and not rel.startswith("docs/00_input/")
        and BANNED_NAME in (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    ]
    assert hits == []
