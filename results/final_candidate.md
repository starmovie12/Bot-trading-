# FINAL CANDIDATE (owner order 4, D-47 / D-48) · EXPERIMENTAL: paper only · NO RELIABLE EDGE IN THIS DATA

**R15-a** = the R14-P3-e3 portfolio (26 setups with >= 20 DESIGN trades and a positive DESIGN stressed net, listed in
results/r14_members.json; priority by DESIGN net per trade; one position at a time; at most 3 entries a day;
cool-off 15 min after a loss; daily loss lock ₹71,400) with lots by priority tier (ranks 1-6 -> 3 lots, 7-14 -> 2,
the rest 1), every trade capped at a by-construction max loss of ₹35,700 (fewer lots when needed).

DESIGN 362 days, stressed costs, PRE-TAX, [BACKTEST·in-sample, SELECTION-BIASED: the members, the priority and the
tiers were all chosen on these same days after 354 earlier trials]:

| number | value |
|---|---|
| trades | 207 (0.57 a day) |
| net per trade (all lots) | +₹859.62 |
| net total / per month | +₹1,77,941 / about +₹10,323 |
| walk-forward folds positive | 4 of 4 |
| VIX halves | +₹1,133 high / +₹443 low |
| without the best 5 trades | +₹244 a trade |
| share of the total net from the best 5 trades | 72% |
| win rate / longest losing streak | 39% / 13 trades |
| max loss per trade (by construction) | ₹35,676 |
| closed-trade max drawdown / DD95 (5-day blocks, 12 months, closed-trade marks: a lower bound) | ₹87,083 / ₹1,14,053 |
| one-sided day-block bootstrap p (mean <= 0) | **0.0495: FAILS the EXPLORE screen (needs < 0.01)** |

Verdict: the screen fails, so the old holdout was NOT opened (it opens only for a candidate that passed every DESIGN
gate: D-40 / D-42 / D-47) and there is no STRATEGY PASS. The candidate is EXPERIMENTAL: paper only. Read it as: a
positive-looking in-sample number, 72% of it from 5 trades, a 13-trade losing streak, a drawdown about 11 months of
its own average profit, and a p-value that does not separate it from luck at the agreed level, after hundreds of
looks at the same 362 days. In this data no reliable edge was found. Phase 4 stays closed (no "build bot").
The untouched old holdout (90 days) is still available: spending it on R15-a would be HOLDOUT_2ND_USE as information
only (the candidate did not pass EXPLORE); that is the owner's call.
