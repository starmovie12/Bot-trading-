#!/usr/bin/env python3
"""Overfitting measures (owner order 5, D-49).

- pbo(m, blocks=16): Probability of Backtest Overfitting by Combinatorially Symmetric Cross-Validation (Bailey,
  Borwein, Lopez de Prado, Zhu). m = T periods x N configurations of per-period returns. The T rows are split into
  `blocks` contiguous blocks; for every choice of half the blocks as in-sample, the configuration with the best
  in-sample Sharpe is located in the out-of-sample ranking; omega = its OOS rank / (N + 1); lambda = ln(omega / (1 -
  omega)); PBO = the share of the splits with lambda <= 0 (the in-sample winner is at or below the OOS median).
- dsr(r, n_trials, sr_var): Deflated Sharpe Ratio (Bailey, Lopez de Prado 2014): P(true Sharpe > SR0), where SR0 is
  the expected maximum Sharpe of n_trials unskilled trials with Sharpe variance sr_var, corrected for the skewness and
  kurtosis of r. Sharpe ratios are per period (no annualising), as the formula requires.
"""

from __future__ import annotations

import itertools
import math
from statistics import NormalDist

import numpy as np

EULER = 0.5772156649015329
ND = NormalDist()


def sharpe(x: np.ndarray) -> float:
    sd = float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
    return float(np.mean(x)) / sd if sd > 0 else 0.0


def pbo(m: np.ndarray, blocks: int = 16) -> tuple[float, np.ndarray]:
    t, n = m.shape
    if n < 2 or t < blocks:
        raise ValueError("pbo needs >= 2 configurations and >= `blocks` periods")
    parts = np.array_split(np.arange(t), blocks)
    s1 = np.array([m[p].sum(axis=0) for p in parts])  # block sums, blocks x n
    s2 = np.array([(m[p] ** 2).sum(axis=0) for p in parts])
    cnt = np.array([len(p) for p in parts], dtype=float)

    def sr(sel: list[int]) -> np.ndarray:
        k = cnt[sel].sum()
        mu = s1[sel].sum(axis=0) / k
        var = (s2[sel].sum(axis=0) - k * mu**2) / (k - 1)
        return np.where(var > 0, mu / np.sqrt(np.maximum(var, 1e-300)), 0.0)

    logits = []
    allb = set(range(blocks))
    for ins in itertools.combinations(range(blocks), blocks // 2):
        oos = sorted(allb - set(ins))
        best = int(np.argmax(sr(list(ins))))
        perf = sr(oos)
        rank = 1 + int((perf < perf[best]).sum()) + 0.5 * int((perf == perf[best]).sum() - 1)
        omega = rank / (n + 1)
        logits.append(math.log(omega / (1 - omega)))
    lam = np.array(logits)
    return float(np.mean(lam <= 0)), lam


def expected_max_sr(n_trials: int, sr_var: float) -> float:
    if n_trials < 2 or sr_var <= 0:
        return 0.0
    a = ND.inv_cdf(1 - 1 / n_trials)
    b = ND.inv_cdf(1 - 1 / (n_trials * math.e))
    return math.sqrt(sr_var) * ((1 - EULER) * a + EULER * b)


def dsr(r: np.ndarray, n_trials: int, sr_var: float) -> float:
    t = len(r)
    if t < 3:
        return 0.0
    sr = sharpe(r)
    x = (r - r.mean()) / (r.std(ddof=0) or 1.0)
    g3, g4 = float(np.mean(x**3)), float(np.mean(x**4))
    sr0 = expected_max_sr(n_trials, sr_var)
    den = 1 - g3 * sr + (g4 - 1) / 4 * sr**2
    z = (sr - sr0) * math.sqrt(t - 1) / math.sqrt(den) if den > 0 else -math.inf
    return ND.cdf(z) if math.isfinite(z) else 0.0
