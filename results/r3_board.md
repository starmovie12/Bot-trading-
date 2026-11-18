# R3 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R3-1-0.1 | 358 | 226.5 | -1.34 | 0.5954 | True | False |
| R3-1-0.15 | 206 | 258.9 | 8.91 | 0.2238 | True | False |
| R3-1-0.2 | 128 | 251.9 | 16.92 | 0.1239 | True | False |
| R3-2-0.1 | 342 | 229.9 | -3.76 | 0.6983 | True | False |
| R3-2-0.15 | 200 | 256.5 | 5.8 | 0.2967 | True | False |
| R3-2-0.2 | 128 | 251.9 | 16.29 | 0.1329 | True | False |
| R3-3-0.0005 | 630 | 243.1 | -5.42 | 0.8571 | True | False |
| R3-3-0.0008 | 361 | 236.0 | 2.24 | 0.3986 | True | False |
| R3-3-0.0011 | 180 | 251.8 | 10.57 | 0.1988 | True | False |
| R3-4-0.0005 | 542 | 225.0 | -4.06 | 0.7602 | True | False |
| R3-4-0.0008 | 285 | 255.6 | 1.11 | 0.4585 | True | False |
| R3-4-0.0011 | 131 | 268.6 | -3.69 | 0.5834 | True | False |
| R3-5-0.03 | 237 | 201.6 | -2.71 | 0.6184 | True | False |
| R3-5-0.045 | 105 | 226.4 | 13.31 | 0.1698 | True | False |
| R3-5-0.06 | 51 | 224.1 | 23.96 | 0.1069 | True | False |
| R3-6-0.03 | 237 | 201.6 | 2.71 | 0.3946 | True | False |
| R3-6-0.045 | 105 | 226.4 | -13.31 | 0.8092 | True | False |
| R3-6-0.06 | 51 | 224.1 | -23.96 | 0.8771 | True | False |
| R3-7-0.003 | 137 | 253.4 | 9.03 | 0.2587 | True | False |
| R3-7-0.004 | 105 | 256.7 | 28.32 | 0.037 | True | True |
| R3-7-0.005 | 84 | 251.8 | 33.81 | 0.036 | True | True |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R3-7-0.004-CAP15-XI2 | 72 | 0.199 | 466.41 | 1/4 | 0.0579 | 357.41 / 684.42 | -381.61 | 15,117 | folds, null_screen, st11, st4c |
| R3-7-0.004-CAP15P-XI2 | 71 | 0.196 | 323.87 | 1/4 | 0.1289 | 250.12 / 477.79 | -495.42 | 15,131 | folds, null_screen, st11, st4c |
| R3-7-0.005-CAP15-XI2 | 57 | 0.157 | 448.84 | 2/4 | 0.1169 | 96.41 / 1212.44 | -612.44 | 15,117 | folds, null_screen, st11, st4c |
| R3-7-0.005-CAP15P-XI2 | 56 | 0.155 | 338.52 | 1/4 | 0.1778 | -93.56 / 1250.69 | -686.46 | 15,131 | folds, vix_halves, null_screen, st11, st4c |
