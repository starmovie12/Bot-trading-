# S3 R0 · Diagnosis (§13.6; not a trial)

[BACKTEST·OOS] PRE-TAX · 290 OOS days · series BASE

| variant | trades | /day | net_base | per trade | net_stress | p | R | p needed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T1-RAW | 882 | 3.04 | -₹146,289 | -₹166 | -₹361,848 | 0.438 | 0.86 | 0.538 |
| T1 | 927 | 3.20 | -₹144,338 | -₹156 | -₹371,144 | 0.521 | 0.63 | 0.614 |
| T1-P | 555 | 1.91 | -₹99,562 | -₹179 | -₹230,499 | 0.506 | 0.62 | 0.616 |

**T1-P · §14.1 gates**

| gate | pass |
|---|---|
| 1_net_base_pos | FAIL |
| 2_net_stress_ge0 | FAIL |
| 3_windows_3of4_25tr | FAIL |
| 4_best5_removed_pos | FAIL |
| 5_vix_halves_ge0 | FAIL |
| 6_trades_ge150 | PASS |
| 7_boot_p_lt_005 | FAIL |
| 8_e12_ge_dd95 | FAIL |
| 9_null_p_le_005 | FAIL |

windows (net, trades): {2: (-13594.61, 114), 3: (-32988.44, 232), 4: (-40018.77, 186), 5: (-12960.46, 23)} · best-5 removed -₹118,744 · VIX halves {'LOW': -99642.95000000001, 'HIGH': 80.66999999999985} · E12 -₹85,830 vs DD95 ₹122,157 · bootstrap p 1.0000 · DSR(N=1) 0.000

MFE median 6.7 pt, MAE median -6.6 pt · reached +5: 68% · +10: 34% · +25: 8% · +30: 4% · MFE capture (winners) 0.58

GAP_SL 36 (worst -₹1,942) · STALE_FORCED 0 (worst -)

Money: gross -₹44,151 · charges ₹55,412 · spread+slip inside fills ₹63,390

**Exit reason**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| CLIMAX_LOCK | 10 | ₹21,669 | ₹2,167 |
| GAP_SL | 36 | -₹8,720 | -₹242 |
| SL_G0 | 165 | -₹227,102 | -₹1,376 |
| SL_G1_LOCK | 173 | -₹21,341 | -₹123 |
| TIME_STOP | 8 | -₹2,352 | -₹294 |
| TRAIL_G2 | 123 | ₹64,986 | ₹528 |
| TRAIL_G3 | 40 | ₹73,297 | ₹1,832 |

**CE vs PE**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| CE | 278 | -₹46,780 | -₹168 |
| PE | 277 | -₹52,782 | -₹191 |

**DTE**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| 0-2 | 51 | -₹5,870 | -₹115 |
| 16+ | 250 | -₹45,952 | -₹184 |
| 3-7 | 95 | -₹7,951 | -₹84 |
| 8-15 | 159 | -₹39,789 | -₹250 |

**Entry half-hour**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| 09:00 | 35 | -₹17,461 | -₹499 |
| 09:30 | 169 | -₹25,938 | -₹153 |
| 10:00 | 109 | -₹2,551 | -₹23 |
| 10:30 | 83 | -₹12,670 | -₹153 |
| 11:00 | 55 | -₹19,887 | -₹362 |
| 13:00 | 26 | -₹1,315 | -₹51 |
| 13:30 | 35 | -₹3,126 | -₹89 |
| 14:00 | 32 | -₹11,218 | -₹351 |
| 14:30 | 11 | -₹5,397 | -₹491 |

**Pattern**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| P1 | 502 | -₹103,499 | -₹206 |
| P2 | 48 | ₹7,064 | ₹147 |
| REENTRY | 5 | -₹3,127 | -₹625 |

**DAY_STATE (EOD, diagnosis only)**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| CHOP | 303 | -₹92,449 | -₹305 |
| DEAD | 2 | -₹650 | -₹325 |
| NORMAL | 143 | -₹4,008 | -₹28 |
| TREND | 107 | -₹2,455 | -₹23 |

**VIX half**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| HIGH | 39 | ₹81 | ₹2 |
| LOW | 516 | -₹99,643 | -₹193 |

**Lot size**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| 30 | 154 | -₹43,335 | -₹281 |
| 35 | 401 | -₹56,227 | -₹140 |

**lots_reason**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| CAP | 306 | -₹39,103 | -₹128 |
| DAY | 1 | -₹537 | -₹537 |
| MODE | 248 | -₹59,922 | -₹242 |

**max gear**

| bucket | trades | net_base | per trade |
|---|---:|---:|---:|
| 0 | 180 | -₹244,548 | -₹1,359 |
| 1 | 189 | -₹19,919 | -₹105 |
| 2 | 142 | ₹78,988 | ₹556 |
| 3 | 44 | ₹85,916 | ₹1,953 |

