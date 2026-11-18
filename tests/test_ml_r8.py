"""lab/ml_r8 (PLAN.md §PREREG-R8): the numpy models learn a planted signal; the day-rule sequencer obeys its grid."""

import numpy as np

from lab import ml_r8
from tools import lab_eval as le


def test_logistic_and_stumps_find_a_planted_signal() -> None:
    rng = np.random.default_rng(1)
    x = np.column_stack([np.ones(4000), rng.normal(size=(4000, 3))])
    y = (x[:, 1] + 0.3 * rng.normal(size=4000) > 0.5).astype(float)
    p1 = ml_r8.predict(ml_r8.logit(x, y), x, "M1")
    p2 = ml_r8.predict(ml_r8.stumps(x[:, 1:], y), x[:, 1:], "M2")
    for p in (p1, p2):
        assert p[y == 1].mean() > p[y == 0].mean() + 0.3


def trades(nets: list[float]) -> le.Trades:
    n = len(nets)
    z = np.zeros(n)
    a = np.array(nets, dtype=float)
    return le.Trades(
        np.arange(n),
        z.astype(int),
        np.arange(n) * 10,
        np.ones(n, int),
        np.arange(n) * 10,
        np.arange(n) * 10 + 5,
        a,
        z,
        z,
        a,
        a,
        np.full(n, 1000.0),
        z,
        z,
    )


def test_day_rules_cap_entries_and_stop_after_a_loss() -> None:
    tr = trades([100, -50, 100, 100, 100])
    idx = np.arange(5)
    assert list(ml_r8.seq(tr, idx, (2, False, 15))) == [0, 1]
    assert list(ml_r8.seq(tr, idx, (10, True, 15))) == [0, 1]  # the day stops after the first loss
    assert list(ml_r8.seq(tr, idx, (10, False, 15))) == [0, 1, 3, 4]  # cool-off 15 min after the loss at minute 15
