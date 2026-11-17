# OWNER_NOTES (MISSION V11 §15): owner text that is not a command line

## session 1, 2026-11-11 (start message, summarised)
The owner attached MISSION_3.md and asked, in order: (1) save it unchanged as MISSION.md and print its
sha256 (done: 109339 bytes, sha256 5eb4f989…1611462, recorded in SHA256SUMS); (2) create `mission/v11`
from main, copy the old docs from `idea` (more on claude/busy-pascal-f7idxf) into docs/00_input/ with
`git show`, list what is missing in MISSING_INPUT.md, stage and commit nothing (T01 commits); (3) read
MISSION.md fully and execute it from T01 without stopping or asking; (4) MISSION.md wins over the
message, including its push rule. No command lines (§15) were in the message.

## session 2, 2026-11-11 (start message)
The owner wrote one line: `Continue` → the `continue` command (§15): a new session, no `seal`, no `budget`, no `data`. No answers to open questions.

## session 3, 2026-11-11 (start message)
The owner wrote one line: `Continue` → the `continue` command (§15) after CP1. No answers to the CP1 questions, so every default stays.

## session 3, 2026-11-11 (mid-run note, not a command line)
The owner wrote (Hinglish, summarised faithfully): "Turn the internet on. None of my data is in there; what you
found belongs to someone else. I did not give any API key or anything. Keep your internet on."
Handling (§3.1, §15): this is not a command line, so it has no effect by itself; the owner was shown the exact
lines that close INCIDENT #1 (`haan F-INC-1 be92`) and allow the platform's variable name in every later session
(`haan F-PROT-3 81a5`). Web fetch stays off until then.

## session 3, 2026-11-12 (two mid-run notes, not command lines)
After a worker restart the owner wrote twice (Hinglish, summarised faithfully): "Upload to GitHub every file you have
made so far." and "Upload all the work done so far to the GitHub repo; stop the work you are doing now; I will say
continue when you should start the next work."
Handling (§3.1, §15): the stop is followed: T11 → DEFERRED(time) checkpoint and SESSION_WRAP; nothing new starts
before `continue`. The upload is a push, which MISSION §3 allows only after `haan F-REMOTE 2350` and with no open
secret / sandbox_breach incident (INCIDENT #1 closes with `haan F-INC-1 be92`). A plain-language request is not a
command line, so the push stays local; every file is committed on `mission/v11`, and the owner was shown the two
exact lines. Found while checking: the GitHub repo is PUBLIC (EVIDENCE/SESSION3/repo_visibility.txt), while
F-REMOTE asks for a private repo first.
