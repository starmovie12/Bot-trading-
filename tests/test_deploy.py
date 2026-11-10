"""Deploy units: restart-loop nahi, ExecStart ka module maujood, sirf paper (open problem 7)."""

from __future__ import annotations

import configparser
import re
from pathlib import Path

import pytest

from bot.__main__ import check, main

ROOT = Path(__file__).resolve().parents[1]


def unit(name: str) -> configparser.RawConfigParser:
    cp = configparser.RawConfigParser(strict=False)
    cp.optionxform = str  # type: ignore[assignment,method-assign]
    cp.read_string(re.sub(r"(?m)^\s*#.*$", "", (ROOT / "deploy" / name).read_text()))
    return cp


@pytest.mark.parametrize("name", ["bot.service", "pehredaar.service"])
def test_no_restart_loop_for_programs_that_exit(name: str) -> None:
    u = unit(name)
    s = u["Service"]
    # Jo program turant band hota hai usmein Restart=always = har kuch second mein loop (pehle ka bug)
    assert s.get("Restart", "no") != "always"
    assert s.get("Type") == "oneshot"
    assert u["Unit"].get("StartLimitBurst")


def test_bot_service_runs_existing_dry_run_entrypoint() -> None:
    s = unit("bot.service")["Service"]
    assert s.get("ExecStart", "").endswith("-m bot --check")
    assert s.get("Environment") == "BOT_MODE=paper"
    assert (ROOT / "src" / "bot" / "__main__.py").exists()


def test_check_passes_in_paper_and_refuses_real(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(ROOT)
    assert check() == 0
    monkeypatch.setenv("BOT_MODE", "real")
    assert check() == 1
    assert main([]) == 2
