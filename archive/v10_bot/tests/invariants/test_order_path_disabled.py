"""I8 / T07 (MISSION V11 §7): the order path is disabled before FULL-B: no module talks to a broker's order
API, the only order module (the PAPER manager) has no network access, and the Recorder and the niyam
entry points cannot even import it."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
ORD = "ord" + "er"  # built from fragments: this file must not contain an order endpoint as text
ORDER_API = re.compile(rf"(?i)/v[23]/{ORD}/|(place|modify|cancel)_{ORD}|{ORD.capitalize()}Api")
NETWORK = {"socket", "http", "urllib", "requests", "httpx", "websockets", "aiohttp", "ssl"}


def test_no_source_file_names_a_broker_order_api() -> None:
    hits = [str(p) for p in SRC.rglob("*.py") if ORDER_API.search(p.read_text(encoding="utf-8"))]
    assert hits == []


def test_the_paper_order_manager_has_no_network_import() -> None:
    tree = ast.parse((SRC / "bot/haath/orders.py").read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert not names & NETWORK


def imported_modules(module: str) -> set[str]:
    code = f"import sys, {module}; print('\\n'.join(sorted(sys.modules)))"
    env = dict(os.environ, PYTHONPATH=str(SRC))
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True).stdout  # noqa: S603
    return set(out.split())


def test_order_modules_are_unreachable_from_the_recorder_and_niyam_entry_points() -> None:
    for entry in ("bot.recorder.__main__", "bot.niyam"):
        assert not {m for m in imported_modules(entry) if m.startswith("bot.haath")}, entry
