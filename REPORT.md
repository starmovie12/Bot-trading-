DHYAN: INCIDENT #1 khula hai (kul 3 khule) · FAISLA: ABHI NAHI (data kam; tumhari file ya jawab chahiye) · INTERIM
SEEDHI BAAT: abhi sirf suraksha ka dhaancha bana hai; ₹ ka hisaab (G0) T04 mein hoga. Ek trade ka max nuksaan abhi ₹1,125 [ginti (maanyata par)].
KYA BAN GAYA: T01 aur T02a: secret guard, mission_check, REPORT banane wala tool, mohar (SEAL) · purane docs hash ke saath
KAAM 1: INCIDENT #1: environment mein ACCESS_TOKEN wala naam mila; INCIDENT.md #1 ka ek raasta chuno, phir haan F-INC-1 be92
KAAM 2: F-REMOTE: ye container mit sakta hai; repo Private ho to haan F-REMOTE 2350
KAAM 3: INCIDENT #3 aur #2 padho (sirf jaankari): haan F-INC-3 d9e1 · haan F-INC-2 fc8c
SAWAL F-INC-1 (code be92): default khula (web + push band) | ₹ asar seedha nahi; par G0 adhoora rahega | jawab: haan / na F-INC-1 be92
SAWAL F-REMOTE (code 2350): default na (sirf local commit) | ₹ asar seedha nahi; par kaam kho sakta hai | jawab: haan / na F-REMOTE 2350
SAWAL F-MAXLOSS (code bca1): default ₹4,500 [maanyata] | ₹ asar ek trade ka max nuksaan ₹1,125 [ginti (maanyata par)] | jawab: haan / na / set F-MAXLOSS <value> bca1
SAWAL F-INC-3 (code d9e1): default khula (kuch nahi rukta) | ₹ asar koi nahi | jawab: haan / na F-INC-3 d9e1
SAWAL F-INC-2 (code fc8c): default khula (kuch nahi rukta) | ₹ asar koi nahi | jawab: haan / na F-INC-2 fc8c
PAISA KAMANE KA RAASTA: abhi nahi pata: pehle G0 (T04) ka hisaab; web band hai, isliye tathya pakke nahi
MANZOORI (is session): koi nahi
BHAROSA: alag jaanch: nahi hui | khuli badi galtiyan: koi nahi (alag jaanch abhi nahi hui) | kya verify NAHI hua: koi bhi bahari tathya (web band: INCIDENT #1) | final check laal: final check abhi nahi chala (T18 mein)
SAMAY: session 1 · 37 min chala · baad mein: T03 (offline), T04 G0, phir CP1 par rukna · SEAL: bc4d856a · TRIALS: khaali · push: local only (F-REMOTE ki manzoori nahi; INCIDENT #1 khula) · baaki: 23 kaam, 10 sawal (OWNER_TODO.md)

---
Technical sections below are in English (MISSION V11 §14). Numbers carry English tags and evidence paths.

## Verdict
NOT_YET(NO_DATA, MISSING_INPUT) · report INTERIM · push: local only (F-REMOTE ki manzoori nahi; INCIDENT #1 khula)

## Tasks
| id | track | status | minutes_used / timebox | evidence files |
|---|---|---|---|---|
| T01 | LITE | PASS | 20 / 40 | 6 |
| T02a | LITE | IN_PROGRESS | 15 / 45 | 0 |
| T03 | LITE | TODO | 0 / 45 | 0 |
| T04 | LITE | TODO | 0 / 45 | 0 |
| T02b | FULL | TODO | 0 / 90 | 0 |
| T05 | FULL | TODO | 0 / 60 | 0 |
| T09 | FULL | TODO | 0 / 45 | 0 |
| T06 | BOTH | TODO | 0 / 30 | 0 |
| T07 | BOTH | TODO | 0 / 45 | 0 |
| T08 | BOTH | TODO | 0 / 20 | 0 |
| T10 | BOTH | TODO | 0 / 60 | 0 |
| T11 | FULL-A | TODO | 0 / 45 | 0 |
| T12 | FULL-A | TODO | 0 / 30 | 0 |
| T13a | FULL-B | TODO | 0 / 60 | 0 |
| T13b | FULL-B | TODO | 0 / 75 | 0 |
| T14 | FULL-B | TODO | 0 / 45 | 0 |
| T15 | FULL-B | TODO | 0 / 60 | 0 |
| T16 | FULL-B | TODO | 0 / 30 | 0 |
| T17-R1 | END | TODO | 0 / 45 | 0 |
| T17-F1 | END | TODO | 0 / 60 | 0 |
| T17-R2 | END | TODO | 0 / 45 | 0 |
| T17-F2 | END | TODO | 0 / 60 | 0 |
| T17-R3 | END | TODO | 0 / 45 | 0 |
| T18 | END | TODO | 0 / 20 | 0 |

## Open incidents
- #1 · sandbox_breach · OPEN · closes with `haan F-INC-1 be92` (INCIDENT.md)
- #2 · env_warn · OPEN · closes with `haan F-INC-2 fc8c` (INCIDENT.md)
- #3 · env_warn · OPEN · closes with `haan F-INC-3 d9e1` (INCIDENT.md)

## G0 (T04)
(not computed yet)

## Numbers (EVIDENCE/numbers.json)
| key | value [tag] | evidence |
|---|---|---|
| limits.CAPITAL_RS | ₹15,000 [OWNER] | limits.toml |
| limits.EQUITY_FLOOR_RS | ₹10,500 [CODE(ASSUMPTION)] | EVIDENCE/T01/limits_chain.txt |
| limits.H2_MONTHLY_RS | ₹1,500/mahina [OWNER] | limits.toml |
| limits.MAX_DRAWDOWN_RS | ₹2,250 [CODE(ASSUMPTION)] | EVIDENCE/T01/limits_chain.txt |
| limits.MAX_TOTAL_LOSS_RS | ₹4,500 [ASSUMPTION] | EVIDENCE/T01/limits_chain.txt |
| limits.MAX_TRADE_LOSS_RS | ₹1,125 [CODE(ASSUMPTION)] | EVIDENCE/T01/limits_chain.txt |

## PROTECTED_CHANGES (since the last seal)
none

## Allowlists
Env allowlist names (tools/env_allowlist.txt): GH_TOKEN, GITHUB_TOKEN, GIT_ASKPASS, GIT_CONFIG_KEY_*, GIT_CONFIG_VALUE_*, CLAUDE_CODE_*, CLAUDE_SESSION_INGRESS_TOKEN_FILE, CCR_*, MAX_THINKING_TOKENS, BUN_TLS_EXTRA_DISTRUSTED_KEYS
Scan allowlist entries (tools/scan_allowlist.toml): 0 (file arrives with T02b)
