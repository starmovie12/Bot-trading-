#!/usr/bin/env bash
# tools/verify/T01.sh (MISSION V11 §12, T01 SYNC_SAFE). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T01).
# Negative controls: a planted `.env` file must be refused by safe_add.sh and by the pre-commit hook;
# a planted fake token in a command's output must not reach EVIDENCE.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T01"
ctl="$tmp/mission-v11-verify-T01-ctl"
failures=0
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; failures=$((failures + 1)); }
cleanup() {
  git -C "$repo" worktree remove --force "$wt" >/dev/null 2>&1
  git -C "$repo" worktree prune >/dev/null 2>&1
  case "$ctl" in "$tmp"/mission-v11-verify-T01-ctl) rm -rf -- "$ctl" ;; esac
}
cleanup
git -C "$repo" worktree add --detach "$wt" HEAD >/dev/null 2>&1 || { echo "FAIL cannot create worktree"; exit 1; }
cd "$wt" || exit 1

# 1. files exist
for f in tools/preflight.sh tools/env_allowlist.txt .gitignore tools/safe_add.sh tools/secret_patterns.txt \
  .githooks/pre-commit .githooks/pre-push tools/ev.sh tools/redact.py tools/clock.sh tools/qcode.py SHA256SUMS \
  STATE.md TASKS.json DECISIONS.md NEGATIVE.md OWNER_TODO.md OWNER_QUESTIONS.md OWNER_APPROVALS.md \
  OWNER_CONFIG.md OWNER_NOTES.md MISSING_INPUT.md INCIDENT.md PR_BODY.md REPORT.md report_fields.json \
  EVIDENCE/INDEX.jsonl EVIDENCE/numbers.json EVIDENCE/seal_log.jsonl trials.jsonl holdout_log.jsonl \
  limits.toml params.toml constants.toml gates.toml PROTECTED.toml MISSION.md Makefile; do
  [ -e "$f" ] || fail "missing file $f"
done
[ "$failures" -eq 0 ] && pass "all T01 files exist"

# 2. the first V11 commit is on mission/v11, not on main
branch=$(git -C "$repo" rev-parse --abbrev-ref HEAD)
[ "$branch" = "mission/v11" ] && pass "repo branch is mission/v11" || fail "repo branch is $branch"
first=$(git log --reverse --format=%H --grep='^T01:' HEAD | head -1)
if [ -z "$first" ]; then
  fail "no T01 commit reachable from HEAD"
else
  on_main=0
  for b in main origin/main; do
    if git rev-parse -q --verify "$b" >/dev/null && git merge-base --is-ancestor "$first" "$b"; then on_main=1; fi
  done
  [ "$on_main" -eq 0 ] && pass "first T01 commit ${first:0:12} is not on main" || fail "T01 commit is on main"
  git -C "$repo" branch --contains "$first" | grep -q 'mission/v11' && pass "first T01 commit is on mission/v11" ||
    fail "first T01 commit not on mission/v11"
fi
[ "$(git -C "$repo" config --get core.hooksPath)" = ".githooks" ] && pass "core.hooksPath = .githooks" ||
  fail "core.hooksPath not set"

# 3. no secret-named file is tracked
if git ls-files -z | xargs -0 python3 tools/redact.py --names >/dev/null; then pass "no secret-named file tracked"; else
  fail "secret-named tracked file(s): $(git ls-files -z | xargs -0 python3 tools/redact.py --names | head -3)"
fi

# 7. STATE BUDGET_MIN / PAUSE_AFTER_G0 equal the MISSION.md header
hdr_budget=$(grep -o 'TIME_BUDGET_MIN = [0-9]*' MISSION.md | head -1 | grep -o '[0-9]*$')
st_budget=$(sed -n 's/^BUDGET_MIN: *\([0-9]*\).*/\1/p' STATE.md | head -1)
[ -n "$hdr_budget" ] && [ "$hdr_budget" = "$st_budget" ] && pass "BUDGET_MIN $st_budget equals header" ||
  fail "BUDGET_MIN '$st_budget' vs header '$hdr_budget'"
hdr_pause=$(grep -o 'PAUSE_AFTER_G0 = [a-z]*' MISSION.md | head -1 | sed 's/.*= //')
st_pause=$(sed -n 's/^PAUSE_AFTER_G0: *\([a-z]*\).*/\1/p' STATE.md | head -1)
[ "$hdr_pause" = "$st_pause" ] && pass "PAUSE_AFTER_G0 $st_pause equals header" || fail "PAUSE_AFTER_G0 mismatch"
grep -q '^SESSION_START: [0-9]\{10\}' STATE.md && pass "SESSION_START recorded" || fail "SESSION_START missing"

