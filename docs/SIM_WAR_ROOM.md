# SIM WAR ROOM (T11, machinery only)

Result file: EVIDENCE/T11/sim.json (inputs: EVIDENCE/T04/g0.json, EVIDENCE/T08/families.json, gates.toml; harness: tools/truth_tests.py unchanged). SIM proves the machinery only: it can neither kill nor crown a family (§9), so no NEGATIVE.md row comes from here and every T08 family stays ALIVE (conditional).

Settings: window 24 months [ASSUMPTION], 21 trading days a month [ASSUMPTION], sigma ₹500.00 per trade [ESTIMATE] (the kindest G0 value), 50 SIM runs per power figure, 200 day-block resamples, seed 2026. Trade profiles are ASSUMPTION (DECISIONS D-039).

| id | family | trades a month, legs | hurdle per trade | credible edge per trade | stress cut per trade | null control | planted control | power at kind edge | power at kind edge, fill ₹0 | net edge needed for 80% power | needed / credible | candidate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a | No-trade-heavy: only the best 5-12 setups a month, cash otherwise | 8 [ASSUMPTION], 1 [ASSUMPTION] | ₹56.25 [CODE(ASSUMPTION)] | ₹37.50 [CODE(ESTIMATE)] | ₹89.07 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 8% [SIM] | ₹246.41 [SIM] | 6.6x [SIM] | no |
| b | Defined-risk premium selling (credit spread / condor) | 4 [ASSUMPTION], 2 [ASSUMPTION] | ₹112.50 [CODE(ASSUMPTION)] | ₹75.00 [CODE(ESTIMATE)] | ₹178.14 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 0% [SIM] | n/a (not judgeable in the window) | n/a (not judgeable in the window) | no |
| c | Option buying with IV-percentile, event and time-stop filters | 12 [ASSUMPTION], 1 [ASSUMPTION] | ₹37.50 [CODE(ASSUMPTION)] | ₹25.00 [CODE(ESTIMATE)] | ₹89.07 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 2% [SIM] | ₹209.11 [SIM] | 8.4x [SIM] | no |
| d | Expiry-day structure (gamma / pinning on the weekly expiry) | 4 [ASSUMPTION], 1 [ASSUMPTION] | ₹112.50 [CODE(ASSUMPTION)] | ₹75.00 [CODE(ESTIMATE)] | ₹89.07 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 0% [SIM] | n/a (not judgeable in the window) | n/a (not judgeable in the window) | no |
| e | Time of day (opening range, closing hour, lunch lull) | 20 [ASSUMPTION], 1 [ASSUMPTION] | ₹22.50 [CODE(ASSUMPTION)] | ₹15.00 [CODE(ESTIMATE)] | ₹89.07 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 0% [SIM] | ₹175.51 [SIM] | 11.7x [SIM] | no |
| f | Gap / event (IV crush before and after scheduled events) | 4 [ASSUMPTION], 2 [ASSUMPTION] | ₹112.50 [CODE(ASSUMPTION)] | ₹75.00 [CODE(ESTIMATE)] | ₹178.14 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 0% [SIM] | n/a (not judgeable in the window) | n/a (not judgeable in the window) | no |
| g | Breadth / heavyweight lead-lag (index heavyweights lead the index) | 20 [ASSUMPTION], 1 [ASSUMPTION] | ₹22.50 [CODE(ASSUMPTION)] | ₹15.00 [CODE(ESTIMATE)] | ₹89.07 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 0% [SIM] | ₹175.51 [SIM] | 11.7x [SIM] | no |
| h | Non-options: equity intraday (cash) and index ETF delivery | NOT_RUN [SIM]: no cost row: equity / ETF charges are not in constants.toml (T03 needs the web) | | | | | | | | | | no |
| i | Own idea: MANUAL low-frequency debit spreads (no server, no static IP) | 8 [ASSUMPTION], 2 [ASSUMPTION] | ₹56.25 [CODE(ASSUMPTION)] | ₹37.50 [CODE(ESTIMATE)] | ₹178.14 [SIM] | FAIL (must FAIL) [SIM] | PASS (must PASS) [SIM] | 0% [SIM] | 2% [SIM] | ₹335.48 [SIM] | 8.9x [SIM] | no |

RESULT: NONE: no family reaches 80% power in 24 months of SIM trades, even at the kind edge (hurdle + credible edge) with every fill at ₹0.

Reading: the kind edge already clears the hurdle by the whole credible edge, yet the T10 stress floors (charges x1.5, fill x2: gates.toml) cut more than the credible edge from every trade, so the stressed lower bound stays under the hurdle. A family needs the 'net edge needed' column, several times the credible edge, before two years of data can show it. This is not a kill: SIM cannot kill, and REAL data (Recorder: spreads, fills, sigma per trade) can move every input of this table.

Cheapest next path: REAL Recorder days (MANUAL, no server) to measure the fill cost and sigma per trade; then re-run this file with those inputs. A smaller REAL fill cost and sigma shrink the needed edge; nothing else here can.
