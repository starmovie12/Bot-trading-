#!/usr/bin/env bash
# tools/safe_add.sh <explicit file paths>: the ONLY way to stage files (MISSION V11 T01 0e).
# Never use `git add -A`, `git add .` or `git commit -a`.
# Allowed: extensions .py .go .toml .md .json .jsonl .sh .yml .yaml .txt .cfg .ini .lock .sha256
#          .service .timer; named files .gitignore .gitattributes SHA256SUMS Makefile go.mod go.sum
#          LICENSE; everything under .githooks/ and .github/workflows/; *.csv only under tests/fixtures/.
# Refused: directories, globs, secret-named files, gitignored files, archives, files > 1 MB,
#          inputs (docs/00_input/, legacy/) not recorded in SHA256SUMS, and files whose content
#          matches tools/secret_patterns.txt (locations printed, values never).
# All-or-nothing: if any path is refused, nothing is staged.
set -u
root=$(git rev-parse --show-toplevel) || exit 2
cd "$root" || exit 2
[ $# -ge 1 ] || { echo "usage: tools/safe_add.sh <explicit file paths>" >&2; exit 64; }
max_bytes=1048576
refused=0
ok=()
for arg in "$@"; do
  p=${arg#"$root"/}
  p=${p#./}
  base=${p##*/}
  reason=""
  case "$p" in
    "" | /* | .. | ../* | */../* | */..) reason="not a path inside the repo" ;;
    -*) reason="looks like an option" ;;
    *'*'* | *'?'* | *'['*) reason="glob characters: explicit paths only" ;;
  esac
  if [ -z "$reason" ] && [ -d "$p" ]; then reason="directory: explicit files only"; fi
  deletion=0
  if [ -z "$reason" ] && [ ! -e "$p" ]; then
    if git ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then deletion=1; else reason="does not exist"; fi
  fi
  if [ -z "$reason" ] && [ "$deletion" -eq 0 ]; then
    allowed=0
    case "$p" in .githooks/* | .github/workflows/*) allowed=1 ;; esac
    case "$base" in .gitignore | .gitattributes | SHA256SUMS | Makefile | go.mod | go.sum | LICENSE) allowed=1 ;; esac
    case "$base" in
      *.py | *.go | *.toml | *.md | *.json | *.jsonl | *.sh | *.yml | *.yaml | *.txt | *.cfg | *.ini | *.lock | *.sha256 | *.service | *.timer) allowed=1 ;;
      *.csv) case "$p" in tests/fixtures/*) allowed=1 ;; esac ;;
    esac
    case "$base" in
      *.zip | *.tar | *.tar.* | *.tgz | *.gz | *.bz2 | *.xz | *.7z | *.rar) reason="archive" ;;
    esac
    if [ -z "$reason" ] && [ "$allowed" -eq 0 ]; then reason="file type not on the allowed list"; fi
    if [ -z "$reason" ] && [ "$(stat -c %s -- "$p")" -gt "$max_bytes" ]; then reason="larger than 1 MB"; fi
    if [ -z "$reason" ] && git check-ignore -q -- "$p"; then reason="gitignored"; fi
    if [ -z "$reason" ]; then
      case "$p" in
        docs/00_input/* | legacy/*)
          sum=$(sha256sum -- "$p" | cut -d' ' -f1)
          grep -qxF "$sum  $p" SHA256SUMS 2>/dev/null || reason="input not recorded in SHA256SUMS (unscanned)" ;;
      esac
    fi
    if [ -z "$reason" ]; then
      if ! hits=$(python3 tools/redact.py --guard "$p"); then reason="secret-like name or content: $hits"; fi
    fi
  fi
  if [ -n "$reason" ]; then
    echo "REFUSED $p: $reason" >&2
    refused=$((refused + 1))
  else
    ok+=("$p")
  fi
done
if [ "$refused" -gt 0 ]; then
  echo "safe_add: $refused path(s) refused; nothing staged." >&2
  exit 1
fi
git add -- "${ok[@]}" || exit 1
printf 'staged %s\n' "${ok[@]}"
