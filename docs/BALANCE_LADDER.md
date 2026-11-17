# BALANCE LADDER (MISSION V19 RULES K2): skeleton from Phase 2c; 3e fills the Monte Carlo columns

1 lot = 30 units; costs PRE-TAX and stressed; premiums = REAL medians at 10:00 IST (results/feasibility.json).
Cell = fits / max loss % of balance / chain OK (2 x max loss <= balance). Spread cash uses the margin ESTIMATE.

| balance | fixed cost % / month | FD ₹ / month | long dte 8-15 ATM | long dte 8-15 1 OTM | long dte 8-15 2 OTM | debit CE dte 8-15 ATM / 2 OTM | P(HARD KILL 12m) | DD p95 |
|---|---|---|---|---|---|---|---|---|
| ₹10,000 | 15.0% | ₹52 | no / 176.33% / no | no / 160.91% / no | no / 148.1% / no | no / 36.98% / OK | 3e | 3e |
| ₹15,000 | 10.0% | ₹78 | no / 117.56% / no | no / 107.27% / no | fits / 98.73% / no | no / 24.65% / OK | 3e | 3e |
| ₹20,000 | 7.5% | ₹104 | fits / 88.17% / no | fits / 80.45% / no | fits / 74.05% / no | no / 18.49% / OK | 3e | 3e |
| ₹25,000 | 6.0% | ₹130 | fits / 70.53% / no | fits / 64.36% / no | fits / 59.24% / no | no / 14.79% / OK | 3e | 3e |
| ₹30,000 | 5.0% | ₹156 | fits / 58.78% / no | fits / 53.64% / no | fits / 49.37% / OK | no / 12.33% / OK | 3e | 3e |
| ₹40,000 | 3.75% | ₹208 | fits / 44.08% / OK | fits / 40.23% / OK | fits / 37.02% / OK | no / 9.24% / OK | 3e | 3e |
| ₹50,000 | 3.0% | ₹260 | fits / 35.27% / OK | fits / 32.18% / OK | fits / 29.62% / OK | no / 7.4% / OK | 3e | 3e |
| ₹75,000 | 2.0% | ₹391 | fits / 23.51% / OK | fits / 21.45% / OK | fits / 19.75% / OK | no / 4.93% / OK | 3e | 3e |
| ₹1,00,000 | 1.5% | ₹521 | fits / 17.63% / OK | fits / 16.09% / OK | fits / 14.81% / OK | no / 3.7% / OK | 3e | 3e |
| ₹1,50,000 | 1.0% | ₹781 | fits / 11.76% / OK | fits / 10.73% / OK | fits / 9.87% / OK | no / 2.47% / OK | 3e | 3e |
| ₹2,00,000 | 0.75% | ₹1,042 | fits / 8.82% / OK | fits / 8.05% / OK | fits / 7.4% / OK | no / 1.85% / OK | 3e | 3e |

MIN_LIVE_BALANCE_RS / MAX_BALANCE_RS: derived in 3e (K2), never from this skeleton alone.
