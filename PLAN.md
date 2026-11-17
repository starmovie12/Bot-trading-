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

## §PREREG-0
