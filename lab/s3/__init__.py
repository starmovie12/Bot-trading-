"""Program S3 (BANKNIFTY_STRATEGY_V3.md): the Adaptive Sniper backtest; numbers from config/strategy_v3.toml."""

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)  # MISSION V19 C3: this process never holds the token
