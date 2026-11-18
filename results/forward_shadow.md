# FORWARD SHADOW (D-43 WATCH MODE) · information only, never a PASS

The seeds S1-S3 of results/final_research.md section 4 did NOT pass EXPLORE, so this is not CONFIRM: it only shows how
they behave on days nobody has seen. Pre-registered here before any fresh day exists; no rule or parameter changes.
Run: on every new data-repo day after 2026-11-13, build the day's features and outcomes with the same lab builders
(lab/build_r2.py, lab/build_r13 mode, lab/p3r.py rules) and append one line per seed per day.

| seed | rule (frozen) |
|---|---|
| S1 | R13-3-0.001-ITM2-XH: 09:45, abs(gap) >= 0.001 and sign(ret_open) = sign(gap); ITM2 long option on sign(gap); hold to 15:10, no index stop |
| S2 | R7-2-0.004-CAP15-XH2: 10:30, dte <= 7, abs(ret_open) >= 0.004; CAP15 long option on sign(ret_open); index stop -2R, else hold to 15:10 |
| S3 | R12-1-5-CAP15-XH: 10:00, trend score 5 of 5 (§PREREG-R12); CAP15 long option on sign(ret_open); hold to 15:10 |

## Log
| date | data repo commit | new days | S1 | S2 | S3 |
|---|---|---|---|---|---|
| 2026-11-18 | 9e7a49d4 | 0 (the last day is 2026-11-13) | - | - | - |
