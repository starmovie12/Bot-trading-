# P3R ROUNDS (owner order D-40) · DESIGN only · stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]

| round | k after | best candidate | net / trade | gates failed | next round changes |
|---|---|---|---|---|---|
| R1 | 67 | R1-5-0.005-C2 (expiry-week momentum, scratch 45) | +₹620.32 (51 trades, 0.14 a day) | folds 1/4, null 0.054, ST11 (0.14 < 0.5 a day), ST4c (-₹93 without the best 5) | the fades have NO index-point edge (S2 means -15 .. +10 points); only expiry-week momentum moved the index (+43.8 points, p 0.032) but too rarely and on a few big days. R2: loss-first structures and index-based exits (ATR / range stop on the index, break-even trail, premium cap, near-expiry and 1-OTM strikes) on momentum families that can fire >= 0.5 a day; needs new matrix columns. Note: R1-2's grid was set in VIX points (vix_chg is in points, not %), so it tested "VIX up since the open", not a spike; a scaled spike test needs its own pre-registration |
