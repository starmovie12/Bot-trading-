"""`python -m bot`: abhi sirf DRY-RUN jaanch. Live order ka koi raasta nahi (iron law).

  python -m bot --check      niyam-file, kharcha model aur paper-only guard jaanch kar 0 (theek) ya 1 lautata hai.
Live feed + paper loop M2 mein aayega; tab tak `deploy/bot.service` oneshot jaanch chalata hai.
"""

from __future__ import annotations

import os
import sys

from bot.haath.orders import Limits, LiveTradingForbidden, OrderManager, PaperBroker
from bot.niyam import NiyamError, consistency_issues, load
from bot.strategy.costs import CostModel


def check(niyam_path: str = "config/niyam.toml") -> int:
    if os.environ.get("BOT_MODE", "paper") != "paper":
        print("FAIL: BOT_MODE sirf 'paper' ho sakta hai (live ka raasta nahi)")
        return 1
    try:
        OrderManager(PaperBroker(), Limits(900, 900, 4000, 15000), mode="real", clock=lambda: 0.0)
        print("FAIL: real mode bana diya gaya (guard toota)")
        return 1
    except LiveTradingForbidden:
        pass
    try:
        n = load(niyam_path)
    except (NiyamError, OSError) as e:
        print(f"FAIL: niyam-file: {e}")
        return 1
    issues = [i for i in consistency_issues(n) if "Bot_Lease_Samay" in i]
    if issues:
        print(f"FAIL: {issues}")
        return 1
    if CostModel().unverified():
        print(f"CHETAVNI: kharcha andaza: {CostModel().unverified()}")
    print("OK: paper-only guard, niyam-file aur kharcha model theek")
    return 0


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
