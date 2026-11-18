# R17 BOARD (owner order 5: NESTED walk-forward; OUT-OF-SAMPLE on the 4 test blocks, 290 DESIGN days;
stressed ₹, PRE-TAX, [BACKTEST·out-of-sample of the selection process]; PBO over every trial with a P&L series)

| id | members per window | trades | per day | net / trade | windows net ₹ | w/o best 5 | 1.5x cost | 12m exp ₹ | DD95 ₹ | PBO | DSR | failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R17-a | [3, 3, 3, 5] | 129 | 0.445 | 370.09 | [-31405.0, 12917.0, -42385.0, 108615.0] | -580.03 | 192.37 | 41,157 | 119,532 | 0.2218 | 0.0 | windows_3of4, per_day_0_5, wo_best5, exp12_ge_dd95, dsr_0_95 |
| R17-b | [3, 3, 3, 5] | 129 | 0.445 | 38.67 | [-24526.0, -4494.0, -22425.0, 56434.0] | -394.82 | -77.92 | 4,300 | 66,193 | 0.2218 | 0.0 | windows_3of4, per_day_0_5, wo_best5, cost_1_5, exp12_ge_dd95, dsr_0_95 |
