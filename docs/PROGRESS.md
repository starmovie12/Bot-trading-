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
| R-a | Research: VPS aur network (subagent) | ho gaya (`docs/research/R_a_VPS_Network.md`) |
| R-b | Research: repo aur licence jaanch (subagent) | ho gaya (`R_b_Repos_Licence.md`) |
| R-c | Research: SEBI/NSE/Upstox niyam (subagent) | ho gaya (`R_c_Compliance.md`) |
| R-d | Research: kharche aur data sources (subagent) | ho gaya (`R_d_Costs_Data.md`) |
| R-e | Benchmark: Python vs Rust vs C++ synthetic tick replay (subagent) | ho gaya (`R_e_Benchmark.md`, code `scratch/bench/`) |
| D1 | `docs/01_Bot_Idea_v4.md` + `docs/01b_Audit_Findings.md` | ho gaya (76 bindu; verify PASS; lint PASS) |
| D2 | `docs/02_Tech_Decisions.md` | baaki |
| D3 | `docs/03_Strategy_Edge_Plan.md` | baaki |
| D4 | `docs/04_Build_Roadmap.md` | baaki |
| FR | Aakhri chhoti report (chat mein), phir ruk jaana | baaki |

## Log
- 10 Nov 2026: Environment bana. Upload ki file `docs/00_input/bot_idea_final.md` mein copy hui (byte-for-byte `cmp` se same). File read-only (chmod 444). sha256 upar likha.
- 10 Nov 2026: 5 research subagents shuru (VPS, repo/licence, SEBI/NSE/Upstox, kharche/data, benchmark). Unki files `docs/research/` mein aayengi.
- 10 Nov 2026: D1 ka tareeka: `scratch/d1_build/build_v4.py` original + `add_*.md` se v4 banata hai aur verify karta hai ki original ki har line usi kram mein maujood hai. Abhi tak: VERIFY PASS, 0 lines missing, instruction block same.
- 10 Nov 2026: Malik ke kehne par abhi tak ka kaam (WIP) GitHub par push karke PR banaya. Baaki kaam isi branch par aage jaayega.
- 10 Nov 2026: 4 research agents usage limit se ruke; limit reset ke baad R-b, R-c, R-d ki files poori mili, R-a resume karke poora hua.
- 10 Nov 2026: D1 poora. Research se naye bindu F-62 se F-76. Sabse bada: Upstox ka "ek user, ek chalu API app" niyam (F-76, khud verify kiya: community.upstox.com post 27 Mar 2026) Pehredaar ke alag app ko rokta hai.
- Agla: D2 (Tech Decisions), phir D3, D4.
