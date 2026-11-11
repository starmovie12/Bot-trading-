#!/usr/bin/env bash
# tools/verify/T02b.sh (MISSION V11 §12, T02b GUARDS_FULL). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T02b).
# Negative controls: every CORE and FULL canary must turn its check RED (a second order call site, a Go
# file naming the broker host, a Class C/D pattern, a hidden trial, a secret in git history, plus the
# eight CORE ones); param_scan.py must fail on a module with too many literals.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T02b"
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

for f in tools/callsite_allowlist.toml tools/scan_allowlist.toml tools/param_scan.py .github/workflows/ci.yml; do
  [ -e "$f" ] || fail "missing $f"
done

# the clean tree passes, including the FULL checks and the git-history scan
out=$(python3 tools/mission_check.py --history 2>&1)
for n in 4 6h 8 10 13 16; do
  printf '%s\n' "$out" | grep -q "^#$n .*: OK" || fail "check #$n missing or not OK"
done
printf '%s\n' "$out" | grep -q '^mission_check: GREEN' && pass "clean checkout GREEN (Tier 1 + FULL + history)" ||
  { fail "clean checkout RED"; printf '%s\n' "$out" | grep -E 'RED|^    ' | head -10; }

# every canary (CORE + FULL) is caught, and the clean copy is GREEN
canary=$(python3 tests/canary/run_canary.py 2>&1)
printf '%s\n' "$canary" | sed 's/^/  canary: /'
caught=$(printf '%s\n' "$canary" | grep -c '^PASS canary')
printf '%s\n' "$canary" | grep -q '^PASS clean copy is GREEN' && [ "$caught" -eq 13 ] &&
  printf '%s\n' "$canary" | grep -q '^canaries: 0 failure(s)$' && pass "13 canaries caught, clean copy GREEN" ||
  fail "canaries: $caught caught"

# call-site allowlist: exactly three sites, all in the gateway module
python3 - <<'PY' && pass "callsite_allowlist: three gateway sites" || fail "callsite_allowlist is not three gateway sites"
import sys, tomllib
s = tomllib.load(open("tools/callsite_allowlist.toml", "rb"))["site"]
ok = len(s) == 3 and {x["file"] for x in s} == {"src/bot/gateway.py"}
ok = ok and {x["function"] for x in s} == {"submit", "reduce_only", "tighten_stop"}
sys.exit(0 if ok else 1)
PY
# scan allowlist: every entry has a path, a pattern and a reason
python3 - <<'PY' && pass "scan_allowlist entries complete" || fail "scan_allowlist entry incomplete"
import sys, tomllib
e = tomllib.load(open("tools/scan_allowlist.toml", "rb"))["entry"]
sys.exit(0 if e and all(x.get("path") and x.get("pattern") and x.get("reason") for x in e) else 1)
PY

# param_scan: positive and negative control on throw-away modules
mod="$tmp/mission-v11-verify-T02b-mod"
mkdir -p "$mod"
printf 'A = 7\nB = 0.5\n' >"$mod/small.py"
python3 - "$mod/big.py" <<'PY'
import sys
open(sys.argv[1], "w").write("".join(f"X{i} = {i + 2}\n" for i in range(13)))
PY
python3 tools/param_scan.py --max 12 --paths "$mod/small.py" | grep -q 'literals counted: 2' && pass "param_scan counts 2 literals" ||
  fail "param_scan miscounted"
python3 tools/param_scan.py --max 12 --paths "$mod/big.py" >/dev/null && fail "param_scan accepted 13 literals" ||
  pass "param_scan rejects 13 literals (> 12)"
case "$mod" in "$tmp"/mission-v11-verify-T02b-mod) rm -rf -- "$mod" ;; esac

# wiring: pre-push and CI run the history scan; CI runs the canaries with full history
grep -q 'mission_check.py" --history' .githooks/pre-push && pass "pre-push runs the history scan" || fail "pre-push lacks --history"
grep -q 'mission_check.py --history' .github/workflows/ci.yml && grep -q 'run_canary.py' .github/workflows/ci.yml &&
  grep -q 'fetch-depth: 0' .github/workflows/ci.yml && pass "CI runs mission_check --history and the canaries" ||
  fail "CI wiring incomplete"

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T02b verify: $failures failure(s)"
[ "$failures" -eq 0 ]
