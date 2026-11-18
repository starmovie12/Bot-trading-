"""The fixed setup universe of §PREREG-R17 (owner order 5): every pre-registered S3 setup of R1-R7, R9, R11-R13 and the
13 Phase 3 trials, each with its candidate trades on DESIGN. DESIGN only. Shared by R17-R22."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from lab import ideas, p3r
from lab import portfolio_r14 as pf
from tools import lab_eval as le

ROOT = Path(__file__).resolve().parent.parent
ROUNDS = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R9", "R11", "R12", "R13")
PHASE3 = {
    "K1": "EXIT0|LONG",
    "K2": "EXIT0|LONG",
    "K3": "EXIT0|LONG",
    "K4": "EXIT0|LONG",
    "A1": "EXIT0|LONG",
    "A2": "EXIT0|LONG",
    "A7": "EXIT0|LONG",
    "A9": "EXIT0|LONG",
    "A10": "EXIT0|LONG",
    "A1+b1": "EXIT0|LONG",
    "A1+b2": "EXIT0|SPREAD",
    "A2+b1": "EXIT0|LONG",
    "A2+b2": "EXIT0|SPREAD",
}


@dataclass
class Setup:
    id: str
    s2_key: tuple[str, str, float] | None  # (round, idea, value) for the S2 index test; None = no S2 (Phase 3)
    path: str
    key: str
    tr: le.Trades
    cand: np.ndarray
    mask: np.ndarray
    side: np.ndarray
    win: tuple[int, int]
    to_close: bool
    legs: int


_TR: dict[tuple[str, str], le.Trades] = {}


def trades(path: str, key: str) -> le.Trades:
    if (path, key) not in _TR:
        f, outs, days = pf.matrix(path)
        _TR[(path, key)] = le.trades(f, outs[key], days)
    return _TR[(path, key)]


def build() -> list[Setup]:
    out: list[Setup] = []
    for rnd in ROUNDS:
        spec = p3r.ROUNDS[rnd]
        path = spec.get("matrix", "data/lab/matrix.npz")
        f = pf.matrix(path)[0]
        for iid, (_t, rule, grid, _o) in spec["ideas"].items():
            for x in grid:
                mask, side, win = rule(f, x)
                mb = np.nan_to_num(mask).astype(bool)
                for ex, st in spec["combos"]:
                    tr = trades(path, f"{ex}|{st}")
                    suffix = ex if st == "LONG" else f"{st}-{ex}"
                    out.append(
                        Setup(
                            f"{iid}-{x}-{suffix}",
                            (rnd, iid, float(x)),
                            path,
                            f"{ex}|{st}",
                            tr,
                            le.select(tr, mb, side),
                            mb,
                            side,
                            win,
                            bool(spec.get("to_close")),
                            1,
                        )
                    )
    path = "data/lab/matrix.npz"
    f = pf.matrix(path)[0]
    by = {i.id: i for i in ideas.BRACKET}
    for tid, key in PHASE3.items():
        idea = by[tid.split("+")[0]]
        mask, side = idea.rule(f, idea.params)
        mb = np.nan_to_num(mask).astype(bool) & ((f["vix_chg"] < 0) if tid.endswith("+b1") else True)
        tr = trades(path, key)
        out.append(
            Setup(
                tid,
                None,
                path,
                key,
                tr,
                le.select(tr, mb, side),
                mb,
                side,
                (15, 315),
                False,
                2 if key.endswith("SPREAD") else 1,
            )
        )
    return out


def alone_daily(s: Setup, n_days: int = 362) -> np.ndarray:
    """The setup traded alone with the RISK SHELL day rules: daily stressed net over DESIGN (PBO / DSR columns)."""
    taken = le.sequence(s.tr, s.cand)
    out = np.zeros(n_days)
    np.add.at(out, s.tr.day[taken], s.tr.net_stressed[taken])
    return out
