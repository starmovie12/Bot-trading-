# R1 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R1-1-0.003 | 501 | 226.5 | -5.97 | 0.8222 | True | False |
| R1-1-0.005 | 350 | 238.2 | -2.02 | 0.6164 | True | False |
| R1-1-0.007 | 212 | 275.3 | 0.17 | 0.4735 | True | False |
| R1-2-0.03 | 609 | 229.9 | 3.38 | 0.2537 | True | False |
| R1-2-0.05 | 594 | 233.3 | 4.54 | 0.1788 | True | False |
| R1-2-0.08 | 576 | 231.0 | 6.05 | 0.1479 | True | False |
| R1-3-0.0025 | 447 | 245.5 | -10.74 | 0.9381 | True | False |
| R1-3-0.004 | 227 | 249.3 | -14.9 | 0.8731 | True | False |
| R1-3-0.006 | 92 | 275.7 | 6.71 | 0.4116 | True | False |
| R1-4-0.004 | 108 | 259.0 | -9.78 | 0.7812 | True | False |
| R1-4-0.006 | 66 | 333.7 | -16.46 | 0.7902 | True | False |
| R1-4-0.008 | 43 | 346.4 | -48.17 | 0.985 | True | False |
| R1-5-0.003 | 82 | 254.0 | 24.96 | 0.0689 | True | False |
| R1-5-0.005 | 58 | 265.4 | 43.82 | 0.032 | True | True |
| R1-5-0.007 | 38 | 281.2 | 33.05 | 0.2368 | True | False |
| R1-6-0.004 | 5 | 152.7 | 4.51 | 0.3686 | True | False |
| R1-6-0.006 | 0 | 0.0 | 0.0 | 1.0 | False | False |
| R1-6-0.008 | 0 | 0.0 | 0.0 | 1.0 | False | False |
| R1-7-0.004 | 492 | 223.5 | -2.09 | 0.6054 | True | False |
| R1-7-0.006 | 315 | 239.7 | 7.39 | 0.1888 | True | False |
| R1-7-0.008 | 174 | 260.5 | 10.13 | 0.2208 | True | False |

## S3 option P&L (ATM long, nearest monthly, RISK SHELL)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R1-5-0.005-EXIT0 | 55 | 0.152 | 556.42 | 1/4 | 0.044 | 585.87 / 504.87 | -119.22 | 31,421 | folds, st11, st4c |
| R1-5-0.005-C2 | 51 | 0.141 | 620.32 | 1/4 | 0.0539 | 619.4 / 622.0 | -93.43 | 31,421 | folds, null_screen, st11, st4c |
| R1-5-0.005-C3 | 58 | 0.16 | 384.57 | 1/4 | 0.04 | 384.63 / 384.46 | -84.48 | 32,695 | folds, st11, st4c |
