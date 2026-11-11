#!/usr/bin/env bash
# tools/verify/T09.sh (MISSION V11 §12, T09 DELIVERY_OPS). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T09).
# Negative controls: `make bundle` must refuse a planted fake token; a tampered data pack must be refused;
# a damaged restored copy must fail backup_verify; `--live` must be refused.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T09"
run_dir="$tmp/mission-v11-bundle-verify-T09"
failures=0
pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; failures=$((failures + 1)); }
cleanup() {
  git -C "$repo" worktree remove --force "$wt" >/dev/null 2>&1
  git -C "$repo" worktree prune >/dev/null 2>&1
  case "$run_dir" in "$tmp"/mission-v11-bundle-verify-T09) rm -rf -- "$run_dir" ;; esac
}
cleanup
git -C "$repo" worktree add --detach "$wt" HEAD >/dev/null 2>&1 || { echo "FAIL cannot create worktree"; exit 1; }
cd "$wt" || exit 1

for f in tools/make_bundle.py tools/pack_data.py tools/backup_verify.py src/bot/recorder/__main__.py \
  src/bot/recorder/notify.py docs/OWNER_START.md docs/RUNBOOK.md tests/test_delivery.py; do
  [ -e "$f" ] || fail "missing $f"
done
[ "$(wc -l <docs/RUNBOOK.md)" -le 120 ] && pass "runbook within two pages" || fail "runbook too long"

# negative control: a planted fake token makes `make bundle` refuse
cp src/bot/recorder/notify.py "$tmp/mission-v11-verify-T09-notify.bak"
printf '\nX = "%s"\n' "ey""J$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)" >>src/bot/recorder/notify.py
if make -s bundle >/dev/null 2>&1; then fail "make bundle accepted a planted token"; else pass "make bundle refused a planted token"; fi
mv "$tmp/mission-v11-verify-T09-notify.bak" src/bot/recorder/notify.py
ls dist/*.zip >/dev/null 2>&1 && fail "a bundle was written despite the refusal" || pass "no bundle written on refusal"

# clean: make bundle passes, the unzipped bundle runs --dry-run offline on the synthetic feed
make -s bundle >/dev/null 2>&1 && pass "make bundle passes on the clean tree" || fail "make bundle failed on the clean tree"
mkdir -p "$run_dir"
python3 -c "import sys,zipfile,glob;zipfile.ZipFile(sorted(glob.glob('dist/*.zip'))[-1]).extractall(sys.argv[1])" "$run_dir"
b=$(find "$run_dir" -maxdepth 1 -type d -name 'recorder_bundle_*' | head -1)
(cd "$b" && sha256sum -c --quiet SHA256SUMS) && pass "bundle SHA256SUMS match" || fail "bundle checksums"
out=$(cd "$b" && python3 -m bot.recorder --dry-run 2>&1)
printf '%s\n' "$out" | grep -q '^DRY-RUN OK: 72 instruments' && pass "unzipped bundle runs --dry-run offline" ||
  fail "bundle dry-run: $out"
(cd "$b" && python3 -m bot.recorder --live >/dev/null 2>&1); [ $? -eq 2 ] && pass "--live refused" || fail "--live not refused"
grep -rqlE 'bot\.(strategy|haath|dimaag)' "$b" && fail "bundle contains strategy or order code" || pass "bundle has no strategy / order code"
# alert dry-run writes message files and sends nothing
(cd "$b" && python3 -m bot.recorder --alert-dry-run "$run_dir/outbox" >/dev/null) &&
  [ "$(ls "$run_dir/outbox" | wc -l)" -eq 2 ] && grep -q 'DRY-RUN, not sent' "$run_dir"/outbox/* &&
  pass "alert dry-run wrote message files" || fail "alert dry-run"

# pack_data round trip, tamper refusal and the restore drill (tests/test_delivery.py)
t=$(python3 -m pytest -o addopts= -v -p no:cacheprovider tests/test_delivery.py 2>&1)
for n in test_data_pack_round_trip_checksums_match test_a_tampered_or_padded_pack_is_refused \
  test_restore_drill_passes_and_a_damaged_copy_fails test_alert_dry_run_writes_a_message_file_and_sends_nothing; do
  printf '%s\n' "$t" | grep -q "::$n PASSED" && pass "$n" || fail "$n"
done

# the Recorder card: three lines, also in OWNER_TODO item 1 and in REPORT
card=$(python3 tools/make_report.py --recorder-card)
[ "$(printf '%s\n' "$card" | wc -l)" -eq 3 ] && pass "Recorder card has three lines" || fail "Recorder card"
grep -q '^1\. \*\*Recorder card' OWNER_TODO.md && grep -q '^RECORDER CARD:' REPORT.md && pass "card in OWNER_TODO #1 and REPORT" ||
  fail "card missing from OWNER_TODO #1 or REPORT"

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T09 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
