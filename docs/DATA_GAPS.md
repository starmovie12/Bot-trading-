DATA: 470 valid din (20 Nov 2024 ke baad; 125 chahiye the) [REAL] · calendar: 2026 official, 2024-25 data se (verify nahi hua).
KAMI: 13 Nov 2026 ka spot nahi; 15 Jan 2026 ka pura din data mein nahi; 12 din adhoore (Muhurat, budget, kuch din ek extra bar); 28 Nov-24 Dec 2024 ke 19 din ATM strike nahi.
KAMI: Mar-Apr 2026 ke 7 din door wale strikes (opt_wide) download nahi hue; bid / ask kabhi nahi tha (sirf Recorder dega).
BHARA: kuch nahi bhara (API token nahi); ye din strategy test se bahar rahenge, baaki data kaafi hai.
CHAHIYE: tumhare Recorder ka asli bid / ask (DATA-R) aur event calendar; aur data ki zaroorat nahi.

# DATA GAPS (MISSION V19 DG) · DATA_SHA 9e7a49d4 · `tools/data_gaps.py` → `results/data_gaps.json`

| id | verdict | numbers [REAL / CODE(REAL)] |
| --- | --- | --- |
| G1 WEEKS AND DAYS | GAP | `INDEX.txt` 27 lines vs 111 folders (84 folders not listed; folders win). 526 days present. Not OK / not READY: 2024-11-01, 2025-10-21 (Muhurat), 2025-02-01, 2026-02-01 (weekend sessions without F&O rows), 2025-04-30, 05-05, 05-13, 05-16, 05-22, 05-28 (one bar outside the session, 30-minute gap), 2026-11-08 (Muhurat), 2026-11-13 (MISSING_SPOT). Exchange calendar (2026 SOURCE, 2024-2025 data-derived): 2026-01-15 is a weekday not on the official holiday list and absent from the data (a special closure or a missing day). |
| G2 BARS | GAP | 17 days off the dated session count: 4 days with 374 index bars (2024-12-12, 2025-03-25, 04-04, 04-23); 6 days with 376 (above); VIX 376 / 377 on 5 days; 2026-11-13 spot and VIX 0. Duplicates 0, bad ticks 0. Cross-copy: 10 / 10 sample days equal (store = ai_ready = CSV). |
| G3 CONTRACTS | GAP | Nearest monthly expiry present on every day with options. Strike band without the ATM zone on 19 days (2024-11-28 .. 2024-12-24: band entirely below spot, e.g. -9.2% .. -4.9%). opt_wide_1m NOT_DOWNLOADED on 7 days (2026-03-04, 03-05, 03-09, 04-01, 04-02, 04-06, 04-07). Contracts in `contracts.csv` without a candle: 0. Expiries covered: 26. |
| G4 SPAN | OK | 2024-11-21 .. 2026-11-12 (current regime from 2024-11-20), 23.7 months; valid_days 470 (503 in the whole window); valid_days_per_week 4.56. No shortfall. |
| G5 TABLES | GAP | spot HAVE · future HAVE · VIX HAVE · options PARTIAL (opt_wide 7 days) · chain / IV / greeks HAVE · constituents HAVE (12 banks) · global indices PARTIAL (newest weeks) · exchange PCR / OI / FII-DII HAVE · recorded bid / ask NONE (DATA_GRADE B). |

## API-CAN-GIVE (Phase 2 documentation facts; API_CHECK = NA: no token this cycle)
- Historical candles v3 for live instruments (spot index, current futures, India VIX, bank stocks): minutes 1-300 and hours from January 2022, days from January 2000: not fetched (no token).
- Expired futures and options OHLC (1, 3, 5, 15, 30 minutes, day): only with the Upstox Plus plan: not fetched (DATA_REQUEST Part H).
- Option chain, market quote, greeks snapshots: live only, not historical: not fetched (no token).
- Cannot be given by any API: historical bid / ask, ticks, historical greeks: the owner's Recorder only (Part R).
Fill plan: nothing filled; the G1 / G2 / G3 days are excluded from valid days (and the 19 G3 days from option P&L).
