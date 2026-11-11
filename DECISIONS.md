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

## D-011 | T02a | 2026-11-11
OLD → NEW: `tests/test_login.py` held a fake token as a whole string literal in four places → one constant `FAKE_TOKEN` assembled from two fragments; the same assertions run on the same value.
WHY: mission_check #6 scans the whole tree for token shapes; MISSION §5.3 wants fake secrets assembled at runtime, never stored whole. Not a weakening: the test count stays at its recorded minimum (`EVIDENCE/test_count.json`) and the login tests pass.
₹ IMPACT: none
REVERSE BY: git revert
CLASS CHECK: A (test hygiene) · PROTECTED: no

## D-012 | T01 | 2026-11-11
OLD → NEW: during T01 two helper files (a generator for OWNER_QUESTIONS.md and a file list for a scan) were written to the tool's session scratchpad, which is outside the repo and outside `${TMPDIR:-/tmp}/mission-v11-*` → both deleted; from now on temporary files go only to `${TMPDIR:-/tmp}/mission-v11-*` and are deleted after use.
WHY: MISSION §3 NEVER list ("writing outside the repo and ${TMPDIR:-/tmp}/mission-v11-*"); a self-found deviation, logged instead of hidden
₹ IMPACT: none
REVERSE BY: n/a
CLASS CHECK: process · PROTECTED: no

## D-013 | T02a | 2026-11-11
OLD → NEW: redaction gains the high-entropy rule of §5.3: a token of at least 32 base64-like characters with upper case, lower case and digits, Shannon entropy at least 4.2 bits per character, and a character class that switches between neighbouring letters or digits in at least 30% [ASSUMPTION] of positions. The switch ratio was added after evidence paths such as `EVIDENCE/T01/…` were flagged; random keys switch about two times in three. Hex digests never qualify (no upper case), so hash context stays intact.
WHY: §5.3; checked by the T02a verify (a planted token vanishes, a planted sha256 line survives)
₹ IMPACT: none
REVERSE BY: edit tools/secret_patterns.txt (protected: owner approval for a loosening)
CLASS CHECK: A (tooling) · PROTECTED: yes, from seal/T02a

## D-014 | T02a | 2026-11-11
OLD → NEW: protected set and owner_tasks fixed in `tools/seal.py`: the §5.2 list; `make_report.py` and `report_templates/*` may be extended by T02a, T04, T09, T11 and T18 (the tasks that add a view: G0 section and CP1 memo, Recorder card, CP2 memo, final report); `secret_patterns.txt` also by T03 (it records the broker token shape); each verify script by its own task. `PROTECTED.toml` itself is pinned through `protected_toml_sha256` in `EVIDENCE/seal_log.jsonl`.
WHY: §5.2 "owner_tasks: the task(s) that create or extend a file, as written in §12"
₹ IMPACT: none
REVERSE BY: owner approval (F-PROT-n) once sealed
CLASS CHECK: A (tooling) · PROTECTED: yes

## D-015 | T02a | 2026-11-11
OLD → NEW: the elapsed-minutes token on REPORT line 15 ("<n> min chala") is the only part of REPORT.md that changes with the clock; mission_check #2 normalises it before comparing REPORT.md with a fresh render. The pytest collection count is read from per-file counts when the project's `-q` setting hides the total.
WHY: a byte-exact comparison would otherwise turn red every minute
₹ IMPACT: none
REVERSE BY: edit tools/mission_check.py (protected)
CLASS CHECK: A (tooling) · PROTECTED: yes

