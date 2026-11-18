# FINAL RESEARCH REPORT (P3R, owner orders D-40 / D-42 / D-43) · 2026-11-18

**Bottom line: no strategy passed.** Across 354 counted trials on the 362 DESIGN days (2024-11-21 .. 2026-07-03;
the 90 holdout days were not used after their one 2026-11-18 opening), no 1-lot intraday BANKNIFTY option rule
reached the EXPLORE screen (stressed net > 0, walk-forward >= 3 of 4, both VIX halves, neighbours, 1.5 x cost, ST4c,
ST11 >= 0.5 trades a day, null p < 0.01). So nothing went to CONFIRM, there is no STRATEGY PASS card, and Phase 4
stays closed. Every ₹ below is per trade, PRE-TAX, stressed costs, [BACKTEST·in-sample on DESIGN] unless marked.

## 1. What was tested (results/rounds.md, results/r*_board.md, trials.jsonl)
| block | families | trials | result |
|---|---|---|---|
| Phase 3 (V19) | Dimaag controls, ORB, VWAP, gap, vol-expansion, lead-lag, last hour, fades, + VIX filter, + debit spread | 13 | no candidate; A1+b1 carried, holdout -₹351 (HOLDOUT_FAIL) |
| STEP 0 | 15 buckets x 2 sides (diagnosis seeds) | 30 | descriptive; counted in k |
| R1-R7 (D-40) | fades, VWAP stretch, gap fade, expiry-week momentum, lead-lag, ORB variants, trend-day, vol expansion, OI positioning, basis, VIX %, passive entry, pullback, wide first hour, prior-day family, hold to close, no-stop holds | 147 | no finalist |
| R8-R13 (D-42) | F3 ML (logistic, boosted stumps; day-rule grid 1..15 entries), F6 strike table, F4 near-expiry widened, F1 iron fly / condor (research only), F2 implied vs realised, F5 regime switch, seeds on ITM2 | 164 | nothing passed EXPLORE |

## 2. Why it failed: the cost wall (results/diagnosis.md, results/f6_breakeven.md, results/r10_board.md)
- One ATM long-option round trip costs about **₹217 stressed** (spread ₹61, brokerage ₹60, STT ₹34, slippage ₹24,
  exchange + SEBI + IPFT ₹22, GST ₹15, stamp ₹1); ₹130 unstressed. With 1 lot the cost is nearly fixed per trade.
- In index points that is a **break-even of 14-17 points per trade** for every strike (ITM2 13.9, ATM 14.8,
  CAP15 16.1 over 30 min): choosing the strike cannot remove the wall.
- A 4-leg defined-risk sale costs about **₹930 stressed** (8 orders) against an intraday premium of only **+₹53 ..
  +₹86 gross**: selling the premium intraday cannot pay for itself on 1 lot.
- More trades only add cost: the F3 models and the 1..15-entry day-rule grid were negative out of sample in all 96
  trials (median -₹684).

## 3. Why the signals were not enough
- **Direction over 60 minutes has no edge** in any family: index-point means sit within about +-15 points of zero
  (the break-even) with p > 0.05 almost everywhere (R1-R5, R11).
- **Edges appear only to the close, and only on rare days** (near expiry with a big morning move, a 5-of-5 trend
  call, a gap that keeps going). Those days are few (28-120 trades in 362 days), the result rests on the best 5 trades
  (ST4c fails), and a rule that holds to the close trades at most once a day (ST11 needs 0.5 a day).
- **Multiple testing:** with k = 354, a single good-looking row is expected by chance; Holm at this k would need p
  around 0.0001, and the CONFIRM step exists for exactly this reason.

## 4. The best seeds (none passed; kept only for the forward shadow, results/forward_shadow.md)
| seed | rule | ₹ / trade | trades (a day) | max loss | what fails |
|---|---|---|---|---|---|
| S1 gap-and-go | 09:45, abs(gap) >= 0.1%, the day agrees; ITM2 long option, hold to 15:10, no index stop (R13-3-0.001-ITM2-XH) | +₹525 | 120 (0.33) | ₹40,938 | low-VIX half -₹401, ST11, ST4c (-₹190), null 0.031 |
| S2 near-expiry | 10:30, DTE <= 7, abs(ret_open) >= 0.4%; CAP15 long option, hold, index stop -2R (R7-2-0.004-CAP15-XH2) | +₹1,223 | 35 (0.10) | ₹14,991 | folds thin, ST11, ST4c (-₹446) |
| S3 strong trend | 10:00, trend score 5 of 5; CAP15 long option, hold to 15:10 (R12-1-5-CAP15-XH) | +₹948 | 28 (0.08) | ₹15,224 | folds thin, ST11, ST4c (-₹595), null 0.037 |

## 5. What could change the picture (DATA_REQUEST.md, docs/FETCH_HISTORY.md)
- **Fresh days after 2026-11-13** (the owner adds them): the forward shadow of S1-S3, and, if any rule ever passes
  EXPLORE, the CONFIRM sample.
- **Index + VIX 1-minute 2022-01 .. 2024-09** (script in docs/FETCH_HISTORY.md, ~40 MB ESTIMATE): sealed first, then
  the index-point tests of S1-S3 on about 2.5 times the days.
- **Recorder bid / ask**: the measured spread replaces the ESTIMATE; at most it removes the stress part of the spread
  and slippage (about ₹43 of the ₹217), not the charges, so it cannot by itself open a route.
- Expired option candles for 2022-24 are not available from Upstox (expired API: ~6 months, Plus plan; SOURCE).

## 6. Honest reading
With 1 lot, intraday-only holding, these costs and these 362 days, no rule was found that trades on most days AND
earns more than its costs robustly. The few positive pockets are rare, concentrated in a handful of days, and fail
the robustness gates; they are watched forward, not traded. No bot is built (D-40); the old holdout stays unused for
any future CONFIRM.
