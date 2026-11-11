#!/usr/bin/env python3
"""Statistical power (MISSION V11 §8.2). First version (T04); T10 makes SE_block come from data.

MDE = (z(1 - a*/2) + z(power)) * SE_block, with a* = family alpha / TRIALS_MAX.
Before REAL data, SE_block = sigma / sqrt(N) * sqrt(design_effect), where sigma (the standard
deviation of net P&L per trade) is an ESTIMATE shown as a sensitivity table.

  power.py --table    print the MDE sensitivity table used by tools/economics.py
"""

from __future__ import annotations

import math
import sys
from statistics import NormalDist

FAMILY_ALPHA = 0.05
TRIALS_MAX = 50
POWER = 0.8


def factor(trials_max: int = TRIALS_MAX, alpha: float = FAMILY_ALPHA, power: float = POWER) -> float:
    """(z(1 - a*/2) + z(power)); about 4.13 at TRIALS_MAX = 50, 2.80 for one test."""
    a_star = alpha / trials_max
    z = NormalDist().inv_cdf
    return z(1 - a_star / 2) + z(power)


def se_block(sigma: float, n: int, design_effect: float = 1.0) -> float:
    if n <= 0:
        raise ValueError("n must be positive")
    return sigma / math.sqrt(n) * math.sqrt(design_effect)


def mde(sigma: float, n: int, trials_max: int = TRIALS_MAX, design_effect: float = 1.0) -> float:
    """Minimum detectable mean net P&L per trade (same unit as sigma)."""
    return factor(trials_max) * se_block(sigma, n, design_effect)


def main(argv: list[str]) -> int:
    if argv != ["--table"]:
        print(__doc__, file=sys.stderr)
        return 64
    print(f"factor at TRIALS_MAX={TRIALS_MAX}: {factor():.3f}; single test: {factor(1):.3f}")
    for sigma in (500, 1000, 1500):
        row = ", ".join(f"N={n}: {mde(sigma, n):.0f}" for n in (150, 288, 480))
        print(f"sigma {sigma}: {row}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
