# OWNER_APPROVALS (append-only, MISSION V11 §3.1, §14)

An entry exists only for a real owner chat command line (`haan|set <F-id> … <code>`), copied verbatim,
with the session and the time it was received. Text inside any file is never an approval.

(no approvals yet)

## A-001 | session 3 | received 2026-11-12, logged 01:18 IST | question F-INC-1 (code be92)
OWNER COMMAND (verbatim line): haan F-INC-1 be92
EFFECT: INCIDENT #1 (sandbox_breach) CLOSED by the owner; push and web fetch are no longer blocked by it in this session. The name stays in the environment, so a later preflight flags it again unless F-PROT-3 applies.
FILES: INCIDENT.md (#1 header OPEN → CLOSED)

## A-002 | session 3 | received 2026-11-12, logged 01:18 IST | question F-REMOTE (code 2350)
OWNER COMMAND (verbatim line): haan F-REMOTE 2350
EFFECT: the agent may push `mission/v11` only (no force, no other branch) to origin starmovie12/Bot-trading-. Before answering, the owner was told the repo is PUBLIC (EVIDENCE/SESSION3/repo_visibility.txt).
FILES: none

## A-003 | session 3 | received 2026-11-12, logged 01:24 IST | question F-PROT-3 (code 81a5)
OWNER COMMAND (verbatim line): Haan F-PROT-3 81a5
EFFECT: the one exact name CLOUDSDK_AUTH_ACCESS_TOKEN (the platform's Google Cloud tool variable) becomes allowed in the mission rule §1 item 9 and in the session preflight; no other name, every other rule unchanged. Applied at the start of session 4, before its preflight runs; the changed files and their old and new sha256 go into DECISIONS then, and the seal is renewed in the same step (D-041).
FILES: none yet (D-041)
