#!/usr/bin/env bash
# tools/verify/T03.sh (MISSION V11 §12, T03 REGULATORY_DATA_RIGHTS). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T03).
# Negative controls: a stale row must turn `mission_check --final` RED (TTL lint); a SOURCE row whose
# value is missing from its extract must turn mission_check #18 RED; the row checker below must
# reject a row whose value is not in its extract.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T03"
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

check_rows() { # $1 = constants file; prints problems; exit 1 on any
  python3 - "$1" <<'PY'
import re, sys, tomllib
from pathlib import Path
rows = tomllib.load(open(sys.argv[1], "rb"))
bad = 0
for name, r in rows.items():
    miss = [k for k in ("value", "unit", "tag", "source_url", "fetched", "ttl_days", "status", "extract") if k not in r]
    if miss:
        print(f"{name}: missing {miss}"); bad += 1; continue
    if not str(r["source_url"]).startswith("https://"):
        print(f"{name}: source_url is not an https URL"); bad += 1
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r["fetched"])):
        print(f"{name}: fetched is not a date"); bad += 1
    if r["status"] not in ("VERIFIED", "UNVERIFIED", "NA"):
        print(f"{name}: bad status"); bad += 1
    if r["status"] == "VERIFIED" and r["tag"] != "SOURCE":
        print(f"{name}: VERIFIED without the SOURCE tag"); bad += 1
    ext = Path(str(r["extract"]))
    if not ext.is_file():
        print(f"{name}: extract file missing"); bad += 1; continue
    if r["value"] == "unknown":
        if r["status"] != "UNVERIFIED":
            print(f"{name}: unknown value must be UNVERIFIED"); bad += 1
        continue
    forms = [str(r["value"]), *[str(x) for x in r.get("value_forms", [])]]
    if not any(f in ext.read_text() for f in forms):
        print(f"{name}: value not found in its extract"); bad += 1
print(f"{len(rows)} rows, {bad} problem(s)")
sys.exit(1 if bad else 0)
PY
}

# 1. every row has URL + date + status + extract, and its value appears in its extract
check_rows constants.toml && pass "every constants row: URL, date, status, extract, value in extract" ||
  fail "constants rows incomplete"
# 2. DATA_RIGHTS verdict present
grep -q '^\[data_rights\]' constants.toml && grep -q 'DATA_RIGHTS = UNVERIFIED\|DATA_RIGHTS = OK\|DATA_RIGHTS = MINIMAL\|DATA_RIGHTS = NOT_ALLOWED' docs/REGULATORY.md &&
  pass "DATA_RIGHTS verdict present" || fail "DATA_RIGHTS verdict missing"
# 3. coverage keywords of the §6 / §10 / T03 lists
for k in "SEBI fee" "stamp" "GST" "contract size" "upfront premium" "position limits" "physical settlement" \
  "MPP" "sandbox" "rate limits" "historical-data" "data-storage" "read-only" "feed schema" "static-IP route" \
  "FD / liquid-fund" "USD/INR" "total-return" "top-percentile" "holiday calendar" "re-registration" "regime change" \
  "IPFT separate"; do
  grep -qF "$k" docs/REGULATORY.md || { fail "REGULATORY.md does not cover: $k"; missing_kw=1; }
done
[ "${missing_kw:-0}" -eq 0 ] && pass "REGULATORY.md covers every listed item"
# 4. mission_check is GREEN on the clean tree (#18 included)
python3 tools/mission_check.py | grep -q '^mission_check: GREEN' && pass "mission_check GREEN" || fail "mission_check RED"

# negative control A: the row checker rejects a value missing from its extract
cp constants.toml "$tmp/mission-v11-verify-T03-c.toml"
sed -i '0,/^value = 18$/s//value = 19/' "$tmp/mission-v11-verify-T03-c.toml"
if check_rows "$tmp/mission-v11-verify-T03-c.toml" >/dev/null; then fail "row checker accepted a wrong value"; else
  pass "row checker rejected a value missing from its extract"; fi
rm -f "$tmp/mission-v11-verify-T03-c.toml"
# negative control B: a SOURCE row whose value is not in its extract → mission_check #18 RED
cp constants.toml constants.toml.orig
python3 - <<'PY'
from pathlib import Path
p = Path("constants.toml"); s = p.read_text()
s = s.replace('[gst]\nvalue = 18\n', '[gst]\nvalue = 19\n', 1).replace('tag = "HISTORY"', 'tag = "SOURCE"')
p.write_text(s)
PY
python3 tools/mission_check.py | grep -q '^#18 .*RED' && pass "#18 RED for a SOURCE value missing from its extract" ||
  fail "#18 did not catch a SOURCE value missing from its extract"
mv constants.toml.orig constants.toml
# negative control C: stale-TTL lint (a row fetched long ago) → mission_check --final RED with "stale"
cp constants.toml constants.toml.orig
sed -i '0,/^fetched = "2026-11-11"$/s//fetched = "2020-01-01"/' constants.toml
out=$(python3 tools/mission_check.py --final)
printf '%s\n' "$out" | grep -q 'stale' && printf '%s\n' "$out" | grep -q '^#T2 .*RED' &&
  pass "stale-TTL lint RED in --final" || fail "stale-TTL lint did not fire"
python3 tools/mission_check.py | grep -q 'warning: .*stale' && pass "stale row is a warning in Tier 1" ||
  fail "no Tier 1 stale warning"
mv constants.toml.orig constants.toml

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T03 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
