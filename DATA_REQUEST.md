# DATA_REQUEST (MISSION V19 Phase 1b) · 7 items (1 MUST, 6 NICE) · DATA_SHA 9e7a49d4

Ye "aur data bhejo" ki list nahi hai: repo mein 470 valid din hain aur mission har naya din apne aap le leta hai.
Sirf woh cheezein jo data repo mein nahi hain aur jinse strategy ka hisaab sach mein sudhrega.

## Part H (owner apne `updl` tool se data repo mein daal sakte hain; agent kuch nahi banata)
1. NICE · gap G1 · `NSE_INDEX|Nifty Bank` spot 1 minute, 2026-11-13 (09:15-15:30): columns time, open, high, low, close · why: the last day has no index bars (MISSING_SPOT) · substitute: the day stays excluded · fallback_ok = yes · where: `week_01_2026-11-07_to_2026-11-13/store/holdout/spot_1m/` (same layout).
2. NICE · gap G1 · every BANKNIFTY table for 2026-01-15, if the exchange was open that day · why: a weekday off the official holiday list is absent · substitute: the day stays out (or it was a closure) · fallback_ok = yes · where: its week folder, same layout.
3. NICE · gap G3 · BANKNIFTY monthly options ATM ± 10 strikes, 1 minute OHLCV + OI, 2024-11-28 .. 2024-12-24 · why: those 19 days have no ATM strikes, so option P&L skips them · substitute: exclude them (452 option days remain) · fallback_ok = yes · where: `store/dev/opt_1m/` of those weeks. Expired contracts need the Upstox Plus Expired Instruments API (price UNVERIFIED; R5 cap ₹1,500 a month).
4. NICE · gap G3 · `opt_wide_1m` for 2026-03-04, 03-05, 03-09, 04-01, 04-02, 04-06, 04-07 · why: far strikes missing on 7 days · substitute: near-ATM `opt_1m` only on those days · fallback_ok = yes · where: `store/dev/opt_wide_1m/`.
5. NICE · gap G5 · event calendar file (RBI policy dates, large bank results, budget) as `external/events.csv` (date, event, time if known) · why: the pack marks EVENT missing; a day filter may skip event days · substitute: no event filter (or the VIX level) · fallback_ok = yes · where: repo root `external/events.csv`.
6. NICE · gap G4 · BANKNIFTY spot, current futures and India VIX, 1 minute, 2022-01-01 .. 2024-09-30 · why: longer index history for direction features and the regime check only (never option P&L) · substitute: the 2024-10 .. 2026-11 window · fallback_ok = yes · where: new week folders, same layout.

## Part R (owner ka Recorder; agent ise na banata hai na chalata hai)
7. MUST · gap G5 (recorded bid / ask NONE) · follow `RECORDER_SPEC.md`: MUST = ts_recv IST, ≤ 60 s snapshots, BANKNIFTY index ltp, current-month futures bid / ask / qty / ltp / volume / oi, nearest-expiry options ATM ± 5 CE and PE with bid / ask / qty / ltp / volume / oi, India VIX ltp, market-status and connection events; NICE = next expiry, ATM ± 10, IV / greeks, depth, HDFCBANK / ICICIBANK · why: real spreads and slippage (DATA-R) for Phase 7 · substitute: spread ESTIMATE x 2 (verdict capped until measured) · fallback_ok = yes. Check the first day with `python tools/check_recording.py <file>`.

## Status after INTAKE-H (cycle 1; STOP-1 was skipped)
Every item above is OPEN_FOR_NEXT_CYCLE (Phase 7 step 1 ticks it). Cap codes this cycle: items 1-6 fall back to
excluding the affected days or features (no V3 cap code); item 7 falls back to the stressed spread ESTIMATE (C4, ST7),
which caps nothing in V3 but keeps every spread number tagged ESTIMATE until DATA-R arrives.

## P3R routes (owner order D-40; after rounds R1-R3, k = 124, no candidate passed)
- Item 5 (event calendar) opens the only family of the owner's list that is still untested: event days (RBI policy, big bank results, the budget).
- Item 7 (recorder bid / ask) replaces the spread ESTIMATE (stressed x2 .. x4) with the measured p90 spread: an honest cost cut on every family; until then the stress stays.
- Item 6 (index, futures and VIX 2022-01 .. 2024-09) gives the direction stage (S2) about 2.5 times the days, enough to tell a real near-expiry momentum effect from noise; option P&L stays on the current regime (ST6).
- New data days after 2026-11-13 are the fresh forward test (results/forward_shadow.md) for any candidate that passes.

## Owner order 2 (D-42), section E
- Item 6 now has exact steps and a script: docs/FETCH_HISTORY.md (BANKNIFTY index + India VIX, 1 minute, 2022-01 .. 2024-09; about 40 MB, ESTIMATE). Expired option candles for 2022-24 are NOT available from Upstox (its expired-instruments API keeps about 6 months of expiries, Plus plan; SOURCE 2026-11-18).
- Items 5 (event calendar) and 7 (recorder bid / ask) stay as asked above; new days after 2026-11-13 are always welcome (fresh CONFIRM data).
