# MISSING_INPUT (session 1, 2026-11-11)

What MISSION.md ("Malik ke liye", step 2) expects in `docs/00_input/`, and what was found.
Copies were made with `git show <branch>:<path>` (never `git checkout`); every copy is byte-identical
to its source blob, and its sha256 is in `SHA256SUMS`. Sources: `origin/idea` (a36092b) and
`origin/claude/busy-pascal-f7idxf` (71fab42). The local branch `idea` (9ac2afe) is one commit behind
`origin/idea`, so `origin/idea` was used.

| expected input | status | what was used / default |
|---|---|---|
| Idea v3.1 | FOUND | `docs/00_input/bot_idea_final.md` (its own `bot_idea_final.md.sha256` verifies; changelog ends at "Version 3.0 → 3.1") |
| Idea v4 | FOUND | `docs/00_input/01_Bot_Idea_v4.md`, plus `01b_Audit_Findings.md`, `02_Tech_Decisions.md`, `03_Strategy_Edge_Plan.md`, `04_Build_Roadmap.md`, `PROGRESS.md`, `research/R_a … R_f` |
| `niyam.toml` | FOUND | `docs/00_input/claude_branch/config/niyam.toml` (copy of `config/niyam.toml`) |
| `STRATEGY_v3.md` | MISSING | Not on any branch (checked: main, idea, bot, website, backup/pre-v3-2026-11-11, claude/busy-pascal-f7idxf). `PREREGISTER.md` names it. Closest material: `docs/00_input/claude_branch/strategy/STRATEGY_v2.md` and the code of commit 5779455 ("Strategy v3 build"). Treated as HISTORY. |
| `PREREGISTER.md` | FOUND | `docs/00_input/claude_branch/PREREGISTER.md` |
| old chats (purani chats) | MISSING | Not in the repo. Not used. |
| owner's answer to Sawal 118 | MISSING | The question exists (`01_Bot_Idea_v4.md` line 1496); no answer found → default of F-S118 (`both`) [ASSUMPTION] |
| owner's answer to Sawal 16 | MISSING | The question exists (`01_Bot_Idea_v4.md` line 1498); no answer found → default of F-S16 (`nifty50`, signals only) [ASSUMPTION] |
| old bot code (or zip) | FOUND, no zip | The code is on branch `main` (origin/main 1060045), which is the base of `mission/v11`. No zip anywhere, so step (0c) had nothing to extract. |
| branches `mission/v9`, `mission/v10` | ABSENT | Not in `git branch -a`. `mission/v11` was created from `main` as the owner asked. |
| V6–V10 `STATE.md` / `TASKS.json` | ABSENT | Nothing to archive. The V3/V5 tracking files (`PROGRESS.md`, `CHECKPOINT.md`, `LEDGER.md`) are moved to `archive/` (DECISIONS D-007). |

Other documents from `origin/claude/busy-pascal-f7idxf` copied to `docs/00_input/claude_branch/`
(same relative paths): `AUDIT_REPORT.md`, `CHECKPOINT.md`, `LEDGER.md`, `PROGRESS.md`, `SETUP_GUIDE.md`,
`README.md`, `strategy/AUDIT_ROUNDS.md`, `deploy/README.md`, `.claude/skills/survival-strategist/SKILL.md`.

Not copied (code or build files, not documents): `origin/idea` `scratch/` (benchmarks, build scripts,
risk simulations), `vercel.json`, `.gitignore`, `README.md`.
