#!/usr/bin/env python3
"""Power table (MISSION V19 Phase 2c, C4): trades needed and the minimum detectable effect -> results/power.json.

n = ceil((2.8016 * sigma / e) ** 2) (5% two-sided, 80% power); MDE = round(2.8016 * sigma / sqrt(n)) [CODE(ASSUMPTION)].
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Z = 2.8016
SIGMAS = (500, 1000, 2000)
EFFECTS = (15, 50, 176)
NS = (30, 50, 60, 100)


def trades_needed(sigma: float, effect: float) -> int:
    return math.ceil((Z * sigma / effect) ** 2)


def mde(sigma: float, n: int) -> int:
    return round(Z * sigma / math.sqrt(n))


def table() -> dict[str, object]:
    return {
        "tag": "CODE(ASSUMPTION)",
        "z": Z,
        "trades_needed": {f"sigma_{s}": {f"e_{e}": trades_needed(s, e) for e in EFFECTS} for s in SIGMAS},
        "mde_rs": {f"sigma_{s}": {f"n_{n}": mde(s, n) for n in NS} for s in SIGMAS},
        "anchors": {
            "sigma_1000_e_15": trades_needed(1000, 15),
            "sigma_1000_e_176": trades_needed(1000, 176),
            "sigma_1000_n_30_mde": mde(1000, 30),
        },
    }


def main() -> int:
    t = table()
    (ROOT / "results/power.json").write_text(json.dumps(t, indent=1) + "\n", encoding="utf-8")
    print("anchors", t["anchors"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
