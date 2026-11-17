# REGULATORY + DATA RIGHTS (MISSION V19 Phase 2, 2026-11-18)

Every fact row lives in `constants.toml` (value, unit, tag, URL, date). Fetches: `results/fetch_log.md` (11 of 30).
The V11 version of this file is archived (`archive/v11_guards/REGULATORY_v11.md`); each of its rows that still matters
for BANKNIFTY was re-checked below or stays UNVERIFIED.

## Data rights (C2 licence gate)
DATA-LICENCE | UNVERIFIED | The Upstox terms of use say nothing specific about storing or processing API market data; the owner downloaded it and put it in his own repo (his decision, tag OWNER), so the mission goes on and prints "DATA-LICENCE UNVERIFIED" on report point 5. | https://upstox.com/terms-of-use-and-privacy-policy/
DATA-PUBLIC | UNVERIFIED | No official page found that allows or forbids keeping exchange-sourced API data in a public repository; the owner's matter (OWNER_TODO line, report point 11), never a deletion or a stop. | https://upstox.com/terms-of-use-and-privacy-policy/

Licence gate result: DATA-LICENCE is not NAHI, so `data/banknifty/repo/` and the files built from it stay (they are
gitignored; only summaries such as `docs/DATA_REPORT.md` and `results/data_gaps.json` are committed).

## Re-verified this cycle [SOURCE, 2026-11-18]
- Option charges (Upstox charges page): brokerage ₹20 per order; STT sell 0.0625% (from 2023-04-01), 0.1% (from
  2024-10-01), 0.15% (from 2026-04-01) of premium; 0.15% on an exercised option (from 2026-04-01); NSE transaction
  0.0495% (Apr-Sep 2024), 0.03503% (from 2024-10-01); IPFT ₹0.50 per lakh; SEBI ₹10 per crore; stamp 0.003% on buys;
  GST 18% on brokerage + transaction + IPFT; auto square-off ₹75 + GST (₹50 with Plus).
- Contract (public instrument master): lot 30, tick ₹0.05, strike step 100 near ATM, freeze quantity 900, monthly
  expiries only (no weekly). Lot history 15 / 30 / 35 / 30 is REAL from the data's `contracts.csv`.
- Upstox API (official docs, full text): order types MARKET, LIMIT, SL, SL-M (API MARKET orders need market protection,
  0 = rejected); tag up to 40 characters; order APIs combined 10 per second, 500 per minute, 2,000 per 30 minutes;
  static IP required for every order API call from 2026-04-01 (one primary + one secondary, change once a week, one
  customer per IP; funds / positions / historical not restricted); algo registration only above 10 orders per second;
  access token valid until 03:30 IST next day; Analytics token read-only for 1 year; funds `available_margin`;
  margin API returns `final_margin` after margin benefit; feed v3 authorize + protobuf; expired contracts' OHLC only
  with Upstox Plus.
- Calendar: 2026 trading holidays (Upstox market-holidays page). Money: USD/INR 93.5703 (RBI), FD 6.25% a year (SBI,
  1-2 years).

## Measured on the data [REAL]
F&O session ends 15:30 until 2026-07-31 and 15:40 from 2026-08-03 (the index stops at 15:30); expiry weekday Thursday
until Aug 2025, last Tuesday from Sep 2025 (the trading day before when it is a holiday).

## Still UNVERIFIED (stressed value in brackets)
Monthly-only rule date 2024-11-20 (POINTER); 2024-2025 holiday lists (data-derived calendar); broker MIS cutoff for index
options (15:15); STT on exercise before 2026-04-01; how many modifies one order allows; whether a repeated tag is rejected;
whether a new login revokes the token; exchange price band; margin to sell Leg 2 of a debit spread (Phase 2c ESTIMATE);
Upstox Plus price (₹1,500, the R5 cap); Lightsail plan price (HISTORY $12, cheapest $5); RBI / bank-result event calendar;
every tax row (incometax.gov.in did not answer from this session).

## Static IP route and fixed cost
API orders need a registered static IP. Cheapest legal route found: a small cloud machine with a static IP (Lightsail
includes one in every plan); its price is UNVERIFIED this cycle. Fixed cost per month = USD price × 93.5703 × 1.18:
$12 → ₹1,324.96 and $5 → ₹552.07 [CODE(HISTORY)]; Phase 2c uses the stressed ₹1,500 (R5 cap) on the PASS side.
SEBI FY26 study: 87.7% of individual F&O traders lost money [POINTER] (the crowd's base rate, not a verdict).
