#!/usr/bin/env python3
"""Statistical power (MISSION V11 §8.2). T04 first version; T10 adds SE_block from REAL trades (day blocks).

MDE = (z(1 - a*/2) + z(power)) * SE_block, with a* = family alpha / TRIALS_MAX.
Before REAL data, SE_block = sigma / sqrt(N) * sqrt(design_effect), where sigma (the standard
deviation of net P&L per trade) is an ESTIMATE shown as a sensitivity table.

  power.py --table    print the MDE sensitivity table used by tools/economics.py
"""

from __future__ import annotations

import math
import random
import statistics
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


def se_block_from_trades(trades_by_day: list[list[float]], n_boot: int = 2000, seed: int = 7) -> float:
    """Final form (T10): SE_block = the standard deviation of day-block bootstrap means of net per trade."""
    rng = random.Random(seed)  # noqa: S311 (statistics, not security)
    means = []
    for _ in range(n_boot):
        sample = [x for _ in trades_by_day for x in trades_by_day[rng.randrange(len(trades_by_day))]]
        means.append(statistics.fmean(sample))
    return statistics.pstdev(means)


def mde_from_trades(trades_by_day: list[list[float]], trials_max: int = TRIALS_MAX) -> float:
    return factor(trials_max) * se_block_from_trades(trades_by_day)


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
