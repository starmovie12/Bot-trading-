# R13 BOARD (P3R; DESIGN 362 days; stressed ₹ per trade, PRE-TAX, [BACKTEST·in-sample]; screening)

## S2 index points (60 min, signals >= 60 min apart, <= 2 a day; break-even 14.2 points)

| id | signals | p90 move | mean pts | null p | S1 | S2 |
|---|---|---|---|---|---|---|
| R13-1-0.002 | 60 | 488.1 | 30.26 | 0.1868 | True | False |
| R13-1-0.003 | 46 | 485.7 | 57.01 | 0.0899 | True | False |
| R13-1-0.004 | 37 | 483.3 | 88.39 | 0.03 | True | True |
| R13-2-3 | 171 | 513.6 | 14.19 | 0.3137 | True | False |
| R13-2-4 | 78 | 504.6 | 34.98 | 0.1359 | True | False |
| R13-2-5 | 34 | 466.0 | 84.77 | 0.04 | True | True |
| R13-3-0.001 | 122 | 497.4 | 47.6 | 0.034 | True | True |
| R13-3-0.002 | 88 | 516.3 | 43.73 | 0.0919 | True | False |
| R13-3-0.003 | 63 | 573.2 | 53.92 | 0.0909 | True | False |

## S3 option P&L (1 lot long option, nearest monthly, RISK SHELL; structure and exit in the id)

| id | trades | per day | net / trade | folds + | p screen | high / low VIX net | w/o best 5 | max loss ₹ | failed gates |
|---|---|---|---|---|---|---|---|---|---|
| R13-1-0.004-ITM2-XH | 35 | 0.097 | 1215.0 | 0/4 | 0.033 | 1054.27 / 1616.82 | -757.76 | 35,031 | folds, vix_halves, st11, st4c |
| R13-1-0.004-ITM2-XH2 | 35 | 0.097 | 1245.16 | 0/4 | 0.036 | 969.02 / 1935.52 | -722.57 | 35,031 | folds, vix_halves, st11, st4c |
| R13-2-5-ITM2-XH | 31 | 0.086 | 1225.98 | 0/4 | 0.034 | 960.7 / 1593.3 | -300.02 | 41,007 | folds, vix_halves, st11, st4c |
| R13-2-5-ITM2-XH2 | 31 | 0.086 | 1273.6 | 0/4 | 0.015 | 1042.71 / 1593.3 | -243.25 | 40,980 | folds, vix_halves, st11, st4c |
| R13-3-0.001-ITM2-XH | 120 | 0.331 | 525.1 | 3/4 | 0.031 | 1061.55 / -401.48 | -189.55 | 40,938 | vix_halves, st11, st4c |
| R13-3-0.001-ITM2-XH2 | 120 | 0.331 | -208.43 | 2/4 | 0.1439 | 23.18 / -608.48 | -925.52 | 40,938 | net, folds, vix_halves, null_screen, st11, cost_1_5, st4c |
