# R12 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R12-1-3 | 171 | 513.6 | 14.19 | 0.3137 | True | False |
| R12-1-4 | 78 | 504.6 | 34.98 | 0.1359 | True | False |
| R12-1-5 | 34 | 466.0 | 84.77 | 0.04 | True | True |
| R12-2-3 | 171 | 440.5 | -18.07 | 0.8382 | True | False |
| R12-2-4 | 77 | 392.9 | -32.95 | 0.9101 | True | False |
| R12-2-5 | 7 | 284.5 | 77.14 | 0.2717 | True | False |
| R12-3-3 | 86 | 494.8 | -8.54 | 0.6464 | True | False |
| R12-3-4 | 33 | 503.4 | 0.0 | 0.3876 | True | False |
| R12-3-5 | 14 | 448.3 | 78.9 | 0.0699 | True | False |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R12-1-5-CAP15-XH | 28 | 0.077 | 948.38 | 0/4 | 0.037 | 564.88 / 1331.87 | -595.25 | 15,224 | folds, vix_halves, st11, st4c |
| R12-1-5-CAP15-XI2 | 28 | 0.077 | 607.44 | 0/4 | 0.1049 | -304.24 / 1519.13 | -904.36 | 15,224 | folds, vix_halves, null_screen, st11, st4c |
