# CHECKPOINT log

**CP1 (11 Nov 2026, Phase 5 shuru).**
- PREREGISTER commit `a6688fb`. Yeh kisi bhi truth-test result se pehle hua.
- Kharcha model ab poora Upstox charges page (SOURCE) par: NSE 0.03553%, BSE 0.0325%, ₹20/order.
- Order limit 8/s, 400/min, 1,800/30min. Upstox ki seema 10/500/2000 hai (SOURCE).
- Deploy bug theek: dono units oneshot hain, `Restart=always` nahi, StartLimit laga hai. `python -m bot --check` dry-run entrypoint bana.
- 83 tests pass. Adversary (red-team) background mein chal raha hai.
- Agla kaam: break-even table, truth-test framework (synthetic par), look-ahead audit, mutation proof.
