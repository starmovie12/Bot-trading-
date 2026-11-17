"""tools/check_pins.py: a pinned file that changes without a PIN BUMP is caught (MISSION V19 C3)."""

from __future__ import annotations

import shutil
from pathlib import Path

from tools import check_pins

ROOT = Path(__file__).resolve().parents[1]


def _copy(tmp: Path) -> Path:
    for rel in check_pins.PINNED:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp / rel)
    (tmp / "config").mkdir(exist_ok=True)
    check_pins.write(tmp)
    return tmp


def test_the_repo_pins_match() -> None:
    assert check_pins.problems() == []


def test_a_changed_pinned_file_is_caught(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    assert check_pins.problems(root) == []
    (root / "limits.toml").write_text((root / "limits.toml").read_text() + "\n# loosened\n")
    assert check_pins.problems(root) == ["limits.toml: sha256 differs from config/PINS.sha256"]


def test_a_missing_pin_line_is_caught(tmp_path: Path) -> None:
    root = _copy(tmp_path)
    lines = (root / "config/PINS.sha256").read_text().splitlines()
    (root / "config/PINS.sha256").write_text("\n".join(x for x in lines if "gates.toml" not in x) + "\n")
    assert "gates.toml: not pinned" in check_pins.problems(root)
