"""tools/overfit.py (owner order 5, D-49): PBO by CSCV and the Deflated Sharpe Ratio on synthetic data."""

import numpy as np

from tools import overfit


def test_pbo_is_high_on_noise_and_low_with_a_real_edge() -> None:
    runs = [overfit.pbo(np.random.default_rng(s).normal(size=(320, 40)), 16) for s in range(1, 9)]
    assert all(len(lam) == 12870 for _, lam in runs)
    assert 0.35 < float(np.mean([p for p, _ in runs])) < 0.65  # pure noise: PBO about 0.5 on average
    noise = np.random.default_rng(3).normal(size=(320, 40))
    edged = noise.copy()
    edged[:, 0] += 0.6  # one configuration with a steady edge
    p_edge, _ = overfit.pbo(edged, 16)
    assert p_edge < 0.05


def test_dsr_falls_as_trials_grow_and_separates_skill_from_noise() -> None:
    rng = np.random.default_rng(5)
    good = rng.normal(0.25, 1.0, 300)
    vals = [overfit.dsr(good, n, 0.01) for n in (1, 10, 100, 1000)]
    assert vals == sorted(vals, reverse=True) and vals[0] > 0.99
    noise = rng.normal(0.0, 1.0, 300)
    assert overfit.dsr(noise, 100, 0.01) < 0.5
    assert overfit.expected_max_sr(1, 0.01) == 0.0 and overfit.expected_max_sr(100, 0.01) > 0.2
