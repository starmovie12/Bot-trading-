---
name: survival-strategist
description: Use when designing, updating, testing or red-teaming an options trading strategy for a tiny-capital bot. Enforces pre-mortem, cost-aware math, evidence rules and the break-fix loop.
---
# Survival Strategist
1. PRE-MORTEM: "24 ghante baad bot delete ho gaya. Kyun?" Kam se kam 10 wajah likho aur har ek ka code-level ilaaj.
2. COST-FIRST: Kisi bhi entry se pehle breakeven (charges + slippage + VPS) nikalo. Breakeven edge se bada ho to wo strategy REJECT.
3. EVIDENCE: Har claim ke saath source ya test. Pehla idea galat maano jab tak sabit na ho.
4. SIZING: Max risk per trade ₹ mein, daily limit ₹ mein, losing-streak simulation (Monte Carlo) ₹15,000 par.
5. NO-TRADE EDGE: "Aaj trade mat karo" ko bhi strategy ka hissa banao, uski conditions likho.
6. BREAK-FIX LOOP: Strategy banao -> khud todo (5 holes) -> fix -> dobara test -> dobara todo. Tab ruko jab ek poora round critical hole na nikaale (min 3 rounds).
7. OVERFIT GUARD: In-sample jeet ko jeet mat maano. Walk-forward ya out-of-sample check zaroori. Look-ahead bias dhundho.
8. HONESTY: Jo nahi mila wo "nahi mila" likho. Chhupana = maut.
9. PREREGISTER: criteria pehle commit, result baad mein.
10. NULL FIRST: strategy ko pehle random-entry se haraao.
11. LEDGER: har claim ka tag (CODE/DATA/SOURCE/SIM), bina tag claim nahi.
12. PARAMETER BUDGET: live max 10-12.
13. NEGATIVE RESULT = SUCCESS agar saboot ke saath ho.
