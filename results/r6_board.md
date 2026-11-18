# R6 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R6-1-0.001 | 307 | 392.9 | -10.89 | 0.7862 | True | False |
| R6-1-0.002 | 244 | 393.6 | -13.6 | 0.7982 | True | False |
| R6-1-0.003 | 202 | 405.2 | -11.69 | 0.7622 | True | False |
| R6-2-0.001 | 300 | 343.4 | -10.26 | 0.7872 | True | False |
| R6-2-0.002 | 257 | 364.5 | -10.41 | 0.7782 | True | False |
| R6-2-0.003 | 219 | 390.5 | -4.55 | 0.5944 | True | False |
| R6-3-0.1 | 202 | 391.0 | -15.27 | 0.8132 | True | False |
| R6-3-0.15 | 116 | 378.9 | -20.47 | 0.8541 | True | False |
| R6-3-0.2 | 69 | 377.4 | 24.05 | 0.1708 | True | False |
| R6-4-0.001 | 122 | 497.4 | 47.6 | 0.034 | True | True |
| R6-4-0.002 | 88 | 516.3 | 43.73 | 0.0919 | True | False |
| R6-4-0.003 | 63 | 573.2 | 53.92 | 0.0909 | True | False |
| R6-5-0.002 | 60 | 488.1 | 30.26 | 0.1868 | True | False |
| R6-5-0.003 | 46 | 485.7 | 57.01 | 0.0899 | True | False |
| R6-5-0.004 | 37 | 483.3 | 88.39 | 0.03 | True | True |
| R6-6-0.001 | 293 | 465.5 | -8.31 | 0.6813 | True | False |
| R6-6-0.002 | 227 | 478.3 | 6.24 | 0.3676 | True | False |
| R6-6-0.003 | 160 | 479.3 | 1.61 | 0.4545 | True | False |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R6-4-0.001-CAP15-XI2 | 91 | 0.251 | -428.4 | 1/4 | 0.8871 | -253.83 / -632.07 | -701.67 | 15,195 | net, folds, vix_halves, null_screen, st11, cost_1_5, st4c |
| R6-4-0.001-ATM-XI2 | 119 | 0.329 | -491.33 | 1/4 | 0.8831 | -238.34 / -922.57 | -723.5 | 37,354 | net, folds, vix_halves, null_screen, st11, cost_1_5, st4c |
| R6-5-0.004-CAP15-XI2 | 35 | 0.097 | -139.26 | 0/4 | 0.1868 | 2.64 / -448.85 | -1631.66 | 14,995 | net, folds, vix_halves, null_screen, st11, cost_1_5, st4c |
| R6-5-0.004-ATM-XI2 | 36 | 0.099 | -300.93 | 0/4 | 0.2428 | -159.15 / -669.56 | -1794.89 | 32,413 | net, folds, vix_halves, null_screen, st11, cost_1_5, st4c |
