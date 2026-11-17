
## RECORDER SPEC (the owner's Recorder; Phase 0 copies this part to `RECORDER_SPEC.md` by command)

*Maqsad: Phase 7 ko asli bid / ask aur spread chahiye. Har MUST field poora ho, warna wo din bekaar ho sakta hai aur 20 din ka clock dobara shuru karna padega.*

**A.1 Files.** The names below are a recommended layout, not a rule: `tools/check_recording.py` judges CONTENT. Recommended: one file per trading day `rec_YYYYMMDD.<csv | csv.gz | parquet | jsonl>` plus `rec_YYYYMMDD.sha256` (the sha256 of that file). `master_YYYYMMDD.json` and `gaps_YYYYMMDD.csv` are NICE: the checker derives gaps from `ts_recv` and takes strike, expiry and type from the option rows. Also accepted: a multi-day archive or the owner's own `updl` pack (a zip with a manifest), and other column names for the same field (a small alias dict in the checker, for example `timestamp` for `ts_recv`). Long layout: one row per instrument per snapshot.

**A.2 Time and cadence.** MUST: every row has `ts_recv` as an IST timestamp with the +05:30 offset; snapshots at most 60 s apart over the whole F&O session, 09:15 IST to its dated close (15:30 IST unless the exchange's later close applies, for example 15:40; the agent takes it from `constants.toml`). NICE: snapshots every 5 s or faster; `ts_exchange` when the feed gives it; the machine clock offset vs NTP once an hour.

**A.3 What to record.**

| Item | Fields | Rank |
| --- | --- | --- |
| BANKNIFTY index | ltp | MUST |
| Current-month BANKNIFTY futures | bid, ask, bid_qty, ask_qty, ltp, volume, oi | MUST |
| Options, nearest expiry, ATM ± 5 strikes, CE and PE (the window follows the spot at every snapshot) | instrument_key, strike, expiry, type, bid, ask, bid_qty, ask_qty, ltp, volume, oi | MUST |
| India VIX | ltp | MUST |
| Daily instrument master | lot size, expiries, strikes, tick | NICE (MUST only when the option rows lack strike / expiry / type; the agent takes the lot size by date from official sources) |
| Market-status events | open, close, pre-open, halt, special session | MUST |
| Connection events | connect, disconnect, reconnect, error | MUST |
| Options, next expiry, ATM ± 5 | same fields as above | NICE |
| Options, ATM ± 10 | same fields | NICE |
| IV and greeks | iv, delta, theta, vega | NICE |
| Top-5 depth for ATM ± 2 | price, qty per level | NICE |
| HDFCBANK, ICICIBANK | ltp, bid, ask | NICE |

**A.4 Gaps.** Never fill or interpolate a gap. Write each one to `gaps_YYYYMMDD.csv` (`gap_start`, `gap_end`, `reason`). A usable day = a full session with gaps ≤ 2% of the session minutes (about 7.5 of 375) and bid / ask present on the futures and the options.

**A.5 Self-check.** After the first recorded day run `python tools/check_recording.py <file>` (the agent builds it in Phase 0). It prints PASS or FAIL for each MUST item and fails a day ONLY when required content is really missing (option bid / ask, timestamps, gaps above 2% of the session); a different file name or column alias is not a failure. Run it on the FIRST recorded day (the repo also holds one synthetic sample day that shows what PASS looks like). A FAIL means: fix the Recorder at once and count the days from the first PASS day.

**A.6 Storage.** The files never go to git. Whether Upstox's terms allow giving them to an AI session is the owner's decision (`docs/REGULATORY.md`, the DATA-LICENCE line).

