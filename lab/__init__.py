"""BANKNIFTY research lab (MISSION V19): data loader, screening, engine of record."""

import os
import sys
from pathlib import Path

os.environ.pop("UPSTOX_RO_TOKEN", None)  # MISSION V19 C3: this process never holds the token
_SRC = str(Path(__file__).resolve().parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)  # the bot package (src/bot) for lab runners started with python -m lab.<module>
