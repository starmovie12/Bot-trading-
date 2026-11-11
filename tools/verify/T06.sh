#!/usr/bin/env bash
# tools/verify/T06.sh (MISSION V11 §12, T06 SUSPECTS). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T06).
# Negative controls (each planted in the worktree, then restored): a second limit source fails;
# EQUITY_FLOOR_RS ≠ CAPITAL_RS − MAX_TOTAL_LOSS_RS fails; the banned name LOSS_FLOOR fails; a lot size taken
# from code fails.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T06"
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
T=tests/test_limits_chain.py
q() { python3 -m pytest -q -o addopts= -p no:cacheprovider "$@" >/dev/null 2>&1; }

q "$T" && pass "limits chain, one source, lot source, banned name: all tests pass" || fail "limits tests fail on the clean tree"
q tests/test_strategy.py -k lot_sizes_come_only && pass "lot sizes only from the instrument file" || fail "lot-size test"
PYTHONPATH=src python3 -c "from bot.limits import load_limits; load_limits()" && pass "the chain holds" || fail "chain broken"
PYTHONPATH=src python3 -m bot --check >/dev/null && pass "entry point check reads limits.toml" || fail "python -m bot --check"
wrong=$(git grep -n "SL-M" -- '*.md' ':!docs/00_input' ':!archive' ':!MISSION.md' ':!EVIDENCE' | grep -vi "reject")
[ -z "$wrong" ] && pass "docs contain 0 wrong SL-M" || fail "wrong SL-M in docs: $wrong"
[ "$(grep -c '^Type=' deploy/pehredaar.service)" -eq 1 ] && pass "one Type= in pehredaar.service" || fail "duplicate Type="

# negative control 1: a second limit source
printf '\nMAX_TOTAL_LOSS_RS = 9000\n' >>src/bot/strategy/rules.py
q "$T" -k one_source && fail "a second limit source was accepted" || pass "a second limit source fails"
git checkout -q -- src/bot/strategy/rules.py
# negative control 2: equity floor not equal to capital minus total loss
sed -i '/^\[EQUITY_FLOOR_RS\]/{n;s/^value = .*/value = 10000/}' limits.toml
PYTHONPATH=src python3 -c "from bot.limits import load_limits; load_limits()" 2>/dev/null &&
  fail "a wrong EQUITY_FLOOR_RS was accepted" || pass "EQUITY_FLOOR_RS ≠ CAPITAL_RS − MAX_TOTAL_LOSS_RS fails"
git checkout -q -- limits.toml
# negative control 3: the banned name anywhere outside archive/ and MISSION.md
printf '\n%s\n' "LOSS_""FLOOR" >>README.md
q "$T" -k banned && fail "the banned name was accepted" || pass "the banned name fails"
git checkout -q -- README.md
# negative control 4: a lot size read from code
printf '\nX = SPECS["Nifty50"].lot\n' >>src/bot/strategy/selection.py
q "$T" -k lot_size_never && fail "a lot size from code was accepted" || pass "a lot size from code fails"
git checkout -q -- src/bot/strategy/selection.py
[ -z "$(git status --porcelain)" ] && pass "worktree restored after the controls" || fail "worktree not restored"

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T06 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
