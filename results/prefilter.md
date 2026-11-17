# PREFILTER (MISSION V19 3b; arithmetic only, no rule run on data; inputs results/market_facts.md and 2c)
Stressed break-even, LONG ATM (₹555 premium, lot 30, 0.5 delta): about ₹197 round trip = 13 index points; 3 x = 40 points.
SPREAD ATM / 2 OTM (net delta about 0.2): about ₹330 = 55 index points; 3 x = 165 points (above most 60-120 min p75 moves).
ST11 floor: 0.5 trades a day = 181 trades on 362 DESIGN days; ≥ 15 per fold (about 72 days) and per VIX half.

| id | target (points / window) | (i) >= 3 x BE | (ii) <= p90 | (iii) trades a day (est.) | result |
|---|---|---|---|---|---|
| K1 | 70 / 60 min | yes | yes | 0.8 | run (control) |
| K2 | 60 / 60 min | yes | yes | 0.5 | run (control) |
| K3 | 60 / 60 min | yes | yes | 0.6 | run (control) |
| K4 | 75 / 60 min | yes | yes | 1.0 | run (control) |
| A1 | 100 / 120 min | yes | yes | 0.6 | run |
| A2 | 80 / 60 min | yes | yes | 0.5 | run |
| A3 | 80 / 60 min | yes | yes | ≤ 0.25 (|gap| ≥ 0.5% on about a quarter of days) | DROPPED: ST11 by arithmetic |
| A4 | 100 / 120 min | yes | yes | ≤ 0.25 (same gap filter, one entry) | DROPPED: ST11 by arithmetic |
| A5 | 100 / 120 min | yes | yes | 0.2-0.3 (range days that stretch 0.3% from VWAP) | DROPPED: ST11 by arithmetic |
| A6 | 60 / 30 min | yes | yes | < 0.2 (both stocks +0.3% while the index lags) | DROPPED: ST11 by arithmetic |
| A7 | 70 / 40 min | yes | yes | 1.0 | run |
| A8 | 100 / 120 min | yes | yes | 0.3 (half of A1) | DROPPED as a Round A idea; kept as a Round B add-on |
| A9 | 60 / 60 min | yes | yes | 0.5 | run |
| A10 | 80 / 90 min | yes | yes | 0.4-0.5 | run (borderline) |
SPREAD as the base structure: dropped for Round A (165-point target above the 60-120 min p75); kept as a Round B add-on.
