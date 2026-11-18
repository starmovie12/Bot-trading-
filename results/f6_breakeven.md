# F6 BREAK-EVEN TABLE (owner order 2; not a trial; DESIGN, every 3rd day, 10:00 / 11:30 / 13:00, both sides)

Index points the trade must move in its favour to cover stressed costs and the option's decay over the hold. [BACKTEST·in-sample, empirical]

| strike | hold | samples | premium (median pts) | delta | decay pts / hour | cost pts / unit | break-even index pts |
|---|---|---|---|---|---|---|---|
| ITM2 | 30 min | 707 | 711 | 0.55 | -0.9 | 7.16 | 13.9 |
| ITM1 | 30 min | 710 | 652 | 0.52 | -1.3 | 6.97 | 14.7 |
| ATM | 30 min | 708 | 600 | 0.49 | -0.8 | 6.82 | 14.8 |
| CAP15 | 30 min | 599 | 417 | 0.39 | -0.1 | 6.26 | 16.1 |
| ITM2 | 60 min | 707 | 711 | 0.55 | -0.6 | 7.16 | 14.0 |
| ITM1 | 60 min | 710 | 652 | 0.52 | -0.6 | 6.97 | 14.4 |
| ATM | 60 min | 708 | 600 | 0.49 | -0.5 | 6.82 | 14.9 |
| CAP15 | 60 min | 599 | 417 | 0.40 | -0.6 | 6.26 | 16.9 |

Reading: the lower the break-even, the smaller the index move each trade needs. Choose the strike per
signal by this table only inside a pre-registered round (each choice is then a trial).
