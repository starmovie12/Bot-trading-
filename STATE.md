# STATE (MISSION V11) · keep ≤ 120 lines · BOOT: resume card + this file + the task section

SESSION_N: 3
CYCLE_N: 1
SESSION_START: 1794401358
BUDGET_MIN: 240
PAUSE_AFTER_G0: yes
TRACK: FULL (G0 CONDITIONAL for U1-U6: EVIDENCE/T04/g0.json; FULL-A next, FULL-B CLOSED)
FULL-B gate: CLOSED (tools/fullb_gate.py arrives in T10; no REAL market data)
IN_PROGRESS: T02b GUARDS_FULL · sub-step: FULL checks, canaries, CI built; next: checkpoint, seal/T02b, verify · minutes_used: 25

## DONE (V11)
- T01 SYNC_SAFE: PASS (verify on 36acdef: EVIDENCE/T01/verify.txt; 20 min)
- T02a GUARDS_CORE: PASS (verify on 3a05345: EVIDENCE/T02a/verify.txt; 8 canaries caught; seal/T02a)
- T03 REGULATORY_DATA_RIGHTS: PASS offline (EVIDENCE/T03/verify.txt; constants.toml all UNVERIFIED; DATA_RIGHTS UNVERIFIED)
- T04 G0_ECONOMICS: PASS (EVIDENCE/T04/verify.txt; G0 CONDITIONAL for U1-U6, TRACK FULL; seal/T04; CP1 memo docs/MEMO_CP1.md)

## NEXT
CP1 pause (owner answers in chat) → next session (RUN ORDER): T02b, T05, T09, T06, T07, T08, T10, then FULL-A T11, T12; FULL-B stays CLOSED (no REAL data)

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
SEAL: 588b53dd (seal/T04; earlier bc4d856a at seal/T02a; log EVIDENCE/seal_log.jsonl)
TRIALS_HEAD: none (trials.jsonl empty)
gates.toml: not written (T10) · STRATEGY.md: not written (T12)

## OLD DONE [HISTORY] (archive/CHECKPOINT_v5.md, archive/PROGRESS_v5.md; the owning V11 task re-verifies)
- M0 base: Python package, CI (ruff, mypy strict, pytest, hash-locked dev deps), niyam.toml + loader → T06 / T07
- Recorder: append-only hash-chained journal, ticks → candles + option book → T05
- Cost model from the Upstox charges page (fetched 11 Nov 2026 in an earlier session) → T03 re-verifies
- PAPER-only order manager with tests (idempotency, SL on fill, partial fills, square-off) → T07 / T13b
- Strategy v3 code (strike selection, rules, regime, setups S1-S3) → T08 / T11
- Backtest engine + metrics; tools/monte_carlo.py; PREREGISTER v5 (superseded by PREREGISTER_v2 in T10)
- Website (separate repo Bot-trading-website-): practice-mode admin panel; not part of this mission

## NOTES
- Session 3: owner wrote `continue` after CP1 without answers → all defaults stay; RUN ORDER resumes at T02b.
- Session 1 ended by a forced stop (worker restart) during T04, after T03 PASS; owner wrote `continue` → session 2 (no seal, no budget, no answers).
- Tools on PATH (pytest, mypy) lack the project's dev deps; always use python3 -m (D-009).
- Temp files only in ${TMPDIR:-/tmp}/mission-v11-* (D-012). Commit cycle: STATE → make_report → mission_check → safe_add → commit.
