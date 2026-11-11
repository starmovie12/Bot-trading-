#!/usr/bin/env bash
# tools/clock.sh (MISSION V11 §1 item 5): elapsed and remaining minutes of this session,
# from SESSION_START and BUDGET_MIN in STATE.md. Run at every task / sub-step boundary.
set -u
root=$(cd "$(dirname "$0")/.." && pwd)
start=$(sed -n 's/^SESSION_START: *\([0-9][0-9]*\).*/\1/p' "$root/STATE.md" | head -1)
budget=$(sed -n 's/^BUDGET_MIN: *\([0-9][0-9]*\).*/\1/p' "$root/STATE.md" | head -1)
if [ -z "$start" ] || [ -z "$budget" ]; then
  echo "clock: SESSION_START or BUDGET_MIN missing in STATE.md" >&2
  exit 2
fi
now=$(date +%s)
elapsed=$(((now - start) / 60))
remaining=$((budget - elapsed))
echo "elapsed ${elapsed} min | remaining ${remaining} min of ${budget} | W1: start a chunk only if elapsed + chunk <= $((budget - 15))"
