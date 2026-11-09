# PROGRESS (Phase 1: sirf soch, faisle aur docs)

**Shuru:** 10 Nov 2026. **Branch:** `claude/busy-pascal-f7idxf`.

## Saar (10 line)
1. Phase 1 mein sirf docs aur throw-away scratch benchmark banenge. Production code nahi.
2. Original idea file `docs/00_input/bot_idea_final.md` read-only hai. Use kabhi edit nahi karna.
3. Original ka sha256: `c8770e6791923dcb9f03786371a3dbe9ae91a92f00164f90fc982239df0dabb1` (file: `docs/00_input/bot_idea_final.md.sha256`).
4. Kaam copy par hota hai: `docs/01_Bot_Idea_v4.md`.
5. Research notes (source + tarikh ke saath) `docs/research/` mein hain.
6. Benchmark aur simulation scripts `scratch/` mein hain. Yeh production code nahi hai.
7. Koi key, token, password kahin nahi likhna. Upstox ya Telegram se asli connection nahi.
8. Jo internet se verify nahi hua, wahan "verify nahi hua" likha jaata hai.
9. Har deliverable ke baad git commit aur yahan status update.
10. Context bhar jaaye toh isi file se aage badhna.

## Todo list
| # | Kaam | Status |
|---|---|---|
| 0 | Environment: input copy, sha256, folders, PROGRESS | ho gaya |
| R-a | Research: VPS aur network (subagent) | chal raha |
| R-b | Research: repo aur licence jaanch (subagent) | chal raha |
| R-c | Research: SEBI/NSE/Upstox niyam (subagent) | chal raha |
| R-d | Research: kharche aur data sources (subagent) | chal raha |
| R-e | Benchmark: Python vs Rust vs C++ synthetic tick replay (subagent) | chal raha |
| D1 | `docs/01_Bot_Idea_v4.md` + `docs/01b_Audit_Findings.md` | baaki |
| D2 | `docs/02_Tech_Decisions.md` | baaki |
| D3 | `docs/03_Strategy_Edge_Plan.md` | baaki |
| D4 | `docs/04_Build_Roadmap.md` | baaki |
| FR | Aakhri chhoti report (chat mein), phir ruk jaana | baaki |

## Log
- 10 Nov 2026: Environment bana. Upload ki file `docs/00_input/bot_idea_final.md` mein copy hui (byte-for-byte `cmp` se same). File read-only (chmod 444). sha256 upar likha.
