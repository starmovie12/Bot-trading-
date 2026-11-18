# S3 round cards (BANKNIFTY_STRATEGY_V3.md §15.6)

## R0 CARD · [BACKTEST·OOS] PRE-TAX · 290 OOS din (DESIGN blocks 2–5) · series BASE
1. Configs 3 (T1-RAW, T1, T1-P), fits 12; mukhya test = T1-P. Step 0 kharcha ₹0.01 tak match; T01–T25 pass.
2. T1-P: 555 trade (1.9/din), net_base −₹99,562 (−₹179/trade); net_stress −₹2,30,499 (STRESS aadha spread ₹1.74, slip ₹0.40).
3. OOS windows 4 mein 0 positive: −₹13,595 (114) · −₹32,988 (232) · −₹40,019 (186) · −₹12,960 (23; IVP gate ne din roke).
4. Best-5 hatakar −₹1,18,744 · E12 −₹85,830 vs DD95 ₹1,22,157 · bootstrap p 1.00 · DSR(N=1) 0.00.
5. NULL-RANDOM p 0.41 (2,000 seeds; random entry jaisa hi) · NULL-FLIP −₹1,17,869 · EXIT-CHECK 10 bar −₹30,938 (gear engine se kam ghaata).
6. CE −₹46,780 (278) · PE −₹52,782 (277) · VIX low half −₹99,643, high half +₹81.
7. Intrabar: **INTRABAR-SENSITIVE** (PATH −₹19,214, WORST −₹1,05,659). Cost curve: ₹0.50 spread par bhi ghaata (−₹80,448), koi zero-crossing nahi.
8. Tulna: T1-RAW −₹1,46,289 (882) · T1 −₹1,44,338 (927). T1-P ke §14.1 ke 9 gate mein se sirf 1 (≥150 trade) pass → **R0 = FAIL**.
9. Seekha: gear 0 wale 180 trade (−15 pt SL) ne −₹2,44,548 khaaye; gear 2–3 ke 186 trade +₹1,64,904 laaye; MFE median sirf 6.7 pt — entry random se behtar nahi.
10. Aage: R1 (G1 {5,8,12} × SL {12,18} × X-A/X-B + N13), nested, grid pehle PLAN.md mein.

### R0 · 10-trade chart table (T1-P; 5 jeet, 5 haar, 10 alag mahine; broker chart par milaayein)
| # | date | entry | exit | strike | CE/PE | entry fill | exit fill | lots (qty) | exit_reason | net_base |
|---|---|---|---|---|---|---:|---:|---|---|---:|
| 1 | 2025-04-07 | 10:13 | 10:16 | 47400 | PE | 351.60 | 371.35 | 3 (90) | TRAIL_G3 | ₹1,668.57 |
| 2 | 2025-06-24 | 10:32 | 10:32 | 56500 | CE | 378.05 | 362.35 | 3 (90) | SL_G0 | ₹-1,521.85 |
| 3 | 2025-08-28 | 10:35 | 10:36 | 54100 | CE | 198.70 | 229.80 | 3 (105) | TRAIL_G3 | ₹3,174.63 |
| 4 | 2025-09-19 | 09:38 | 09:44 | 55600 | PE | 330.70 | 313.25 | 3 (105) | GAP_SL | ₹-1,941.81 |
| 5 | 2025-10-09 | 09:36 | 09:37 | 55700 | PE | 338.50 | 322.80 | 3 (105) | SL_G0 | ₹-1,759.85 |
| 6 | 2025-11-21 | 09:43 | 09:46 | 59300 | PE | 377.90 | 414.65 | 2 (70) | TRAIL_G3 | ₹2,472.16 |
| 7 | 2025-12-16 | 13:47 | 13:56 | 59700 | CE | 334.75 | 319.05 | 3 (105) | SL_G0 | ₹-1,759.12 |
| 8 | 2026-01-21 | 10:42 | 10:43 | 59000 | PE | 368.05 | 425.05 | 3 (90) | CLIMAX_LOCK | ₹5,013.54 |
| 9 | 2026-06-29 | 10:16 | 10:16 | 58200 | PE | 376.75 | 361.05 | 3 (90) | SL_G0 | ₹-1,537.88 |
| 10 | 2026-07-03 | 11:09 | 11:13 | 56800 | PE | 346.40 | 351.90 | 3 (90) | TRAIL_G2 | ₹372.94 |
