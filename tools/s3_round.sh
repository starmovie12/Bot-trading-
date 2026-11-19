#!/usr/bin/env bash
# S3 round driver (owner order 6): append the round grid to PLAN.md, commit it, preflight + run the nested round,
# then commit the round's files and push. Usage: tools/s3_round.sh R2 "<one-line description>" <trial cap>
set -euo pipefail
cd "$(dirname "$0")/.."
R="$1"; DESC="$2"; CAP="$3"
TRAILER=$'\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01LRxckDYW2poWT87Myqm9w1'
if ! grep -q "<!-- S3-GRID $R -->" PLAN.md; then
  {
    printf '\n## S3 · %s (owner order 6; §13.3; committed before any %s number)\n' "$R" "$R"
    printf 'Nested as S3 R1 (per-window base = the previous round'"'"'s training choice; best training net_base wins, base wins ties).\n'
    printf '%s\nTrial cap added: %s\n' "$DESC" "$CAP"
    PYTHONPATH=. python -m lab.s3.round_main plan "$R"
  } >> PLAN.md
  bash tools/safe_add.sh PLAN.md > /dev/null
  git commit -q -m "P3: S3 $R grid committed in PLAN.md (before any $R number)$TRAILER"
fi
PYTHONPATH=. python -m lab.s3.round_main run "$R" > "wip/rounds_${R}_stdout.log" 2>&1
lower=$(echo "$R" | tr '[:upper:]' '[:lower:]')
python - "$R" <<'PY'
import re, sys, json
r = sys.argv[1]
s = json.load(open(f"results/s3_{r.lower()}_summary.json"))
p = "STATE.md"; t = open(p).read()
t = re.sub(r"^NEXT=.*$", f"NEXT=S3 next round after {r} ({'PASS' if s['gates']['all_pass'] else 'FAIL'}; card in results/s3_rounds.md)", t, flags=re.M)
open(p, "w").write(t)
PY
new_runs=$(git ls-files --others --exclude-standard wip/s3_runs)
# shellcheck disable=SC2086
bash tools/safe_add.sh results/s3_rounds.md "results/s3_${lower}_summary.json" "results/s3_${lower}_trades.csv" \
  wip/s3_chain.json STATE.md trials.jsonl wip/s3_runner_calls.json $new_runs > /dev/null
git commit -q -m "P3: S3 $R done (card in results/s3_rounds.md)$TRAILER"
for i in 1 2 3 4; do
  if git push -q origin bot/banknifty-v1:bot-banknifty-v1; then break; fi
  sleep $((2 ** i))
done
tail -12 "wip/rounds_${R}_stdout.log"
