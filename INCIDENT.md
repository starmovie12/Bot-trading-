# INCIDENT log (MISSION V11 §1 item 8, §14)

Values of secrets or environment variables are never read, printed or written here: names and paths only.

## #1 · sandbox_breach (STOP-THE-LINE) · OPEN
WHAT HAPPENED: `tools/preflight.sh` found an environment-variable NAME that contains `ACCESS_TOKEN`: `CLOUDSDK_AUTH_ACCESS_TOKEN`. MISSION §1 item 9 says such a name can never be allowlisted, so it is a sandbox_breach. Its value was never read.
WHERE: the process environment of this cloud session · evidence `EVIDENCE/T01/preflight.txt`
WHEN: 2026-11-11 13:48 IST · session 1 · T01 step (0a)
WHAT I DID: push and web fetch are OFF for the rest of this session (the pre-push hook refuses every push); T03 and T04 run offline, so facts stay UNVERIFIED / HISTORY and G0 cannot become FEASIBLE this session; the live flag stays OFF in code (`src/bot/__main__.py:18` refuses every mode except paper; the order manager is PAPER-only; no bot process runs: `EVIDENCE/T01/live_process_check.txt`). Offline work continues.
CONTEXT (evidence, not an excuse): this name is not one of the 8 variables in the owner's environment settings ("trading-bot-phase1": BASH_DEFAULT_TIMEOUT_MS, BASH_MAX_TIMEOUT_MS, LANG, LIVE_TRADING_ENABLED, PROJECT_PHASE, PYTHONDONTWRITEBYTECODE, PYTHONUNBUFFERED, TZ), and that environment has no saved network secrets. The `CLOUDSDK_` prefix belongs to the Google Cloud command-line tool, which the cloud platform pre-configures. So it is most likely the platform's own variable and not a broker token. This is not verified, because the value may not be read.
MALIK KO KYA KARNA HAI (ek raasta chuno):
  (a) Agar cloud environment ki settings se ye variable hat sakta hai, hata do.
  (b) Agar ye platform ka apna hai aur hat nahi sakta: MISSION.md §1 item 9 mein khud ek line jodo ki sirf ye exact naam `CLOUDSDK_AUTH_ACCESS_TOKEN` (Google Cloud tool ka) allowlist ho sakta hai, phir chat mein `mission badla` likho.
  (c) Ya agent ko aisi jagah chalao jahan ye variable na ho.
  Uske baad: `haan F-INC-1 be92`.
CLOSES WITH: `haan F-INC-1 be92`

## #2 · env_warn · OPEN
WHAT HAPPENED: secret-looking environment-variable NAMES that are not on the allowlist: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`. Values never read.
WHERE: the process environment of this cloud session · evidence `EVIDENCE/T01/preflight.txt`
WHEN: 2026-11-11 13:48 IST · session 1 · T01 step (0a)
WHAT I DID: nothing uses them; the agent never spends money and never calls a cloud API. They are not in the owner's environment settings, so the platform most likely sets them. Push and web fetch are not blocked by this incident.
MALIK KO KYA KARNA HAI: agar tumne kahin apni Amazon (AWS) key daali ho to use hatao aur Amazon par nayi key banao (purani band karo). Warna kuch nahi. Phir `haan F-INC-2 fc8c`.
CLOSES WITH: `haan F-INC-2 fc8c`

## #3 · env_warn · OPEN
WHAT HAPPENED: an environment-variable NAME that looks like a live-trading switch: `LIVE_TRADING_ENABLED` (it is in the owner's own environment settings). Value never read.
WHERE: the owner's environment settings ("trading-bot-phase1") · evidence `EVIDENCE/T01/preflight.txt`
WHEN: 2026-11-11 13:48 IST · session 1 · T01 step (0a)
WHAT I DID: checked that no code in the repo reads this name (`EVIDENCE/T01/live_flag_code_refs.txt`) and that no bot, recorder or watchdog process runs here (`EVIDENCE/T01/live_process_check.txt`). The live path stays OFF in code. Not STOP-THE-LINE: nothing on this machine can act on this variable. The future live lock (I8, FULL-B only) will use a different name and a test that this variable has no effect (DECISIONS D-006).
MALIK KO KYA KARNA HAI: kuch zaroori nahi. Chaaho to environment settings se ye variable hata do. Phir `haan F-INC-3 d9e1`.
CLOSES WITH: `haan F-INC-3 d9e1`
