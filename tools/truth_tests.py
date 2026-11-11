#!/usr/bin/env python3
"""Truth-test harness core (MISSION V11 §8.2, T10). Standard library only; works on trade lists.

A trade is a dict: {"day": "YYYY-MM-DD", "net_rs": float, "charges_rs": float, "slippage_rs": float}
(net after charges and slippage). The engine is wired to this harness in T14 (FULL-B). Results on
synthetic trades are SIM: they prove the machinery, never an edge.

Pieces: Holm correction, day-block bootstrap CI and SE, null-model p-value, anchored walk-forward folds,
parameter stability share, Monte Carlo of equity paths, a look-ahead prefix test, cost checks, the gates
vs floors check, and a hash-chained holdout log that refuses a second open.
"""

from __future__ import annotations

import hashlib
import json
import random
import statistics
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

Trade = dict[str, Any]


def holm(pvalues: Sequence[float], alpha: float) -> list[bool]:
    """Rejections (True = significant) in input order, Holm step-down at family level alpha."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    rejected = [False] * len(pvalues)
    for rank, i in enumerate(order):
        if pvalues[i] <= alpha / (len(pvalues) - rank):
            rejected[i] = True
        else:
            break
    return rejected


def by_day(trades: Sequence[Trade]) -> list[list[float]]:
    days: dict[str, list[float]] = {}
    for t in trades:
        days.setdefault(str(t["day"]), []).append(float(t["net_rs"]))
    return [days[d] for d in sorted(days)]


def bootstrap_means(trades: Sequence[Trade], n_boot: int, seed: int) -> list[float]:
    """Mean net per trade over day-block resamples (blocks = trading days)."""
    blocks = by_day(trades)
    rng = random.Random(seed)  # noqa: S311 (statistics, not security)
    means = []
    for _ in range(n_boot):
        sample = [x for _ in blocks for x in blocks[rng.randrange(len(blocks))]]
        means.append(statistics.fmean(sample))
    return means


def block_ci(trades: Sequence[Trade], level: float, n_boot: int = 2000, seed: int = 7) -> tuple[float, float]:
    means = sorted(bootstrap_means(trades, n_boot, seed))
    lo = means[int((1 - level) / 2 * n_boot)]
    hi = means[min(n_boot - 1, int((1 + level) / 2 * n_boot))]
    return lo, hi


def se_block(trades: Sequence[Trade], n_boot: int = 2000, seed: int = 7) -> float:
    return statistics.pstdev(bootstrap_means(trades, n_boot, seed))


def null_pvalue(strategy_total: float, null_totals: Sequence[float]) -> float:
    """One-sided p: share of null runs at least as good as the strategy (with the +1 correction)."""
    return (1 + sum(1 for x in null_totals if x >= strategy_total)) / (1 + len(null_totals))


def walk_forward_folds(days: Sequence[str], folds: int) -> list[tuple[list[str], list[str]]]:
    """Anchored folds: train on everything before each test window; the windows tile the last part."""
    ordered = sorted(set(days))
    size = len(ordered) // (folds + 1)
    return [(ordered[: size * (k + 1)], ordered[size * (k + 1) : size * (k + 2)]) for k in range(folds)]


def stability_share(perturbed_expectancies: Sequence[float]) -> float:
    return sum(1 for x in perturbed_expectancies if x > 0) / len(perturbed_expectancies)


def monte_carlo(
    trades: Sequence[Trade],
    *,
    paths: int,
    months: int,
    trades_per_month: int,
    capital: float,
    equity_floor: float,
    max_drawdown: float,
    seed: int = 11,
) -> dict[str, float]:
    """Day-block bootstrap of trades into equity paths; P(touch floor), P(hard kill), 95th-pct drawdown."""
    blocks = by_day(trades)
    rng = random.Random(seed)  # noqa: S311 (simulation, not security)
    touch = kill = 0
    drawdowns = []
    for _ in range(paths):
        equity = peak = capital
        worst = 0.0
        taken = 0
        hit_floor = hit_kill = False
        while taken < months * trades_per_month:
            for x in blocks[rng.randrange(len(blocks))]:
                equity += x
                peak = max(peak, equity)
                worst = max(worst, peak - equity)
                hit_floor |= equity <= equity_floor
                hit_kill |= peak - equity >= max_drawdown
                taken += 1
        touch += hit_floor
        kill += hit_kill
        drawdowns.append(worst)
    drawdowns.sort()
    return {"p_touch_floor": touch / paths, "p_hard_kill": kill / paths, "p95_drawdown": drawdowns[int(0.95 * paths)]}


def lookahead_free(feature: Callable[[Sequence[float]], list[float]], series: Sequence[float]) -> bool:
    """Prefix test: the value at i computed from series[: i + 1] must equal the value at i from the full series."""
    full = feature(series)
    return all(abs(feature(series[: i + 1])[i] - full[i]) < 1e-12 for i in range(len(series)))


def cost_problems(trades: Sequence[Trade]) -> list[str]:
    if not trades:
        return ["no trades"]
    if any(float(t.get("charges_rs", 0)) <= 0 for t in trades):
        return ["a trade without charges: a zero-cost run proves nothing"]
    return []


def gates_problems(gates: dict[str, Any], floors: dict[str, Any]) -> list[str]:
    """Every floor key must be in gates.toml with a value no weaker than the floor."""
    problems = []
    for key, floor in floors["floors"].items():
        row = gates.get(key)
        if not isinstance(row, dict) or "value" not in row:
            problems.append(f"gates.toml lacks {key}")
            continue
        value, direction = row["value"], floors["direction"][key]
        weaker = (
            (direction == "higher_is_tighter" and value < floor)
            or (direction == "lower_is_tighter" and value > floor)
            or (direction == "exact" and value != floor)
        )
        if weaker:
            problems.append(f"gates.toml {key} = {value} is weaker than the floor {floor}")
    return problems


def evaluate(
    trades: Sequence[Trade],
    gates: dict[str, Any],
    *,
    hurdle_per_trade: float,
    null_totals: Sequence[float] = (),
    wf_fold_expectancies: Sequence[float] = (),
    perturbed_expectancies: Sequence[float] = (),
) -> dict[str, Any]:
    """Floor-by-floor result. Missing inputs are FAIL (never assumed)."""
    g = {k: v["value"] for k, v in gates.items() if isinstance(v, dict) and "value" in v}
    res: dict[str, Any] = {}
    res["costs"] = not cost_problems(trades)
    days = len(by_day(trades)) if trades else 0
    res["min_data"] = len(trades) >= g["min_trades"] and days >= g["min_trading_days"]
    stressed = [
        {
            **t,
            "net_rs": float(t["net_rs"])
            - (g["cost_stress_charges_mult"] - 1) * float(t["charges_rs"])
            - (g["cost_stress_slippage_mult"] - 1) * float(t.get("slippage_rs", 0)),
        }
        for t in trades
    ]
    lo, _ = block_ci(stressed, g["ci_level"]) if trades else (float("-inf"), 0.0)
    res["ci_lower_stressed"] = lo
    res["ci_above_hurdle"] = lo > hurdle_per_trade
    total = sum(float(t["net_rs"]) for t in trades)
    res["null_model"] = (
        bool(null_totals)
        and len(null_totals) >= g["null_runs"]
        and (null_pvalue(total, null_totals) <= g["null_p_max"])
    )
    res["walk_forward"] = len(wf_fold_expectancies) >= g["wf_folds"] and (
        sum(1 for x in wf_fold_expectancies if x > 0) >= g["wf_positive_folds_min"]
    )
    res["stability"] = (
        bool(perturbed_expectancies) and stability_share(perturbed_expectancies) >= g["stability_positive_share_min"]
    )
    keys = ("costs", "min_data", "ci_above_hurdle", "null_model", "walk_forward", "stability")
    res["pass"] = all(res[k] for k in keys)
    return res


class Holdout:
    """The holdout is sealed (hash + date cutoff) once and opened once; the log is hash-chained."""

    def __init__(self, log: Path) -> None:
        self.log = log

    def _rows(self) -> list[dict[str, Any]]:
        if not self.log.is_file():
            return []
        return [json.loads(x) for x in self.log.read_text().splitlines() if x.strip()]

    def _append(self, row: dict[str, Any]) -> None:
        rows = self._rows()
        prev = hashlib.sha256(json.dumps(rows[-1], sort_keys=True).encode()).hexdigest() if rows else "0" * 64
        with self.log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({**row, "prev_hash": prev}, sort_keys=True) + "\n")

    def seal(self, trades: Sequence[Trade], cutoff: str) -> str:
        if any(r["event"] == "seal" for r in self._rows()):
            raise RuntimeError("the holdout is already sealed")
        digest = hashlib.sha256(json.dumps(sorted(trades, key=str), sort_keys=True).encode()).hexdigest()
        self._append({"event": "seal", "cutoff": cutoff, "sha256": digest})
        return digest

    def open(self) -> None:
        rows = self._rows()
        if not any(r["event"] == "seal" for r in rows):
            raise RuntimeError("no sealed holdout")
        if any(r["event"] == "open" for r in rows):
            raise RuntimeError("the holdout was already opened once: a second open is refused")
        self._append({"event": "open"})
