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
