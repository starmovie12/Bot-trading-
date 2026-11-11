#!/usr/bin/env bash
# tools/preflight.sh (MISSION V11 §1 item 9). Run at every session start.
# Looks at environment-variable NAMES and at path EXISTENCE only: it never reads or prints
# a value and never opens a file (test -e and find -maxdepth 2 -iname only).
# Exit: 0 clean · 10 env_warn only · 20 sandbox_breach (STOP-THE-LINE) · 30 bad allowlist.
set -u
root=$(cd "$(dirname "$0")/.." && pwd)
home=${HOME:-/root}

env_result=$(python3 - "$root/tools/env_allowlist.txt" <<'PY'
import fnmatch, os, re, sys
BANNED = ("UPSTOX", "BROKER", "ACCESS_TOKEN", "API_SECRET", "CLIENT_ID")
BREACH = ("UPSTOX", "BROKER", "ACCESS_TOKEN", "API_SECRET")
SECRETISH = re.compile(r"TOKEN|SECRET|PASSW|ASKPASS|KEY|CREDENTIAL|COOKIE|PRIVATE|CLIENT_ID|AUTH", re.I)
LIVEISH = re.compile(r"LIVE.*(TRAD|ORDER)|(TRAD|ORDER).*LIVE", re.I)
allow = []
for line in open(sys.argv[1], encoding="utf-8"):
    entry = line.split("#", 1)[0].strip()
    if not entry:
        continue
    if "#" not in line or not line.split("#", 1)[1].strip():
        print(f"BAD_ALLOWLIST entry without a reason: {entry}"); sys.exit(30)
    if any(b in entry.upper() for b in BANNED):
        print(f"BAD_ALLOWLIST banned name: {entry}"); sys.exit(30)
    allow.append(entry)
names = sorted(os.environ)  # names only; values are never touched
code, ok, other = 0, [], []
for n in names:
    up = n.upper()
    hit = next((b for b in BREACH if b in up), None)
    if hit:
        print(f"SANDBOX_BREACH env name: {n} (contains {hit}; never allowlistable)"); code = 20; continue
    if LIVEISH.search(n):
        print(f"ENV_WARN env name: {n} (live-trading-flag-like name; value not read)"); code = max(code, 10); continue
    if any(fnmatch.fnmatchcase(n, a) for a in allow):
        ok.append(n); continue
    if SECRETISH.search(n):
        print(f"ENV_WARN env name: {n} (secret-looking name, not allowlisted; value not read)"); code = max(code, 10); continue
    other.append(n)
print(f"ALLOWLISTED env names ({len(ok)}): " + " ".join(ok))
print(f"OTHER env names, not secret-looking ({len(other)}): " + " ".join(other))
print(f"ENV_CODE {code}")
PY
)
rc=$?
printf '%s\n' "$env_result" | grep -v '^ENV_CODE '
[ "$rc" -eq 30 ] && { echo "RESULT bad_allowlist"; exit 30; }
code=$(printf '%s\n' "$env_result" | sed -n 's/^ENV_CODE //p')
code=${code:-0}

# Paths: existence only.
keys=$(find "$home/.ssh" -maxdepth 1 -name 'id_*' ! -name '*.pub' 2>/dev/null)
if [ -n "$keys" ]; then
  printf '%s\n' "$keys" | sed 's/^/ENV_WARN private-key file present (not opened): /'
  [ "$code" -lt 10 ] && code=10
else
  echo "ok: no ~/.ssh/id_* private-key file"
fi
if test -e "$home/.aws/credentials"; then
  echo "SANDBOX_BREACH path present (not opened): ~/.aws/credentials"; code=20
else
  echo "ok: ~/.aws/credentials absent"
fi
for d in .mozilla .config/google-chrome .config/chromium .config/BraveSoftware .config/microsoft-edge \
         snap/chromium snap/firefox "Library/Application Support/Google/Chrome" "Library/Application Support/Firefox"; do
  if test -e "$home/$d"; then echo "SANDBOX_BREACH browser profile directory present (not opened): ~/$d"; code=20; fi
done
tok=$(find "$home" -maxdepth 2 \( -iname '*upstox*' -o -iname '*access_token*' \) 2>/dev/null)
if [ -n "$tok" ]; then
  printf '%s\n' "$tok" | sed "s|^$home|~|; s/^/SANDBOX_BREACH token-like file name in home (not opened): /"
  code=20
else
  echo "ok: no broker-token-like file name in ~ (maxdepth 2)"
fi
case $code in
  0) echo "RESULT clean" ;;
  10) echo "RESULT env_warn" ;;
  *) echo "RESULT sandbox_breach (STOP-THE-LINE: no push, no web fetch this session)" ;;
esac
exit "$code"
