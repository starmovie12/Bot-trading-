"""BANKNIFTY options bot ka code (MISSION V19: paper by default, live locked).

Milestone abhi: M0 (Neev). Kisi broker se connection NAHI hai.
"""

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)  # MISSION V19 C3: this process never holds the token

__version__ = "0.0.1"
