# PREREGISTER_v2 (MISSION V11 §16, T10): narrative and decision rule

Written before any trial: `trials.jsonl` is empty and no REAL market data exists. Every gate number lives in
`gates.toml` (never weaker than `tools/floors_baseline.toml`, the §8.2 STAT FLOORS); this file holds none.
The old `PREREGISTER.md` (v5) is superseded; its numbers are HISTORY.

## What is being tested

H0: after ALL costs no candidate in the tested set earns more than the cost hurdle per trade. The burden of
proof is on the candidate. Synthetic (SIM) results prove machinery only and can neither pass nor kill.

## Decision rule (the only way a verdict is set; `make verdict DATA=<path>`)

1. **STOP(G0_FAIL_ARITH / G0_FAIL_CREDIBILITY)** when G0 is FAIL for every universe member on SOURCE facts and
   OWNER or approved limits only. **STOP(DATA_KILL)** when REAL data kills every candidate of the tested set by
   the §9 rule (the upper bound of the day-block CI of net per trade stays below the hurdle even at the most
   favourable fills). STOP names the cheapest next path and what would reopen it.
2. **GO_PAPER** only when G0 = FEASIBLE for the candidate's member, G1 passes (REAL data: enough trading days
   with near-complete one-minute coverage), G2 passes (every floor in `gates.toml` on stressed BACKTEST /
   SHADOW trades from REAL data: Holm over every trial, day-block CI lower bound above the hurdle under cost
   stress, the random-entry null, walk-forward, parameter stability, Monte Carlo, the sealed holdout opened
   once) and G3 passes (no open reproducible Sev1 / Sev2). It starts R0 / R1 only, never live.
3. **NOT_YET** otherwise (the default), with every reason code that applies: NO_DATA, UNDERPOWERED,
   G0_CONDITIONAL, DATA_RIGHTS_OPEN, MISSING_INPUT, OPEN_FINDINGS, NOT_REVIEWED, BLOCKED_INPUT.

Caps (verdict at most NOT_YET): synthetic-only or too little data; G0 still CONDITIONAL; a decisive input
UNVERIFIED; the first adversary review not finished; an open Sev1 / Sev2; a blocked dependency with
UNVERIFIED inputs. A cap forbids GO_PAPER only; STOP stays possible under its own rule.

## Trials and the holdout

Every configuration, variant or feature set evaluated on data that shares information with the test is one
row in `trials.jsonl` (hash-chained; its own commit; the head hash on REPORT line 15). Reaching TRIALS_MAX
needs a new pre-registration that still counts every earlier trial. The holdout is the last part of the
planned REAL data span (`gates.toml`), sealed by hash and date cutoff when the first REAL data arrives,
opened once at the very end (`holdout_log.jsonl`; a second open is refused).

## Harness

`tools/truth_tests.py` (core, tested on synthetic trade lists: a random-entry strategy, a look-ahead feature
and a zero-cost run each fail it), `tools/power.py` (MDE from the day-block SE), `tools/fullb_gate.py`.
