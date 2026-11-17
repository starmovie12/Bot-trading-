# Phase 2b probe (MISSION V19)
2b.1 public probe (no token) [SOURCE, 2026-11-18]: public instrument master (assets.upstox.com NSE.json.gz):
BANKNIFTY options lot 30, tick ₹0.05, strike step 100 near ATM, freeze 900, monthly expiries 2026-11-23, 2026-12-29,
2027-01-25, 2027-03-30, 2027-06-29, 2027-09-28; index key `NSE_INDEX|Nifty Bank`. Feed v3 from the official docs:
authorize call → one-time wss URL, protobuf messages, modes ltpc / full / option_greeks / full_d30, bid / ask in
marketLevel.bidAskQuote (schema = SOURCE, live shape = UNVERIFIED_LIVE).
2b.2 token probe: SKIPPED at once (TOKEN not set): spreads, funds field and API_CHECK are UNVERIFIED_LIVE / NA.
