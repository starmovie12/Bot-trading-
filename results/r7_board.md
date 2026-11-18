# R7 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R7-1-0.001 | 122 | 497.4 | 47.6 | 0.034 | True | True |
| R7-1-0.002 | 88 | 516.3 | 43.73 | 0.0919 | True | False |
| R7-1-0.003 | 63 | 573.2 | 53.92 | 0.0909 | True | False |
| R7-2-0.002 | 60 | 488.1 | 30.26 | 0.1868 | True | False |
| R7-2-0.003 | 46 | 485.7 | 57.01 | 0.0899 | True | False |
| R7-2-0.004 | 37 | 483.3 | 88.39 | 0.03 | True | True |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R7-1-0.001-CAP15-XH | 91 | 0.251 | 39.36 | 1/4 | 0.1199 | 15.16 / 67.59 | -598.81 | 15,231 | folds, null_screen, st11, cost_1_5, st4c |
| R7-1-0.001-CAP15-XH2 | 91 | 0.251 | -192.71 | 1/4 | 0.1818 | -334.07 / -27.78 | -844.37 | 15,193 | net, folds, vix_halves, null_screen, st11, cost_1_5, st4c |
| R7-2-0.004-CAP15-XH | 35 | 0.097 | 1152.72 | 0/4 | 0.013 | 1040.92 / 1396.64 | -527.81 | 15,021 | folds, vix_halves, st11, st4c |
| R7-2-0.004-CAP15-XH2 | 35 | 0.097 | 1222.55 | 0/4 | 0.011 | 1048.97 / 1601.28 | -446.34 | 14,991 | folds, vix_halves, st11, st4c |
