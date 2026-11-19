# PLAN (MISSION V19): one tick line per step
- [x] Phase 0 ORIENT
- [x] Phase 1 DATA INTAKE (+ DG audit)
- [x] Phase 2 FACTS
- [x] Phase 2b PROBE (2b.1 public: master + feed docs; 2b.2 skipped: TOKEN not set)
- [x] Phase 2c FEASIBILITY
- [x] Phase 1b DATA REQUEST + STOP-1 skipped (results/stage1_card.md)
- [x] INTAKE-H (cycle 1: Phase 1 snapshot kept, DATA_SHA 9e7a49d4; holdout sealed in holdout_log.jsonl)
- [ ] Phase 3 LAB (grade B: REAL option candles, spreads ESTIMATE; DESIGN 362 days 2024-11-21..2026-07-03, HOLDOUT 90 days 2026-07-06..2026-11-12)
  - 3a matrix + market facts (5-minute decision bars; REAL option OHLC for ATM and 2 OTM, nearest monthly expiry; lot by contract)
  - 3b blueprint, prefilter, bracket in §PREREG-0 (cap 30 trials) · 3c tournament + contracts + engine of record
  - 3d loss-first rank + STRATEGY.md · 3e holdout once + Monte Carlo + limits + ladder + verdict
- [ ] 4A · 4B · 4C · 5 · 6 → STOP-2
- [ ] Phase 7 · P7rev → FINAL-2

## WANT-LIST (Phase 1; gap ids from docs/DATA_GAPS.md)
- Real decision-time bid / ask, spread and slippage (G5 recorded bid / ask NONE): DATA-R from the owner's Recorder (Part R). Until then spread = ESTIMATE x 2.
- Event calendar (RBI policy, large bank results, budget): the pack marks it MISSING; Phase 2 fetches official dates where reachable.
- 2026-11-13 spot 1m (G1 MISSING_SPOT): one day; excluded meanwhile (API fill needs a token).
- ATM strikes for 2024-11-28 .. 2024-12-24 (G3): excluded from option P&L meanwhile (expired options: Plus plan).
- opt_wide_1m for 7 days in Mar-Apr 2026 (G3): far strikes only; NICE.
- Next-month option contracts (only 25 days carry two expiries): needed only if a candidate rolls before expiry; NICE.
- Spot / futures / VIX before 2024-10-01: NICE (direction features and regime check only).
- 2c economics: margin to sell Leg 2 of a debit spread (Phase 2 SOURCE), official charges and lot history (Phase 2).

## §PREREG-0 (committed before any OUTCOME; the bracket of 3b is appended below before any trial runs)
RISK SHELL (identical for every candidate and control; constants, never tuned):
- Structures: LONG = 1 lot of the ATM option of the nearest monthly expiry (CE for an up signal, PE for a down signal);
  SPREAD = debit spread, buy ATM and sell 2 strikes (200 points) further OTM, same expiry (Leg 1 filled first).
- Entry window: decision on 5-minute index closes 09:30..14:30 IST; entry at the open of the next non-stale 1-minute
  option bar (v > 0, not stale) within 2 bars, else NO_FILL_STALE. One structure at a time; <= 2 entries a day.
- Max loss by construction: LONG = premium x lot + stressed costs; SPREAD = debit x lot + stressed costs (K1 sizes the cap
  from this in 3e).
- Stops: LONG at -30% of the premium, SPREAD at -40% of the debit (R = the stop distance); tighten-only trail: stop to
  break-even after +1R. Pessimistic intrabar rule: a bar touching stop and target exits at the stop (a gap: the worse open).
