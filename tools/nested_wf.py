"""Nested walk-forward for program S3 (BANKNIFTY_STRATEGY_V3.md §13.4).

DESIGN days -> 5 chronological blocks (equal size, remainder in the last). Expanding window: train on blocks 1..k,
test on block k+1, k = 1..4 -> 4 OOS windows (blocks 2-5). For a fixed rule (T1-P) the OOS result is simply its
trades on blocks 2-5; for a grid, each window picks the best candidate on its training blocks only.
Every evaluation goes through `fit`, which the caller wires to the trial ledger (one row per fit, §13.2).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

N_BLOCKS = 5


@dataclass(frozen=True)
class Window:
    k: int  # 1..4: test block index (0-based block k)
    train: tuple[dt.date, ...]
    test: tuple[dt.date, ...]


def blocks(days: Sequence[dt.date], n: int = N_BLOCKS) -> list[tuple[dt.date, ...]]:
    ds = sorted(days)
    if len(set(ds)) != len(ds) or len(ds) < n:
        raise ValueError("days must be unique and at least one per block")
    size = len(ds) // n
    cuts = [i * size for i in range(n)] + [len(ds)]
    return [tuple(ds[cuts[i] : cuts[i + 1]]) for i in range(n)]


def windows(days: Sequence[dt.date], n: int = N_BLOCKS) -> list[Window]:
    b = blocks(days, n)
    return [Window(k, tuple(d for blk in b[:k] for d in blk), b[k]) for k in range(1, n)]


def oos_days(days: Sequence[dt.date], n: int = N_BLOCKS) -> tuple[dt.date, ...]:
    return tuple(d for w in windows(days, n) for d in w.test)


@dataclass
class Choice:
    window: int
    chosen: int
    train_scores: list[float]
    test: Any


def nested(
    days: Sequence[dt.date],
    candidates: Sequence[Any],
    fit: Callable[[Any, tuple[dt.date, ...], str], Any],
    score: Callable[[Any], float],
    n: int = N_BLOCKS,
) -> list[Choice]:
    """Per window: fit every candidate on train (role 'train:k'), pick the best score (first on ties),
    then fit the chosen one on the test block (role 'test:k'). Only training numbers drive the choice."""
    out = []
    for w in windows(days, n):
        scores = [float(score(fit(c, w.train, f"train:{w.k}"))) for c in candidates]
        best = max(range(len(candidates)), key=lambda i: (scores[i], -i))
        out.append(Choice(w.k, best, scores, fit(candidates[best], w.test, f"test:{w.k}")))
    return out