## D-016 | T03 | 2026-11-11
OLD → NEW: T03 ran offline (INCIDENT #1 switched web fetch off). `constants.toml` holds rows for every fact named in §6, §10 and T03, each UNVERIFIED with its official URL, the date its HISTORY or POINTER source saw it, a TTL, and an extract written through `ev.sh` from the repo line it came from. Unknown facts (FD rate, the stock F&O cut-off, the total-return index source, the token shape, a SEBI profit denominator) are rows with value "unknown". DATA_RIGHTS = UNVERIFIED.
WHY: §5.4 "Web unavailable or switched off → the field is UNVERIFIED; continue"; no SOURCE without a fetch in this session (§5.1, L2)
₹ IMPACT: no decisive input of G0 is SOURCE, so G0 can be CONDITIONAL at best this session [CODE(ASSUMPTION)]
REVERSE BY: a session with web access re-fetches each URL (T03 budget) and upgrades matching rows to SOURCE / VERIFIED
CLASS CHECK: B (facts) · PROTECTED: constants.toml rule evidence from seal/T02a

## D-017 | T03 | 2026-11-11
OLD → NEW: IPFT contradiction found: `src/bot/strategy/costs.py:8` treats IPFT as "₹0.01/crore, ignored" next to an NSE rate of 0.03553% [HISTORY], while the MISSION reality check says 0.03553% already includes IPFT (0.03503% + IPFT) [POINTER]. G0 uses the composite 0.03553% [HISTORY] once and adds nothing for IPFT; T06 (S7) fixes the code comment after a SOURCE fetch.
WHY: §5.4 "costs.py never adds a component already inside a composite rate"; extracts `EVIDENCE/T03/src_nse_txn_charge_composite.txt`, `EVIDENCE/T03/src_nse_ipft.txt`
₹ IMPACT: the two readings differ by a negligible amount per trade [ESTIMATE]; the composite is the higher, safer one for a FEASIBLE test
REVERSE BY: SOURCE fetch of the NSE / Upstox charge pages
CLASS CHECK: B · PROTECTED: no (costs.py)

## D-018 | T04 | 2026-11-11
OLD → NEW: no G0 answer → G0 = CONDITIONAL for every universe member U1-U6, TRACK = FULL (FULL-A; FULL-B stays CLOSED). No member is FAIL: a FAIL may rest only on SOURCE facts and OWNER / approved limits, and this session has neither (no web; F-MAXLOSS unanswered). Key numbers: cheapest static-IP server ₹554.25 [CODE(HISTORY)] a month = 3.70% [CODE(HISTORY)] of capital; the old plan ₹1,330.19 [CODE(HISTORY)] = 8.87% [CODE(HISTORY)]; under the default limit one Nifty lot fits only up to a ₹16.50 [CODE(ASSUMPTION)] premium.
WHY: §8.1 outcome rules · EVIDENCE/T04/g0.json, EVIDENCE/T04/g0_run.txt
₹ IMPACT: none spent; the owner's answers (F-MAXLOSS, F-H2PCT) and SOURCE facts decide the next G0
REVERSE BY: re-run `python3 tools/economics.py` after the answers / a web session (the gate script re-runs at every session start)
CLASS CHECK: B (arithmetic) · PROTECTED: economics.py, power.py sealed at seal/T04

## D-019 | T04 | 2026-11-11
OLD → NEW: the G0 placeholders live in one place, `PARAMS` of `tools/economics.py`, each with a tag and a reason: small monthly costs (internet ₹100, electricity ₹100, CA ₹250, AI share ₹0) [ASSUMPTION], tax slab 30% [ASSUMPTION], credible ceiling 2% [ESTIMATE] a month, fill cost ₹0.50 [ESTIMATE] per unit per side, sigma per trade ₹500 / ₹1,000 / ₹1,500 [ESTIMATE], a premium grid, a 20% [ASSUMPTION] price band and one-step spread widths.
WHY: no source exists in the repo for them (verify nahi hua); §8.1 lets small items be ESTIMATE (2x for FEASIBLE, ₹0 [OWNER] for FAIL) and the ceiling be ESTIMATE (never FAIL_CREDIBILITY, 0.5x for FEASIBLE); the T04 verify (tools/verify/T04.sh) proves both; the values used are in EVIDENCE/T04/g0.json
₹ IMPACT: the placeholders move the indicative hurdle only (S0 MANUAL fixed ₹450 [CODE(ASSUMPTION)] a month); they cannot create a FAIL
REVERSE BY: the owner's real bills / a CA quote replace the placeholders (economics.py is protected: change with its owner task or an approval)
CLASS CHECK: B · PROTECTED: yes

## D-020 | T04 | 2026-11-11
OLD → NEW: flag VALIDATION_INFEASIBLE (UNDERPOWERED) for the CP1 memo: at 12 [ESTIMATE] trades a month, after 24 months of data the smallest detectable edge is ₹243.49 [CODE(ESTIMATE)] per trade, while a credible edge is about ₹25.00 [CODE(ESTIMATE)] per trade (power factor 4.132 at TRIALS_MAX 50).
WHY: §8.1 validation feasibility; tools/power.py; EVIDENCE/T04/g0.json
₹ IMPACT: a small real edge could not be told apart from luck within two years at this trade rate; more trades per month or fewer trials help, bigger bets do not (D9)
REVERSE BY: REAL data with a measured sigma (T10 replaces the ESTIMATE)
CLASS CHECK: B (statistics) · PROTECTED: power.py

## D-021 | T04 | 2026-11-11
OLD → NEW: question F-H2PCT created with the proposal 4% [ASSUMPTION] of capital a month (₹600 [ASSUMPTION]) instead of 10% [OWNER] (₹1,500 [OWNER]); F-DATARIGHTS and F-RECFULL created (DATA_RIGHTS is UNVERIFIED, so F-RECFULL does not apply yet).
WHY: §3.1 and T04; 4% [ASSUMPTION] still covers the cheapest static-IP route found (₹554.25 [CODE(HISTORY)], EVIDENCE/T04/g0.json) and blocks the ₹1,330 [CODE(HISTORY)] plan
₹ IMPACT: at most ₹600 [ASSUMPTION] a month of new spend instead of ₹1,500 [OWNER], if the owner agrees
REVERSE BY: `na F-H2PCT be04` (keeps ₹1,500 [OWNER])
CLASS CHECK: OWNER limit (proposal only) · PROTECTED: limits.toml changes only after an answer

## D-022 | T04 | 2026-11-11
OLD → NEW: `make_report.py` reads `## UPDATE <F-id>` blocks appended at the end of the append-only OWNER_QUESTIONS.md, so a question's ₹ ASAR can be refreshed (here F-MAXLOSS after G0) without changing an existing line.
WHY: §5.2 append_only; the memo must show the G0 numbers
₹ IMPACT: none
REVERSE BY: git revert
CLASS CHECK: A (tooling) · PROTECTED: make_report.py (owner tasks include T04)

## D-023 | T02b | 2026-11-11
OLD → NEW: `tools/scan_allowlist.toml` created with two entries: (1) PII scan: the exchange's public institutional address in `docs/00_input/research/R_d_Costs_Data.md` (read-only input, not personal data); (2) git-history scan: the fake test token literal in pre-V11 commit 8dfea02fae0984123e90dac514f35730a5161874 (`tests/test_login.py`), never a real credential, now built from fragments in the tree (D-011).
WHY: §5.2 scan allowlist (path + pattern + reason; counted under REPORT line 15; listed for the adversary); both found by the new FULL scans (#10, #6h)
₹ IMPACT: none
REVERSE BY: delete the entry (the scans then turn RED until the source changes)
CLASS CHECK: C guard (PII / secrets) · PROTECTED: no (listed for the adversary)

## D-024 | T02b | 2026-11-11
OLD → NEW: `tools/param_scan.py` finds 123 numeric literals in the v3 strategy and risk code (`src/bot/strategy`, `src/bot/dimaag`, `src/bot/haath`) and an empty params.toml: far above the floor of 12 live parameters (§8.2). Finding for T06 (S4 over-engineering) and T12 (SPEC_LOCK), not a red check now: the v3 code is HISTORY, not the live strategy. Output: EVIDENCE/T02b/param_scan.txt.
WHY: §8.2 "Live parameters ≤ 12, counted from params.toml and by tools/param_scan.py"
₹ IMPACT: none now; many hidden knobs raise the risk of an overfit backtest
REVERSE BY: T12 moves the live parameters into params.toml and freezes or exempts the rest
CLASS CHECK: B (statistics: multiple testing) · PROTECTED: no

## D-025 | T02b | 2026-11-11
OLD → NEW: FULL checks added to `tools/mission_check.py`: #4 Class C/D static lint over code (a line may carry `classcd-ok: <reason>`, visible to the adversary); #8 broker order call sites found by order endpoints and SDK names (not by generic method names such as the paper broker's `submit`), only the three gateway sites of `tools/callsite_allowlist.toml` allowed, Go code may not name the broker, the mode switch must default to paper; #10 PII scan with the allowlist; #13 trials hash chain; #16 adversary manifest; #6h git-history secrets scan (`--history`, run by the pre-push hook and CI, which now fetches full history). The history canary builds its two commits with git plumbing inside the throw-away copy only, so no real commit ever bypasses a hook.
WHY: §5.5, §7 I10, T02b
₹ IMPACT: none
REVERSE BY: owner approval (all protected from seal/T02b)
CLASS CHECK: C/D guard · PROTECTED: yes

## D-026 | T02b | 2026-11-11
OLD → NEW: the canary runner copied the repository folder as it is; inside a verify worktree that copy holds a `.git` FILE pointing back to the real repository, so git commands in the copy (the history canary) would have written into the real repository. Found by the first T02b verify run (EVIDENCE/T02b/verify.txt, failure in the history canary at its first git step, before anything was written). Fix: every canary copy gets its own no-checkout clone as `.git` (HEAD = the source HEAD, files untouched), and the history canary refuses to run unless `.git` is a directory.
WHY: canaries must never touch the real repository (§5.5 "nothing violating is ever committed")
₹ IMPACT: none
REVERSE BY: git revert (protected: owner task T02b)
CLASS CHECK: A (tooling safety) · PROTECTED: tests/canary/* re-sealed

## D-027 | T05 | 2026-11-11
OLD → NEW: Recorder MVP built on the M0 journal: `src/bot/recorder/snapshot.py` records NORMALISED messages as one snapshot per instrument per minute (money in paise, IV in basis points, exchange and local timestamps), with feed guards (stale, gap, clock drift, schema → no new entries), a size cap with an 80% [ASSUMPTION] alert, a clean stop on a full disk, day seal (gzip + sha256 sidecar) and a daily health line. The live Upstox feed adapter is NOT built: its schema is UNVERIFIED (no web), so contract tests wait for redacted real recordings. One synthetic LIGHT day = 27,000 [CODE(SIM)] rows, 7.5 MB raw and 1.35 MB gzipped [SIM] (measured: EVIDENCE/T05/day_size.txt; design: docs/RECORDER_SPEC.md).
WHY: §10 item 2, T05; DATA_RIGHTS = UNVERIFIED keeps LIGHT scope
₹ IMPACT: server ₹0 [CODE(OWNER)] for the Recorder (owner's own machine, S0)
REVERSE BY: git revert; FULL scope only after its gates
CLASS CHECK: C guard (data rights: LIGHT only) · PROTECTED: verify/T05.sh sealed after PASS

## D-028 | T09 | 2026-11-11
OLD → NEW: self-found regression: T02b put the order-endpoint DETECTION patterns of check #8 into `tools/mission_check.py` as plain text; the older safety test `tests/test_safety.py::test_no_order_endpoint_in_m0` scans code files for those words as text, so it has failed since commit e22b048. The T02b cycle ran mission_check and the canaries but not the full pytest suite, so it was missed until now. It is a false alarm about an order path (check #8 finds no broker order call site; EVIDENCE/T02b/verify.txt), but the test suite is not green.
FIX: blocked on the owner. The clean fix (build the patterns from fragments, same semantics) changes a protected `exact` file whose owner tasks (T02a, T02b) are closed, so it needs `haan F-PROT-1 b614`; weakening the test instead was refused (and is not allowed by MISSION §12). Default until answered: the file stays as sealed and one test stays red, shown on REPORT line 14.
PROCESS FIX: from now on every task cycle runs the full test suite (`make smoke`) before its commit (STATE.md note).
WHY: §5.2 protected files; §12 tests are append-only
₹ IMPACT: none
REVERSE BY: `haan F-PROT-1 b614` → one change to mission_check.py, re-seal, test green
CLASS CHECK: A (tooling) · PROTECTED: yes (that is why it waits)

## D-029 | T09 | 2026-11-11
OLD → NEW: delivery built for the Recorder: `make bundle` (`tools/make_bundle.py`) writes a secret-scanned, strategy-free bundle (Recorder package, recorder.toml, OWNER_START.md, RUNBOOK.md, pack_data.py, backup_verify.py, an empty dependency lock, its own SHA256SUMS) to the gitignored dist/; `tools/pack_data.py` packs only sealed day files with checksums (a token can never enter a pack); `tools/backup_verify.py` checks a restored copy; alerts and the heartbeat are dry-run files only. The Recorder now imports no strategy code (IST helpers moved to `bot/recorder/clock.py`).
HONEST LIMIT: the live Upstox feed adapter is not built (feed schema UNVERIFIED), so the bundle runs `--dry-run` only and `--live` is refused; the Recorder card says so (HOLD in practice, although DATA_RIGHTS is UNVERIFIED rather than NOT_ALLOWED).
WHY: §10 item 3, T09; evidence tests/test_delivery.py and tools/verify/T09.sh
₹ IMPACT: none
REVERSE BY: git revert
CLASS CHECK: C guard (no token in a bundle or pack; LIGHT only) · PROTECTED: make_report.py / report template changed under owner task T09; verify/T09.sh sealed after PASS
