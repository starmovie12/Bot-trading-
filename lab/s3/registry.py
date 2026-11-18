"""The S3 registry (V3 §12): config/strategy_v3.toml is the only source of numbers for the S3 code (test T02)."""

import copy
import hashlib
import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/strategy_v3.toml"
RAW: dict[str, Any] = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
FIX: dict[str, Any] = RAW["fixed"]
_LIMITS = tomllib.loads((ROOT / "limits.toml").read_text(encoding="utf-8"))
FIX |= {k: _LIMITS[k]["value"] for k in ("CAPITAL_RS", "MAX_TRADE_LOSS_RS")}  # one source of risk limits (D-55)
CHK: dict[str, Any] = RAW["checks"]
STATS: dict[str, Any] = RAW["stats"]
COST: dict[str, Any] = RAW["cost"]
SCORE: dict[str, Any] = RAW["score"]
SEED: int = RAW["meta"]["seed"]
MIN_PER_HOUR, OPEN_H, OPEN_M = 60, 9, 15  # clock arithmetic only: the session opens 09:15 IST


def minute(hhmm: str) -> int:
    """'HH:MM' -> minutes after 09:15 (the minute index of a 1-minute bar's ts_open)."""
    h, m = hhmm.split(":")
    return (int(h) - OPEN_H) * MIN_PER_HOUR + int(m) - OPEN_M


def hhmm(m: int) -> str:
    t = m + OPEN_H * MIN_PER_HOUR + OPEN_M
    return f"{t // MIN_PER_HOUR:02d}:{t % MIN_PER_HOUR:02d}"


_FILTER_IDS = (1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 29)
FILTER_CHECKS = tuple(f"K{i:02d}" for i in _FILTER_IDS)
FAMILY = {
    **dict.fromkeys(("K01", "K14", "K16"), "Disha"),
    **dict.fromkeys(("K04", "K20"), "IV"),
    **dict.fromkeys(("K06", "K10", "K11"), "Volume"),
    **dict.fromkeys(("K08", "K09", "K12", "K13"), "Breakout"),
    **dict.fromkeys(("K17", "K18", "K21"), "OI"),
    "K07": "Liquidity",
    "K19": "Stocks",
    "K29": "Levels",
    "K02": "-",
}


@dataclass
class Cfg:
    """One run's settings: the T1 values of §12.1, overridden only inside their range, plus variant and flags."""

    variant: str = "T1-P"
    overrides: dict[str, Any] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)
    intrabar: str = "BARCLOSE"  # BARCLOSE (the rule) | PATH | WORST (V3 §6.3 report only)
    checks: tuple[str, ...] = ()  # R7: §9 checks used as filters (RED blocks; on/off only, numbers unchanged)
    slots_off: tuple[str, ...] = ()  # N9 (R9): half-hour entry slots switched off, chosen on training data only

    def __post_init__(self) -> None:
        for k, v in self.overrides.items():
            if k not in RAW["tunable"]:
                raise KeyError(f"{k} is not a §12.1 tunable")
            if v not in RAW["tunable"][k]["range"]:
                raise ValueError(f"{k} = {v!r} is outside its §12.1 range {RAW['tunable'][k]['range']}")
        for k in self.flags:
            if k not in RAW["flags"]:
                raise KeyError(f"{k} is not a §12.3 flag")
        if self.variant not in RAW["variants"]:
            raise KeyError(self.variant)
        bad = [c for c in self.checks if c not in FILTER_CHECKS]
        if bad:
            raise KeyError(f"{bad} are not R7 filter checks")

    def __getitem__(self, name: str) -> Any:
        if name in self.overrides:
            return self.overrides[name]
        if name in RAW["tunable"]:
            return RAW["tunable"][name]["t1"]
        if name in FIX:
            return FIX[name]
        raise KeyError(name)

    def flag(self, name: str) -> bool:
        return bool(self.flags.get(name, RAW["flags"][name]))

    def var(self, name: str) -> bool:
        return bool(RAW["variants"][self.variant][name])

    def config_hash(self) -> str:
        blob = {"variant": self.variant, "overrides": self.overrides, "flags": self.flags, "intrabar": self.intrabar,
                "registry": hashlib.sha256(CONFIG.read_bytes()).hexdigest()}  # fmt: skip
        if self.checks:
            blob["checks"] = sorted(self.checks)
        if self.slots_off:
            blob["slots_off"] = sorted(self.slots_off)
        return hashlib.sha256(json.dumps(blob, sort_keys=True, default=str).encode()).hexdigest()[:16]

    def copy(self, **kw: Any) -> "Cfg":
        c = copy.deepcopy(self)
        for k, v in kw.items():
            setattr(c, k, v)
        c.__post_init__()
        return c
