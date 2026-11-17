# DATA REPORT (MISSION V19 Phase 1) · DATA_SHA 9e7a49d4eb838d0127fe9267c007888f69c0cc58

Source: `starmovie12/Bot-trading-historical-Bank-Nifty-` main @ 9e7a49d4 (commit 2026-11-17 13:51 IST): 111 week folders
(Saturday-to-Friday exports), 17,708 files [REAL]. Read: the quality files, `BANKNIFTY/contracts.csv`, `store/` spot_1m,
fut_1m, vix_1m, opt_1m + opt_wide_1m, spot_1d, vix_1d, stock_1m (12 bank constituents); 972 MB checked out (partial clone,
gitignored). Script: `tools/profile_data.py` → `data/lab/data_profile.json` (gitignored: daily prices); loader `lab/data.py`.

- **Span:** 2024-10-01 .. 2026-11-13, 526 days in the quality files [REAL]. `INDEX.txt` lists 27 of 111 weeks (folders win).
- **Columns (store):** instrument_key, underlying, segment, expiry_date, strike, option_type, interval, ts_open, ts_close,
  o, h, l, c, v, oi, has_volume, is_stale, is_filled, session_type, trading_date, source, adjusted_status, fetch_run_id,
  raw_sha256. CSV copies use time, open, high, low, close, volume, oi.
- **Time:** IST, tz-aware (+05:30); 1-minute bars stamped at the candle START, known one minute later.
- **Bars per day [REAL]:** spot 375 (09:15-15:29) on 512 days; futures best contract 375 until 2026-07-31 and 385
  (to 15:39) from 2026-08-03 (71 days); VIX 375 on 513 days. Exceptions: `docs/DATA_GAPS.md` G2.
- **Duplicates / bad ticks:** 0 conflicting rows, 0 day partitions in two folders, 0 bad ticks (spot, futures, options) [REAL].
- **Special sessions:** Muhurat 2024-11-01 (18:00-18:59) and 2025-10-21 (13:45-14:44), 60 bars each; 2026-11-08 Muhurat
  (70 spot bars, no F&O rows): excluded, `NO_TRADE SPECIAL_SESSION`. Full-length weekend sessions 2025-02-01 (Saturday) and
  2026-02-01 (Budget Sunday) have index bars but NO futures or option rows: not valid days.
- **Options [REAL]:** 1-minute OHLC, volume, OI; NO bid / ask → **DATA_GRADE = B**. Median 32,850 rows a day (both tables);
  carried (stale) minutes 23.4% median: never an entry fill. Strike step 100 on every day. Strike band median -4.1% .. +4.0%
  of spot. One expiry a day on 498 days, two on 25.
- **Expiries [REAL]:** 26, monthly only (2024-10-30 .. 2026-11-23). Weekday Thursday until Aug 2025, Tuesday from 2025-09-30
  (holiday shifts: Wednesday 2, Monday 2).
- **Lot per contract (`contracts.csv`) [REAL]:** 15 for expiries to 2025-01-30; 30 for 2025-02-27 .. 2025-06-26; 35 for
  2025-07-31 .. 2025-12-30; 30 from 2026-01-27. Rupee P&L always uses the contract's own lot.
- **Regime breaks in the window:** monthly-only Bank Nifty options from 20 Nov 2024 (SEBI rule, POINTER until Phase 2;
  the data holds monthly contracts only even before); the lot changes above; expiry weekday Thursday → Tuesday (Sep 2025);
  F&O session to 15:40 from 2026-08-03 (index stops 15:30).
- **Other tables:** futures near + next contract (750 / 770 rows a day); VIX; 12 bank constituents (AUBANK, AXISBANK,
  BANKBARODA, CANBK, FEDERALBNK, HDFCBANK, ICICIBANK, IDFCFIRSTB, INDUSINDBK, KOTAKBANK, PNB, SBIN) on 525 days. Present
  but not read yet: bars_3m, bars_15m, chain_1m, chain_metrics_1m, iv_greeks_1m, iv_daily_DERIVED, daily_metrics_DERIVED
  (each with `available_from_ts`), xcheck_csv (exchange PCR / OI / FII-DII), chain_15min.
- **Counted and ignored (R1):** non-bank stocks INFY and RELIANCE (63 days each) and `global_1m` (CAC_40, DAX, DOW_JONES,
  FTSE_100, GIFT_NIFTY, HANG_SENG, NIKKEI_225, Oil Brent / WTI, S&P, USD_INR, US_30, US_Tech_100; newest weeks only;
  allowed later as signal inputs). No other index's option or futures files exist in this repo.
- **Cross-copy check:** on 10 sample days spread over the span, store = ai_ready = CSV row counts [REAL] (G2).
- **Valid days [CODE(REAL)]:** 503 overall; 470 in the current regime (2024-11-21 .. 2026-11-12), above the 125 of ST6.
- **Fetch log:** no API fetch (TOKEN not set, Phase 2b.2 skipped); everything above comes from the data repo snapshot.
