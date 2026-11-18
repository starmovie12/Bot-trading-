# PREMORTEM (MISSION V19 3d): how this bot dies in 6 months, and the code-level answer

1. **Costs eat the gross** (it already happens on DESIGN: results/edge_decomposition.md). Answer: verdict STOP / paper only; `LIVE_POSSIBLE = false` in limits.toml, which the live gate reads first (RULES K3).
2. **Real spreads wider than the ESTIMATE** (DATA_GRADE B). Answer: the cost model takes spread multipliers by time bucket and expiry day; Phase 7 replaces the ESTIMATE with spreads measured on DATA-R and may only tighten limits.
3. **A jump through the stop.** Answer: the structure is a long option, so the loss is capped by construction at the premium paid; MAX_TRADE_LOSS_RS is sized on that bound; the daily lock is a backstop on mark-to-market.
4. **Stale quotes, no fill, a partial fill.** Answer: entries only on a non-stale bar within 2 bars (else NO_FILL_STALE); an exit on a stale bar pays 2 x spread in every test; the gateway's state machine handles partial fills and never sends a second entry while one is open.
5. **The broker's intraday auto square-off** (cutoff UNVERIFIED, stressed to 15:15). Answer: FORCE_FLAT_IST 15:10 in the bot and the engine; the fee is in constants.toml.
6. **Token expiry (03:30 IST next day), a second login, a static-IP mismatch.** Answer: no arm without a fresh token read from `~/.config/bnbot/token`; a failed funds call or a rejected order = LIVE_BLOCKED and flat; orders only from the host in `config/live_host.toml`.
7. **Holding an ITM long into expiry (exercise STT).** Answer: force-flat 15:10 every day, expiry days included; never an overnight position.
8. **A contract or session change** (lot 15 / 30 / 35 / 30, Tuesday expiry, F&O to 15:40 from 2026-08-03). Answer: lot from the instrument master per contract, dated constants rows, session end by date.
9. **Overfitting and multiple testing.** Answer: pre-registered bracket, Holm over every trial (k counts all), a holdout opened once, GO only after 40 days and 60 paper trades from the latest `strategy_hash`.
10. **Too few trades to learn anything** (about 24 a year). Answer: flagged EXPERIMENTAL / RARE; the paper journal and the owner's Recorder create the data for the next cycle; no parameter change from a thin sample.
11. **A restart that doubles an order.** Answer: `intent_id` idempotency in the gateway, the journal replayed at start, `state/hard_kill.flag` read before any entry.
