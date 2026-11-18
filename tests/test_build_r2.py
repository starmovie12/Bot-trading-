"""lab/build_r2.index_exit (PLAN.md §PREREG-R2): hand-computed exits on a synthetic index path."""

import math

from lab.build_r2 import FF, index_exit

NAN = math.nan


def path(bars: dict[int, tuple[float, float]]) -> tuple[list[float], list[float]]:
    hi, lo = [NAN] * 385, [NAN] * 385
    for m, (h, low) in bars.items():
        hi[m], lo[m] = h, low
    return hi, lo


def test_stop_break_even_target_trail_time_and_force_flat() -> None:
    hi, lo = path({10: (101, 99), 11: (102, 90)})
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI1") == (11, "stop")
    hi, lo = path({10: (111, 99), 11: (105, 100)})
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI1") == (11, "breakeven")  # BE acts from the next minute
    hi, lo = path({10: (121, 95)})
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI1") == (10, "target")
    hi, lo = path({10: (121, 95), 11: (122, 110)})
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI2") == (11, "trail")  # best 121 -> stop 111 -> low 110
    hi, lo = path({10: (99, 79)})
    assert index_exit(hi, lo, 10, -1, 100.0, 10.0, "XI1") == (10, "target")  # a PE: down 2R
    hi, lo = path({10: (101, 99)})
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI1") == (129, "time")
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI2") == (FF, "force_flat")


def test_stop_wins_when_stop_and_target_share_a_minute() -> None:
    hi, lo = path({10: (125, 85)})
    assert index_exit(hi, lo, 10, 1, 100.0, 10.0, "XI1") == (10, "stop")
