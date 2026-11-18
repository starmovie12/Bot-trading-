# RESEARCH PLAN (P3R, owner order D-40) · DESIGN only · every gate as before, none loosened

Edge per trade: E = p x W - (1 - p) x L - C > 0 (₹, stressed, PRE-TAX). STEP 0 (results/diagnosis.md) says:
C is about ₹217 a trade and nearly fixed (1 lot: brokerage, spread and slippage per unit); the market moves enough
(p90 index move in 30 min 140-190 points vs a 14-point break-even); A1+b1 lost on p and W (75% of trades scratched
at 30 min with no follow-through). Chasing the day's move loses gross almost everywhere; fading it is the seed.

## Options (each is tested only as a pre-registered trial; k counts every one)
| route | what changes | how it is tested |
|---|---|---|
| (b) p, W: fade, not chase | fade the day's move after 12:00; fade a VIX fear spike; VWAP stretch reversion; gap fade with a 15-min reversal; follow the two big banks when the index lags; expiry-week momentum (the DTE 3-7 seed) | R1 (now) |
| (b) hold for follow-through | patient exits: scratch 45 min (C2), time-stop 60 (C3) next to EXIT0 | R1 exit grid |
| (c) L: loss-first structure | stop on the INDEX (ATR / the opening range), trail to break-even at +1R, premium cap, near-expiry or 1-OTM strike, debit spread | R2 (needs new matrix columns) |
| (a) C: honest cost cuts | fewer trades with bigger moves; passive limit entry filled only when the price trades THROUGH the limit; no entry in the first / last buckets; measured p90 spread once recorder bid / ask exists (none yet: DATA_GRADE B) | R2-R3 |
| new data | recorder bid / ask (DATA_REQUEST item 7), event calendar (item 5), longer index history (item 6) | asked in DATA_REQUEST.md |

## Funnel per round (cheap first)
1. Break-even move vs the p90 forward index move over the hold horizon at the idea's rows (needs p90 >= 2 x break-even).
2. Index points: the signal's forward index move (60 min, its side) vs break-even, matched null 1,000 runs, p <= 0.05.
3. Option P&L (engine-matched lab matrix, stressed costs, the RISK SHELL day rules) on each survivor x the exit grid.

## PASS = all at once (DESIGN, stressed)
net / trade > 0 · walk-forward >= 3 of 4 folds positive (>= 15 trades each) · both VIX halves positive (>= 15
trades each) · null test after Holm over the total k (finalist N = max(10,000, 400 k)) · every +-1 grid step
neighbour positive (knife edge = fail) · ST11 >= 0.5 trades a day · net >= 0 at 1.5 x the stressed cost · ST4c
(without the best 5) > 0 · ST7 entry delay +1 / +2 bars > 0 (engine of record) · max loss per trade reported,
loss-first rank among passers. Then HOLDOUT_2ND_USE once; then forward shadow on days after 2026-11-13.

## Round rules
PLAN.md §PREREG-R<n> before the round (<= 10 ideas; params, exit grid and trial cap frozen at the commit) · every
tested combination at every funnel stage is one trials.jsonl line (the 13 earlier + the 30 STEP 0 bucket cells
included: D-41) · results/rounds.md gets one line per round · a progress card every 3 rounds · a failed family
gives way to the next family; when all are spent, DATA_REQUEST.md names the data that opens a new route.
