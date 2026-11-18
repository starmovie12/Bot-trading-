# DIAGNOSIS (P3R STEP 0, owner order D-40): why A1+b1 lost

DESIGN only (362 days; the old holdout stays closed). ₹ per trade, PRE-TAX, [BACKTEST·in-sample]. Source:
`python -m lab.diagnose` -> data/lab/diagnosis.json. Bucket numbers are descriptive seeds, not evidence: the
30 bucket cells below count as trials in k (D-41).

## 1. Cost of one round trip (A1+b1, 24 engine trades, lot 30; gross ₹158.43)

| part | stressed ₹ | unstressed ₹ |
|---|---|---|
| spread (₹1.00 / unit ESTIMATE, x2 .. x4 by bucket) | 60.83 | 29.79 |
| brokerage (₹20 x 2 orders, x1.5) | 60.00 | 40.00 |
| STT (sell side, by date, x1.5) | 34.38 | 22.92 |
| slippage (₹0.20 / unit / side, x2) | 23.83 | 11.92 |
| exchange + SEBI + IPFT (x1.5) | 21.88 | 14.59 |
| GST (x1.5) | 14.74 | 9.83 |
| stamp (x1.5) | 0.92 | 0.61 |
| **total** | **216.58** | **129.66** |

Biggest parts: spread (₹61) and brokerage (₹60), then STT. The stress adds ₹87 a trade
(2x spread alone +₹31). Unstressed, the gross ₹158 would beat ₹130; stressed it does not. The stress stays (no
gate is loosened): the cost is about fixed per trade (1 lot), so only a bigger gross per trade can beat it.

## 2. Gross by bucket: every DESIGN decision row, ATM long, EXIT0, both sides (momentum = the side of the
day's move so far, fade = the other); cost = stressed

| group | bucket | rows | gross momentum | gross fade | cost | gross > cost |
|---|---|---|---|---|---|---|
| time | 09:45-10:29 | 3165 | -49.2 | -70.2 | 213.5 | no |
| time | 10:30-11:59 | 6389 | -30.0 | 0.7 | 213.0 | no |
| time | 12:00-13:29 | 6378 | -130.8 | 115.7 | 214.6 | no |
| time | 13:30-14:30 | 4611 | -198.0 | 136.9 | 225.2 | no |
| DTE | 0-2 | 2415 | -178.1 | 26.4 | 184.1 | no |
| DTE | 3-7 | 3609 | 79.4 | -55.3 | 195.9 | no |
| DTE | 8-15 | 5924 | -131.5 | 122.1 | 215.1 | no |
| DTE | 16+ | 9644 | -129.4 | 61.9 | 232.5 | no |
| VIX | low < 12.2 | 7220 | -61.0 | -34.4 | 218.9 | no |
| VIX | mid | 7080 | -78.4 | 7.5 | 208.2 | no |
| VIX | high >= 15.0 | 7292 | -161.1 | 188.5 | 221.4 | no |
| day | trend (eff >= 0.35) | 1007 | -106.4 | 55.1 | 212.8 | no |
| day | range (eff <= 0.20) | 18196 | -100.8 | 77.7 | 217.0 | no |
| day | gap |gap| >= 0.5% | 5475 | -83.6 | 31.2 | 221.3 | no |
| day | no gap | 16056 | -105.1 | 60.8 | 214.8 | no |

No bucket has gross > cost. Seeds (the gap is smallest): FADE after 12:00 (+₹116 / +₹137), FADE at high VIX
(+₹189), FADE at DTE 8-15 (+₹122), MOMENTUM at DTE 3-7 (+₹79). Momentum loses gross almost everywhere: chasing
the day's move pays the option's IV drop (spot-vol link) and the reversal. Moneyness: the matrix holds only the
ATM long and the ATM / +2 OTM spread, so strike choice is untested so far (Round 2 builds it).

Cheap filter (break-even vs move): break-even = 14.2 index points (cost / lot / ATM delta 0.5, ASSUMPTION);
p90 of the |index move| next 30 / 60 / 120 min: 09:45-10:29 186 / 248 / 332; 10:30-11:59 150 / 217 / 319; 12:00-13:29 145 / 210 / 302; 13:30-14:30 142 / 213 / nan.
Moves are large enough; the loss is direction (p) and follow-through (W), not the size of the market.

## 3. MAE / MFE (A1+b1, 24 DESIGN trades; R = 30% of the premium)

Exits: stop 1, target 2, scratch 18, time 3. Median MFE +0.28R, median MAE -0.16R, median hold 32 min.
Only 2 trades were up >= 0.5R and closed at a loss; 0 were up >= 1R and lost. The stop is not too tight
(1 stop in 24); the target is far (2 of 24 reached 2R). The real killer is the 30-minute scratch on trades
that go nowhere: 75% of the trades pay the full cost for almost no gross. Entries lack follow-through.

## 4. Max loss ₹35,700 per trade (against loss-first)

It comes from 2025-04-28, 55300 CE (ATM, nearest MONTHLY expiry, about a month away), premium
1179.65 points x lot 30 = ₹35,390 + stressed costs. A long option's by-construction bound is the whole
premium (a gap can skip the stop); the -30% stop alone would lose about ₹10,617. Median premium paid 699.
ATM premium at 09:45 by days to expiry (median, points): DTE 0-2: 200.1, DTE 3-7: 383.8, DTE 8-15: 560.6, DTE 16+: 811.6.
Fixes (to test, pre-registered): a premium cap, near-expiry or OTM strikes, a debit spread; each changes p, W and C.
