#!/usr/bin/env bash
# tools/verify/T07.sh (MISSION V11 §12, T07 AUTOPSY). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T07).
# Negative control: the Recorder from the commit before the fix (6136144) must FAIL the autopsy tests
# (fail → pass is reproduced, not just claimed); then the current code must pass them.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T07"
prefix=6136144
failures=0
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; failures=$((failures + 1)); }
cleanup() {
  git -C "$repo" worktree remove --force "$wt" >/dev/null 2>&1
  git -C "$repo" worktree prune >/dev/null 2>&1
}
cleanup
git -C "$repo" worktree add --detach "$wt" HEAD >/dev/null 2>&1 || { echo "FAIL cannot create worktree"; exit 1; }
cd "$wt" || exit 1
q() { python3 -m pytest -q -o addopts= -p no:cacheprovider "$@" >/dev/null 2>&1; }

for f in docs/AUTOPSY.md tests/test_recorder_autopsy.py tests/invariants/test_order_path_disabled.py \
  tests/invariants/test_i08_live_flag_off.py EVIDENCE/T07/inventory.txt; do
  [ -e "$f" ] || fail "missing $f"
done
grep -q '^| 1 | SL miss' docs/AUTOPSY.md && grep -q 'bug A' docs/AUTOPSY.md && pass "ranked bug list present" || fail "ranked list"

# fail → pass reproduction for bug A
git show "$prefix:src/bot/recorder/snapshot.py" >src/bot/recorder/snapshot.py
q tests/test_recorder_autopsy.py && fail "autopsy tests pass on the pre-fix Recorder (they cannot fail)" ||
  pass "autopsy tests fail on the pre-fix Recorder ($prefix)"
git checkout -q -- src/bot/recorder/snapshot.py
q tests/test_recorder_autopsy.py && pass "autopsy tests pass after the fix" || fail "autopsy tests fail after the fix"

# the order path is unreachable and the live flag is OFF
q tests/invariants/test_order_path_disabled.py tests/invariants/test_i08_live_flag_off.py &&
  pass "order path unreachable; live flag OFF; LIVE_TRADING_ENABLED has no effect" || fail "I8 tests"
q tests/test_recorder_mvp.py tests/invariants && pass "Recorder and invariant suites pass" || fail "Recorder suite"
out=$(python3 tools/mission_check.py)
printf '%s\n' "$out" | grep -q '^#14 .*: OK' && pass "invariant coverage (#14) OK" || fail "#14 coverage"
[ -z "$(git status --porcelain)" ] && pass "worktree restored" || fail "worktree not restored"

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T07 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
