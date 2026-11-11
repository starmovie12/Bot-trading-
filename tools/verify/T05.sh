#!/usr/bin/env bash
# tools/verify/T05.sh (MISSION V11 §12, T05 RECORDER_MVP). Exits non-zero on any failure.
# Runs on a clean checkout of HEAD (git worktree in ${TMPDIR:-/tmp}/mission-v11-verify-T05).
# Negative controls: the size-cap alert must fire; a corrupted day file must be detected; a message with
# an unknown enum must be refused; a stale feed must block entries.
set -u
repo=$(git rev-parse --show-toplevel) || exit 2
tmp=${TMPDIR:-/tmp}
wt="$tmp/mission-v11-verify-T05"
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

for f in docs/RECORDER_SPEC.md recorder.toml src/bot/recorder/snapshot.py src/bot/recorder/synthetic_feed.py \
  tests/test_recorder_mvp.py tests/invariants/test_i04_feed_stale_gap.py tests/invariants/test_i11_time.py \
  tests/invariants/test_i13_feed_schema.py tests/invariants/COVERAGE.md; do
  [ -e "$f" ] || fail "missing $f"
done
git check-ignore -q data/recorder/2026-11-12.jsonl && pass "recorded data is gitignored" || fail "recorder data not ignored"
grep -q '^scope = "LIGHT"' recorder.toml && pass "LIGHT scope by default" || fail "scope is not LIGHT"

out=$(python3 -m pytest -o addopts= -v -p no:cacheprovider tests/test_recorder_mvp.py tests/invariants/test_i04_feed_stale_gap.py \
  tests/invariants/test_i11_time.py tests/invariants/test_i13_feed_schema.py 2>&1)
for t in test_one_synthetic_day_journals_and_replays_identically test_five_simulated_days_soak_without_gaps \
  test_kill_9_mid_write_leaves_a_recoverable_journal test_full_disk_stops_cleanly_and_the_journal_stays_readable \
  test_size_cap_alert_fires_then_recording_stops_without_deleting test_a_corrupted_day_file_is_detected \
  test_a_stale_feed_blocks_entries_and_fresh_data_reopens test_unknown_enum_blocks_entries_and_is_not_recorded \
  test_clock_drift_raises_an_alert_and_blocks_entries; do
  printf '%s\n' "$out" | grep -q "::$t PASSED" && pass "$t" || fail "$t"
done
printf '%s\n' "$out" | grep -qE '[0-9]+ (failed|errors?)\b' && fail "a recorder test failed" || pass "no recorder test failed"

# direct negative controls, outside pytest
PYTHONPATH=src python3 - <<'PY' && pass "direct controls: cap alert fires, corruption detected" || fail "direct controls"
import datetime as dt, sys, tempfile
from pathlib import Path
from bot.recorder.snapshot import RecorderConfig, SnapshotRecorder, verify_day
from bot.recorder.synthetic_feed import light_keys, synthetic_day
with tempfile.TemporaryDirectory(prefix="mission-v11-verify-T05-") as d:
    rec = SnapshotRecorder(RecorderConfig(data_dir=Path(d) / "a", size_cap_bytes=300_000))
    for local, msg in synthetic_day(dt.date(2026, 11, 12), 9, light_keys()):
        rec.on_message(msg, local)
    kinds = [a.kind for a in rec.alerts]
    ok = "size_cap_80" in kinds and rec.stopped == "size_cap"
    rec2 = SnapshotRecorder(RecorderConfig(data_dir=Path(d) / "b", size_cap_bytes=10**9))
    for local, msg in synthetic_day(dt.date(2026, 11, 12), 9, light_keys()[:3]):
        rec2.on_message(msg, local)
    gz = rec2.end_day()
    raw = bytearray(gz.read_bytes()); raw[100] ^= 0x01; gz.write_bytes(bytes(raw))
    ok = ok and not verify_day(gz)
sys.exit(0 if ok else 1)
PY

cd "$repo" || exit 1
cleanup
left=$(find "$tmp" -maxdepth 1 -name 'mission-v11-*' 2>/dev/null)
[ -z "$left" ] && pass "no mission-v11 temp dir left" || fail "temp dir(s) left: $left"
echo "T05 verify: $failures failure(s)"
[ "$failures" -eq 0 ]
