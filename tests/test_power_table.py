"""tools/power_table.py reproduces the self-test anchors of MISSION V19 Phase 2c."""

from tools import power_table as pt


def test_the_three_anchors() -> None:
    assert pt.trades_needed(1000, 15) == 34885
    assert pt.trades_needed(1000, 176) == 254
    assert pt.mde(1000, 30) == 511


def test_more_trades_lower_the_detectable_effect() -> None:
    assert pt.mde(1000, 100) < pt.mde(1000, 60) < pt.mde(1000, 30)
