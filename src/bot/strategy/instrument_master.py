"""Lot sizes come ONLY from the broker's instrument master (MISSION V11 S6, T06).

The future feed adapter writes a normalised file `index,lot_size` from the daily Upstox instrument master
(its format is UNVERIFIED this session). No lot size is hard-coded anywhere else; `IndexSpec.lot_crosscheck`
exists only for a test that cross-checks a sample file. Missing or bad data means no trading.
"""

from __future__ import annotations

import csv
from pathlib import Path


class InstrumentMasterError(ValueError):
    """The instrument file is missing, malformed or lacks an index: no trading."""


def load_lot_sizes(path: Path) -> dict[str, int]:
    lots: dict[str, int] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["index", "lot_size"]:
            raise InstrumentMasterError("instrument file header must be: index,lot_size")
        for row in reader:
            try:
                size = int(row["lot_size"])
            except (TypeError, ValueError) as e:
                raise InstrumentMasterError(f"bad lot size for {row.get('index')}") from e
            if size <= 0 or not row["index"]:
                raise InstrumentMasterError(f"bad row for {row.get('index')}")
            lots[row["index"]] = size
    if not lots:
        raise InstrumentMasterError("instrument file is empty")
    return lots
