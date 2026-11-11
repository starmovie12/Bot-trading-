"""T10 harness core on SYNTHETIC trade lists (MISSION V11 §8.2): machinery only (tag SIM), never an edge.

Negative controls: a random-entry strategy, a look-ahead feature and a zero-cost run must each FAIL; a gates
file weaker than the floors is rejected; a second holdout open is refused.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from tools import truth_tests as tt

ROOT = Path(__file__).resolve().parents[1]
GATES = tomllib.loads((ROOT / "gates.toml").read_text())
FLOORS = tomllib.loads((ROOT / "tools/floors_baseline.toml").read_text())


def synthetic_trades(
    mean: float, sd: float, days: int, per_day: int, seed: int, charges: float = 48.0
) -> list[dict[str, Any]]:
    rng = random.Random(seed)  # noqa: S311 (simulation)
    start = dt.date(2026, 1, 1)
    return [
        {
            "day": str(start + dt.timedelta(days=d)),
            "net_rs": rng.gauss(mean, sd),
            "charges_rs": charges,
            "slippage_rs": 30.0,
        }
        for d in range(days)
        for _ in range(per_day)
    ]


def test_holm_matches_a_hand_example() -> None:
    assert tt.holm([0.01, 0.04, 0.03, 0.005], 0.05) == [True, False, False, True]


def test_the_block_ci_covers_the_true_mean_of_a_synthetic_series() -> None:
    lo, hi = tt.block_ci(synthetic_trades(100.0, 50.0, 130, 2, seed=1), 0.95)
    assert lo < 100.0 < hi


def test_a_random_entry_strategy_fails_the_harness() -> None:
    trades = synthetic_trades(-48.0, 600.0, 130, 2, seed=2)  # no edge: it pays its costs and nothing more
    null = [sum(t["net_rs"] for t in synthetic_trades(-48.0, 600.0, 130, 2, seed=100 + i)) for i in range(1000)]
    res = tt.evaluate(
        trades,
        GATES,
        hurdle_per_trade=40.0,
        null_totals=null,
        wf_fold_expectancies=[1, -1, 1, -1],
        perturbed_expectancies=[-1.0] * 10,
    )
    assert not res["pass"] and not res["ci_above_hurdle"] and not res["null_model"]


def test_a_zero_cost_run_fails_the_harness() -> None:
    trades = synthetic_trades(500.0, 50.0, 130, 2, seed=3, charges=0.0)
    res = tt.evaluate(trades, GATES, hurdle_per_trade=40.0)
    assert not res["costs"] and not res["pass"]


def centered_average(xs: Sequence[float]) -> list[float]:
    return [sum(xs[max(0, i - 1) : i + 2]) / len(xs[max(0, i - 1) : i + 2]) for i in range(len(xs))]


def trailing_average(xs: Sequence[float]) -> list[float]:
    return [sum(xs[max(0, i - 2) : i + 1]) / len(xs[max(0, i - 2) : i + 1]) for i in range(len(xs))]


def test_a_look_ahead_feature_fails_the_prefix_test_and_a_causal_one_passes() -> None:
    series = [float(x) for x in [5, 7, 6, 9, 8, 10, 12, 11]]
    assert not tt.lookahead_free(centered_average, series)
    assert tt.lookahead_free(trailing_average, series)


def test_gates_weaker_than_the_floors_are_rejected() -> None:
    assert tt.gates_problems(GATES, FLOORS) == []
    weak = json.loads(json.dumps(GATES))
    weak["min_trades"]["value"] = 100
    weak["null_p_max"]["value"] = 0.10
    assert len(tt.gates_problems(weak, FLOORS)) == 2


def test_a_second_holdout_open_is_refused(tmp_path: Path) -> None:
    h = tt.Holdout(tmp_path / "holdout_log.jsonl")
    h.seal(synthetic_trades(10.0, 5.0, 30, 1, seed=4), cutoff="2026-12-31")
    h.open()
    with pytest.raises(RuntimeError, match="second open"):
        h.open()


def test_walk_forward_folds_are_anchored_and_in_time_order() -> None:
    days = [str(dt.date(2026, 1, 1) + dt.timedelta(days=i)) for i in range(50)]
    folds = tt.walk_forward_folds(days, 4)
    assert len(folds) == 4
    for train, test in folds:
        assert train[0] == days[0] and max(train) < min(test)


def test_monte_carlo_is_reproducible_with_a_fixed_seed() -> None:
    trades = synthetic_trades(5.0, 300.0, 60, 1, seed=5)

    def run() -> dict[str, float]:
        return tt.monte_carlo(
            trades,
            paths=300,
            months=12,
            trades_per_month=12,
            capital=15000.0,
            equity_floor=10500.0,
            max_drawdown=2250.0,
        )

    assert run() == run()


def test_verdict_without_real_data_is_not_yet_and_a_g0_fail_fixture_is_stop(tmp_path: Path) -> None:
    out = subprocess.run([sys.executable, str(ROOT / "tools/verdict.py")], capture_output=True, text=True, check=True)  # noqa: S603
    assert out.stdout.startswith("NOT_YET(NO_DATA")
    fail = {"g0": "FAIL_ARITH", "members": {f"U{i}": {"outcome": "FAIL_ARITH"} for i in range(1, 7)}}
    fixture = tmp_path / "g0_fail.json"
    fixture.write_text(json.dumps(fail))
    out = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "tools/verdict.py"), "--g0", str(fixture)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == "STOP(G0_FAIL_ARITH)"
