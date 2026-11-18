# R2 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R2-1-0.1 | 457 | 229.6 | -3.41 | 0.6903 | True | False |
| R2-1-0.2 | 206 | 240.8 | 10.69 | 0.1379 | True | False |
| R2-1-0.3 | 94 | 262.4 | 18.27 | 0.1349 | True | False |
| R2-2-0.001 | 545 | 239.1 | -2.43 | 0.6683 | True | False |
| R2-2-0.002 | 423 | 247.4 | 2.0 | 0.4036 | True | False |
| R2-2-0.003 | 294 | 245.6 | 0.1 | 0.4975 | True | False |
| R2-3-0.002 | 574 | 206.2 | 10.21 | 0.043 | True | False |
| R2-3-0.004 | 385 | 218.3 | 5.0 | 0.3307 | True | False |
| R2-3-0.006 | 232 | 259.4 | -14.6 | 0.951 | True | False |
| R2-4-0.002 | 162 | 254.7 | 1.19 | 0.4446 | True | False |
| R2-4-0.004 | 105 | 256.7 | 28.32 | 0.037 | True | True |
| R2-4-0.006 | 69 | 248.5 | 16.76 | 0.2617 | True | False |
| R2-5-0.002 | 537 | 242.0 | 7.27 | 0.1309 | True | False |
| R2-5-0.003 | 335 | 252.2 | 13.36 | 0.0849 | True | False |
| R2-5-0.004 | 187 | 272.4 | -5.96 | 0.6663 | True | False |
| R2-6-0.3 | 50 | 169.7 | 5.81 | 0.3387 | True | False |
| R2-6-0.4 | 13 | 121.7 | 11.02 | 0.3127 | True | False |
| R2-6-0.5 | 2 | 103.5 | -46.85 | 0.8711 | True | False |
| R2-7-1.3 | 255 | 284.8 | 12.97 | 0.1009 | True | False |
| R2-7-1.6 | 83 | 290.5 | -13.54 | 0.7293 | True | False |
| R2-7-2.0 | 8 | 618.8 | 180.71 | 0.043 | True | True |
| R2-8-0.001 | 704 | 241.6 | 0.15 | 0.4775 | True | False |
| R2-8-0.002 | 562 | 251.6 | 4.2 | 0.2458 | True | False |
| R2-8-0.003 | 367 | 259.8 | 8.11 | 0.1688 | True | False |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R2-4-0.004-ATM-XI1 | 86 | 0.238 | 19.23 | 2/4 | 0.3497 | -206.38 / 486.55 | -457.6 | 31,591 | folds, vix_halves, null_screen, st11, cost_1_5, st4c |
| R2-4-0.004-CAP15-XI1 | 84 | 0.232 | 73.19 | 2/4 | 0.3477 | -282.92 / 785.4 | -429.35 | 15,104 | folds, vix_halves, null_screen, st11, cost_1_5, st4c |
| R2-4-0.004-ATM-XI2 | 72 | 0.199 | 330.47 | 1/4 | 0.0929 | 267.08 / 457.25 | -527.7 | 31,420 | folds, null_screen, st11, st4c |
| R2-4-0.004-CAP15-XI2 | 72 | 0.199 | 466.41 | 1/4 | 0.0579 | 357.41 / 684.42 | -381.61 | 15,117 | folds, null_screen, st11, st4c |
| R2-7-2.0-ATM-XI1 | 8 | 0.022 | 1825.87 | 0/4 | 0.0819 | 2384.11 / -2081.85 | -3564.81 | 32,779 | folds, vix_halves, null_screen, st11, st4c |
| R2-7-2.0-CAP15-XI1 | 7 | 0.019 | 1266.75 | 0/4 | 0.1548 | 1783.37 / -1832.94 | -4306.28 | 14,924 | folds, vix_halves, null_screen, st11, st4c |
| R2-7-2.0-ATM-XI2 | 8 | 0.022 | 1267.01 | 0/4 | 0.1648 | 1155.69 / 2046.26 | -3582.55 | 32,779 | folds, vix_halves, null_screen, st11, st4c |
| R2-7-2.0-CAP15-XI2 | 7 | 0.019 | 778.58 | 0/4 | 0.2527 | 625.93 / 1694.45 | -4306.28 | 14,951 | folds, vix_halves, null_screen, st11, st4c |
