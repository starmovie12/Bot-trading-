"""P3R round runner (owner order D-40): python -m lab.p3r R1 -> trials.jsonl lines, results/r1_board.md, rounds.md.

DESIGN only (data/lab/matrix.npz). Funnel per PLAN.md §PREREG-R<n>: S1 p90 move vs break-even, S2 index points with a
matched null, S3 option P&L (lab matrix, stressed costs, RISK SHELL day rules) with every PASS gate of
results/research_plan.md. A candidate passing every screen gate is a FINALIST: full null N = max(10,000, 400 k) and Holm
over the total k, then the engine of record (ST7 delay) before any PASS card.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from lab.run_round import VIX_MEDIAN
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
BE_PTS, H = 14.2, 12  # break-even index points (results/diagnosis.md); horizon 60 min = 12 decision rows
Rule = Callable[[le.A, float], tuple[np.ndarray, np.ndarray, tuple[int, int]]]


def sg(x: np.ndarray) -> np.ndarray:
    return np.where(x >= 0, 1, -1)


def r1_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return (f["t"] >= 165) & (f["t"] <= 255) & (np.abs(f["ret_open"]) >= x), -sg(f["ret_open"]), (165, 255)


def r1_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    up, dn = (f["vix_chg"] >= x) & (f["ret_open"] < 0), (f["vix_chg"] <= -x) & (f["ret_open"] > 0)
    return (f["t"] >= 45) & (f["t"] <= 255) & (up | dn), np.where(up, 1, -1), (45, 255)


def r1_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return (f["t"] >= 75) & (f["t"] <= 255) & (np.abs(f["vwap_dist"]) >= x), -sg(f["vwap_dist"]), (75, 255)


def r1_4(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    g = np.nan_to_num(f["gap"])
    m = (f["t"] >= 30) & (f["t"] <= 75) & (np.abs(g) >= x) & (sg(np.nan_to_num(f["ret15"])) == -sg(g))
    return m, -sg(g), (30, 75)


def r1_5(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    m = (f["dte"] >= 3) & (f["dte"] <= 7) & (f["t"] >= 45) & (f["t"] <= 165) & (np.abs(f["ret_open"]) >= x)
    return m, sg(f["ret_open"]), (45, 165)


def r1_6(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    h, i, r = (np.nan_to_num(f[k]) for k in ("hdfc15", "icici15", "ret15"))
    up, dn = (h >= x) & (i >= x) & (r <= x / 2), (h <= -x) & (i <= -x) & (r >= -x / 2)
    return (f["t"] >= 30) & (f["t"] <= 255) & (up | dn), np.where(up, 1, -1), (30, 255)


def r1_7(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    m = (f["t"] >= 105) & (f["t"] <= 285) & (f["eff"] <= 0.20) & (np.abs(f["ret_open"]) >= x)
    return m, -sg(f["ret_open"]), (105, 285)


def r2_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15 = np.nan_to_num(f["ret15"])
    up, dn = (f["spot"] > f["or30_hi"]) & (r15 > 0), (f["spot"] < f["or30_lo"]) & (r15 < 0)
    return (f["t"] >= 30) & (f["t"] <= 255) & (f["eff"] >= x) & (up | dn), np.where(up, 1, -1), (30, 255)


def r2_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15 = np.nan_to_num(f["ret15"])
    up, dn = (f["spot"] >= f["or15_hi"] * (1 + x)) & (r15 > 0), (f["spot"] <= f["or15_lo"] * (1 - x)) & (r15 < 0)
    return (f["t"] >= 30) & (f["t"] <= 255) & (up | dn), np.where(up, 1, -1), (30, 255)


def r2_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return (f["t"] >= 75) & (f["t"] <= 165) & (np.abs(f["ret_open"]) >= x), sg(f["ret_open"]), (75, 165)


def r2_4(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    m = (f["dte"] <= 7) & (f["t"] >= 45) & (f["t"] <= 165) & (np.abs(f["ret_open"]) >= x)
    return m, sg(f["ret_open"]), (45, 165)


def r2_5(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r30 = np.nan_to_num(f["ret30"])
    m = (f["t"] >= 45) & (f["t"] <= 255) & (np.abs(r30) >= x) & (sg(r30) == sg(f["ret_open"]))
    return m, sg(r30), (45, 255)


def r2_6(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return (f["t"] >= 75) & (f["t"] <= 195) & (f["eff"] >= x), sg(f["ret_open"]), (75, 195)


def r2_7(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15 = np.nan_to_num(f["ret15"])
    m = (f["t"] >= 30) & (f["t"] <= 255) & (np.nan_to_num(f["rv5"]) >= x * f["rv30"]) & (np.abs(r15) >= 0.0015)
    return m, sg(r15), (30, 255)


def r2_8(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    vd, r15 = f["vwap_dist"], np.nan_to_num(f["ret15"])
    m = (f["t"] >= 45) & (f["t"] <= 255) & (np.abs(vd) >= x) & (sg(r15) == sg(vd))
    return m, sg(vd), (45, 255)


def r3_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    oi = np.nan_to_num(f["oi_skew"])
    return (f["t"] >= 45) & (f["t"] <= 255) & (np.abs(oi) >= x), sg(oi), (45, 255)


def r3_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    m, side, win = r3_1(f, x)
    return m & (side == sg(f["ret_open"])), side, win


def r3_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    b = np.nan_to_num(f["basis_chg"])
    return (f["t"] >= 45) & (f["t"] <= 255) & (np.abs(b) >= x), sg(b), (45, 255)


def r3_4(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    m, side, win = r3_3(f, x)
    return m & (sg(np.nan_to_num(f["ret15"])) == side), side, win


def r3_5(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    v = np.nan_to_num(f["vix_pct"])
    up, dn = (v >= x) & (f["ret_open"] < 0), (v <= -x) & (f["ret_open"] > 0)
    return (f["t"] >= 45) & (f["t"] <= 255) & (up | dn), np.where(up, 1, -1), (45, 255)


def r3_6(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    m, side, win = r3_5(f, x)
    return m, -side, win


def r4_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    g, r15 = np.nan_to_num(f["gap"]), np.nan_to_num(f["ret15"])
    beyond = np.where(g > 0, f["spot"] > f["or15_hi"], f["spot"] < f["or15_lo"])
    m = (f["t"] >= 30) & (f["t"] <= 75) & (np.abs(g) >= x) & (sg(r15) == sg(g)) & beyond
    return m, sg(g), (30, 75)


def r4_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15 = np.nan_to_num(f["ret15"])
    up = (f["day_hi"] > f["or30_hi"]) & (np.abs(f["spot"] / f["or30_hi"] - 1) <= x) & (r15 > 0)
    dn = (f["day_lo"] < f["or30_lo"]) & (np.abs(f["spot"] / f["or30_lo"] - 1) <= x) & (r15 < 0)
    return (f["t"] >= 45) & (f["t"] <= 255) & (up | dn), np.where(up, 1, -1), (45, 255)


def r4_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    rng = (f["day_hi"] - f["day_lo"]) / f["spot"]
    return (f["t"] == 60) & (rng >= x), sg(f["ret_open"]), (60, 60)


def r4_4(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r30 = np.nan_to_num(f["ret30"])
    hi, lo = (f["spot"] >= f["day_hi"] * (1 - x)) & (r30 > 0), (f["spot"] <= f["day_lo"] * (1 + x)) & (r30 < 0)
    return (f["t"] >= 180) & (f["t"] <= 285) & (hi ^ lo), np.where(hi, 1, -1), (180, 285)


def r4_5(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    g = np.nan_to_num(f["gap"])
    m = (f["t"] >= 45) & (f["t"] <= 120) & (np.abs(g) >= x) & (f["vix_chg"] < 0) & (sg(f["ret_open"]) == sg(g))
    return m, sg(g), (45, 120)


def r4_6(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15, r30 = np.nan_to_num(f["ret15"]), np.nan_to_num(f["ret30"])
    m = (f["t"] >= 45) & (f["t"] <= 255) & (sg(r15) == sg(r30 - r15)) & (np.abs(r30) >= x)
    return m, sg(r30), (45, 255)


def r5_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15, rr = np.nan_to_num(f["ret15"]), np.nan_to_num(f["prev_rr"], nan=9.0)
    up, dn = (f["spot"] > f["or30_hi"]) & (r15 > 0), (f["spot"] < f["or30_lo"]) & (r15 < 0)
    return (f["t"] >= 30) & (f["t"] <= 165) & (rr <= x) & (up | dn), np.where(up, 1, -1), (30, 165)


def r5_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    cl = f["prev_cl"]
    up, dn = (
        (np.nan_to_num(cl, nan=0.5) >= 1 - x) & (f["ret_open"] > 0),
        (np.nan_to_num(cl, nan=0.5) <= x) & (f["ret_open"] < 0),
    )
    return (f["t"] >= 30) & (f["t"] <= 120) & (up | dn), np.where(up, 1, -1), (30, 120)


def r5_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    pr = np.nan_to_num(f["prev_ret"])
    m = (f["t"] >= 45) & (f["t"] <= 120) & (np.abs(pr) >= x) & (sg(f["ret_open"]) == sg(pr)) & (pr != 0)
    return m, sg(pr), (45, 120)


def r5_4(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15, hi, lo = np.nan_to_num(f["ret15"]), f["prev_hi"], f["prev_lo"]
    up = (f["spot"] >= np.nan_to_num(hi, nan=np.inf) * (1 + x)) & (r15 > 0)
    dn = (f["spot"] <= np.nan_to_num(lo, nan=-np.inf) * (1 - x)) & (r15 < 0)
    return (f["t"] >= 30) & (f["t"] <= 255) & (up | dn), np.where(up, 1, -1), (30, 255)


def fixed(t: int, f: le.A, cond: np.ndarray, side: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return (f["t"] == t) & cond, side, (t, t)


def r6_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return fixed(105, f, np.abs(f["ret_open"]) >= x, sg(f["ret_open"]))


def r6_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return fixed(165, f, np.abs(f["ret_open"]) >= x, sg(f["ret_open"]))


def r6_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return fixed(105, f, f["eff"] >= x, sg(f["ret_open"]))


def r6_4(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    g = np.nan_to_num(f["gap"])
    return fixed(30, f, (np.abs(g) >= x) & (sg(f["ret_open"]) == sg(g)), sg(g))


def r6_5(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return fixed(75, f, (f["dte"] <= 7) & (np.abs(f["ret_open"]) >= x), sg(f["ret_open"]))


def r6_6(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    return fixed(60, f, np.abs(f["ret_open"]) >= x, sg(f["ret_open"]))


def r9(dmax: int) -> Rule:
    def rule(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
        return fixed(75, f, (f["dte"] <= dmax) & (np.abs(f["ret_open"]) >= x), sg(f["ret_open"]))

    return rule


def r11_1(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    ir = np.nan_to_num(f["impl_ratio"])
    return (f["t"] >= 45) & (f["t"] <= 255) & (ir >= x), sg(f["ret_open"]), (45, 255)


def r11_2(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    r15 = np.nan_to_num(f["ret15"])
    m = (np.nan_to_num(f["rv_iv"]) >= x) & (np.nan_to_num(f["rv5"]) > f["rv30"]) & (np.abs(r15) >= 0.001)
    return (f["t"] >= 45) & (f["t"] <= 255) & m, sg(r15), (45, 255)


def r11_3(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    ir = np.nan_to_num(f["impl_ratio"])
    return (f["t"] >= 165) & (f["t"] <= 285) & (ir >= x), -sg(f["ret_open"]), (165, 285)


def trend_score(f: le.A) -> np.ndarray:
    so = sg(f["ret_open"])
    h, i = np.nan_to_num(f["hdfc15"]), np.nan_to_num(f["icici15"])
    return np.asarray(
        (f["eff"] >= 0.30).astype(int)
        + (np.abs(f["ret_open"]) >= 0.003)
        + (sg(np.nan_to_num(f["ret15"])) == so)
        + ((sg(h) == so) & (sg(i) == so))
        + (sg(f["vwap_dist"]) == so)
    )


def r12(t: int, vix_calm: bool) -> Rule:
    def rule(f: le.A, x: float) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
        cond = trend_score(f) >= x
        if vix_calm:
            cond = cond & (f["vix_chg"] <= 0)
        return fixed(t, f, cond, sg(f["ret_open"]))

    return rule


ROUNDS: dict[str, dict[str, Any]] = {
    "R1": {
        "combos": (("EXIT0", "LONG"), ("C2", "LONG"), ("C3", "LONG")),
        "ideas": {
            "R1-1": ("fade the day's move after 12:00", r1_1, (0.003, 0.005, 0.007), (0.001, 0.009)),
            "R1-2": ("fade a VIX fear spike (vix_chg in VIX points)", r1_2, (0.03, 0.05, 0.08), (0.01, 0.11)),
            "R1-3": ("VWAP stretch reversion", r1_3, (0.0025, 0.004, 0.006), (0.001, 0.008)),
            "R1-4": ("gap fade after a 15-min reversal", r1_4, (0.004, 0.006, 0.008), (0.002, 0.010)),
            "R1-5": ("expiry-week momentum", r1_5, (0.003, 0.005, 0.007), (0.001, 0.009)),
            "R1-6": ("follow HDFCBANK + ICICIBANK when the index lags", r1_6, (0.004, 0.006, 0.008), (0.002, 0.010)),
            "R1-7": ("range-day band fade", r1_7, (0.004, 0.006, 0.008), (0.002, 0.010)),
        },
    },
    "R2": {
        "matrix": "data/lab/matrix_r2.npz",
        "combos": (("XI1", "ATM"), ("XI1", "CAP15"), ("XI2", "ATM"), ("XI2", "CAP15")),
        "ideas": {
            "R2-1": ("30-min range break, low trend gate", r2_1, (0.10, 0.20, 0.30), (0.00, 0.40)),
            "R2-2": ("15-min range break by a margin", r2_2, (0.001, 0.002, 0.003), (0.000, 0.004)),
            "R2-3": ("late-morning day-direction momentum", r2_3, (0.002, 0.004, 0.006), (0.000, 0.008)),
            "R2-4": ("near-expiry momentum (DTE 0..7)", r2_4, (0.002, 0.004, 0.006), (0.000, 0.008)),
            "R2-5": ("30-min momentum aligned with the day", r2_5, (0.002, 0.003, 0.004), (0.001, 0.005)),
            "R2-6": ("trend-day continuation", r2_6, (0.30, 0.40, 0.50), (0.20, 0.60)),
            "R2-7": ("volatility expansion with a 15-min move", r2_7, (1.3, 1.6, 2.0), (1.0, 2.4)),
            "R2-8": ("VWAP-side momentum", r2_8, (0.001, 0.002, 0.003), (0.000, 0.004)),
        },
    },
    "R3": {
        "matrix": "data/lab/matrix_r3.npz",
        "combos": (("XI2", "CAP15"), ("XI2", "CAP15P")),
        "ideas": {
            "R3-1": ("option-writer positioning (OI skew)", r3_1, (0.10, 0.15, 0.20), (0.05, 0.25)),
            "R3-2": ("writer positioning + the day's move agree", r3_2, (0.10, 0.15, 0.20), (0.05, 0.25)),
            "R3-3": ("futures basis momentum", r3_3, (0.0005, 0.0008, 0.0011), (0.0002, 0.0014)),
            "R3-4": ("basis + the 15-min move agree", r3_4, (0.0005, 0.0008, 0.0011), (0.0002, 0.0014)),
            "R3-5": ("fade a VIX spike (in %)", r3_5, (0.03, 0.045, 0.06), (0.015, 0.075)),
            "R3-6": ("follow a VIX move (in %)", r3_6, (0.03, 0.045, 0.06), (0.015, 0.075)),
            "R3-7": ("near-expiry momentum, passive entry next to market", r2_4, (0.003, 0.004, 0.005), (0.002, 0.006)),
        },
    },
    "R4": {
        "matrix": "data/lab/matrix_r2.npz",
        "combos": (("XI2", "CAP15"), ("XI1", "CAP15")),
        "ideas": {
            "R4-1": ("gap follow beyond the 15-min range", r4_1, (0.003, 0.005, 0.007), (0.001, 0.009)),
            "R4-2": (
                "30-min range break, then a pullback to the edge",
                r4_2,
                (0.0005, 0.001, 0.0015),
                (0.00025, 0.002),
            ),
            "R4-3": ("wide first hour = trend day: follow it", r4_3, (0.006, 0.008, 0.010), (0.004, 0.012)),
            "R4-4": ("afternoon push to a new day extreme", r4_4, (0.0005, 0.001, 0.0015), (0.00025, 0.002)),
            "R4-5": ("gap follow while VIX falls", r4_5, (0.003, 0.005, 0.007), (0.001, 0.009)),
            "R4-6": ("two 15-min candles the same way", r4_6, (0.002, 0.003, 0.004), (0.001, 0.005)),
        },
    },
    "R5": {
        "matrix": "data/lab/matrix_r5.npz",
        "combos": (("XI2", "CAP15"), ("XI1", "CAP15")),
        "ideas": {
            "R5-1": ("a narrow prior day, then a 30-min range break", r5_1, (0.65, 0.80, 0.95), (0.50, 1.10)),
            "R5-2": ("prior close at its extreme, today the same way", r5_2, (0.15, 0.25, 0.35), (0.05, 0.45)),
            "R5-3": ("a prior trend day, today continues it", r5_3, (0.004, 0.007, 0.010), (0.001, 0.013)),
            "R5-4": ("break of the prior day's high / low", r5_4, (0.000, 0.001, 0.002), (-0.001, 0.003)),
        },
    },
    "R6": {
        "matrix": "data/lab/matrix_r2.npz",
        "to_close": True,
        "combos": (("XI2", "CAP15"), ("XI2", "ATM")),
        "ideas": {
            "R6-1": ("11:00 day direction, hold to close", r6_1, (0.001, 0.002, 0.003), (0.0005, 0.004)),
            "R6-2": ("12:00 day direction, hold to close", r6_2, (0.001, 0.002, 0.003), (0.0005, 0.004)),
            "R6-3": ("11:00 trend efficiency, hold to close", r6_3, (0.10, 0.15, 0.20), (0.05, 0.25)),
            "R6-4": ("gap-and-go at 09:45, hold to close", r6_4, (0.001, 0.002, 0.003), (0.0005, 0.004)),
            "R6-5": ("near-expiry 10:30 direction, hold to close", r6_5, (0.002, 0.003, 0.004), (0.001, 0.005)),
            "R6-6": ("first-hour direction at 10:15, hold to close", r6_6, (0.001, 0.002, 0.003), (0.0005, 0.004)),
        },
    },
    "R7": {
        "matrix": "data/lab/matrix_r7.npz",
        "to_close": True,
        "combos": (("XH", "CAP15"), ("XH2", "CAP15")),
        "ideas": {
            "R7-1": ("gap-and-go at 09:45, hold to close (R6-4 rule)", r6_4, (0.001, 0.002, 0.003), (0.0005, 0.004)),
            "R7-2": (
                "near-expiry 10:30 direction, hold to close (R6-5 rule)",
                r6_5,
                (0.002, 0.003, 0.004),
                (0.001, 0.005),
            ),
        },
    },
    "R9": {
        "matrix": "data/lab/matrix_r9.npz",
        "to_close": True,
        "combos": (("XH", "CAP15"), ("XH2", "CAP15"), ("XI2", "CAP15")),
        "ideas": {
            f"R9-{i}": (
                f"near-expiry direction at 10:30, DTE <= {d}, hold to close",
                r9(d),
                (0.0005, 0.0015, 0.0025),
                (0.0, 0.0035),
            )
            for i, d in ((1, 10), (2, 15), (3, 20))
        },
    },
    "R11": {
        "matrix": "data/lab/matrix_r11.npz",
        "combos": (("XI2", "CAP15"), ("XH", "CAP15")),
        "ideas": {
            "R11-1": ("the move passes X of the implied daily move: follow", r11_1, (0.5, 0.75, 1.0), (0.25, 1.25)),
            "R11-2": ("realised vol above implied and rising: buy the move", r11_2, (0.8, 1.0, 1.2), (0.6, 1.4)),
            "R11-3": ("afternoon overshoot of the implied move: fade", r11_3, (1.0, 1.25, 1.5), (0.75, 1.75)),
        },
    },
    "R12": {
        "matrix": "data/lab/matrix_r11.npz",
        "to_close": True,
        "combos": (("XH", "CAP15"), ("XI2", "CAP15")),
        "ideas": {
            "R12-1": ("trend score at 10:00, follow to the close", r12(45, False), (3, 4, 5), (2, 6)),
            "R12-2": ("trend score at 11:00, follow to the close", r12(105, False), (3, 4, 5), (2, 6)),
            "R12-3": ("trend score at 10:00 with VIX not rising", r12(45, True), (3, 4, 5), (2, 6)),
        },
    },
}


def index_stage(
    f: le.A, mask: np.ndarray, side: np.ndarray, win: tuple[int, int], to_close: bool = False
) -> dict[str, Any]:
    spot, t = f["spot"].reshape(-1, 61), f["t"][:61]
    m, s = mask.reshape(-1, 61), side.reshape(-1, 61)
    picks: list[tuple[int, int, int]] = []
    for day in range(m.shape[0]):
        last, n = -99, 0
        for col in np.nonzero(m[day])[0]:
            if col - last >= H and n < 2:
                picks.append((day, int(col), int(s[day, col])))
                last, n = int(col), n + 1
    if not picks:
        return {"signals": 0, "p90_move": 0.0, "mean_pts": 0.0, "p": 1.0, "s1": False, "s2": False}
    d, j, sd = (np.array(c) for c in zip(*picks, strict=True))
    end = np.full(len(j), 60) if to_close else np.minimum(j + H, 60)  # §PREREG-R6: to 14:30
    fwd = (spot[d, end] - spot[d, j]) * sd
    p90 = float(np.nanpercentile(np.abs(fwd), 90))
    wcols = np.nonzero((t >= win[0]) & (t <= win[1]))[0]
    rng = np.random.default_rng(le.SEED)
    rj = rng.choice(wcols, size=(1000, len(d)))
    rs = np.where(rng.random((1000, len(d))) < float(np.mean(sd > 0)), 1, -1)
    rend = np.full(rj.shape, 60) if to_close else np.minimum(rj + H, 60)
    null = np.nanmean((spot[d, rend] - spot[d, rj]) * rs, axis=1)
    mean = float(np.nanmean(fwd))
    p = (1 + int((null >= mean).sum())) / 1001
    return {
        "signals": len(d),
        "p90_move": round(p90, 1),
        "mean_pts": round(mean, 2),
        "p": round(p, 4),
        "s1": p90 >= 2 * BE_PTS,
        "s2": p90 >= 2 * BE_PTS and mean > BE_PTS and p <= 0.05,
    }


def option_stage(
    f: le.A,
    outs: dict[str, le.A],
    days: list[str],
    mask: np.ndarray,
    side: np.ndarray,
    key: str,
    win: tuple[int, int],
) -> dict[str, Any]:
    tr = le.trades(f, outs[key], days)
    taken = le.sequence(tr, le.select(tr, mask, side))
    n_days = len(days)
    met = le.metrics(tr, taken, n_days, VIX_MEDIAN)
    fold = le.folds(tr, taken, n_days)
    cost = le.STRESS_CHARGES * tr.charges[taken] + tr.fill_stressed[taken]
    pool = np.nonzero((tr.t >= win[0]) & (tr.t <= win[1]))[0]
    p = le.null_p(tr, taken, pool, 1000) if len(taken) else 1.0
    hi, lo = met["n_high_vix"], met["n_low_vix"]
    lot = f["lot"][tr.row[taken]] if len(taken) else np.array([0.0])
    gates = {
        "net": met["net_mean"] > 0,
        "folds": fold["pass"],
        "vix_halves": hi >= 15
        and lo >= 15
        and (met["net_mean_high_vix"] or 0) > 0
        and (met["net_mean_low_vix"] or 0) > 0,
        "null_screen": p <= 0.05,
        "st11": met["per_day"] >= 0.5,
        "cost_1_5": bool(len(taken)) and float(np.mean(tr.gross[taken] - 1.5 * cost)) >= 0,
        "st4c": (met["net_mean_wo_best5"] or 0) > 0,
    }
    max_loss = float(np.max(tr.max_loss[taken])) if len(taken) else 0.0
    return met | {
        "folds_positive": fold["positive"],
        "folds_thin": fold["thin"],
        "p_screen": round(p, 4),
        "max_loss_rs": round(max_loss, 0),
        "max_premium_x_lot": round(float(np.max(outs[key]["entry"][taken] * lot)) if len(taken) else 0.0, 0),
        "gates": gates,
        "screen_pass": all(gates.values()),
    }


def run(rnd: str) -> list[dict[str, Any]]:
    spec = ROUNDS[rnd]
    f, outs, days = le.load(ROOT / spec.get("matrix", "data/lab/matrix.npz"))
    rows: list[dict[str, Any]] = []
    s3: dict[tuple[str, float, str, str], dict[str, Any]] = {}

    def opt(iid: str, x: float, ex: str, st: str) -> dict[str, Any]:
        if (iid, x, ex, st) not in s3:
            mask, side, win = spec["ideas"][iid][1](f, x)
            res = option_stage(f, outs, days, np.nan_to_num(mask).astype(bool), side, f"{ex}|{st}", win)
            s3[(iid, x, ex, st)] = res
            suffix = ex if st == "LONG" else f"{st}-{ex}"
            rows.append(
                {"id": f"{iid}-{x}-{suffix}", "stage": "S3", "idea": iid, "x": x, "exit": ex, "structure": st} | res
            )
        return s3[(iid, x, ex, st)]

    for iid, (_text, rule, grid, outside) in spec["ideas"].items():
        for x in grid:
            mask, side, win = rule(f, x)
            r = index_stage(f, np.nan_to_num(mask).astype(bool), side, win, spec.get("to_close", False))
            rows.append({"id": f"{iid}-{x}", "stage": "S2", "idea": iid, "x": x} | r)
            if not r["s2"]:
                continue
            for ex, st in spec["combos"]:
                res = opt(iid, x, ex, st)
                if not res["screen_pass"]:
                    continue
                full = (outside[0], *grid, outside[1])
                k = full.index(x)
                nb = [opt(iid, v, ex, st)["net_mean"] > 0 for v in (full[k - 1], full[k + 1])]
                res["gates"]["neighbours"] = all(nb)
                res["finalist"] = all(nb)
    return rows


def trial_lines(rnd: str, rows: list[dict[str, Any]]) -> None:
    text = {k: v[0] for k, v in ROUNDS[rnd]["ideas"].items()}
    for r in rows:
        le.append_trial(
            {
                "id": r["id"],
                "cycle": 1,
                "idea": text[r["idea"]],
                "params": {"X": r["x"]} | ({"exit": r["exit"], "structure": r["structure"]} if "exit" in r else {}),
                "design_net_stressed": r.get("net_total"),
                "p_screen": r["p"] if r["stage"] == "S2" else r["p_screen"],
                "source": f"P3R {rnd} {r['stage']}" + (f" index {r['mean_pts']} pts" if r["stage"] == "S2" else ""),
            }
        )


def board(rnd: str, rows: list[dict[str, Any]]) -> list[str]:
    out = [
        f"# {rnd} BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)",
        "",
        "## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)",
        "",
        "| id | signals | p90 move | mean pts | null p | S1 | S2 |",
        "|---|---|---|---|---|---|---|",
    ]
    out += [
        f"| {r['id']} | {r['signals']} | {r['p90_move']} | {r['mean_pts']} | {r['p']} | {r['s1']} | {r['s2']} |"
        for r in rows
        if r["stage"] == "S2"
    ]
    out += [
        "",
        "## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)",
        "",
        "| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ "
        "| failed gates |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in (x for x in rows if x["stage"] == "S3"):
        failed = [k for k, v in r["gates"].items() if not v] or ["none (FINALIST)" if r.get("finalist") else "none"]
        out.append(
            f"| {r['id']} | {r['trades']} | {r['per_day']} | {r['net_mean']} | {r['folds_positive']}/4 | "
            f"{r['p_screen']} | {r['net_mean_high_vix']} / {r['net_mean_low_vix']} | {r['net_mean_wo_best5']} | "
            f"{r['max_loss_rs']:,.0f} | {', '.join(failed)} |"
        )
    return out


def main(argv: list[str]) -> int:
    rnd = argv[0]
    rows = run(rnd)
    trial_lines(rnd, rows)
    (ROOT / f"data/lab/{rnd.lower()}_rows.json").write_text(json.dumps(rows, default=str) + "\n", encoding="utf-8")
    (ROOT / f"results/{rnd.lower()}_board.md").write_text("\n".join(board(rnd, rows)) + "\n", encoding="utf-8")
    s3 = [r for r in rows if r["stage"] == "S3"]
    best = max(s3, key=lambda r: r["net_mean"]) if s3 else None
    print(
        json.dumps(
            {
                "rows": len(rows),
                "s2_pass": sum(r.get("s2", False) for r in rows),
                "s3": len(s3),
                "finalists": [r["id"] for r in s3 if r.get("finalist")],
                "best": best and {k: best[k] for k in ("id", "net_mean", "trades", "per_day", "gates")},
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
