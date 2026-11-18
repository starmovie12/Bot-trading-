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


@dataclass
class Cfg:
    """One run's settings: the T1 values of §12.1, overridden only inside their range, plus variant and flags."""

    variant: str = "T1-P"
    overrides: dict[str, Any] = field(default_factory=dict)
    flags: dict[str, bool] = field(default_factory=dict)
    intrabar: str = "BARCLOSE"  # BARCLOSE (the rule) | PATH | WORST (V3 §6.3 report only)

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
        return hashlib.sha256(json.dumps(blob, sort_keys=True, default=str).encode()).hexdigest()[:16]

    def copy(self, **kw: Any) -> "Cfg":
        c = copy.deepcopy(self)
        for k, v in kw.items():
            setattr(c, k, v)
        c.__post_init__()
        return c
