#!/usr/bin/env python3
"""Exchange trading days for DG (MISSION V19 Phase 1b) -> results/calendar.txt.

2026: weekdays minus the SOURCE holiday list in constants.toml (holidays_2026). 2024-2025: the official list was not
reachable (constants.toml holidays_2024_2025 = UNVERIFIED), so those years use the weekdays present in the data.
Weekend sessions present in the data (budget days) are added for every year.
"""

import datetime as dt
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build(holidays_2026: set[str], data_days: set[str], first: dt.date, last: dt.date) -> list[str]:
    out = []
    day = first
    while day <= last:
        d = str(day)
        if day.year == 2026:
            if (day.weekday() < 5 and d not in holidays_2026) or (day.weekday() >= 5 and d in data_days):
                out.append(d)
        elif d in data_days:
            out.append(d)
        day += dt.timedelta(days=1)
    return out


def main() -> int:
    consts = tomllib.loads((ROOT / "constants.toml").read_text(encoding="utf-8"))
    profile = json.loads((ROOT / "data/lab/data_profile.json").read_text(encoding="utf-8"))
    days = set(profile["days"])
    cal = build(
        set(consts["holidays_2026"]["value"]), days, dt.date.fromisoformat(min(days)), dt.date.fromisoformat(max(days))
    )
    head = "# calendar: 2026 = SOURCE (Upstox market-holidays page, 2026-11-18); 2024-2025 = data days (UNVERIFIED)\n"
    (ROOT / "results/calendar.txt").write_text(head + "\n".join(cal) + "\n", encoding="utf-8")
    print(f"{len(cal)} trading days written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
