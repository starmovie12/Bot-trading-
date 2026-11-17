#!/usr/bin/env bash
# tools/verify/T02a.sh (MISSION V11 §12, T02a GUARDS_CORE). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T02a).
# Negative controls: every CORE canary (untagged number, fake secret, skipped test, protected change,
# fake approval with a wrong code, digit in report_fields.json, constants value missing from its
# extract, FULL-B PASS with the gate CLOSED) must turn mission_check RED; a commit with an untagged
# number must be refused by the pre-commit hook; pushes must be refused by the pre-push hook.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T02a"
cp_dir="$tmp/mission-v11-verify-T02a-hook"
failures=0
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; failures=$((failures + 1)); }
cleanup() {
  git -C "$repo" worktree remove --force "$wt" >/dev/null 2>&1
  git -C "$repo" worktree prune >/dev/null 2>&1
  case "$cp_dir" in "$tmp"/mission-v11-verify-T02a-hook) rm -rf -- "$cp_dir" ;; esac
}
cleanup
git -C "$repo" worktree add --detach "$wt" HEAD >/dev/null 2>&1 || { echo "FAIL cannot create worktree"; exit 1; }
cd "$wt" || exit 1

# files of T02a exist
for f in tools/mission_check.py tools/make_report.py tools/tag_scope.toml tools/seal.py tools/redact.py \
  report_templates/report.md report_templates/memo.md report_templates/recorder_card.md \
  tests/canary/run_canary.py .githooks/pre-commit .githooks/pre-push PROTECTED.toml; do
  [ -e "$f" ] || fail "missing $f"
done

# the clean tree passes
out=$(python3 tools/mission_check.py 2>&1)
if printf '%s\n' "$out" | grep -q '^mission_check: GREEN'; then pass "clean checkout: mission_check GREEN"; else
  fail "clean checkout is RED"; printf '%s\n' "$out" | grep -E 'RED|^    ' | head -10
fi

# seal: PROTECTED.toml matches the seal log, and the tag exists
python3 - <<'PY' && pass "PROTECTED.toml seal matches seal_log and its entries" || fail "seal mismatch"
import hashlib, json, re, tomllib, sys
prot = tomllib.load(open("PROTECTED.toml", "rb"))
log = [json.loads(x) for x in open("EVIDENCE/seal_log.jsonl") if x.strip()]
canon = "\n".join(f"{e['path']}  {e['sha256']}" for e in sorted(prot["file"], key=lambda e: e["path"]))
ok = log and prot["seal"] == hashlib.sha256(canon.encode()).hexdigest()[:8] == log[-1]["new_seal"]
ok = ok and hashlib.sha256(open("PROTECTED.toml", "rb").read()).hexdigest() == log[-1]["protected_toml_sha256"]
sys.exit(0 if ok else 1)
PY
git -C "$repo" rev-parse -q --verify "refs/tags/seal/T02a" >/dev/null && pass "tag seal/T02a exists" || fail "tag seal/T02a missing"

# every CORE canary is caught (and the clean copy is GREEN)
canary=$(python3 tests/canary/run_canary.py 2>&1)
printf '%s\n' "$canary" | sed 's/^/  canary: /'
printf '%s\n' "$canary" | grep -q '^canaries: 0 failure(s)$' && [ "$(printf '%s\n' "$canary" | grep -c '^PASS canary')" -eq 8 ] &&
  pass "all 8 CORE canaries caught" || fail "a canary was not caught"
printf '%s\n' "$canary" | grep -q "^PASS canary 'fake approval with a wrong code' → #17 RED" &&
  pass "approval line with a wrong code rejected" || fail "wrong-code approval not rejected"
printf '%s\n' "$canary" | grep -q "^PASS canary 'digit in report_fields.json' → #2 RED" &&
  pass "digit in report_fields.json rejected" || fail "digit in report_fields.json not rejected"

# redaction removes a planted token and keeps a planted sha256 line
tok="ey""J$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"
h=$(printf 'z' | sha256sum | cut -d' ' -f1)
red=$(printf 'Authorization: Bearer %s\nsha256 %s\n' "$tok" "$h" | python3 tools/redact.py)
printf '%s' "$red" | grep -qF "$tok" && fail "planted token survived redaction" || pass "planted token redacted"
printf '%s' "$red" | grep -qxF "sha256 $h" && pass "planted sha256 line kept" || fail "sha256 line damaged"

# the pre-commit hook runs mission_check: a commit with an untagged number is refused (full copy)
head=$(git rev-parse HEAD)
git clone -q --no-hardlinks "$repo" "$cp_dir" >/dev/null 2>&1
(
  cd "$cp_dir" && git checkout -q --detach "$head" 2>/dev/null || exit 1
  git config core.hooksPath .githooks
  printf '\n## D-998 | verify | 2026-11-11\nOLD → NEW: a limit of ₹77 with no tag\n' >>DECISIONS.md
  git add DECISIONS.md
  if git -c user.name=verify -c user.email=verify@local commit -q -m "T02a: verify untagged" >/dev/null 2>&1; then exit 1; fi
  exit 0
) && pass "pre-commit hook refused a commit with an untagged number" || fail "pre-commit hook accepted an untagged number"

# the pre-push hook refuses (no F-REMOTE approval / incident open) and refuses other refs
z=0000000000000000000000000000000000000000
printf 'refs/heads/mission/v11 %s refs/heads/mission/v11 %s\n' "$(git rev-parse HEAD)" "$z" |
  .githooks/pre-push origin x >/dev/null 2>&1 && fail "pre-push allowed a push" || pass "pre-push refused the push"

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T02a verify: $failures failure(s)"
[ "$failures" -eq 0 ]
