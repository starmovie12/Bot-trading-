# STRATEGY (MISSION V19 3d) · A1+b1 · EXPERIMENTAL: paper only

**Result of the tournament: NO EDGE FOUND IN THE TESTED SET** (13 trials; results/scoreboard.md). This is the carried
candidate with the smallest DD95 (results/loss_first_rank.json); it is shipped only so the bot's paper run can collect
data. It is not expected to make money: on DESIGN its stressed net per trade is negative (results/edge_decomposition.md).

| layer | choice |
|---|---|
| L1 day filter | trend day (efficiency of the index move since the open at or above a threshold) and India VIX lower than at the day's first bar (IV falling) |
| L2 setup | the index closes beyond the 30-minute opening range (09:15-09:44) with the last 15 minutes in the same direction |
| L3 cost gate | none in this version (the add-on was not reached: no Round A survivor) |
| L4 structure | 1 lot of the ATM option of the nearest monthly expiry: CE above the range, PE below; never a credit structure |
| L5 risk shell | PLAN.md §PREREG-0: stop at a fixed share of the premium, tighten-only trail to break-even after +1R, scratch, time-stop, <= 2 entries a day, cool-off after a loss, the day ends after a full loss, force-flat 15:10 IST |

- **Entry:** decisions on 5-minute index closes 09:45..14:30 IST; the order goes in at the next non-stale option bar (limit price, never MARKET).
- **Exit:** stop (by construction the loss can never exceed the premium paid), target at a multiple of R, break-even trail, scratch, time-stop, force-flat.
- **No-trade:** before 09:45; not a trend day; VIX not falling; no range break; a position already open; 2 entries done; cool-off; the day ended after a full loss; any RISK limit or HARD KILL flag; special sessions.
- **Parameters (6 live):** trend-efficiency threshold, opening-range minutes, stop share of premium, target in R, scratch minutes, time-stop minutes. The repo is public (C9): the values the bot loads live in `config/params.local.toml` (gitignored); `params.example.toml` holds placeholders.
- **Source of edge:** DIRECTION (the weakest source: "where price will go"). No structural or risk-premium reason backs it.
- **Where it fails:** costs. Gross per trade is smaller than the stressed spread + slippage + charges; the rule fires on about 0.07 days in 1 (ST11 RARE), so even a real edge could not be confirmed in a sensible paper run; spreads are an ESTIMATE until the owner's Recorder measures them.
