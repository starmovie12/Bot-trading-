#!/usr/bin/env bash
# tools/verify/T08.sh (MISSION V11 §12, T08 ARITH_WAR_ROOM). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T08).
# Negative controls: a family list with only two unconventional families, a kill resting on SIM, a kill resting
# on a HISTORY fact, and a family without a tagged number must each be rejected by the checker.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T08"
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

python3 tools/war_room.py --check EVIDENCE/T08/families.json >/dev/null && pass "families: >= 8, >= 3 unconventional, tagged numbers" ||
  fail "families check"
python3 tools/war_room.py >/dev/null && git diff --quiet -- docs/WAR_ROOM.md EVIDENCE/T08/families.json &&
  pass "WAR_ROOM.md and families.json reproduce byte for byte" || fail "war room output is stale"
python3 - <<'PY' && pass "every NEGATIVE.md data row carries a number and a tag" || fail "NEGATIVE.md row without a tag"
import re, sys
rows = [l for l in open("NEGATIVE.md") if l.startswith("|") and not l.startswith(("| family", "|---"))]
sys.exit(0 if all(re.search(r"\d.*\[[A-Z(·)]+\]", r) for r in rows) else 1)
PY
for control in two_unconventional sim_kill history_kill untagged; do
  python3 - "$control" "$tmp/mission-v11-verify-T08-$control.json" <<'PY'
import json, sys
kind, out = sys.argv[1], sys.argv[2]
fams = json.load(open("EVIDENCE/T08/families.json"))
if kind == "two_unconventional":
    for f in fams:
        if f["kind"] == "unconventional" and sum(1 for g in fams if g["kind"] == "unconventional") > 2:
            f["kind"] = "conventional"
if kind == "sim_kill":
    fams[0]["killed"] = True; fams[0]["numbers"] = [["x", {"value": "1", "tag": "SIM"}]]
if kind == "history_kill":
    fams[0]["killed"] = True
if kind == "untagged":
    fams[0]["numbers"] = [["x", {"value": "1", "tag": ""}]]
json.dump(fams, open(out, "w"))
PY
  if python3 tools/war_room.py --check "$tmp/mission-v11-verify-T08-$control.json" >/dev/null; then
    fail "checker accepted $control"
  else pass "checker rejected $control"; fi
  rm -f "$tmp/mission-v11-verify-T08-$control.json"
done

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T08 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