# 8. MISSION.md hash recorded (SHA256SUMS and STATE.md); inputs match SHA256SUMS
mh=$(sha256sum MISSION.md | cut -d' ' -f1)
grep -qxF "$mh  MISSION.md" SHA256SUMS && pass "MISSION.md sha256 in SHA256SUMS" || fail "MISSION.md hash not in SHA256SUMS"
grep -q "${mh:0:16}" STATE.md && pass "MISSION.md hash in STATE.md" || fail "MISSION.md hash not in STATE.md"
sha256sum -c --quiet SHA256SUMS && pass "every SHA256SUMS entry matches" || fail "SHA256SUMS mismatch"

# 9. smoke exits 0, or BASELINE_RED.txt is recorded
if make -s smoke >/dev/null 2>&1; then pass "smoke (make smoke) exits 0"; elif [ -f BASELINE_RED.txt ]; then
  pass "smoke red but BASELINE_RED.txt recorded"
else fail "smoke red and no BASELINE_RED.txt"; fi

# evidence of T01 holds no secret or PII shape
if python3 tools/redact.py --scan EVIDENCE/T01/*.txt EVIDENCE/INDEX.jsonl >/dev/null; then pass "EVIDENCE clean"; else
  fail "secret/PII shape in EVIDENCE: $(python3 tools/redact.py --scan EVIDENCE/T01/*.txt | head -3)"
fi

# 4-6. controls in a separate throw-away repository
mkdir -p "$ctl" && cd "$ctl" && git init -q -b ctl . && git config core.hooksPath .githooks
mkdir -p tools .githooks && cp "$wt"/tools/{safe_add.sh,redact.py,secret_patterns.txt,ev.sh} tools/ &&
  cp "$wt"/.githooks/pre-commit .githooks/ && cp "$wt"/.gitignore . && printf 'CYCLE_N: 1\n' >STATE.md
# negative control A: a planted .env file is refused by safe_add.sh
printf 'X=1\n' >.env
if tools/safe_add.sh .env >/dev/null 2>&1; then fail "safe_add.sh accepted .env"; else pass "safe_add.sh refused .env"; fi
# negative control B: forced into the index, the pre-commit hook refuses the commit
git add -f .env
if git -c user.name=verify -c user.email=verify@local commit -q -m "planted" >/dev/null 2>&1; then
  fail "pre-commit hook accepted a commit with .env"
else pass "pre-commit hook refused .env"; fi
git rm -q --cached .env
# positive control: allowed names are accepted
printf '%s  %s\n' "$(printf 'x' | sha256sum | cut -d' ' -f1)" "docs/a.md" >SHA256SUMS
printf 'smoke:\n\ttrue\n' >Makefile
printf 'example.com/m v1.0.0 h1:abc=\n' >go.sum
: >trials.jsonl
printf '#!/bin/sh\nexit 1\n' >.githooks/pre-push
for f in SHA256SUMS .gitignore Makefile go.sum trials.jsonl .githooks/pre-push; do
  tools/safe_add.sh "$f" >/dev/null 2>&1 && pass "safe_add.sh accepted $f" || fail "safe_add.sh refused $f"
done
# the same hook accepts a clean commit, so the refusal above came from the .env file
if git -c user.name=verify -c user.email=verify@local commit -q -m "clean" >/dev/null 2>&1; then
  pass "pre-commit hook accepted a clean commit"
else fail "pre-commit hook refused a clean commit"; fi
# negative control C: a fake token in a command's output never reaches EVIDENCE
fake="ey""J$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"
tools/ev.sh VT01 faketoken -- printf 'Authorization: Bearer %s\n' "$fake" >/dev/null 2>&1
if grep -rqF "$fake" EVIDENCE/; then fail "fake token reached EVIDENCE"; else pass "fake token redacted from EVIDENCE"; fi
grep -q 'REDACTED' EVIDENCE/VT01/faketoken.txt && pass "redaction marker present" || fail "no redaction marker"
# a sha256 line survives redaction (hash context)
h=$(printf 'y' | sha256sum | cut -d' ' -f1)
[ "$(printf 'sha256 %s\n' "$h" | python3 tools/redact.py)" = "sha256 $h" ] && pass "sha256 line kept by redactor" ||
  fail "redactor damaged a sha256 line"

cd "$repo" || exit 1
cleanup
# 10. no temp dir left
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T01 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
