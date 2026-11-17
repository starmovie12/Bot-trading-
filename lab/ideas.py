"""Phase 3b bracket (MISSION V19 LAB): every idea is a mask over FEATURES rows + a direction per row + a structure.

Masks read only the decision row and earlier days (rolling statistics use prior days only), so no look-ahead.
The bracket (ids, rules, params) is pre-registered in PLAN.md §PREREG-0 before any trial runs (ST1).
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

A = dict[str, np.ndarray]


@dataclass(frozen=True)
class Idea:
    id: str
    text: str
    edge: str
    structure: str
    preset: str
    params: dict[str, float]
    rule: Callable[[A, dict[str, float]], tuple[np.ndarray, np.ndarray]]


def sign(x: np.ndarray) -> np.ndarray:
    return np.where(x >= 0, 1, -1)


def first30(f: A) -> np.ndarray:
    """Per row: the day's return from the prior close to 09:45 (known from 09:45 on; NaN before)."""
    out = np.full(len(f["t"]), np.nan)
    for d in np.unique(f["day_i"]):
        rows = np.nonzero(f["day_i"] == d)[0]
        at = rows[f["t"][rows] == 30]
        if len(at):
            r = (1 + f["gap"][at[0]]) * (1 + f["ret_open"][at[0]]) - 1
            out[rows[f["t"][rows] >= 30]] = r
    return out


