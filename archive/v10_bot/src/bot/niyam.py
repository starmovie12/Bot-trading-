"""Niyam-file (config/niyam.toml) ka loader aur validation.

Idea v4 ki "Numbers ki list" ka har number yahan aata hai. Code kabhi number guess nahi karta:
- jis number ki typed value nahi hai (range, "Tay nahi", ulajha text), uske liye `typed()` NeedsDecision deta hai;
- galat file (status, unit, range) par load hi fail hota hai.

Chalao:  PYTHONPATH=src python -m bot.niyam config/niyam.toml
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ALLOWED_STATUS: Final = frozenset({"Pakka", "Andaza", "Prastaavit", "Tay nahi"})
ALLOWED_UNITS: Final = frozenset(
    {
        "ms",
        "s",
        "min",
        "pct",
        "points",
        "x",
        "trading_din",
        "din",
        "saal",
        "dhadkan",
        "koshish",
        "signal",
        "trade",
        "inr",
        "delta",
    }
)
_SECONDS: Final = {"ms": 0.001, "s": 1.0, "min": 60.0}


class NiyamError(ValueError):
    """Niyam-file galat hai. Bot ko is file se chalna nahi chahiye."""


class NeedsDecision(LookupError):
    """Is number ki pakki typed kimat nahi hai; malik ka faisla chahiye. Code guess nahi karega."""


@dataclass(frozen=True, slots=True)
class Number:
    name: str
    kimat: str
    status: str
    prastaavit_cc: bool
    kahan: str
    wajah: str
    value: float | None = None
    unit: str | None = None
    range: tuple[float, float] | None = None
    time_ist: str | None = None

    @property
    def is_typed(self) -> bool:
        return self.value is not None or self.range is not None or self.time_ist is not None


@dataclass(frozen=True, slots=True)
class IndexNumber:
    name: str
    banknifty: str
    nifty50: str
    sensex: str
    status_text: str
    prastaavit_cc: bool
    wajah: str


@dataclass(frozen=True, slots=True)
class Niyam:
    idea_version: str
    source_sha256: str
    numbers: dict[str, Number]
    index_numbers: dict[str, IndexNumber]

    def get(self, name: str) -> Number:
        try:
            return self.numbers[name]
        except KeyError:
            raise NiyamError(f"niyam-file mein '{name}' naam ka number nahi hai") from None

    def typed(self, name: str) -> tuple[float, str]:
        """Ek saaf kimat aur unit do, warna NeedsDecision."""
        n = self.get(name)
        if n.value is None or n.unit is None:
            raise NeedsDecision(f"{name}: pakki ek kimat nahi ({n.status}): {n.kimat!r}")
        return n.value, n.unit

    def seconds(self, name: str) -> float:
        value, unit = self.typed(name)
        if unit not in _SECONDS:
            raise NiyamError(f"{name}: unit '{unit}' samay nahi hai")
        return value * _SECONDS[unit]

    def needs_decision(self) -> list[Number]:
        return [n for n in self.numbers.values() if not n.is_typed]


def _str(row: dict[str, object], key: str, where: str) -> str:
    v = row.get(key)
    if not isinstance(v, str) or not v.strip():
        raise NiyamError(f"{where}: '{key}' khaali ya galat")
    return v


def _bool(row: dict[str, object], key: str, where: str) -> bool:
    v = row.get(key)
    if not isinstance(v, bool):
        raise NiyamError(f"{where}: '{key}' true/false hona chahiye")
    return v


def _number(name: str, row: dict[str, object]) -> Number:
    where = f"number.{name}"
    status = _str(row, "status", where)
    if status not in ALLOWED_STATUS:
        raise NiyamError(f"{where}: status '{status}' allowed nahi")
    unknown = set(row) - {"kimat", "status", "prastaavit_cc", "kahan", "wajah", "value", "unit", "range", "time_ist"}
    if unknown:
        raise NiyamError(f"{where}: anjaan field {sorted(unknown)}")
    value = row.get("value")
    unit = row.get("unit")
    rng = row.get("range")
    time_ist = row.get("time_ist")
    if status == "Tay nahi" and (value is not None or rng is not None or time_ist is not None):
        raise NiyamError(f"{where}: 'Tay nahi' par koi kimat nahi ho sakti")
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise NiyamError(f"{where}: value number hona chahiye")
    if unit is not None and unit not in ALLOWED_UNITS:
        raise NiyamError(f"{where}: unit '{unit}' allowed nahi")
    if value is not None and unit is None:
        raise NiyamError(f"{where}: value ke saath unit zaroori")
    if value is not None and value < 0:
        raise NiyamError(f"{where}: value negative nahi ho sakti")
    if value is not None and unit == "pct" and value > 100:
        raise NiyamError(f"{where}: percent 100 se zyada")
    rng_t: tuple[float, float] | None = None
    if rng is not None:
        if not (isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, (int, float)) for x in rng)):
            raise NiyamError(f"{where}: range [min, max] hona chahiye")
        lo, hi = float(rng[0]), float(rng[1])
        if lo > hi or lo < 0:
            raise NiyamError(f"{where}: range galat ({lo} > {hi} ya negative)")
        rng_t = (lo, hi)
    if time_ist is not None:
        if not isinstance(time_ist, str) or len(time_ist) != 5 or time_ist[2] != ":":
            raise NiyamError(f"{where}: time_ist 'HH:MM' hona chahiye")
        hh, mm = int(time_ist[:2]), int(time_ist[3:])
        if not (0 <= hh < 24 and 0 <= mm < 60):
            raise NiyamError(f"{where}: time_ist galat")
    return Number(
        name=name,
        kimat=_str(row, "kimat", where),
        status=status,
        prastaavit_cc=_bool(row, "prastaavit_cc", where),
        kahan=_str(row, "kahan", where),
        wajah=_str(row, "wajah", where),
        value=float(value) if isinstance(value, (int, float)) else None,
        unit=unit if isinstance(unit, str) else None,
        range=rng_t,
        time_ist=time_ist if isinstance(time_ist, str) else None,
    )


def parse(data: dict[str, object]) -> Niyam:
    meta = data.get("meta")
    if not isinstance(meta, dict):
        raise NiyamError("[meta] section nahi hai")
    nums = data.get("number")
    idx = data.get("index_number")
    if not isinstance(nums, dict) or not nums:
        raise NiyamError("[number.*] khaali hai")
    if not isinstance(idx, dict):
        raise NiyamError("[index_number.*] nahi hai")
    numbers = {k: _number(k, v) for k, v in nums.items() if isinstance(v, dict)}
    if len(numbers) != len(nums):
        raise NiyamError("number section mein galat entry")
    index_numbers: dict[str, IndexNumber] = {}
    for k, v in idx.items():
        if not isinstance(v, dict):
            raise NiyamError(f"index_number.{k} galat")
        w = f"index_number.{k}"
        index_numbers[k] = IndexNumber(
            name=k,
            banknifty=_str(v, "banknifty", w),
            nifty50=_str(v, "nifty50", w),
            sensex=_str(v, "sensex", w),
            status_text=_str(v, "status_text", w),
            prastaavit_cc=_bool(v, "prastaavit_cc", w),
            wajah=_str(v, "wajah", w),
        )
    if meta.get("number_count") != len(numbers) or meta.get("index_number_count") != len(index_numbers):
        raise NiyamError("meta ki ginti aur asli entries mel nahi khaati (file adhoori?)")
    version = meta.get("idea_version")
    sha = meta.get("source_sha256")
    if not isinstance(version, str) or not isinstance(sha, str) or len(sha) != 64:
        raise NiyamError("meta: idea_version / source_sha256 galat")
    return Niyam(idea_version=version, source_sha256=sha, numbers=numbers, index_numbers=index_numbers)


def load(path: str | Path) -> Niyam:
    with Path(path).open("rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise NiyamError(f"TOML padh nahi paaye: {e}") from e
    return parse(data)


def consistency_issues(n: Niyam) -> list[str]:
    """Numbers ke aapas ke niyam (idea v4 ke invariants). Khaali list = sab theek."""
    issues: list[str] = []
    try:
        lease = n.seconds("Bot_Lease_Samay")
        beat = n.seconds("Pehredaar_Dhadkan_Samay")
        misses, _ = n.typed("Pehredaar_Dhadkan_Chhoot_Ginti")
        if not lease < beat * misses:
            issues.append(
                f"Bot_Lease_Samay ({lease}s) Pehredaar ke control samay ({beat * misses}s) se kam hona chahiye (F-05)"
            )
    except NeedsDecision as e:
        issues.append(f"Lease jaanch nahi ho saki: {e}")
    try:
        skew = n.seconds("Ghadi_Skew_Sakht_Hadd")
        stale = n.seconds("Data_Purana_Hadd")
        if not skew < stale / 5:
            issues.append("Ghadi_Skew_Sakht_Hadd Data_Purana_Hadd ke paanchve hisse se kam hona chahiye (F-07)")
    except NeedsDecision as e:
        issues.append(f"Ghadi jaanch nahi ho saki (malik ka faisla baaki): {e}")
    try:
        entry = n.get("Aakhri_Entry_Samay").time_ist
        sq = n.get("Auto_Square_Off_Samay").time_ist
        if entry is None or sq is None:
            issues.append("Aakhri_Entry_Samay / Auto_Square_Off_Samay ka saaf samay nahi")
        elif not entry < sq:
            issues.append("Aakhri_Entry_Samay Auto_Square_Off_Samay se pehle hona chahiye")
    except NiyamError as e:
        issues.append(str(e))
    return issues


def main(argv: list[str]) -> int:
    path = argv[1] if len(argv) > 1 else "config/niyam.toml"
    try:
        n = load(path)
    except NiyamError as e:
        print(f"FAIL: {e}")
        return 1
    by_status: dict[str, int] = {}
    for x in n.numbers.values():
        by_status[x.status] = by_status.get(x.status, 0) + 1
    print(f"Idea v{n.idea_version}, source sha256 {n.source_sha256[:12]}…")
    print(f"Numbers: {len(n.numbers)} {by_status}; typed: {sum(x.is_typed for x in n.numbers.values())}")
    print(f"Malik/backtest ke faisle ka intezaar (typed kimat nahi): {len(n.needs_decision())}")
    for issue in consistency_issues(n):
        print(f"  - {issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
