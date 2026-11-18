# R4 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R4-1-0.003 | 61 | 246.8 | 24.93 | 0.1289 | True | False |
| R4-1-0.005 | 32 | 262.3 | 39.15 | 0.1109 | True | False |
| R4-1-0.007 | 18 | 314.3 | 89.73 | 0.014 | True | True |
| R4-2-0.0005 | 443 | 218.6 | 2.98 | 0.3207 | True | False |
| R4-2-0.001 | 531 | 237.7 | 2.58 | 0.3197 | True | False |
| R4-2-0.0015 | 570 | 217.0 | 3.72 | 0.2567 | True | False |
| R4-3-0.006 | 191 | 257.9 | 9.01 | 0.2547 | True | False |
| R4-3-0.008 | 98 | 271.8 | 10.89 | 0.2697 | True | False |
| R4-3-0.01 | 42 | 259.0 | 6.41 | 0.4625 | True | False |
| R4-4-0.0005 | 298 | 194.0 | 4.04 | 0.3007 | True | False |
| R4-4-0.001 | 415 | 199.3 | 7.09 | 0.1129 | True | False |
| R4-4-0.0015 | 514 | 200.0 | 7.3 | 0.0809 | True | False |
| R4-5-0.003 | 84 | 246.8 | 3.77 | 0.3906 | True | False |
| R4-5-0.005 | 41 | 307.0 | -5.25 | 0.5604 | True | False |
| R4-5-0.007 | 25 | 328.0 | 1.65 | 0.4735 | True | False |
| R4-6-0.002 | 577 | 248.7 | 4.92 | 0.2118 | True | False |
| R4-6-0.003 | 367 | 264.6 | 14.7 | 0.049 | True | True |
| R4-6-0.004 | 209 | 270.0 | 7.65 | 0.2637 | True | False |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R4-1-0.007-CAP15-XI2 | 13 | 0.036 | 283.47 | 0/4 | 0.4176 | -487.81 / 2018.85 | -1656.45 | 14,826 | folds, vix_halves, null_screen, st11, st4c |
| R4-1-0.007-CAP15-XI1 | 14 | 0.039 | 277.26 | 0/4 | 0.3207 | -175.48 / 1092.19 | -1263.76 | 14,827 | folds, vix_halves, null_screen, st11, st4c |
| R4-6-0.003-CAP15-XI2 | 247 | 0.682 | -427.05 | 1/4 | 0.8871 | -356.96 / -531.82 | -643.93 | 15,236 | net, folds, vix_halves, null_screen, cost_1_5, st4c |
| R4-6-0.003-CAP15-XI1 | 273 | 0.754 | -124.29 | 2/4 | 0.4066 | -134.32 / -108.49 | -262.86 | 15,218 | net, folds, vix_halves, null_screen, cost_1_5, st4c |
