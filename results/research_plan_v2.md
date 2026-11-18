# RESEARCH PLAN v2 (owner order 2, D-42) · EXPLORE on DESIGN, CONFIRM on untouched data · Phase 4 closed

Math: break-even ~14 index points a trade (ATM, delta 0.5, stressed ~₹217). More trades help only if EACH trade's edge
is larger; so look for (1) a structural source (time decay, mispriced IV) or (2) a model that adds many weak signals.

| family | logic | test plan | data |
|---|---|---|---|
| F6 structure + cost (table, not a trial) | the strike with the lowest break-even in index points: ITM (delta 0.6-0.7) vs ATM vs CAP15, and hold time vs theta | empirical delta (option change / index change) and decay per hour from DESIGN option bars | have |
| F3 ML probability (R8) | many weak features -> P(move > break-even + 5 points in H min); the threshold sets the day's trades (no-edge day = NO-TRADE) | logistic (numpy, L2) and boosted stumps (numpy), <= 20 features, walk-forward 4 test folds, 1-day embargo; H and threshold chosen inside training folds only; x exits {CAP15-XH, CAP15-XI2} x the day-rule grid | have |
| F4 near-expiry seed | R7-2 widened: DTE <= 10, hold to close, trail, F3 as a filter | EXPLORE (R9); CONFIRM on the old holdout + fresh days | have (+ older index history: S2 only) |
| F5 regime switch | at 10:00 call the day trend or range (eff, realised vol, VIX change, breadth); trend -> momentum long option; range -> defined-risk selling (research) or NO-TRADE | classifier in training folds; R10 | have |
| F2 implied vs realised | opening ATM straddle = the market's expected move: (a) move > X% of it -> momentum; (b) cheap IV + rising RV -> long option; (c) rich IV + range day -> defined-risk selling (research) | needs iv_greeks_1m, chain_metrics_1m, iv_daily_DERIVED (in the data repo, not yet checked out; size to check first) | in repo |
| F1 volatility premium (research only, D-42 (4)) | iron fly / iron condor at a fixed time; IV percentile filter; skip on a trend signal; wing width, exit time, underlying-move or MTM stop | new 4-leg outcomes, long wings bought FIRST, never naked; costs 8 orders stressed | have |

Day rules (D-42 (1)): every S3 run spans max entries a day {1, 2, 3, 5, 10, 15} x stop after a loss {yes, no} x
cool-off {15, 30} min; one structure at a time, 1 lot, a daily ₹ loss lock = 2 x the structure's max loss (loss-first;
Monte Carlo sizing at CONFIRM); ranking prefers the higher frequency among passers.

EXPLORE screen (DESIGN): stressed net > 0, walk-forward >= 3 of 4 folds, both VIX halves, grid neighbours positive,
net >= 0 at 1.5 x the stressed cost, ST4c, ST11 >= 0.5 a day, matched null p < 0.01; Holm-k reported (not a gate).
CONFIRM (untouched): <= 3 pre-registered candidates, Bonferroni, once: the old holdout (HOLDOUT_2ND_USE), older
history if it comes (sealed first), fresh days after 2026-11-13; pass = >= 60 trades and the 90% CI lower bound of the
stressed net per trade > 0. STRATEGY PASS = EXPLORE + CONFIRM. A failed set is never re-tried after a tweak.

Data asked (DATA_REQUEST.md, docs/FETCH_HISTORY.md): older index + VIX 1 minute 2022-01 .. 2024-09 (script given;
expired option candles 2022-24 are NOT available from Upstox: its expired API keeps ~6 months of expiries, SOURCE);
recorder bid / ask (item 7); event calendar (item 5); new days as they come.
Order: R8 F3 (+ F6 table) -> R9 F4 -> R10 F5 -> R11 F2 -> R12 F1; a progress card every 3 rounds.
