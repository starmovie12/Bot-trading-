"""BANKNIFTY research lab (MISSION V19): data loader, screening, engine of record."""

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)  # MISSION V19 C3: this process never holds the token