- Day rules: the day ends after a full loss (stressed net loss >= 0.5 x that trade's by-construction max loss); cool-off
  30 minutes after any losing trade; force-flat 15:10 IST (before the stressed MIS cutoff 15:15, D-17).
- Costs (ST7, PASS side): charges by date x 1.5; slippage ₹0.20 per unit per side x 2; spread = 2 x the ₹1.00 ATM bid-ask
  ESTIMATE (half per side), 4 x in 09:15-09:25 and 14:45-15:10, 3 x on an expiry day; an exit on a stale bar pays 2 x
  spread. Kill side: slippage ₹0, spread 0 (fewer than 100 measured snapshots), charges as sourced.
EXIT PRESETS (lab/build_matrix.py PRESETS): EXIT0 = stop as above, target +2R, scratch 30 min (exit when value <= entry
and the trail is off), time-stop 120 min. Round C grid (finalists only, <= 4 each, <= 8 in all, each a trial):
C1 scratch 20 · C2 scratch 45 · C3 time-stop 60 · C4 target +3R.

BRACKET (3b; lab/ideas.py holds the exact rules and params; trials counted in trials.jsonl; cap 30):
- Controls (4): K1 ORB break + retest {near 0.001} · K2 VWAP pullback {trend 0.004, eff 0.3, near 0.0005} ·
  K3 afternoon momentum {move 0.005} · K4 fixed 10:00 entry {t 45}. All LONG, EXIT0.
- Round A (5 after the prefilter, results/prefilter.md): A1 30-min range break {eff 0.35} · A2 volatility expansion
  {ratio 1.5, move 0.0025} · A7 first-30-min -> last hour {t 315} · A9 afternoon extreme fade {near 0.001, eff 0.25} ·
  A10 trend resumption {eff 0.4}. All LONG, EXIT0. Screen: stressed net mean > 0, ST4, ST11, screening null (1,000 runs).
- Round B (<= 6): the best <= 3 Round A ideas by the loss-first order (if none survived, the 2 least bad), each with two
  add-ons in this order: (b1) VIX falling at entry (vix_chg < 0), (b2) SPREAD structure instead of LONG.
- Round C (<= 8): finalists only, presets C1..C4 of the exit grid above.

## §PREREG-R1 (P3R round 1, owner order D-40; committed before any R1 number is computed)

Data: DESIGN 362 days (data/lab/matrix.npz); the old holdout stays closed. Structure: 1 lot ATM long option, nearest
monthly expiry (OUTCOMES `<preset>|LONG`); RISK SHELL day rules of §PREREG-0; stressed costs (ST7). Trial cap added: 120
Funnel: S1 p90 forward |index move| (60 min) >= 2 x break-even (14.2 points) · S2 forward index move in the idea's
side (60 min, signals >= 60 min apart, <= 2 a day) > 14.2 points and matched-null p <= 0.05 (1,000 runs, SEED) ·
S3 option P&L on each S2 survivor x exit grid {EXIT0, C2, C3}; gates as in results/research_plan.md (PASS).
Every S2 combination and every S3 combination is one trials.jsonl line (id R1-<idea>-<value>[-<exit>]).
D0-1 .. D0-30: the 30 STEP 0 bucket cells (computed before this section; counted in k with p = 1, never candidates).
Neighbours: the adjacent grid values; an end value that reaches the neighbour gate also runs its outside neighbour
(listed below), counted as a trial.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R1-1 | fade the day's move after 12:00 | STRUCTURAL (intraday reversal, spot-vol) | t 165..255, abs(ret_open) >= X, side = -sign(ret_open) | X 0.003, 0.005, 0.007 (0.001, 0.009) |
| R1-2 | fade a VIX fear spike | STRUCTURAL (fear spikes mean-revert) | t 45..255, vix_chg >= X and ret_open < 0 -> CE; vix_chg <= -X and ret_open > 0 -> PE | X 0.03, 0.05, 0.08 (0.01, 0.11) |
| R1-3 | VWAP stretch reversion | STRUCTURAL (liquidity provision) | t 75..255, abs(vwap_dist) >= X, side = -sign(vwap_dist) | X 0.0025, 0.004, 0.006 (0.001, 0.008) |
| R1-4 | gap fade after a 15-min reversal | STRUCTURAL (overnight imbalance) | t 30..75, abs(gap) >= X, sign(ret15) = -sign(gap), side = -sign(gap) | X 0.004, 0.006, 0.008 (0.002, 0.010) |
| R1-5 | expiry-week momentum | DIRECTION (DTE 3-7 seed) | dte 3..7, t 45..165, abs(ret_open) >= X, side = sign(ret_open) | X 0.003, 0.005, 0.007 (0.001, 0.009) |
| R1-6 | follow HDFCBANK + ICICIBANK when the index lags | STRUCTURAL (index arbitrage lag) | t 30..255, hdfc15 and icici15 >= X and ret15 <= X/2 -> CE; mirror -> PE | X 0.004, 0.006, 0.008 (0.002, 0.010) |
| R1-7 | range-day band fade | STRUCTURAL (range-day liquidity) | t 105..285, eff <= 0.20, abs(ret_open) >= X, side = -sign(ret_open) | X 0.004, 0.006, 0.008 (0.002, 0.010) |

## §PREREG-R2 (P3R round 2, owner order D-40; committed before any R2 number is computed)

Data: DESIGN 362 days; the old holdout stays closed. Funnel S1 / S2 exactly as §PREREG-R1 (60 min, break-even 14.2
points, signals >= 60 min apart, <= 2 a day, matched null 1,000 runs). Trial cap added: 150
S3 builds new outcomes (lab/build_r2.py -> data/lab/matrix_r2.npz) for every DESIGN decision row, both sides, on the
engine-of-record data reader: entry at the next non-stale option bar within 2 bars (as the engine), 1 lot, RISK SHELL
day rules, stressed costs (ST7, as R1). Index risk unit R = max(0.0015, rv30 x sqrt(60)) x spot (the next-hour move
implied by the last 30 minutes' 1-minute volatility; floor 0.15%). Index levels are read from 1-minute index bars;
stop before target in the same minute; the break-even / trail switch acts from the next minute.
Structure grid: ATM = the ATM strike of the nearest monthly expiry; CAP15 = the strike nearest ATM, walking OTM (CE up,
PE down, <= 10 steps of 100), whose entry premium x lot <= ₹15,000 (none -> no trade); max loss per trade <= ₹15,000 +
stressed costs.
Exit grid: XI1 = index stop -1R, break-even after +1R, index target +2R, time-stop 120 min, force-flat 15:10;
XI2 = index stop -1R, break-even after +1R, trail 1R behind the best index price after +2R, no target, force-flat 15:10.
Option fill at an index-triggered exit: stop / break-even / trail -> the option bar's LOW of that minute (pessimistic);
target, time, force-flat -> its close; a missing bar -> the last close, stale (2 x spread).
S3 combinations = each S2 survivor x {ATM, CAP15} x {XI1, XI2}; ids R2-<idea>-<value>[-<structure>-<exit>].
PASS gates and neighbours as §PREREG-R1 / results/research_plan.md (the outside neighbour runs only when needed).

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R2-1 | 30-min range break, low trend gate | DIRECTION | t 30..255, eff >= X, spot beyond or30 with ret15 the same way; side = the break | X 0.10, 0.20, 0.30 (0.00, 0.40) |
| R2-2 | 15-min range break by a margin | DIRECTION | t 30..255, spot beyond or15 by >= X (fraction of or15 level), ret15 the same way; side = the break | X 0.001, 0.002, 0.003 (0.000, 0.004) |
| R2-3 | late-morning day-direction momentum | DIRECTION | t 75..165, abs(ret_open) >= X, side = sign(ret_open) | X 0.002, 0.004, 0.006 (0.000, 0.008) |
| R2-4 | near-expiry momentum (R1-5 widened to DTE 0..7) | DIRECTION | dte 0..7, t 45..165, abs(ret_open) >= X, side = sign(ret_open) | X 0.002, 0.004, 0.006 (0.000, 0.008) |
| R2-5 | 30-min momentum aligned with the day | DIRECTION | t 45..255, abs(ret30) >= X, sign(ret30) = sign(ret_open), side = sign(ret30) | X 0.002, 0.003, 0.004 (0.001, 0.005) |
| R2-6 | trend-day continuation | DIRECTION | t 75..195, eff >= X, side = sign(ret_open) | X 0.30, 0.40, 0.50 (0.20, 0.60) |
| R2-7 | volatility expansion with a 15-min move | DIRECTION | t 30..255, rv5 >= X x rv30, abs(ret15) >= 0.0015, side = sign(ret15) | X 1.3, 1.6, 2.0 (1.0, 2.4) |
| R2-8 | VWAP-side momentum | DIRECTION | t 45..255, abs(vwap_dist) >= X, sign(ret15) = sign(vwap_dist), side = sign(vwap_dist) | X 0.001, 0.002, 0.003 (0.000, 0.004) |

## §PREREG-R3 (P3R round 3, owner order D-40; committed before any R3 outcome is computed)

Data: DESIGN 362 days; the old holdout stays closed. New features (lab/build_r3.py features; only their scale was
read before this section: p90 oi_skew 0.135, basis_chg 0.00072, vix_pct 0.030): oi_skew = (PE OI change - CE OI
change since 09:29) / (CE + PE OI at 09:29) over ATM +- 5 strikes of the nearest monthly expiry; basis_chg = futures
basis now - at 09:30; vix_pct = VIX change since the open / VIX open (R1-2's intent, now in %). Trial cap added: 100
Funnel S1 / S2 as §PREREG-R1. S3 combinations = each S2 survivor x {CAP15-XI2 (market entry, as R2), CAP15P-XI2
(passive entry)}. Passive entry: a buy limit at the last closed option bar's close, filled only when a bar in the next
3 minutes trades THROUGH it (low < limit), at the limit; no fill -> no trade; the entry pays no half spread, keeps the
stressed slippage; the exit pays the full stressed spread. Strike: CAP15 walk on the limit price. ids
R3-<idea>-<value>[-<structure>-<exit>]. PASS gates and neighbours as §PREREG-R1 / results/research_plan.md.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R3-1 | option-writer positioning | STRUCTURAL (writers defend strikes) | t 45..255, oi_skew >= X -> CE; oi_skew <= -X -> PE | X 0.10, 0.15, 0.20 (0.05, 0.25) |
| R3-2 | writer positioning + the day's move agree | STRUCTURAL | R3-1 and side = sign(ret_open) | X 0.10, 0.15, 0.20 (0.05, 0.25) |
| R3-3 | futures basis momentum | STRUCTURAL (futures demand leads) | t 45..255, basis_chg >= X -> CE; <= -X -> PE | X 0.0005, 0.0008, 0.0011 (0.0002, 0.0014) |
| R3-4 | basis + the 15-min move agree | STRUCTURAL | t 45..255, abs(basis_chg) >= X, sign(ret15) = sign(basis_chg), side = sign(basis_chg) | X 0.0005, 0.0008, 0.0011 (0.0002, 0.0014) |
| R3-5 | fade a VIX spike (in %) | STRUCTURAL (fear spikes mean-revert) | t 45..255, vix_pct >= X and ret_open < 0 -> CE; vix_pct <= -X and ret_open > 0 -> PE | X 0.03, 0.045, 0.06 (0.015, 0.075) |
| R3-6 | follow a VIX move (in %) | DIRECTION | t 45..255, vix_pct >= X and ret_open < 0 -> PE; vix_pct <= -X and ret_open > 0 -> CE | X 0.03, 0.045, 0.06 (0.015, 0.075) |
| R3-7 | near-expiry momentum (R2-4 rule) with passive entry next to market | DIRECTION | dte 0..7, t 45..165, abs(ret_open) >= X, side = sign(ret_open) | X 0.003, 0.004, 0.005 (0.002, 0.006) |

## §PREREG-R4 (P3R round 4, owner order D-40; committed before any R4 number is computed)

Data: DESIGN 362 days (no new data in the data repo: DATA_SHA unchanged); the old holdout stays closed. Feature scales
read before this section (no outcomes): first-hour range / spot at 10:15 p50 0.0062, p75 0.0083; distance to the day's
extreme after 12:00 p25 0.0009; abs(gap) p50 0.0025, p75 0.0050. Trial cap added: 80
Funnel S1 / S2 as §PREREG-R1. S3 on data/lab/matrix_r2.npz: each S2 survivor x {CAP15-XI2, CAP15-XI1} (§PREREG-R2
definitions). ids R4-<idea>-<value>[-CAP15-<exit>]. PASS gates and neighbours as §PREREG-R1 / research_plan.md.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R4-1 | gap follow beyond the 15-min range | DIRECTION | t 30..75, abs(gap) >= X, sign(ret15) = sign(gap), spot beyond or15 on the gap's side; side = sign(gap) | X 0.003, 0.005, 0.007 (0.001, 0.009) |
| R4-2 | 30-min range break, then a pullback to the range edge | DIRECTION | t 45..255, day_hi > or30_hi and abs(spot / or30_hi - 1) <= X and ret15 > 0 -> CE; mirror at or30_lo -> PE | X 0.0005, 0.001, 0.0015 (0.00025, 0.002) |
| R4-3 | wide first hour = trend day: follow it | DIRECTION | t = 60 only, (day_hi - day_lo) / spot >= X, side = sign(ret_open) | X 0.006, 0.008, 0.010 (0.004, 0.012) |
| R4-4 | afternoon push to a new day extreme | DIRECTION | t 180..285, spot >= day_hi x (1 - X) and ret30 > 0 -> CE; spot <= day_lo x (1 + X) and ret30 < 0 -> PE (not both) | X 0.0005, 0.001, 0.0015 (0.00025, 0.002) |
| R4-5 | gap follow while VIX falls | DIRECTION | t 45..120, abs(gap) >= X, vix_chg < 0, sign(ret_open) = sign(gap); side = sign(gap) | X 0.003, 0.005, 0.007 (0.001, 0.009) |
| R4-6 | two 15-min candles the same way (second-candle confirmation) | DIRECTION | t 45..255, sign(ret15) = sign(ret30 - ret15), abs(ret30) >= X; side = sign(ret30) | X 0.002, 0.003, 0.004 (0.001, 0.005) |

## §PREREG-R5 (P3R round 5, owner order D-40; committed before any R5 number is computed)

Data: DESIGN 362 days (the data repo is unchanged: DATA_SHA 9e7a49d4); the old holdout stays closed. New family:
the PRIOR DAY (lab/build_r5.py; only the scales were read: prev_rr p25 0.78 / p50 0.99; prev_cl p25 0.17 / p75 0.82;
prev_ret p10 -0.0083 / p90 0.0102; 30% of rows are above the prior high). Trial cap added: 60
Funnel S1 / S2 as §PREREG-R1. S3 on data/lab/matrix_r5.npz (= matrix_r2 outcomes): each S2 survivor x {CAP15-XI2,
CAP15-XI1}. ids R5-<idea>-<value>[-CAP15-<exit>]. PASS gates and neighbours as §PREREG-R1 / research_plan.md.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R5-1 | a narrow prior day, then a 30-min range break | STRUCTURAL (volatility contraction -> expansion) | t 30..165, prev_rr <= X, spot beyond or30 with ret15 the same way; side = the break | X 0.65, 0.80, 0.95 (0.50, 1.10) |
| R5-2 | prior close at its extreme, today the same way | DIRECTION | t 30..120, prev_cl >= 1 - X and ret_open > 0 -> CE; prev_cl <= X and ret_open < 0 -> PE | X 0.15, 0.25, 0.35 (0.05, 0.45) |
| R5-3 | a prior trend day, today continues it | DIRECTION | t 45..120, abs(prev_ret) >= X, sign(ret_open) = sign(prev_ret); side = sign(prev_ret) | X 0.004, 0.007, 0.010 (0.001, 0.013) |
| R5-4 | break of the prior day's high / low | DIRECTION | t 30..255, spot >= prev_hi x (1 + X) and ret15 > 0 -> CE; spot <= prev_lo x (1 - X) and ret15 < 0 -> PE | X 0.000, 0.001, 0.002 (-0.001, 0.003) |

## §PREREG-R6 (P3R round 6, owner order D-40 + "no new data: continue on this data"; before any R6 number)

Data: DESIGN 362 days (no new data); the old holdout stays closed. New family: HOLD TO CLOSE at a fixed decision time
(one signal a day at most). Only scales were read: abs(ret_open) p50 0.0034 at 11:00, 0.0037 at 12:00; eff p50 0.17 at
11:00; abs(gap) p50 0.0025. Trial cap added: 60
Funnel change, pre-registered for this round only: S2 measures the forward index move from the decision to 14:30 (the
last decision row) instead of 60 min (the trades hold to the close); S1 / S2 thresholds and the null as §PREREG-R1.
S3 on data/lab/matrix_r2.npz: each S2 survivor x {CAP15-XI2, ATM-XI2} (index stop -1R, break-even, 1R trail, no
target, force-flat 15:10). ids R6-<idea>-<value>[-<structure>-XI2]. PASS gates and neighbours as before.
Not tested, by design: event days (about 10 RBI-type days in DESIGN, a count UNVERIFIED, can never meet ST11 >= 0.5 a
day); option-only (IV) edges, because the owner's funnel requires an index-point edge before option P&L (D-40).

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R6-1 | 11:00 day direction, hold to close | DIRECTION | t = 105, abs(ret_open) >= X, side = sign(ret_open) | X 0.001, 0.002, 0.003 (0.0005, 0.004) |
| R6-2 | 12:00 day direction, hold to close | DIRECTION | t = 165, abs(ret_open) >= X, side = sign(ret_open) | X 0.001, 0.002, 0.003 (0.0005, 0.004) |
| R6-3 | 11:00 trend efficiency, hold to close | DIRECTION | t = 105, eff >= X, side = sign(ret_open) | X 0.10, 0.15, 0.20 (0.05, 0.25) |
| R6-4 | gap-and-go at 09:45, hold to close | DIRECTION | t = 30, abs(gap) >= X, sign(ret_open) = sign(gap), side = sign(gap) | X 0.001, 0.002, 0.003 (0.0005, 0.004) |
| R6-5 | near-expiry 10:30 direction, hold to close | DIRECTION | t = 75, dte <= 7, abs(ret_open) >= X, side = sign(ret_open) | X 0.002, 0.003, 0.004 (0.001, 0.005) |
| R6-6 | first-hour direction at 10:15, hold to close | DIRECTION | t = 60, abs(ret_open) >= X, side = sign(ret_open) | X 0.001, 0.002, 0.003 (0.0005, 0.004) |

## §PREREG-R7 (P3R round 7, owner order D-40; before any R7 number)

Data: DESIGN 362 days (no new data); the old holdout stays closed. Question from R6: do the two ideas with an index
edge to the close keep it in options when the trade is NOT cut early by an index stop? Trial cap added: 30
Funnel S1 / S2 as §PREREG-R6 (forward index move to 14:30). S3 on data/lab/matrix_r7.npz (lab/build_r2.py r7):
CAP15 structure only (loss-first: max loss <= ₹15,000 + stressed costs), exits XH = no index stop, no target, hold to
force-flat 15:10; XH2 = index stop -2R only (no break-even, no trail, no target), else hold to force-flat. Fill rules
as §PREREG-R2. ids R7-<idea>-<value>[-CAP15-<exit>]. PASS gates and neighbours as before. R6-4 / R6-5 rules are
re-run under new ids (their S2 lines count again in k).

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R7-1 | gap-and-go at 09:45, hold to close (R6-4 rule) | DIRECTION | t = 30, abs(gap) >= X, sign(ret_open) = sign(gap), side = sign(gap) | X 0.001, 0.002, 0.003 (0.0005, 0.004) |
| R7-2 | near-expiry 10:30 direction, hold to close (R6-5 rule) | DIRECTION | t = 75, dte <= 7, abs(ret_open) >= X, side = sign(ret_open) | X 0.002, 0.003, 0.004 (0.001, 0.005) |

## §PREREG-R8 (P3R v2 round 8, owner order 2 / D-42; EXPLORE; before any R8 number)

Family F3 (ML probability). Data: DESIGN 362 days; the old holdout stays closed. Trial cap added: 200
Features (20, as of the decision row, no look-ahead): t, dte, gap, ret_open, ret15, ret30, eff, rv5, rv15, rv30,
vwap_dist, basis, basis_chg, vix, vix_chg, vix_pct, oi_skew, hdfc15, icici15, prev_ret (NaN -> the training median;
standardised on the training folds).
Targets: up = forward index move over H >= 14.2 + 5 points; down = the mirror; two models per fold.
Models: M1 logistic regression (numpy, L2 = 1.0, Newton steps); M2 boosted decision stumps (numpy, 50 rounds,
learning rate 0.1, logistic loss).
Walk-forward: DESIGN days in 5 equal blocks; test blocks 2..5 (the 4 folds of ST4), each trained on all earlier blocks
with a 1-day embargo. Inside the training blocks only (an inner split: the last training block validates), choose
H in {30, 60, to 14:30} and the probability threshold in {0.55, 0.60, 0.65, 0.70} that maximise the validation stressed
net with >= 0.5 trades a day. Signal: side = the model with the higher probability if it is >= the threshold, else
NO-TRADE. t 30..285.
S3 (option P&L, out-of-sample predictions only): structures / exits {CAP15-XH, CAP15-XI2} (matrix_r7 / matrix_r2) x day
rules {max entries 1, 2, 3, 5, 10, 15} x {stop the day after a losing trade: yes, no} x {cool-off 15, 30 min}; one
structure at a time; daily ₹ loss lock = 2 x the structure's max loss. ids R8-<model>-<exit>-e<n>-s<y|n>-c<min>.
Every id is a trial (2 x 2 x 24 = 96 lines). EXPLORE screen as results/research_plan_v2.md (null: random sides and
times on the same days, same count, p < 0.01, 2,000 runs).
F6 (not a trial): the break-even table by strike (ITM delta 0.6-0.7 / ATM / CAP15) and hold time -> results/f6_breakeven.md.

## §PREREG-R9 (P3R v2 round 9 = F4 near-expiry seed, owner order 2; EXPLORE; before any R9 number)

Data: DESIGN 362 days; the old holdout stays closed. Only scales were read: share of DESIGN days with DTE <= 7 / 10 /
15 / 20 = 0.28 / 0.37 / 0.55 / 0.70. A hold-to-close rule trades at most once a day, so ST11 (>= 0.5 a day) needs a DTE
limit above about 15; the grid therefore spans DTE 10 / 15 / 20. The F3 filter is NOT used: R8 found no out-of-sample
edge in the F3 models, so filtering by them has no evidence behind it (the owner may overrule). The day-rule grid is
moot here (one signal a day at 10:30); no trials are spent on it. Trial cap added: 60
Rule (R7-2 widened): t = 75 (10:30), dte <= D, abs(ret_open) >= X, side = sign(ret_open). Funnel S1 / S2 to 14:30 as
§PREREG-R6. S3 on data/lab/matrix_r9.npz (= matrix_r7 XH / XH2 + matrix_r2 XI2, CAP15 only): each S2 survivor x
{CAP15-XH, CAP15-XH2, CAP15-XI2}. ids R9-<idea>-<value>[-CAP15-<exit>]. EXPLORE screen as research_plan_v2.md.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R9-1 | near-expiry direction at 10:30, DTE <= 10, hold to close | DIRECTION | t = 75, dte <= 10, abs(ret_open) >= X | X 0.0005, 0.0015, 0.0025 (0.0, 0.0035) |
| R9-2 | the same, DTE <= 15 | DIRECTION | t = 75, dte <= 15, abs(ret_open) >= X | X 0.0005, 0.0015, 0.0025 (0.0, 0.0035) |
| R9-3 | the same, DTE <= 20 | DIRECTION | t = 75, dte <= 20, abs(ret_open) >= X | X 0.0005, 0.0015, 0.0025 (0.0, 0.0035) |

## §PREREG-R10 (P3R v2 round 10 = F1 defined-risk volatility premium, RESEARCH ONLY (D-42 (4)); before any R10 number)

Data: DESIGN 362 days; the old holdout stays closed. Re-ordered before F2 / F5 (rounds.md R9 line). Trial cap added: 40
Structures (nearest monthly expiry, 1 lot each leg; the long wings are bought FIRST, then the shorts; never a naked
short): IF300 = sell ATM CE + ATM PE, buy CE ATM+300 and PE ATM-300; IF500 = the same with wings +-500; IC = sell CE
ATM+200 and PE ATM-200, buy CE ATM+500 and PE ATM-500. Entry: the first minute in [t, t+2] where all 4 legs are live
(non-stale, volume) at their opens; t in {45 (10:00), 135 (11:30)}. Exit: E1 = hold to force-flat 15:10 at the closes;
E2 = stop when the worst-case cost to close (shorts at the bar HIGH, longs at the bar LOW) exceeds the credit by
>= 1.0 x credit, filled at that worst-case value; else 15:10. Filter: none / trend-skip (skip when eff >= 0.35 or
abs(ret_open) >= 0.006 at entry). Costs: SOURCE charges per leg and side by date (a short leg sells first) x 1.5 +
the stressed spread and slippage on 4 legs (ST7). Max loss by construction = (wing distance - credit) x lot + costs.
24 trials = 3 structures x 2 entry times x 2 exits x 2 filters; ids R10-<structure>-t<t>-<exit>-<filter>.
EXPLORE screen as research_plan_v2.md; the null for a non-directional fixed-time structure = one-sided day-block
bootstrap (5-day blocks, 10,000 resamples, SEED) of the mean stressed net: p = share of resampled means <= 0, < 0.01.
Neighbours = the trials that differ in ONE grid value (structure, entry time) must also be net > 0. The day-rule grid
is moot (one structure a day). Margin is not modelled here (research only; a bot would need the broker's margin).

## §PREREG-R11 (P3R v2 round 11 = F2 implied vs realised move; EXPLORE; before any R11 number)

Data: DESIGN 362 days (347 with an opening straddle); the old holdout stays closed. Features (lab/build_r11.py; only
scales read: impl_ratio p50 0.48 / p75 0.80 / p90 1.17; rv_iv p50 0.74 / p75 0.93 / p90 1.14): impl_ratio = abs(spot -
open) / (opening ATM straddle / sqrt(max(1, dte x 5 / 7))); rv_iv = realised daily vol (rv30 x sqrt(375)) / the
straddle-implied daily vol. F2 (c) (rich IV -> selling) is not run: R10 showed 4-leg selling cannot cover its costs.
Trial cap added: 50. Funnel S1 / S2 (60 min) as §PREREG-R1. S3 on data/lab/matrix_r11.npz: each S2 survivor x
{CAP15-XI2, CAP15-XH}. ids R11-<idea>-<value>[-CAP15-<exit>]. EXPLORE screen as research_plan_v2.md.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R11-1 | the day's move passes X of the implied daily move: follow | STRUCTURAL (an implied-move break = new information) | t 45..255, impl_ratio >= X, side = sign(ret_open) | X 0.5, 0.75, 1.0 (0.25, 1.25) |
| R11-2 | realised vol above implied and rising: buy the move | STRUCTURAL (IV too cheap for the realised move) | t 45..255, rv_iv >= X, rv5 > rv30, abs(ret15) >= 0.001, side = sign(ret15) | X 0.8, 1.0, 1.2 (0.6, 1.4) |
| R11-3 | the move overshoots the implied move in the afternoon: fade | STRUCTURAL (implied move as a fair range) | t 165..285, impl_ratio >= X, side = -sign(ret_open) | X 1.0, 1.25, 1.5 (0.75, 1.75) |

## §PREREG-R12 (P3R v2 round 12 = F5 regime switch; EXPLORE; before any R12 number)

Data: DESIGN 362 days; the old holdout stays closed. Trend score at the decision row = number of these that hold
(0..5): eff >= 0.30; abs(ret_open) >= 0.003; sign(ret15) = sign(ret_open); sign(hdfc15) = sign(icici15) =
sign(ret_open) (breadth of the two biggest constituents); sign(vwap_dist) = sign(ret_open). Trend day = score >= X ->
momentum long option on sign(ret_open), held to the close; a range day -> NO-TRADE (R10: 4-leg selling cannot cover
its costs). Trial cap added: 40. Funnel S1 / S2 to 14:30 (§PREREG-R6). S3 on data/lab/matrix_r11.npz: each S2 survivor
x {CAP15-XH, CAP15-XI2}. ids R12-<idea>-<value>[-CAP15-<exit>]. Outside neighbour 6 = an empty rule (score max 5).

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R12-1 | trend score at 10:00 | DIRECTION (regime) | t = 45, score >= X | X 3, 4, 5 (2, 6) |
| R12-2 | trend score at 11:00 | DIRECTION (regime) | t = 105, score >= X | X 3, 4, 5 (2, 6) |
| R12-3 | trend score at 10:00 with VIX not rising | DIRECTION (regime) | t = 45, score >= X, vix_chg <= 0 | X 3, 4, 5 (2, 6) |

## §PREREG-R13 (P3R v2 round 13 = the last round of remaining combos (D-43 C3); EXPLORE; before any R13 number)

Data: DESIGN 362 days; the old holdout stays closed. The three seeds with an index edge to the close (R6-4 gap-and-go,
R6-5 / R7-2 near-expiry 10:30, R12-1 trend score) on the strike F6 found cheapest per index point: ITM2 = 200 points
in the money (CE strike ATM-200, PE strike ATM+200), nearest monthly. Loss-first trade-off, reported: ITM2's
by-construction max loss is its premium (median ~711 points x lot ~= ₹21,000), above CAP15's ₹15,000.
Trial cap added: 40. Funnel S1 / S2 to 14:30 (§PREREG-R6). S3 on data/lab/matrix_r13.npz (lab/build_r2.py r13: ITM2 x
{XH, XH2}, §PREREG-R7 exits). ids R13-<idea>-<value>[-ITM2-<exit>]. EXPLORE screen as research_plan_v2.md.

| id | idea (side) | edge source | rule | grid (outside neighbours) |
|---|---|---|---|---|
| R13-1 | near-expiry 10:30 direction on ITM2 (R6-5 rule) | DIRECTION | t = 75, dte <= 7, abs(ret_open) >= X | X 0.002, 0.003, 0.004 (0.001, 0.005) |
| R13-2 | trend score at 10:00 on ITM2 (R12-1 rule) | DIRECTION (regime) | t = 45, score >= X | X 3, 4, 5 (2, 6) |
| R13-3 | gap-and-go at 09:45 on ITM2 (R6-4 rule) | DIRECTION | t = 30, abs(gap) >= X, sign(ret_open) = sign(gap) | X 0.001, 0.002, 0.003 (0.0005, 0.004) |

## §PREREG-R14 (owner order 4 / D-47: PORTFOLIO OF SETUPS; EXPLORE; before any R14 number)

Data: DESIGN 362 days; the old holdout stays closed. Members = every S3 setup with a positive DESIGN stressed net in
rounds R1-R13 plus the Phase 3 trials with a positive net (A2, A2+b1): 29 setups, listed in results/r14_members.json
in PRIORITY order (DESIGN stressed net per trade, highest first; ties keep the listed order). Each member keeps its
own rule, structure, exit and outcome matrix. Trial cap added: 30
Portfolio rule: the union of the members' candidate trades in time order; ONE position at a time (a candidate enters
only after the previous trade's exit minute); when two members fire at the same minute the higher priority wins;
1 lot; a trade whose by-construction max loss exceeds the pinned MAX_TRADE_LOSS_RS ₹35,700 is skipped; daily loss
lock ₹71,400 (DAILY_LOSS_LOCK_RS); cool-off 15 min after a loss; no day stop after a loss.
Variants: P1 = S1 + S2 + S3 only (R7-2-0.004-CAP15-XH2, R12-1-5-CAP15-XH, R13-3-0.001-ITM2-XH; priority as listed);
P2 = all 29; P3 = the members with >= 20 DESIGN trades. Day rule: max entries a day {2, 3, 5}. 9 trials, ids
R14-<P>-e<n>. EXPLORE screen (D-42) on the whole portfolio: stressed net > 0, folds >= 3 of 4, both VIX halves,
ST11 >= 0.5 a day, net >= 0 at 1.5 x cost, ST4c, one-sided day-block bootstrap p < 0.01 (5-day blocks, 10,000),
neighbours = the adjacent max-entries values must be net > 0. Selection for R15: the R14 trial passing the most
gates, ties -> the higher total net.

| member (priority order) | DESIGN net / trade | DESIGN trades |
|---|---|---|
| R2-7-2.0-ATM-XI1 | 1825.87 | 8 |
| R13-2-5-ITM2-XH2 | 1273.60 | 31 |
| R2-7-2.0-ATM-XI2 | 1267.01 | 8 |
| R2-7-2.0-CAP15-XI1 | 1266.75 | 7 |
| R13-1-0.004-ITM2-XH2 | 1245.16 | 35 |
| R13-2-5-ITM2-XH | 1225.98 | 31 |
| R7-2-0.004-CAP15-XH2 | 1222.55 | 35 |
| R13-1-0.004-ITM2-XH | 1215.00 | 35 |
| R7-2-0.004-CAP15-XH | 1152.72 | 35 |
| A2+b1 | 1118.57 | 34 |
| R12-1-5-CAP15-XH | 948.38 | 28 |
| R2-7-2.0-CAP15-XI2 | 778.58 | 7 |
| R1-5-0.005-C2 | 620.32 | 51 |
| R12-1-5-CAP15-XI2 | 607.44 | 28 |
| R1-5-0.005-EXIT0 | 556.42 | 55 |
| R13-3-0.001-ITM2-XH | 525.10 | 120 |
| R2-4-0.004-CAP15-XI2 | 466.41 | 72 |
| R3-7-0.004-CAP15-XI2 | 466.41 | 72 |
| R3-7-0.005-CAP15-XI2 | 448.84 | 57 |
| R1-5-0.005-C3 | 384.57 | 58 |
| R3-7-0.005-CAP15P-XI2 | 338.52 | 56 |
| R2-4-0.004-ATM-XI2 | 330.47 | 72 |
| R3-7-0.004-CAP15P-XI2 | 323.87 | 71 |
| R4-1-0.007-CAP15-XI2 | 283.47 | 13 |
| R4-1-0.007-CAP15-XI1 | 277.26 | 14 |
| A2 | 258.25 | 73 |
| R2-4-0.004-CAP15-XI1 | 73.19 | 84 |
| R7-1-0.001-CAP15-XH | 39.36 | 91 |
| R2-4-0.004-ATM-XI1 | 19.23 | 86 |

## §PREREG-R15 (owner order 4 / D-47: SIZING + SCALE-OUT + PYRAMIDING on R14-P3-e3; EXPLORE; before any R15 number)

Base: the R14-P3-e3 portfolio (26 members, priority, one position at a time, max 3 a day). The entry times and the
sequencing stay those of R14 (an earlier pyramid exit never frees time for an extra trade: conservative). Lots per
trade by the member's priority rank (results/r14_members.json order restricted to P3): ranks 1-6 -> 3 lots, 7-14 ->
2 lots, 15-26 -> 1 lot; then capped so the by-construction max loss of the WHOLE position (premium x qty + stressed
costs) <= MAX_TRADE_LOSS_RS ₹35,700 (fewer lots if needed; never fewer than 1 when 1 lot fits). R = 0.30 x the entry
premium. Costs: SOURCE charges per order by date (brokerage flat per order) x 1.5 for the actual orders; stressed spread
+ slippage per lot as the member's 1-lot fill. Trial cap added: 10
- R15-a TIERS: all lots enter together and exit at the member's own exit.
- R15-b TIERS + SCALE-OUT (lots >= 2): one lot books at entry x 1.30, filled at that price in the first minute (after
  entry, before the member's exit) whose option HIGH is above it; the other lots exit at the member's exit; one extra
  exit order is paid.
- R15-c PYRAMID ONLY IN PROFIT: enter 1 lot; at the first minute (before the member's exit) whose option CLOSE >= entry x
  1.30, add (tier lots - 1) lots at the next minute's open (a new buy order); the added lots are cut so the position's
  by-construction max loss stays <= ₹35,700; the stop of ALL lots then moves to S = max(E, (a x A + 0.7 x E) / (a + 1))
  (E = first entry, A = add price, a = added lots), so the position's loss at S <= the first lot's initial risk 0.3 x E;
  a minute whose LOW <= S exits all lots at min(S, that minute's open); else all exit at the member's exit. Never adds
  to a loser (Class D).
3 trials, ids R15-<a|b|c>; the EXPLORE screen of R14 on the result (bootstrap p < 0.01 etc.).

## §PREREG-R16 (owner order 4 / D-47: COST-AWARE FILTER on R15-a; EXPLORE; before any R16 number)

Base: R15-a (the R14-P3-e3 portfolio with the R15 tiers and the ₹35,700 cap). Filter on every CANDIDATE before the
sequencing (a filtered candidate never holds the position): keep it only when the expected index move left in the day
>= X x its break-even. Expected move = m_d x sqrt((355 - entry minute) / 375), m_d = the opening ATM straddle /
sqrt(max(1, dte x 5 / 7)) (§PREREG-R11; lab/build_r11.py now also stores m_d as F_md). Break-even (index points) =
results/lots_math.md for the candidate's strike and its R15 lot count: ATM 14.9 / 12.5 / 11.7, CAP15 17.0 / 14.0 /
13.0, ITM2 14.0 / 11.8 / 11.1 for 1 / 2 / 3 lots (matrix.npz LONG members = ATM; CAP15P = CAP15). Days without a
straddle: the candidate is dropped. Grid X in {2, 4, 6}; neighbours = the adjacent X. Trial cap added: 10. ids
R16-x<X>. EXPLORE screen as R14. Then ONE final candidate = the R14 / R15 / R16 trial passing the most gates
(ties -> the higher total net), and the EXPLORE verdict decides whether CONFIRM (the old holdout, once) runs.

## §PREREG-R17 (owner order 5 / D-49: NESTED walk-forward of the R14 + R15 pipeline; before any R17 number)

Universe U (fixed now): every pre-registered S3 setup of R1-R7, R9, R11-R13 = each idea x each grid value x each
structure / exit combination of lab/p3r.py ROUNDS (whether it passed S2 on DESIGN or not), plus the 13 Phase 3 trials
(results/scoreboard.json). Windows: DESIGN days in 5 blocks (72 / 72 / 72 / 72 / 74 days); test windows = blocks 2..5;
each trained on all earlier blocks with a 1-day embargo. Inside each training window ONLY, the whole selection is
redone: (1) S2: the idea's index test on the training days (mean > 14.2 points and matched-null p <= 0.05; the round's
horizon; Phase 3 trials skip S2 as they did); (2) S3: the setup alone (RISK SHELL day rules) has training stressed net
per trade > 0 and >= 20 x (training days / 362) trades; (3) members = the S3 survivors, priority = training net per
trade; (4) tiers by training rank: 1-6 -> 3 lots, 7-14 -> 2, else 1, capped at the ₹35,700 by-construction max loss.
Then the next block is traded with the R14 / R15 rules (one position at a time, max 3 entries a day, cool-off 15 min,
daily lock ₹71,400; exact charges per order x 1.5 and the stressed fill per lot). Only the 4 test blocks (290 days)
count. Trial cap added: 10. Trials: R17-a = with tiers (R15-a pipeline); R17-b = 1 lot (R14-P3 pipeline).
Gates (D-49 (4)): OOS stressed net > 0, >= 3 of 4 test windows positive, >= 0.5 trades a day, net > 0 without the best
5 trades, net >= 0 at 1.5 x cost, 12-month expected net >= DD95 (5-day blocks, 12 months, closed-trade marks), PBO <=
0.25 (CSCV 16 blocks over the daily P&L of every universe setup alone on DESIGN plus the R14-R16 portfolios), DSR >=
0.95 (the candidate's OOS daily P&L; N = every trials.jsonl line; Sharpe variance over the universe series).

## §PREREG-R18 (owner order 5 / D-49, D-50: META-LABELING, nested walk-forward; before any R18 number)

Windows, universe, S2 / S3 rules and the test-window trading rules as §PREREG-R17. Primary signals per training window:
M-a = the R17 selection; M-b = every universe setup whose training trades (traded alone, RISK SHELL) have a positive
stressed net per trade and >= 20 x (training days / 362) trades. Meta-label: 1 if the candidate trade's 1-lot stressed
net > 0. Features: the 20 of §PREREG-R8 at the decision row + one-hot structure (ATM / CAP15 / ITM2 / spread) + exit
type (hold to close / other). Models (numpy, trained on the training window's candidate trades only): L = logistic
(L2 = 1.0); S = boosted stumps (50 rounds, learning rate 0.1). Test window: a candidate is taken only if p >= 0.50;
lots 1 / 2 / 3 at p >= 0.50 / 0.60 / 0.70, capped at the ₹35,700 by-construction max loss; priority = p (highest
first); one position at a time, max 3 a day, cool-off 15, daily lock ₹71,400. Trial cap added: 10.
Trials: R18-Ma-L, R18-Ma-S, R18-Mb-L (stumps on M-b skipped: too many rows for the numpy stumps; logged here).
Gates and PBO / DSR exactly as §PREREG-R17.

## §PREREG-R19 (owner order 5 / D-49: JAMES-STEIN SHRINKAGE sizing, nested walk-forward; before any R19 number)

Windows, universe and test-window trading as §PREREG-R17. In each training window, eligible setups = every universe
setup with >= 20 x (training days / 362) training trades (traded alone, RISK SHELL): R19-a = all of them; R19-b =
only those whose idea passes the S2 index test on the training days (Phase 3 trials stay eligible without S2).
For eligible setup i: m_i = training stressed net per trade, se_i^2 = its sample variance / n_i; grand mean m =
the trade-weighted mean of the m_i; B = (k - 3) x mean(se_i^2) / sum (m_i - m)^2; shrunk mu_i = m + max(0, 1 - B) x
(m_i - m) (positive-part James-Stein toward the grand mean). Members = setups with mu_i > 0, priority = mu_i (highest
first); lots: mu_i >= ₹600 -> 3, >= ₹300 -> 2, else 1, capped at the ₹35,700 max loss. Trial cap added: 10.
Trials: R19-a, R19-b. Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R20 / R21 / R22 (owner order 5 / D-49; nested walk-forward; committed together before any of their numbers)

Windows, universe, S2 / S3 selection (= "the R17 selection") and test-window trading as §PREREG-R17 unless stated.
Daily series from DESIGN rows (no look-ahead): prev_close_d = today's open / (1 + gap_d); range_d = day high - day low
through 14:30; ATR10_d = the mean range of the 10 previous DESIGN days. Trial cap added: 20.
- R20 VOLATILITY-TARGETED LOTS: lots = clip(round(2 x ATR_target / ATR10_d), 1, 3), ATR_target = the median ATR10 of
  the training window; capped at the ₹35,700 max loss. Trials: R20-a (the R17 selection), R20-b (M-b of §PREREG-R18).
- R21 PER-SETUP HOLD AND TRAIL: for each idea value (round, idea, X) keep only its structure / exit combination with the
  best training stressed net per trade; members = those that pass S2 + S3, priority = training net. Trials: R21-a
  (1 lot), R21-b (R15 tiers by training rank).
- R22 DAILY TREND BIAS: a candidate is kept only if its side agrees with the sign of trend_N = prev_close_d /
  prev_close_(d-N) - 1 (N trading days back; no trade when trend_N is unknown or 0). Members = the R17 selection, 1
  lot. Trials: R22-n5, R22-n10, R22-n20 (neighbours = the adjacent N).
Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R23 (owner order 5 / D-49: ROLLING selection for drifting edges, nested; before any R23 number)

Idea: if edges drift (R17-R22 were positive only in the latest test window), choose on the most recent block only.
Windows and test-window trading as §PREREG-R17, but each test block b (2..5) is trained ONLY on block b-1 (72 days,
1-day embargo), not on all earlier blocks. Min training trades = 20 x (72 / 362). Trial cap added: 10.
Trials: R23-a (the R17 S2 + S3 selection, 1 lot), R23-b (the same, R15 tiers by training rank), R23-c (M-b: S3 only,
1 lot). Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R24 (owner order 5 / D-49: COMBINATIONS of the nested pieces; before any R24 number)

Combined from the pieces whose OUT-OF-SAMPLE mean was positive (R17-a tiers, R20-a vol lots, R22 trend filters); that
choice was itself made on out-of-sample numbers, which the trial count in DSR and the PBO matrix carry. Windows,
selection (the R17 S2 + S3, anchored) and test-window trading as §PREREG-R17. Trial cap added: 10.
Trials: R24-a = trend filter N 20 + R15 tiers; R24-b = trend filter N 20 + vol-targeted lots; R24-c = trend filter N 5
+ R15 tiers. Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R25 (owner order 5 / D-49, D-51: LONG STRADDLE when realised vol beats implied; RESEARCH ONLY; nested)

Structure: buy ATM CE + ATM PE of the nearest monthly expiry, 1 lot each (research only: R2 lets the bot hold one long
option or a debit spread; a pass would need the owner's decision). Entry: the first minute in [t, t+2] where both legs
are live, at their opens; debit D. Exits: SX1 = hold to force-flat 15:10 at the closes; SX2 = exit when the
worst-case value (both legs at the bar LOW) <= 0.70 x D, at that value, else 15:10. Costs: SOURCE charges per leg
(both long) x 1.5 + the stressed fill on 2 legs; max loss by construction = D x lot + costs. Non-directional (no S2).
Setups (data/lab/matrix_r25.npz, lab/straddle_r25.py): R25-1 rv_iv >= X, t 45..255, X in {1.0, 1.2, 1.4}; R25-2
rv5 >= X x rv30, t 45..255, X in {1.5, 2.0, 2.5}; R25-3 every day at 10:00 (t = 45); each x {SX1, SX2} = 14 setups,
each a trial line (DESIGN alone, also a PBO column). Nested trial R25-n: windows and test trading as §PREREG-R17,
members per training window = the straddle setups with a positive training net and >= 20 x (training days / 362)
trades, priority = training net, 1 lot. Trial cap added: 20. Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R26 (owner order 5 / D-49: CONSENSUS VOTING across the selected setups; nested; before any R26 number)

Idea: many weak signals agreeing at the same time may be stronger than any one. Windows, universe and test-window
trading as §PREREG-R17 (1 lot). In each training window the selection is either the R17 S2 + S3 selection or M-b
(§PREREG-R18). In the test window a candidate of a selected setup is kept only when at least K DIFFERENT selected
setups have a candidate on the same day, on the same side, with a decision time within 15 minutes of it (itself
included); priority = the training net per trade. Trial cap added: 10. Trials: R26-r17-k2, R26-r17-k3, R26-mb-k2,
R26-mb-k3. Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R27 (owner order 5 / D-49, D-52: EARLIER TIME EXITS for the hold-to-close families; nested; before any R27 number)

The late-day decay may eat the hold-to-close trades. Setups: the ideas and grids of R6, R9 and R12 (to-14:30 S2) on
CAP15 with time exits XT255 = exit at 13:30 and XT315 = exit at 14:30 at the option close, no stop (lab/build_r2.py
r27 -> data/lab/matrix_r27.npz). Nested as §PREREG-R17 over these setups only (S2 + S3 in each training window,
priority = training net). The setups are evaluated only inside the training windows, so the nested runs are the
trials. Trial cap added: 10. Trials: R27-a (1 lot), R27-b (R15 tiers by training rank). Gates, PBO and DSR as R17.

## §PREREG-R28 (owner order 5 / D-49: CLASSIC INDICATOR families; nested; before any R28 number)

Indicators on 1-minute index bars of the same day, the last bar closed before the decision (lab/build_r28.py; only
the scales were read: RSI14 p5 31 / p95 69; Bollinger z p5 -2.0 / p95 2.0; MACD histogram / price ~1e-4). Setups on
data/lab/matrix_r28.npz (CAP15 x {XI2, XH}), t 45..285: R28-1 RSI fade (RSI <= X -> CE, >= 100 - X -> PE), X in {25,
30, 35}; R28-2 RSI momentum (RSI >= 100 - X -> CE, <= X -> PE), X in {30, 35, 40}; R28-3 Bollinger breakout (z >= X ->
CE, <= -X -> PE), X in {1.5, 2.0, 2.5}; R28-4 Bollinger fade (z >= X -> PE, <= -X -> CE), X in {1.5, 2.0, 2.5};
R28-5 MACD histogram cross (prev <= 0 < now and now >= X -> CE; mirror -> PE), X in {0, 0.00005, 0.0001}; R28-6
Supertrend(10, X) flip (prev dir -1 -> now +1 -> CE; mirror -> PE), X in {2, 3, 4}. S2 = 60-min index test.
Nested as §PREREG-R17 over these 36 setups only (S2 + S3 per training window); the nested runs are the trials. Trial
cap added: 10. Trials: R28-a (1 lot), R28-b (R15 tiers). Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R29 / R30 (owner order 5 / D-49: INDEX vs CONSTITUENTS and FUTURES VOLUME; nested; before any number)

Features (lab/build_r29.py; only scales read: div p5 -0.0061 / p95 +0.0063; fvol_ratio p50 0.48 / p90 1.14; fret15
p5 -0.0020 / p95 +0.0020). Setups on data/lab/matrix_r29.npz (CAP15 x {XI2, XH}); S2 = 60-min index test.
R29 (index vs HDFCBANK + ICICIBANK; t 45..255): R29-1 the index converges to the banks (div >= X -> PE, div <= -X ->
CE), X in {0.002, 0.003, 0.004}; R29-2 the index keeps leading (div >= X -> CE, <= -X -> PE), same X.
R30 (near-futures volume surge with a 15-min move, abs(fret15) >= 0.001; t 45..285): R30-1 follow (side =
sign(fret15)) when fvol_ratio >= X, X in {1.0, 1.25, 1.5}; R30-2 fade (side = -sign(fret15)), same X.
Nested as §PREREG-R17 over each round's own 12 setups (S2 + S3 per training window), 1 lot; the nested runs are the
trials. Trial cap added: 10. Trials: R29-a, R30-a. Gates, PBO and DSR as §PREREG-R17.

## §PREREG-R31 (owner order 5 / D-49: CALENDAR family; nested; before any R31 number)

Setups on data/lab/matrix_r9.npz (CAP15 x {XI2, XH}); weekday from the DESIGN date (0 = Monday .. 4 = Friday); S2 =
60-min index test. R31-1 weekday follow: at 10:30 (t = 75), on weekday X, abs(ret_open) >= 0.002, side =
sign(ret_open), X in {0, 1, 2, 3, 4}; R31-2 weekday afternoon fade: at 13:00 (t = 225), on weekday X, abs(ret_open)
>= 0.003, side = -sign(ret_open), X in {0, 1, 2, 3, 4}; R31-3 expiry-day afternoon follow: dte = 0, at 12:30 (t =
195), abs(ret_open) >= X, side = sign(ret_open), X in {0.002, 0.004, 0.006}. Nested as §PREREG-R17 over these 26
setups (S2 + S3 per training window), 1 lot; the nested run is the trial. Trial cap added: 5. Trial: R31-a.
Gates, PBO and DSR as §PREREG-R17.

## S3 · R0 (owner order 6; BANKNIFTY_STRATEGY_V3.md §13.3; committed before any R0 number)
R0 = the three fixed V3 variants, no tuning (3 configs, cap 3). Each is run on the 4 OOS windows (DESIGN blocks 2-5,
290 days) and logged per window by the runner. T1-P is the main test; T1-RAW and T1 are comparison only.
Series BASE (half spread 0.50, slip 0.20); STRESS frozen from the T1-P OOS entry bars (§5.3). Reports: NULL-RANDOM
(2,000 seeds, SEED 20261119), NULL-FLIP, EXIT-CHECK, diagnosis, cost curve (full spread 0.50-4.00), intrabar
(BARCLOSE / PATH / WORST), trades and signals CSV, R0 card + 10-trade chart table.
<!-- S3-GRID R0 -->
```json
[{"variant": "T1-RAW"}, {"variant": "T1"}, {"variant": "T1-P"}]
```

Trial cap added: 12 (S3 R0 fits, already run under the grid above)

## S3 · R1 (owner order 6; §13.3; committed before any R1 number)
Nested (§13.4): per OOS window k the base (T1-P for R1) and the 13 R1 configs are fitted on blocks 1..k; the
highest training net_base wins (the base wins ties); the winner is tested on block k+1. Each fit is one ledger row.
R1 = G1_TRIGGER_PTS {5, 8, 12} x SL_INIT_PTS {12, 18} x EXIT_MODE {X-A, X-B} (12) + N13 (1) = 13 configs.
Nulls (NULL-RANDOM 2,000 seeds on the nested candidate), PBO (CSCV 16 blocks) and DSR (N_eff) after the round.
Trial cap added: 60
<!-- S3-GRID R1 -->
```json
[{"variant": "T1-P", "overrides": {}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 5, "SL_INIT_PTS": 12, "EXIT_MODE": "X-A"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 5, "SL_INIT_PTS": 12, "EXIT_MODE": "X-B"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 5, "SL_INIT_PTS": 18, "EXIT_MODE": "X-A"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 5, "SL_INIT_PTS": 18, "EXIT_MODE": "X-B"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 8, "SL_INIT_PTS": 12, "EXIT_MODE": "X-A"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 8, "SL_INIT_PTS": 12, "EXIT_MODE": "X-B"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 8, "SL_INIT_PTS": 18, "EXIT_MODE": "X-A"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 8, "SL_INIT_PTS": 18, "EXIT_MODE": "X-B"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 12, "SL_INIT_PTS": 12, "EXIT_MODE": "X-A"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 12, "SL_INIT_PTS": 12, "EXIT_MODE": "X-B"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 12, "SL_INIT_PTS": 18, "EXIT_MODE": "X-A"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"G1_TRIGGER_PTS": 12, "SL_INIT_PTS": 18, "EXIT_MODE": "X-B"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_N13": true}, "checks": [], "slots_off": []}]
```

## S3 · R2 (owner order 6; §13.3; committed before any R2 number)
Nested as S3 R1 (per-window base = the previous round's training choice; best training net_base wins, base wins ties).
R2 = STRIKE_MODE {DELTA_BAND, N6, N15} on each window's R1 base (3 configs; DTE 0 keeps the Delta 0.55-0.65 strike).
Trial cap added: 20
<!-- S3-GRID R2 -->
```json
[{"variant": "T1-P", "overrides": {}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"STRIKE_MODE": "DELTA_BAND"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"STRIKE_MODE": "N6"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"STRIKE_MODE": "N15"}, "flags": {}, "checks": [], "slots_off": []}]
```

## S3 · R3 (owner order 6; §13.3; committed before any R3 number)
Nested as S3 R1 (per-window base = the previous round's training choice; best training net_base wins, base wins ties).
R3 = exit modules on each window's R2 base: X-C (N3 runner), X-D, N2 k 1.0, N2 k 1.5, N7, N12, N14 (7 configs).
Trial cap added: 36
<!-- S3-GRID R3 -->
```json
[{"variant": "T1-P", "overrides": {}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"EXIT_MODE": "X-C"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"EXIT_MODE": "X-D"}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"N2_K": 1.0}, "flags": {"FLAG_N2": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {"N2_K": 1.5}, "flags": {"FLAG_N2": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_N7": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_N12": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_N14": true}, "checks": [], "slots_off": []}]
```

## S3 · R4 (owner order 6; §13.3; committed before any R4 number)
Nested as S3 R1 (per-window base = the previous round's training choice; best training net_base wins, base wins ties).
R4 = filters on each window's R3 base: K25 STRETCH, K26 ROOM, K27 CHOP, K28 DEAD alone (4), then the training-best two together (1).
Trial cap added: 28
<!-- S3-GRID R4 -->
```json
[{"variant": "T1-P", "overrides": {}, "flags": {}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_K25": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_K26": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_K27": true}, "checks": [], "slots_off": []}, {"variant": "T1-P", "overrides": {}, "flags": {"FLAG_K28": true}, "checks": [], "slots_off": []}]
```