def orb_retest(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    up = (f["day_hi"] > f["or15_hi"]) & (np.abs(f["spot"] / f["or15_hi"] - 1) <= p["near"]) & (f["ret15"] > 0)
    dn = (f["day_lo"] < f["or15_lo"]) & (np.abs(f["spot"] / f["or15_lo"] - 1) <= p["near"]) & (f["ret15"] < 0)
    return (f["t"] >= 30) & (up | dn), np.where(up, 1, -1)


def vwap_pullback(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    trend = (np.abs(f["ret_open"]) >= p["trend"]) & (f["eff"] >= p["eff"])
    m = trend & (np.abs(f["vwap_dist"]) <= p["near"]) & (f["t"] >= 45) & (f["t"] <= 255)
    return m, sign(f["ret_open"])


def afternoon_momentum(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    m = (f["t"] >= 255) & (np.abs(f["ret_open"]) >= p["move"]) & (sign(f["ret30"]) == sign(f["ret_open"]))
    return m, sign(f["ret_open"])


def fixed_time(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    return f["t"] == p["t"], sign(f["ret_open"])


def or30_break(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    up = (f["spot"] > f["or30_hi"]) & (f["ret15"] > 0)
    dn = (f["spot"] < f["or30_lo"]) & (f["ret15"] < 0)
    m = (f["t"] >= 30) & (f["eff"] >= p["eff"]) & (up | dn)
    if p.get("vix_falling", 0):
        m &= f["vix_chg"] < 0
    return m, np.where(up, 1, -1)


def vol_expansion(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    m = (f["rv5"] >= p["ratio"] * f["rv30"]) & (np.abs(f["ret15"]) >= p["move"]) & (f["t"] >= 30) & (f["t"] <= 300)
    return m, sign(f["ret15"])


def gap_fade(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    m = (np.abs(f["gap"]) >= p["gap"]) & (f["t"] >= 30) & (f["t"] <= 75) & (sign(f["ret15"]) == -sign(f["gap"]))
    return m, -sign(f["gap"])


def gap_go(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    beyond = np.where(f["gap"] > 0, f["spot"] > f["or15_hi"], f["spot"] < f["or15_lo"])
    m = (np.abs(f["gap"]) >= p["gap"]) & (f["t"] == 30) & (sign(f["ret_open"]) == sign(f["gap"])) & beyond
    return m, sign(f["gap"])


def vwap_revert(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    m = (f["eff"] <= p["eff"]) & (np.abs(f["vwap_dist"]) >= p["dist"]) & (f["t"] >= 75) & (f["t"] <= 270)
    return m, -sign(f["vwap_dist"])


def lead_lag(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    up = (f["hdfc15"] >= p["lead"]) & (f["icici15"] >= p["lead"]) & (f["ret15"] <= p["lag"])
    dn = (f["hdfc15"] <= -p["lead"]) & (f["icici15"] <= -p["lead"]) & (f["ret15"] >= -p["lag"])
    return (f["t"] >= 30) & (up | dn), np.where(up, 1, -1)


def last_hour(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    r = first30(f)
    return (f["t"] == p["t"]) & (np.abs(np.nan_to_num(r)) >= p["min"]), sign(np.nan_to_num(r))


def extreme_fade(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    at_hi = f["spot"] >= f["day_hi"] * (1 - p["near"])
    at_lo = f["spot"] <= f["day_lo"] * (1 + p["near"])
    m = (f["t"] >= 240) & (f["t"] <= 300) & (f["eff"] <= p["eff"]) & (at_hi ^ at_lo)
    return m, np.where(at_hi, -1, 1)


def trend_resume(f: A, p: dict[str, float]) -> tuple[np.ndarray, np.ndarray]:
    s = sign(f["ret_open"])
    m = (f["t"] >= 105) & (f["t"] <= 195) & (f["eff"] >= p["eff"]) & (sign(f["ret30"]) == -s) & (sign(f["ret15"]) == s)
    return m, s


L, E = "LONG", "EXIT0"
DIRECTION = "DIRECTION (weakest source)"
BRACKET = [
    Idea(
        "K1", "control: Dimaag S1 ORB break + retest of the 15-min range", DIRECTION, L, E, {"near": 0.001}, orb_retest
    ),
    Idea(
        "K2",
        "control: Dimaag S2 VWAP pullback on a trend day",
        DIRECTION,
        L,
        E,
        {"trend": 0.004, "eff": 0.3, "near": 0.0005},
        vwap_pullback,
    ),
    Idea("K3", "control: Dimaag S3 afternoon momentum", DIRECTION, L, E, {"move": 0.005}, afternoon_momentum),
    Idea("K4", "control: fixed 10:00 entry in the day's direction", DIRECTION, L, E, {"t": 45}, fixed_time),
    Idea("A1", "30-min range break on a trending day (efficiency gate)", DIRECTION, L, E, {"eff": 0.35}, or30_break),
    Idea(
        "A2",
        "volatility compression -> expansion with a confirmed 15-min move",
        DIRECTION,
        L,
        E,
        {"ratio": 1.5, "move": 0.0025},
        vol_expansion,
    ),
    Idea(
        "A3",
        "gap fade after a 15-min reversal",
        "STRUCTURAL (overnight order-imbalance reversal)",
        L,
        E,
        {"gap": 0.005},
        gap_fade,
    ),
    Idea("A4", "gap continuation beyond the 15-min range", DIRECTION, L, E, {"gap": 0.005}, gap_go),
    Idea(
        "A5",
        "VWAP-band mean reversion on range days",
        "STRUCTURAL (liquidity provision on range days)",
        L,
        E,
        {"eff": 0.2, "dist": 0.003},
        vwap_revert,
    ),
    Idea(
        "A6",
        "HDFCBANK + ICICIBANK lead the index by 15 min",
        "STRUCTURAL (index arbitrage lag)",
        L,
        E,
        {"lead": 0.003, "lag": 0.0015},
        lead_lag,
    ),
    Idea(
        "A7",
        "first-30-min return -> last-hour direction [POINTER: Gao et al. 2018, JFE, Market intraday momentum]",
        "STRUCTURAL (late hedging flows)",
        L,
        E,
        {"t": 315, "min": 0.0},
        last_hour,
    ),
    Idea(
        "A8",
        "30-min range break with VIX falling (buy premium only when IV falls)",
        DIRECTION,
        L,
        E,
        {"eff": 0.35, "vix_falling": 1},
        or30_break,
    ),
    Idea(
        "A9",
        "own: fade the day's extreme in the afternoon on range days",
        "STRUCTURAL (range-day liquidity)",
        L,
        E,
        {"near": 0.001, "eff": 0.25},
        extreme_fade,
    ),
    Idea(
        "A10", "own: late-morning trend resumption after a 30-min pullback", DIRECTION, L, E, {"eff": 0.4}, trend_resume
    ),
]
