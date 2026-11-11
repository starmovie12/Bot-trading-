#!/usr/bin/env bash
# tools/ev.sh <task> <name> -- <cmd...>   (MISSION V11 §5.3)
# Runs <cmd>, pipes stdout+stderr through tools/redact.py BEFORE anything is written
# (raw output is never stored), writes EVIDENCE/<task>/<name>.txt (EVIDENCE/cycle<N>/<task>/ when
# CYCLE_N > 1) and appends {path, sha256, cmd, time, exit} to EVIDENCE/INDEX.jsonl.
# Exits with the command's exit code.
set -u
if [ $# -lt 4 ] || [ "$3" != "--" ]; then
  echo "usage: tools/ev.sh <task> <name> -- <cmd...>" >&2
  exit 64
fi
task=$1
name=$2
shift 3
case "$task$name" in
  *[!A-Za-z0-9_.-]* | *..*) echo "ev.sh: task/name may use only A-Z a-z 0-9 _ . -" >&2; exit 64 ;;
esac
root=$(cd "$(dirname "$0")/.." && pwd)
cycle=$(sed -n 's/^CYCLE_N: *\([0-9][0-9]*\).*/\1/p' "$root/STATE.md" 2>/dev/null | head -1)
cycle=${cycle:-1}
if [ "$cycle" -gt 1 ]; then rel="EVIDENCE/cycle$cycle/$task"; else rel="EVIDENCE/$task"; fi
mkdir -p "$root/$rel"
out="$rel/$name.txt"
when=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cmdline=$(printf '%q ' "$@" | python3 "$root/tools/redact.py")
{
  printf '$ %s\n' "$cmdline"
  "$@" 2>&1
  rc=$?
  printf '[exit %d]\n' "$rc"
  exit "$rc"
} | python3 "$root/tools/redact.py" >"$root/$out.part"
statuses=("${PIPESTATUS[@]}")
rc=${statuses[0]}
if [ "${statuses[1]}" -ne 0 ]; then
  rm -f "$root/$out.part"
  echo "ev.sh: redactor failed; nothing written" >&2
  exit 70
fi
mv "$root/$out.part" "$root/$out"
sum=$(sha256sum "$root/$out" | cut -d' ' -f1)
python3 - "$out" "$sum" "$cmdline" "$when" "$rc" >>"$root/EVIDENCE/INDEX.jsonl" <<'PY'
import json, sys
path, sha, cmd, when, rc = sys.argv[1:6]
print(json.dumps({"path": path, "sha256": sha, "cmd": cmd.strip(), "time": when, "exit": int(rc)}, ensure_ascii=False))
PY
echo "evidence: $out (exit $rc)" >&2
exit "$rc"
