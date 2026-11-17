"""tools/webgrep.py keeps page text out of the context (MISSION V19 C7 rule 5)."""

from __future__ import annotations

from pathlib import Path

from tools import webgrep


def test_scripts_are_dropped_and_matches_printed(tmp_path: Path, capsys: object) -> None:
    page = tmp_path / "p.html"
    page.write_text("<html><script>var lot = 99;</script><p>Lot size</p><td>30</td><p>other</p></html>")
    assert webgrep.text_lines(page.read_text()) == ["Lot size", "30", "other"]
    assert webgrep.main([str(page), "lot size"]) == 0
    assert webgrep.main([str(page), "absent"]) == 1
