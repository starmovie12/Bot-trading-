#!/usr/bin/env bash
# tools/verify/T10.sh (MISSION V11 §12, T10 VERDICT_CORE). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T10).
# Negative controls: a gates.toml weaker than the floors is rejected; a second holdout open is refused;
# a random-entry strategy, a look-ahead feature and a zero-cost run on synthetic data each FAIL the harness;
# the FULL-B gate is CLOSED without REAL data.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T10"
syn="$tmp/mission-v11-verify-T10-syn"
failures=0
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; failures=$((failures + 1)); }
cleanup() {
  git -C "$repo" worktree remove --force "$wt" >/dev/null 2>&1
  git -C "$repo" worktree prune >/dev/null 2>&1
  case "$syn" in "$tmp"/mission-v11-verify-T10-syn) rm -rf -- "$syn" ;; esac
}
cleanup
git -C "$repo" worktree add --detach "$wt" HEAD >/dev/null 2>&1 || { echo "FAIL cannot create worktree"; exit 1; }
cd "$wt" || exit 1

for f in gates.toml PREREGISTER_v2.md tools/floors_baseline.toml tools/power.py tools/truth_tests.py tools/fullb_gate.py \
  tools/verdict.py tests/test_truth_tests.py; do
  [ -e "$f" ] || fail "missing $f"
done
# make verdict on synthetic data (kind SIM) and without data → NOT_YET(NO_DATA)
mkdir -p "$syn" && echo SIM >"$syn/kind.txt"
PYTHONPATH=src python3 - "$syn" <<'PY'
import datetime as dt, sys
from pathlib import Path
from bot.recorder.snapshot import RecorderConfig, SnapshotRecorder
from bot.recorder.synthetic_feed import light_keys, synthetic_day
rec = SnapshotRecorder(RecorderConfig(data_dir=Path(sys.argv[1]), size_cap_bytes=10**9))
for i in range(3):
    for local, msg in synthetic_day(dt.date(2026, 11, 12) + dt.timedelta(days=i), i, light_keys()[:2]):
        rec.on_message(msg, local)
    rec.end_day()
PY
v=$(make -s verdict DATA="$syn")
case "$v" in NOT_YET\(NO_DATA*) pass "make verdict on synthetic data: $v" ;; *) fail "synthetic verdict: $v" ;; esac
v=$(make -s verdict)
case "$v" in NOT_YET\(NO_DATA*) pass "make verdict without data: $v" ;; *) fail "no-data verdict: $v" ;; esac
printf '{"g0": "FAIL_ARITH", "members": {"U1": {"outcome": "FAIL_ARITH"}, "U2": {"outcome": "FAIL_ARITH"}}}' >"$syn/g0_fail.json"
v=$(python3 tools/verdict.py --g0 "$syn/g0_fail.json")
[ "$v" = "STOP(G0_FAIL_ARITH)" ] && pass "G0-FAIL fixture gives STOP(G0_FAIL_ARITH)" || fail "G0-FAIL fixture: $v"
# gates vs floors on the clean tree, and a weaker gates file rejected
python3 - <<'PY' && pass "gates.toml not weaker than the floors; a weaker copy is rejected" || fail "gates vs floors"
import copy, sys, tomllib
sys.path.insert(0, ".")
from tools.truth_tests import gates_problems
g = tomllib.load(open("gates.toml", "rb")); f = tomllib.load(open("tools/floors_baseline.toml", "rb"))
weak = copy.deepcopy(g); weak["min_trading_days"]["value"] = 60
sys.exit(0 if not gates_problems(g, f) and gates_problems(weak, f) else 1)
PY
# harness negative controls (synthetic trade lists)
out=$(python3 -m pytest -o addopts= -v -p no:cacheprovider tests/test_truth_tests.py 2>&1)
for t in test_a_random_entry_strategy_fails_the_harness test_a_zero_cost_run_fails_the_harness \
  test_a_look_ahead_feature_fails_the_prefix_test_and_a_causal_one_passes test_a_second_holdout_open_is_refused \
  test_gates_weaker_than_the_floors_are_rejected; do
  printf '%s\n' "$out" | grep -q "::$t PASSED" && pass "$t" || fail "$t"
done
# FULL-B gate CLOSED without REAL data
g=$(python3 tools/fullb_gate.py)
case "$g" in "FULL-B gate: CLOSED"*) pass "fullb_gate CLOSED without REAL data" ;; *) fail "fullb_gate: $g" ;; esac
# trials.jsonl still empty: gates were written before any trial
[ ! -s trials.jsonl ] && pass "no trial before the pre-registration" || fail "trials.jsonl not empty"

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T10 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
