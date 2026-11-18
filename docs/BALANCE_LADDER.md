# BALANCE LADDER (MISSION V19 RULES K2; filled in 3e; PROVISIONAL until Phase 7)

Strategy A1+b1 (EXPERIMENTAL: paper only), 1 lot long ATM option. Per-trade cap ₹35,700, MAX_TOTAL_LOSS ₹157,500, P(HARD KILL 12m) 0.042 and DD p95 ₹157,584: worst of four Monte Carlo ensembles, stressed, PRE-TAX [BACKTEST].
Base-case stressed net per month: ₹-146 [BACKTEST]; fixed monthly cost ₹1,500 [ESTIMATE].

| balance | 1 lot fits | max loss % | chain | P(kill) <= 5% | fixed cost % / month | cost <= half net | FD ₹ / month | DD p95 % | spread (fits / max loss % / chain) | row passes |
|---|---|---|---|---|---|---|---|---|---|---|
| ₹10,000 | no | 357.0% | no | yes | 15.0% | no | ₹52 | 1575.8% | no / 37.55% / OK | no |
| ₹15,000 | no | 238.0% | no | yes | 10.0% | no | ₹78 | 1050.6% | no / 25.03% / OK | no |
| ₹20,000 | no | 178.5% | no | yes | 7.5% | no | ₹104 | 787.9% | no / 18.78% / OK | no |
| ₹25,000 | no | 142.8% | no | yes | 6.0% | no | ₹130 | 630.3% | no / 15.02% / OK | no |
| ₹30,000 | no | 119.0% | no | yes | 5.0% | no | ₹156 | 525.3% | no / 12.52% / OK | no |
| ₹40,000 | yes | 89.2% | no | yes | 3.75% | no | ₹208 | 394.0% | no / 9.39% / OK | no |
| ₹50,000 | yes | 71.4% | no | yes | 3.0% | no | ₹260 | 315.2% | no / 7.51% / OK | no |
| ₹75,000 | yes | 47.6% | no | yes | 2.0% | no | ₹391 | 210.1% | no / 5.01% / OK | no |
| ₹100,000 | yes | 35.7% | no | yes | 1.5% | no | ₹521 | 157.6% | no / 3.76% / OK | no |
| ₹150,000 | yes | 23.8% | no | yes | 1.0% | no | ₹781 | 105.1% | no / 2.5% / OK | no |
| ₹200,000 | yes | 17.8% | yes | yes | 0.75% | no | ₹1,042 | 78.8% | no / 1.88% / OK | no |

No row up to ₹2,00,000 passes: LIVE_POSSIBLE = false (NO_LIVE_BALANCE_UP_TO_2L). The bot ships PAPER only.
