"""I8 (MISSION V11 §7): the live path is OFF by default and cannot be switched on from this machine.

The live lock of FULL-B (config flag + env var + the owner's daily `arm`) does not exist yet; until then the
only mode is paper. The owner's environment variable LIVE_TRADING_ENABLED has no effect (DECISIONS D-006).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from bot.haath.orders import Limits, LiveTradingForbidden, OrderManager, PaperBroker
from bot.limits import load_limits

ROOT = Path(__file__).resolve().parents[2]


def run_bot(env_extra: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in ("BOT_MODE", "LIVE_TRADING_ENABLED")}
    env |= {"PYTHONPATH": str(ROOT / "src"), **env_extra}
    return subprocess.run([sys.executable, "-m", *args], cwd=ROOT, env=env, capture_output=True, text=True, check=False)  # noqa: S603


def test_real_mode_order_manager_is_forbidden() -> None:
    lim = load_limits()
    with pytest.raises(LiveTradingForbidden):
        OrderManager(
            PaperBroker(),
            Limits(lim.max_trade_loss_rs, lim.daily_loss_lock_rs, lim.max_total_loss_rs, lim.capital_rs),
            mode="real",
            clock=lambda: 0.0,
        )


def test_bot_mode_other_than_paper_is_refused() -> None:
    r = run_bot({"BOT_MODE": "live"}, "bot", "--check")
    assert r.returncode == 1 and "BOT_MODE" in r.stdout


@pytest.mark.parametrize("value", ["true", "1", "yes", "TRUE"])
def test_the_owners_live_trading_variable_has_no_effect(value: str) -> None:
    r = run_bot({"LIVE_TRADING_ENABLED": value}, "bot", "--check")
    assert r.returncode == 0 and r.stdout.startswith("OK: paper-only guard")
    assert "LIVE_TRADING_ENABLED" not in (ROOT / "src/bot/__main__.py").read_text()


def test_the_recorder_refuses_live() -> None:
    r = run_bot({}, "bot.recorder", "--live")
    assert r.returncode == 2 and r.stdout.startswith("REFUSED")
