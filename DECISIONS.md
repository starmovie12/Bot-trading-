# DECISIONS (MISSION V11 §14 template)

## D-001 | T01 | 2026-11-11
OLD → NEW: no V11 branch → `mission/v11` created from `origin/main` 1060045 (the owner's setup message: "Create branch mission/v11 from main"). No `mission/v9` or `mission/v10` exists. The local branch `main` was stale (32 commits behind), so `origin/main` was used; the old working branch HEAD 71fab42 is an ancestor of it, so no committed work is lost.
WHY: §12 "Branch and old versions"; owner setup step [EVIDENCE: `git branch -a` output in the session log; `git merge-base --is-ancestor` exit 0]
₹ IMPACT: none
REVERSE BY: create another branch from any commit; nothing is deleted
CLASS CHECK: A (process) · PROTECTED: no

## D-002 | T01 | 2026-11-11
OLD → NEW: inputs scattered on branches → `docs/00_input/` (read-only): `origin/idea` docs at their `docs/` paths, and the documents of `origin/claude/busy-pascal-f7idxf` under `docs/00_input/claude_branch/`. Copied with `git show`; every copy has the same blob id as its source; sha256 of each in `SHA256SUMS` (mission_check #11 from T02a).
WHY: §3 "Originals stay safe"; owner setup step 2 · details in MISSING_INPUT.md
₹ IMPACT: none
REVERSE BY: `git mv` to archive/
CLASS CHECK: A · PROTECTED: hash-checked via SHA256SUMS

## D-003 | T01 | 2026-11-11
OLD → NEW: uncommitted V5 work on the old branch (truth-test hooks in `src/bot/backtest/engine.py`, `synthetic.py`, `truth.py`, `tools/breakeven.py`) → kept as `git stash` "v5 WIP truth framework (engine hooks, synthetic, truth, breakeven)", not committed to `mission/v11`.
WHY: never tested inside V11 and never reviewed; V11 owns this area in T10 / T14 and re-verifies anything taken from it [HISTORY]
₹ IMPACT: none
REVERSE BY: `git stash show -p` / `git stash apply` (the stash is listed in STATE.md)
CLASS CHECK: A · PROTECTED: no

## D-004 | T01 | 2026-11-11
OLD → NEW: secret NAME rules would also hide code files (`secrets.*` matches `src/bot/login/secrets.py`) → `.gitignore` re-includes `*.py` and `*.go` after the secret patterns, and `tools/secret_patterns.txt` has `exempt` rules for `*.py` / `*.go`. Code files are scanned by CONTENT instead.
WHY: MISSION T01 (0b): "Code files such as token_manager.py are NOT ignored; they are scanned by content."
₹ IMPACT: none
REVERSE BY: edit the two files (protected from the T02a seal on: an owner approval is then needed for a loosening)
CLASS CHECK: A (tooling) · PROTECTED: from seal/T02a

## D-005 | T01 | 2026-11-11
OLD → NEW: one pattern list; the hook and `safe_add.sh` refuse secret NAMES and secret CONTENT; the redactor also removes PII (phone, PAN, email) from evidence. The PII scan of the tree (mission_check #10, with `tools/scan_allowlist.toml`) arrives in T02b.
FOUND: one PII-shaped hit in the inputs: `docs/00_input/research/R_d_Costs_Data.md:219` pii/email = a stock exchange's public institutional contact address (not personal data). Kept; to be listed in `tools/scan_allowlist.toml` when T02b creates it. Two content hits in an existing test (`tests/test_login.py:116`, `:160`: fake token literals in a dict) → T02a assembles them at runtime from fragments (same test, not weakened) before mission_check #6 scans the tree.
WHY: §5.3, §5.5; MISSION T01 (0f) "minimal secret guard"
₹ IMPACT: none
REVERSE BY: n/a
CLASS CHECK: A (tooling) · PROTECTED: from seal/T02a

## D-006 | T01 | 2026-11-11
OLD → NEW: preflight classification of this machine: `CLOUDSDK_AUTH_ACCESS_TOKEN` → sandbox_breach (INCIDENT #1, STOP-THE-LINE: no push and no web fetch this session); `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` → env_warn (INCIDENT #2); `LIVE_TRADING_ENABLED` → env_warn (INCIDENT #3), not STOP-THE-LINE.
WHY: §1 item 9 is literal: a name containing ACCESS_TOKEN can never be allowlisted, even if (as the evidence suggests) it is the platform's own Google Cloud variable. `LIVE_TRADING_ENABLED` is the owner's own environment variable; nothing in the repo reads it (`EVIDENCE/T01/live_flag_code_refs.txt`), no bot process runs (`EVIDENCE/T01/live_process_check.txt`), the live path is OFF in code; calling it STOP-THE-LINE would be a false alarm. Follow-up for FULL-B (T13a / T13b): the I8 live lock must use a different variable name, and a test must show that `LIVE_TRADING_ENABLED` has no effect.
₹ IMPACT: this session cannot fetch official pages, so T03 facts stay UNVERIFIED and G0 stays CONDITIONAL at best [CODE(ASSUMPTION)]
REVERSE BY: the owner's `haan F-INC-1 be92` after fixing the sandbox (INCIDENT.md #1)
CLASS CHECK: C/D guard (sandbox) · PROTECTED: preflight.sh and env_allowlist.txt from seal/T02a

## D-007 | T01 | 2026-11-11
OLD → NEW: old V3 / V5 tracking files at the repo root (`PROGRESS.md`, `CHECKPOINT.md`, `LEDGER.md`) → `archive/PROGRESS_v5.md`, `archive/CHECKPOINT_v5.md`, `archive/LEDGER_v5.md` (git mv). Their DONE items are folded into STATE.md as "old DONE" [HISTORY].
WHY: one source of truth for state (§12 tracking-file list is complete); a V5 "STATE" next to the V11 STATE.md would contradict it
₹ IMPACT: none
REVERSE BY: `git mv` back
CLASS CHECK: A · PROTECTED: no

## D-008 | T01 | 2026-11-11
OLD → NEW: SESSION_START = the time the owner's MISSION.md copy was made (step 1, 13:33:21 IST, file mtime 1794384201), not the start of T01.
WHY: the minutes spent reading MISSION.md belong to this session's budget; counting from T01 would overstate the time left
₹ IMPACT: none
REVERSE BY: edit STATE.md
CLASS CHECK: A · PROTECTED: no

## D-009 | T01 | 2026-11-11
OLD → NEW: smoke command = `make smoke` (ruff check, ruff format --check, mypy, pytest through `python3 -m`, plus gofmt, go vet and go test in `pehredaar/`). Baseline is green (83 tests passed), so no BASELINE_RED.txt.
WHY: the bare `pytest` / `mypy` on PATH are separate tool installs without the project's dev dependencies (no hypothesis, no pytest stubs) and give a false red; `python3 -m` uses the interpreter that has them [EVIDENCE/T01/smoke_baseline.txt]
₹ IMPACT: none
REVERSE BY: edit Makefile
CLASS CHECK: A · PROTECTED: no

## D-010 | T01 | 2026-11-11
OLD → NEW: `limits.toml` created with the §5.4 / §11 defaults: CAPITAL_RS ₹15,000 [OWNER]; MAX_TOTAL_LOSS_RS ₹4,500 [ASSUMPTION until F-MAXLOSS]; EQUITY_FLOOR_RS ₹10,500 and MAX_DRAWDOWN_RS ₹2,250 and MAX_TRADE_LOSS_RS ₹1,125 and EARLY_SLIP_RS ₹225 [CODE(ASSUMPTION)]; H2_MONTHLY_RS ₹1,500 [OWNER]; MAX_LOTS 1 [ASSUMPTION]. Loss locks and the cool-off are migrated from niyam.toml in T06 (the lower ₹ risk wins).
WHY: §5.4 one source; T04 needs these inputs [EVIDENCE/T01/limits_chain.txt]
₹ IMPACT: max loss per trade ₹1,125 [CODE(ASSUMPTION)]; any long option above that premium × lot is out by construction
REVERSE BY: owner answer to F-MAXLOSS (`set F-MAXLOSS <₹> bca1`)
CLASS CHECK: D guard (D4, D8) · PROTECTED: per_value from seal/T02a
