# STATE (MISSION V11) · keep ≤ 120 lines · BOOT: resume card + this file + the task section

SESSION_N: 3
CYCLE_N: 1
SESSION_START: 1794401358
BUDGET_MIN: 240
PAUSE_AFTER_G0: yes
TRACK: FULL (G0 CONDITIONAL for U1-U6: EVIDENCE/T04/g0.json; FULL-A next, FULL-B CLOSED)
FULL-B gate: CLOSED (EVIDENCE/T10/fullb_gate.txt: G0 CONDITIONAL, no REAL days yet, no T12 candidate) → T13a-T16 SKIPPED_BY_GATE
IN_PROGRESS: none · T11 SIM_WAR_ROOM DEFERRED(time) after sub-step: tools/sim_war_room.py run (EVIDENCE/T11/sim.json: RESULT NONE); left: claim lint, CP2 memo, tests, verify, seal/T11 · minutes_used: 25

## DONE (V11)
- T01 SYNC_SAFE: PASS (verify on 36acdef: EVIDENCE/T01/verify.txt; 20 min)
- T02a GUARDS_CORE: PASS (verify on 3a05345: EVIDENCE/T02a/verify.txt; 8 canaries caught; seal/T02a)
- T03 REGULATORY_DATA_RIGHTS: PASS offline (EVIDENCE/T03/verify.txt; constants.toml all UNVERIFIED; DATA_RIGHTS UNVERIFIED)
- T02b GUARDS_FULL: PASS (EVIDENCE/T02b/verify.txt; 13 canaries; seal/T02b-2; param_scan finding D-024)
- T05 RECORDER_MVP: PASS (EVIDENCE/T05/verify.txt; synthetic feed only, SIM; live adapter not built: schema UNVERIFIED)
- T09 DELIVERY_OPS: PASS (EVIDENCE/T09/verify.txt; bundle dry-run only: live adapter not built)
- T06 SUSPECTS: PASS (EVIDENCE/T06/verify.txt; limits one source, MAX_TRADE_LOSS ₹450 [CODE(HISTORY)] (D-032); niyam.toml move waits for F-PROT-2)
- T07 AUTOPSY: PASS (EVIDENCE/T07/verify.txt; Recorder bug A fixed test-first; order-path bugs listed for T13a/T13b)
- T08 ARITH_WAR_ROOM: PASS (EVIDENCE/T08/verify.txt; 9 families, 4 unconventional, no valid kill yet)
- T10 VERDICT_CORE: PASS (EVIDENCE/T10/verify.txt; make verdict = NOT_YET(NO_DATA, G0_CONDITIONAL, DATA_RIGHTS_OPEN))
- T04 G0_ECONOMICS: PASS (EVIDENCE/T04/verify.txt; G0 CONDITIONAL for U1-U6, TRACK FULL; seal/T04; CP1 memo docs/MEMO_CP1.md)

## NEXT
Session 3 ended on the owner's stop (OWNER_NOTES.md). On `continue` (session 4): T11 resume (claim lint, CP2 memo, tests, verify, seal/T11) → T12 (T11 NONE → SKIPPED_BY_GATE, D-039) → END: T17-R1 → T18. FULL-B stays CLOSED. GitHub upload (push) waits for the owner's lines `haan F-INC-1 be92` + `haan F-REMOTE 2350`.

## OPEN INCIDENTS (INCIDENT.md)
- #1 sandbox_breach: env name CLOUDSDK_AUTH_ACCESS_TOKEN → no push, no web fetch this session (closes: haan F-INC-1 be92)
- #2 env_warn: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY names (closes: haan F-INC-2 fc8c)
- #3 env_warn: LIVE_TRADING_ENABLED name (closes: haan F-INC-3 d9e1)

## PUSH
local only (F-REMOTE not approved; INCIDENT #1 open; .githooks/pre-push enforces both)

## STASHES
- stash@{0} "v5 WIP truth framework (engine hooks, synthetic, truth, breakeven)" from the old branch (DECISIONS D-003)

## SMOKE
make smoke (ruff, ruff format, mypy, pytest via python3 -m; gofmt, go vet, go test) · baseline green: EVIDENCE/T01/smoke_baseline.txt

## POINTERS
limits.toml (one source of limits) · constants.toml (T03) · assumptions: DECISIONS.md D-010 and the defaults in OWNER_QUESTIONS.md · inputs: docs/00_input (MISSING_INPUT.md)

## OWNER_TODO top 3 (full list: OWNER_TODO.md)
0. INCIDENT #1: sandbox theek karo, phir haan F-INC-1 be92
1. INCIDENT #3 + #2 (sirf jaankari): haan F-INC-3 d9e1 · haan F-INC-2 fc8c
2. DATA_RIGHTS: Upstox se likhit jawab; CP1 sawal docs/MEMO_CP1.md (F-MAXLOSS bca1, F-H2PCT be04, ...); F-REMOTE 2350

## HASHES
SHA256SUMS: sha256 20ab86987b20971e (file; covers docs/00_input and MISSION.md)
MISSION.md: 5eb4f9899b59b43a21d753bcd9123922ac82cbb0c2232f151be24a14b1611462
SEAL: a0baa30a (seal/T10; earlier 8ad3471a T08, a46a280f T07, 046774aa T06-2, 513c662e T09, c1f36384 T05, cf5bb14b T02b-2, 588b53dd T04, bc4d856a T02a; log EVIDENCE/seal_log.jsonl)
TRIALS_HEAD: none (trials.jsonl empty)
gates.toml: written in T10 (sealed at seal/T10) · STRATEGY.md: not written (T12)

## OLD DONE [HISTORY] (archive/CHECKPOINT_v5.md, archive/PROGRESS_v5.md; the owning V11 task re-verifies)
- M0 base: Python package, CI (ruff, mypy strict, pytest, hash-locked dev deps), niyam.toml + loader → T06 / T07
- Recorder: append-only hash-chained journal, ticks → candles + option book → T05
- Cost model from the Upstox charges page (fetched 11 Nov 2026 in an earlier session) → T03 re-verifies
- PAPER-only order manager with tests (idempotency, SL on fill, partial fills, square-off) → T07 / T13b
- Strategy v3 code (strike selection, rules, regime, setups S1-S3) → T08 / T11
- Backtest engine + metrics; tools/monte_carlo.py; PREREGISTER v5 (superseded by PREREGISTER_v2 in T10)
- Website (separate repo Bot-trading-website-): practice-mode admin panel; not part of this mission

## NOTES
- Session 3 end (2026-11-12): a worker restart pushed the clock past the budget; the owner then asked to stop and upload to GitHub (notes, not command lines) → T11 DEFERRED(time), SESSION_WRAP done, push still local only.
- Session 3: owner wrote `continue` after CP1 without answers → all defaults stay; RUN ORDER resumes at T02b.
- Session 1 ended by a forced stop (worker restart) during T04, after T03 PASS; owner wrote `continue` → session 2 (no seal, no budget, no answers).
- Tools on PATH (pytest, mypy) lack the project's dev deps; always use python3 -m (D-009).
- Run the FULL test suite (make smoke) in every task cycle before the commit (D-028). Seal BEFORE marking a task PASS; unstage after a refused commit (D-030). Known red: test_no_order_endpoint_in_m0 until haan F-PROT-1 b614.
- Temp files only in ${TMPDIR:-/tmp}/mission-v11-* (D-012). Commit cycle: STATE → make_report → mission_check → safe_add → commit.
