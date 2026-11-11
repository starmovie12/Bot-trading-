# R-d: Kharche (Cost Model) aur Backtest Data Plan

**Banaya:** 10 Nov 2026 (research subagent R-d). **Phase:** 1 (sirf docs). Koi account, login ya key use nahi hui.
**Saath ki script:** `scratch/cost_model/cost_model.py` (sirf ganit, koi network nahi). Chalao: `python3 scratch/cost_model/cost_model.py`.
**Niyam:** har number ke saath source + "dekha: 10 Nov 2026". Jo pakka nahi hua, wahan saaf "verify nahi hua" likha hai. Kisi munafe ki guarantee nahi.

## Saar (10 line)
1. STT Budget 2026 mein badla: option bechne par **0.15% of premium** (pehle 0.10%), exercise par **0.15% of intrinsic value** (pehle 0.125%). Lagu **1 Apr 2026** (Finance Act 2026, assent 30 Mar 2026; NSE circular NSE/FATAX/73524).
2. NSE index options transaction charge **0.03553% of premium** (Rs 3,552.99 + Rs 0.01 IPFT per crore), lagu 1 Mar 2026 (NSE/FA/73061). Kul kharcha pehle jaisa hi raha, sirf IPFT ka hissa txn mein chala gaya.
3. BSE Sensex options transaction charge **0.0325%** (Rs 3,250/crore premium), 1 Oct 2024 se. BSE ka asli notice nahi khula (403); Upstox aur Zerodha ke pages se liya.
4. Upstox: options **Rs 20 per executed order**; API se order **Rs 10/order "Valid till 31st Dec 2026"** (GTT par nahi). API subscription Rs 0. DP charge options par nahi.
5. Lot size abhi: **NIFTY 65, BANKNIFTY 30** (NSE file, 30 Oct 2026), **SENSEX 20** (Nov/Dec 2026 contracts); Jan 2027 ke Sensex contracts mein **25** dikh raha hai (Upstox master; BSE notice verify nahi hua). Tick Rs 0.05.
6. Round-trip kharcha 1 lot, Rs 20 brokerage par: **Nifty Rs 80.52**, **BankNifty Rs 67.39**, **Sensex Rs 57.91**. Breakeven (slippage ke bina): Nifty +1.20, BankNifty +2.29, Sensex +2.83 premium points.
7. 1-lot trade mein sabse bada kharcha **brokerage** hai (Rs 40 of Rs 80 Nifty mein), phir STT. Slippage ka asli number koi rigorous public study mein nahi mila; isliye "andaza" + naapne ka plan likha hai.
8. Depth (top 5) ka itihas sasta nahi: NSE Historical Order & Trade Data **Rs 12.5 lakh/saal** (budget se bahar); BSE order book **Rs 47,000/mahina**. Sabse sasta raasta: Paper stage mein Upstox WebSocket (5-level depth) khud record karna.
9. Sabse kaam ka khareed: **NSE Historical Trade Data (F&O) Rs 1,10,000/saal + tax** (har trade, saare contracts, expired bhi). Licence mein "commercial use / financial gain" ki pabandi wali line hai: kharidne se pehle NSE se likhit clarification zaroori.
10. Data ki badi dikkatein: lot size kai baar badla, expiry weekday 2025 mein badla, holiday par expiry khisakti hai (jaise Nifty 9 Nov 2026 Monday). Isliye har din ka lot aur expiry **bhavcopy/contract master se** lena, kabhi hard-code nahi.

---

## 1. Charges table (index options buy, same-day sell)

| Charge | Rate | Kis par | Lagu tarikh | Source (dekha: 10 Nov 2026) |
|---|---|---|---|---|
| Brokerage (Upstox, standard) | Rs 20 per executed order | Har executed order (buy aur sell alag) | Page par tarikh nahi | upstox.com/brokerage-charges ("Flat ₹20 per executed order") |
| Brokerage (Upstox, API se order) | Rs 10 per order | API se lage order; GTT par nahi | "Valid till 31st Dec 2026" | upstox.com/trading-api. Note: brokerage-charges page abhi bhi purani tarikh "31 Dec 2025" dikhata hai, yani pages mein takraav |
| Brokerage (Upstox Plus) | Rs 30 (equity options) | Har executed order (manual) | Plus "can be activated for free initially" | upstox.com/help-center T&C Upstox Plus |
| API subscription | Rs 0 ("All trading + data APIs are free of cost") | — | — | upstox.com/trading-api |
| Upstox Plus plan fee | Abhi free ("free initially"); baad mein charge ho sakta hai | Expired Instruments API aur full_d30 depth ke liye zaroori | — | Upstox Plus T&C; Upstox API docs (error UDAPI1149) |
| DP charges | Equity Options: "No charges" | — | — | upstox.com/brokerage-charges |
| Call & Trade | Rs 75 + GST | Dealer se phone par order | — | upstox.com/brokerage-charges |
| Auto square-off | Rs 75 + GST (Basic), Rs 50 + GST (Plus) | Agar broker khud position kaate | — | upstox.com/brokerage-charges |
| **STT (sell)** | **0.15%** (31 Mar 2026 tak 0.10%) | Sell side, option premium par; seller deta hai | **1 Apr 2026** | NSE circular NSE/FATAX/73524 (31 Mar 2026); NSE investor page (updated 17/04/2026) |
| STT (exercise) | **0.15%** (31 Mar 2026 tak 0.125%) | Exercise hua option: intrinsic value par; purchaser deta hai | 1 Apr 2026 | Same NSE circular + NSE investor page ("On Intrinsic value w.e.f. 01.09.2019") |
| **NSE transaction charge** | **0.03553%** (Rs 3,552.99 txn + Rs 0.01 IPFT = Rs 3,553 per crore, each side) | Premium turnover, buy aur sell dono | **1 Mar 2026** | NSE circular NSE/FA/73061 (27 Feb 2026) |
| NSE txn (pehle) | Rs 3,503 txn + Rs 50 IPFT = Rs 3,553/crore | — | 1 Oct 2024 se 28 Feb 2026 | Same circular ("Existing outflow") |
| **BSE transaction charge (Sensex options)** | **0.0325%** (Rs 3,250/crore premium) | Premium turnover, dono side | 1 Oct 2024 | Upstox + Zerodha charges pages; Business Standard (27 Sep 2024). BSE notice khud nahi khula (verify nahi hua) |
| SEBI turnover fee | 0.0001% (Rs 10/crore) | Turnover, dono side | — | NSE investor page "SEBI Turnover Fees, STT and Other levies" |
| Stamp duty | 0.003% | Sirf buy side, premium par; buyer deta hai | 1 Jul 2020 | NSE investor page "Stamp Duty" (Finance Act 2019 amendment) |
| GST | 18% | Brokerage + exchange txn (+IPFT). Zerodha SEBI fee ko bhi base mein ginta hai; Upstox page nahi likhta. Script conservative hai (SEBI fee bhi base mein) | — | NSE investor page (GST 18% on stockbroker services); upstox.com/brokerage-charges; zerodha.com/charges |
| IPFT (NSE) | Rs 0.01/crore (ab txn ke andar) | Premium | 1 Mar 2026 | NSE/FA/73061 |
| Clearing charge (alag) | Upstox aur Zerodha pages par koi alag row nahi | — | — | verify nahi hua ki koi aur charge nahi |

**Budget 2026 ka jawab (verify hua):** Haan, badla. Budget 1 Feb 2026 ko pesh hua, Finance Act 2026 ko 30 Mar 2026 ko Presidential assent mila, aur naye STT rate 1 Apr 2026 se lage: option sale 0.10% se 0.15%, exercise 0.125% se 0.15%, futures sale 0.02% se 0.05%. Primary source: NSE circular NSE/FATAX/73524 (Circular Ref 02/2026), jo Finance Act 2026 quote karta hai.

**Backtest ke liye date-aware rates zaroori:** purane data par purane rate lagne chahiye. Verified points: STT sale 0.10% (31 Mar 2026 tak, NSE circular), 0.15% (1 Apr 2026 se). 1 Oct 2024 se pehle ke rate (STT 0.0625%, NSE txn 0.0495%) sirf Zerodha bulletin (28 Sep 2024) ke snippet mein dikhe: **verify nahi hua** primary se.

### Contract details (bot ke liye)

| Index | Lot (abhi) | Tick | Freeze qty | Expiry (abhi) | Source |
|---|---|---|---|---|---|
| NIFTY | 65 | Rs 0.05 | 1,755 | Weekly Tuesday; holiday ho toh pichla trading din | NSE `fo_mktlots.csv` (last-modified 30 Oct 2026); Upstox `NSE.json.gz` (8 Nov 2026); NSE bhavcopy 06 Nov 2026 |
| BANKNIFTY | 30 | Rs 0.05 | 900 | Sirf monthly (last Tuesday); weekly nahi | Same |
| SENSEX | 20 (Nov/Dec 2026); 25 (Jan 2027 contracts se, master mein) | Rs 0.05 | 1,000 | Weekly Thursday | Upstox `BSE.json.gz` (8 Nov 2026). Lot 25 ka BSE notice verify nahi hua |

Holiday shift ka asli udaharan: NSE bhavcopy (06 Nov 2026) mein NIFTY expiry **2026-11-09 (Mon)**, **2026-11-23 (Mon)** aur **2027-01-25 (Mon)** hai, Tuesday nahi. Matlab weekday ginkar expiry nikaalna galat hoga.

---

## 2. Formula + 3 udaharan

### Formula (ek round trip = 1 buy order + 1 sell order, usi din)
```
Q        = lots x lot_size
B        = buy_price  x Q          (buy premium turnover)
S        = sell_price x Q          (sell premium turnover)
Brokerage= Rs_per_order x (buy_orders + sell_orders)
STT      = 0.15%   x S
Txn      = 0.03553% x (B+S)   [NSE]   ya   0.0325% x (B+S) [BSE]
SEBI     = 0.0001% x (B+S)
Stamp    = 0.003%  x B
GST      = 18% x (Brokerage + Txn + SEBI)
Kul kharcha = Brokerage + STT + Txn + SEBI + Stamp + GST
Net P&L  = (S - B) - Kul kharcha - Slippage

Breakeven sell price (slippage ke bina):
  F   = Brokerage x 1.18
  v_b = 0.003% + (txn + 0.0001%) x 1.18
  v_s = 0.15%  + (txn + 0.0001%) x 1.18
  P_be = ( P_buy x (1 + v_b) + F/Q ) / (1 - v_s)
```
Dhyan: agar ek order kai tukdon mein (order slicing) ya cancel karke dobara lagaya jaaye aur har ek execute ho, toh har executed order par brokerage lagegi. Script mein `orders_per_side` isi ke liye hai.

### 3 udaharan (script ka output, 1 lot, Rs 20/order brokerage)

| Udaharan | Lot | Buy -> Sell | Gross P&L | Brokerage | STT | Txn | Stamp | GST | **Kul kharcha** | % of buy premium | **Net P&L** | Breakeven (premium pts) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nifty50 | 65 | 200 -> 220 | +1,300.00 | 40.00 | 21.45 | 9.70 | 0.39 | 8.95 | **80.52** | 0.62% | **+1,219.48** | +1.20 (24 ticks) |
| BankNifty | 30 | 300 -> 280 | -600.00 | 40.00 | 12.60 | 6.18 | 0.27 | 8.32 | **67.39** | 0.75% | **-667.39** | +2.29 (46 ticks) |
| Sensex | 20 | 200 -> 240 | +800.00 | 40.00 | 7.20 | 2.86 | 0.12 | 7.72 | **57.91** | 1.45% | **+742.09** | +2.83 (57 ticks) |
| Sensex (lot 25, Jan 2027 se) | 25 | 200 -> 240 | +1,000.00 | 40.00 | 9.00 | 3.57 | 0.15 | 7.85 | **60.58** | 1.21% | **+939.42** | +2.35 (47 ticks) |

(SEBI fee har case mein 1 paisa se 3 paise hai, isliye column mein nahi dikhaya.)

**Brokerage badalne par kul kharcha (Rs):**

| Scenario | Nifty | BankNifty | Sensex (20) |
|---|---|---|---|
| API promo Rs 10/order (31 Dec 2026 tak) | 56.92 | 43.79 | 34.31 |
| Standard Rs 20/order | 80.52 | 67.39 | 57.91 |
| Upstox Plus Rs 30/order | 104.12 | 90.99 | 81.51 |

**Breakeven move (index points, sirf andaza):** ATM delta ~0.5 maan kar, Nifty ~2.4 index points, BankNifty ~4.6, Sensex ~5.7 (Rs 20 brokerage, slippage ke bina). Delta ka 0.5 hona ek maanyata hai, sach nahi.

**Seekh:**
- 1 lot mein brokerage fixed hai, isliye chhote premium/chhote lot (Sensex) mein % kharcha zyada hai. Kharcha_Filter ko % nahi, rupaye mein dekhna chahiye.
- Slippage har side 1 tick = Nifty Rs 6.50, BankNifty Rs 3.00, Sensex Rs 2.00 round trip mein (1 lot). 4 tick/side = Nifty Rs 26.00. Script mein poori sensitivity table hai.
- Date-aware: 1 Apr 2026 se pehle STT 0.10% tha. Nifty udaharan mein purane rate se STT Rs 14.30 hota (Rs 7.15 kam).
- Agar position expiry tak ITM reh jaaye toh exercise STT 0.15% of intrinsic value lagega aur broker ke exercise/square-off charge bhi ho sakte hain (Upstox ka exercise brokerage: verify nahi hua). Bot intraday exit karta hai, par failure ke case mein yeh risk hai.

---

## 3. Slippage evidence

**Pakki baatein:**
- Tick size Rs 0.05 teeno index options mein (Upstox instrument master, 8 Nov 2026: `tick_size` 5.0 paise).
- Upstox WebSocket `full` mode mein 5-level depth milti hai (Plus mein `full_d30` 30-level). Normal account: 2 connections, `full` mode mein 2,000 instruments tak (Upstox API docs, v3 market data feed).

**Public study:** NSE/BSE/SEBI ki koi rigorous study nahi mili jo Nifty/BankNifty/Sensex ATM option ka bid-ask spread time-of-day ke hisaab se de. Jo mila woh kamzor aur aapas mein takraata hai:

| Source | Daawa | Bharosa |
|---|---|---|
| onetradejournal.com/glossary/bid-ask-spread (19 Jun 2026) | Nifty weekly ATM "often just 25 to 50 paise"; OTM/far month "2 to 5 rupee"; khud "illustrative" likhta hai | Kamzor, data source nahi |
| navia.co.in/blog/what-is-bid-ask-spread | BankNifty ATM weekly call Rs 1.00 – 2.00 | Kamzor; BankNifty weekly ab hai hi nahi |
| bankniftyoptions-com.pages.dev (Nifty vs BankNifty) | ATM current expiry Rs 1–2, next week Rs 2–4, monthly Rs 3–5 | Kamzor, data source nahi |
| equitiesindia.com glossary; tradingqna thread "Why SENSEX options feel inefficient" | Sensex spread "historically wider" than Nifty | Kamzor, number nahi |

**Humne khud try kiya:** NSE ki official sample file (Historical Trade Data, F&O order-book snapshot `FAO_OB_30122024_11.DAT`, 30 Dec 2024) se Nifty ATM spread nikalne ki koshish ki. Natija: book **crossed** tha (bid > ask, jaise 23850CE bid 111.70 / ask 110.65) aur "11 baje" ke snapshot mein 13:41 tak ke timestamps the. Isliye yeh sample spread ke saboot ke liye bekaar hai (sample shayad badla hua ho). Seekh: kisi bhi depth/snapshot data par "crossed book" aur "timestamp" check pehle lagao (dekho section 5).

**Andaza (koi source nahi; sirf conservative shuruaat, Paper mein badalna hai):**
- Normal ghante, ATM/near-ATM: Nifty weekly 2 tick/side, BankNifty monthly 4 tick/side, Sensex weekly 4 tick/side.
- Expiry din dopahar, khabar/event ke waqt, 9:15–9:20: upar ka 2 se 5 guna.
- Backtest ko 1, 2, 4, 10 tick/side ki poori grid par chalana; agar strategy sirf 0–1 tick par hi munafa deti hai, toh use kamzor maano.

**Naapne ka plan:**
1. **Phase 2 (paisa nahi lagega):** Upstox WebSocket `full` mode se teeno index ke current expiry ke ATM±5 strikes (CE+PE) aur futures ka har message raw save karo. Kam se kam 4 hafte, jismein har index ke 4+ expiry din aur 1+ event din ho.
2. Har strike, har minute ke liye nikaalo: spread (ticks aur % of mid), top-5 depth qty (lots mein) dono taraf, aur 1 lot ko turant khareedne/bechne ka "walk-the-book" kharcha. Time bucket (9:15–9:30, ..., 15:00–15:30), moneyness, days-to-expiry, expiry/non-expiry ke hisaab se percentiles (median, p90, p99).
3. **Paper stage:** har signal par asli book se "agar abhi order lagta toh kya fill hota" record karo; backtest fill model se milao.
4. **Stage 2 (1 lot asli):** asli fill price aur time ko model se milao. Paimana (prastaavit): median farak ≤ 1 tick aur p90 farak tay limit ke andar; warna slippage parameter badlo.
5. Sensex ke liye agar budget ho toh BSE order book history (1–2 mahine) se bhi calibrate karo (section 6).

---

## 4. Data vendors table

Price GST/tax ke bina hai jab tak alag na likha ho. "Dekha" sab 10 Nov 2026.

| Source | Kya milta hai | Kitne saal | Granularity | Expired contracts | Depth | Format / delivery | Licence / terms | Price | Source |
|---|---|---|---|---|---|---|---|---|---|
| **NSE Data & Analytics: Historical Trade Data (F&O)** | Har trade, Bhavcopy, Masters, Circulars; spec ke mutabik din mein 5 order-book snapshots (11,12,13,14,15 baje) | Spec 2003 se data batata hai; kitna bechte hain: verify nahi hua | Tick (trade level) | Haan (saare contracts) | Sirf snapshot (5/din), wo bhi sample mein kharab mila | .gz text, pipe-delimited | Undertaking (stamp paper, notary): sirf internal use, redistribution nahi, **"not be exploited ... for any commercial purposes or for deriving any financial gains or profits"** aur "virtual trading or simulation" platforms par use nahi. Bot ke liye allowed hai ya nahi: NSE se likhit clarification zaroori | **Rs 1,10,000 per annum/site** (tariff lagu 1 Apr 2026). "Per annum" = 1 saal ka data ya 1 saal subscription: verify nahi hua | NSE tariff PDF (Domestic, 1 Apr 2026); nseindia.com/market-data/eod-historical-data-subscription; spec Data_Details_F_n_O.pdf; NDAL Historical Trade Undertaking .doc |
| **NSE Historical Order & Trade Data (F&O)** | Har order message (add/modify/cancel) + har trade. Isse poori order book (top 5 bhi) dobara banayi ja sakti hai | Verify nahi hua | Tick (order level, jiffy time) | Haan | Haan (reconstruct karke) | SFTP / downloader / AWS S3 Mumbai; Order data 90 din lag, Trade 30 din lag; "trim version" 18 May 2026 se | Same type ki NSE terms | **Rs 12,50,000 per annum** single site (Rs 31,30,000 global) | NSE tariff PDF; NSE spec "Historical Order and Trade" v1.19 (3 Aug 2026) |
| NSE 1-min Snapshot (F&O) | Real-time snapshot feed (historical nahi) | — | 1 min | — | — | — | Display/vending ke liye | Rs 16,00,000/annum | NSE tariff PDF |
| **NSE free archives** | F&O UDiFF bhavcopy (har contract: OHLC, close, settle, OI, volume, lot `NewBrdLotQty`, expiry), participant-wise OI aur volume, `fo_mktlots.csv`, index closes; India VIX history page | Roz ka (bhavcopy mein purana data bhi) | Daily (EOD) | Haan (us din tak) | Nahi | CSV/ZIP | NSE website terms (bulk/automatic download ki ijaazat: verify nahi hua) | Rs 0 | Files khud download karke check kiye: `fao_participant_oi_06112026.csv`, `BhavCopy_NSE_FO_0_0_0_20261106_F_0000.csv.zip` (200 OK) |
| **BSE Historical (Equity & Index Derivatives)** | Trade Book history; Order Book history; Combined | BSE product page ke mutabik tick data 2003 se (search snippet; verify nahi hua) | Tick | Haan (anumaan) | Order Book se haan | Verify nahi hua | "Each legal entity counted separately" | Trade Book **Rs 47,000/month** ya Rs 4,70,000/annum; Order Book same; Combined Rs 78,000/month ya Rs 7,80,000/annum | BSE "Information Products Domestic Tariff Sheet" (Feb 2025; file last-modified 11 Nov 2025) |
| **Upstox (apna broker)** | (a) Historical Candle V3: active instruments; (b) Expired Instruments API: expired options/futures ki candles + OI; (c) WebSocket live depth | (a) minutes/hours Jan 2022 se, daily Jan 2000 se; (b) Upstox team (May 2025): "last six months", aage 2 saal ka plan; user ke mutabik Sensex ki sabse purani expiry 2024-10-04 (verify nahi hua) | 1/3/5/15/30 min, day | (b) Haan, sirf Upstox Plus | Live 5-level (`full`), 30-level Plus | JSON API | Upstox API terms: verify nahi hua | Rs 0 (Plus abhi free) | upstox.com/developer/api-documentation (v3 historical candle, expired historical candle, market data feed); community.upstox.com threads |
| Dhan (DhanHQ) | Expired options "rolling" (ATM ke relative strike): index near expiry ATM±10, baaki ATM±3; OHLC, volume, **OI, IV, spot** | "Up to the last 5 years" | 1/5/15/25/60 min | Haan (rolling form mein, har strike alag contract nahi) | Nahi (docs mein) | JSON API, 30 din per call | Verify nahi hua | Data API Rs 499 (har 30 din, secondary source); Dhan account chahiye | dhanhq.co/docs/v2/expired-options-data; dhanhq.co/trading-apis; onetradejournal (14 Oct 2026) |
| ICICI Breeze | "3 years of second level LTP data", "3 years of Futures and Options historical data" | 3 saal | 1 sec LTP, 1 min, day | Expired options coverage pakka nahi | Nahi | API | Verify nahi hua | Rs 0 ("No charges ... for access to the historical data"); ICICI Direct account chahiye | api.icicidirect.com/apiuser/home |
| Zerodha Kite Connect | Historical candles | "Several years" | 1 min+ | Expired options intraday **nahi** ("We don't provide historical data for expired options instruments", staff, Mar 2020; Oct 2026 secondary bhi yahi kehta hai) | Nahi | API | — | Connect Rs 500/app/month (secondary) | kite.trade forum discussion 7294; onetradejournal (14 Oct 2026) |
| Fyers | Historical API | Minute history 3 Jul 2017 se (secondary) | Seconds (30 din), minutes, day | Pakka nahi | Nahi | API | — | Free (secondary) | onetradejournal (14 Oct 2026) |
| TrueData | Velocity (live + backfill); tick add-on "5/10/20 Days"; REST default: tick 5 din, bars 6 mahine | Bulk expired options history ka public page nahi mila | Tick, 1 min | Verify nahi hua | L1 (anumaan) | Software/API (API alag approval) | Verify nahi hua | Velocity Rs 1,699–3,299/m; bulk historical: quote maangna | truedata.in/price; feedback.truedata.in KB |
| Global Datafeeds (GDFL) | "After Market Data": "Periodicity: Tick, 1minute", "Data of entire exchange", CSV/NinjaTrader | Verify nahi hua | Tick, 1 min | Verify nahi hua | Verify nahi hua | CSV | Verify nahi hua | Public price nahi; purana forum (2021): 1-min FnO ~Rs 17.7k/saal incl GST (purana, verify nahi hua) | globaldatafeeds.in/products; kite.trade forum |
| Accelpix | "15+ Years of history", "Tick By tick, level 1", "OI adjusted with the price" | 15+ saal (claim) | Tick L1 | Verify nahi hua | L1 hi | API / bulk (institution) | "Commercial licensing" institution tier | Plans "from ₹1,599 per month + GST, one segment"; bulk: contact | accelpix.com |
| NSE Indices (niftyindices.com) | Current constituents CSV; monthly weightage reports | Purane monthly files ki uplabdhta: verify nahi hua | Monthly | — | — | CSV/PDF | — | Rs 0 (current) | Secondary (tradingqna, marketcalls) |

### Zarooraton ke hisaab se mapping

| Zaroorat | Kahan se | Note |
|---|---|---|
| (1) Index options tick ya 1-min OHLCV + OI, expired, saare strikes | NSE Historical Trade Data (tick, Nifty+BankNifty); Upstox Plus expired candles (1-min + OI, Oct 2024 ke aas-paas se?); vendor 1-min; Dhan rolling (sirf ATM ke aas-paas) | Trade data mein intraday OI nahi hota; EOD OI bhavcopy se. Intraday OI ke liye Upstox/vendor/Dhan candles |
| (2) Option chain snapshots (OI, IV) | 1-min candles ka OI + IV khud nikaalo (option price + futures/spot se Black-76) | IV kharidne ki zaroorat nahi. Exchange OI kitni der mein update hota hai: verify nahi hua, data se naapo |
| (3) Market depth history (top 5) | NSE Order & Trade (Rs 12.5 lakh/saal), BSE Order Book (Rs 47k/mahina); warna khud record karo (Upstox `full`) | Vendors mostly L1 dete hain |
| (4) Futures 1-min | Upstox V3 (current), Upstox expired futures (Plus); NSE trade data mein futures bhi | VWAP ke liye volume chahiye |
| (5) India VIX history | NSE "Historical Data - India Vix" page (free, daily); intraday 1-min broker API se (VIX ke liye V3 kaam karega: verify nahi hua) | |
| (6) Participant-wise OI daily | NSE archives `fao_participant_oi_DDMMYYYY.csv` (free) | 06 Nov 2026 ki file khud check ki |
| (7) Index constituents/weights history | niftyindices.com (Nifty 50, Nifty Bank); Sensex ke liye BSE/Asia Index | Survivorship bias se bachne ke liye har date ka sahi constituent list chahiye |
| (8) Corporate actions | NSE corporate actions page (free) | Sirf breadth (stocks) ke liye; index options par seedha asar nahi |
| Breadth (index ke stocks 1-min) | Upstox V3 (equities, minutes Jan 2022 se) | Free |

---

## 5. Data quality checklist (har dikkat + kaise check karein)

| # | Dikkat | Kaise check karein |
|---|---|---|
| 1 | **Missing strikes** | Us din ki NSE bhavcopy mein jitne contracts hain (zero-volume wale bhi), unse vendor data milao. Coverage % per din/expiry nikaalo; ATM±10 mein 100% chahiye. Upstox forum par bhi "missing strikes" ki shikayat hai (BSE_FO 24-12-2025) |
| 2 | **Illiquid strike ke stale prints** | Har bar ka "last trade time" ya volume dekho. Volume 0 wala bar ya N minute se purana LTP = stale. Stale price par kabhi fill mat do |
| 3 | **Bad ticks** | Price ≤ 0; ek tick mein bahut bada jump bina volume ke; **crossed book (bid > ask)**; trading hours ke bahar timestamp; timestamps ulte kram mein. NSE sample mein crossed book sach mein mila |
| 4 | **Pre-open** | NSE spec v1.17 (8 Dec 2025) ne FAO order/trade data mein Pre-Open "PO" status joda. 9:00–9:15 ke records ko alag rakho |
| 5 | **OI update frequency** | Har minute OI badla ya nahi, iska % nikaalo; EOD OI ko bhavcopy ke OI se milao. Exchange ka asli update interval: verify nahi hua |
| 6 | **Lot size changes** | Har contract ka lot bhavcopy `NewBrdLotQty` / contract master se lo. Itihas: 20 Nov 2024 se Nifty 25→75, BankNifty 15→30 (NSE/FAOP/64625); beech mein BankNifty 35 hua (kab: verify nahi hua); Nifty 75→65, BankNifty 35→30 (NSE/FAOP/70616, 3 Oct 2025; weekly/monthly 30 Dec 2025 expiry ke baad); Sensex 10→20 (BSE notice 20241021-13, Angel One ke mutabik); Sensex 20→25 Jan 2027 contracts (Upstox master; verify nahi hua). SEBI ka semi-annual revision niyam (SEBI/HO/MRD-PoD2/CIR/P/2024/00181, 30 Dec 2024) hai, toh aage bhi badlega |
| 7 | **Expiry weekday changes** | Kabhi weekday se mat ginna; bhavcopy ke `XpryDt`/`FininstrmActlXpryDt` se calendar banao. Itihas (secondary sources): Nifty weekly Thursday → Tuesday 1 Sep 2025 se; Sensex weekly Friday → Tuesday 1 Jan 2025 (3 Jan 2025 wala Friday hi raha) → Thursday 1 Sep 2025 se; BankNifty weekly SEBI ke 1 Oct 2024 circular ("ek exchange, ek benchmark weekly") ke baad band; BankNifty monthly ab last Tuesday |
| 8 | **Holiday shift** | Bhavcopy 06 Nov 2026: Nifty expiry Mon 9 Nov 2026, Mon 23 Nov 2026, Mon 25 Jan 2027. Holiday list NSE circular se; har expiry ko contract master se confirm karo |
| 9 | **Special sessions** | Budget din Sunday 1 Feb 2026 ko live session hua (Zerodha bulletin, NSE circular ka hawala); Muhurat trading (chhota session); BCP/DR "special live sessions" mein volume kam (NSE spec FAQ). Inhe flag karke training se alag rakho |
| 10 | **Sensex weekly itihas** | BSE ne Sensex/Bankex derivatives May 2023 mein dobara launch kiye (Business Standard, 15 May 2023). Isse pehle data patla. Expiry regime 3 baar badla (Fri → Tue → Thu), toh har regime alag test karo |
| 11 | **Regime/niyam badlav** | 20 Nov 2024 (contract size 15–20 lakh, weekly ek index), 1 Feb 2025 (upfront premium), 1 Sep 2025 (expiry din), 1 Mar 2026 (NSE txn+IPFT), 1 Apr 2026 (STT). Cost model aur walk-forward windows date-aware ho |
| 12 | **Timestamps / timezone** | Upstox candles "+05:30" ke saath; NSE order/trade data "jiffy" time (spec section 4) ko convert karo; spot, futures aur options ka time align karo |
| 13 | **Survivorship** | Expired contracts aur purane index constituents dono dataset mein hone chahiye |
| 14 | **Vendor vs exchange cross-check** | Har din vendor ke 1-min data se banaya daily OHLC/volume ko NSE/BSE bhavcopy se milao; farak > tolerance toh us din ko flag karo |

---

## 6. 10 lakh mein kharid ki salah (priority)

Pehle sabse zaroori baat: **walk-forward ke liye sabse kaam ka data Nov 2024 ke baad ka hai** (naya lot size, BankNifty weekly band), aur expiry-din ke niyam ke liye Sep 2025 ke baad ka (Tuesday/Thursday). Isliye 2 saal (Nov 2024 se ab tak) "core" data hai; purana data sirf robustness check ke liye.

| Priority | Kya | Kharcha (andaza) | Kyun |
|---|---|---|---|
| P0 | Free: NSE F&O bhavcopy, participant OI, fo_mktlots, India VIX history, index closes, NSE/BSE circulars, niftyindices constituents; Upstox V3 1-min (index, futures, stocks) | Rs 0 | Calendar, lot, expiry, EOD OI, breadth, VIX ki neev. Vendor data ko check karne ka paimana |
| P0 | **Khud depth record karna** (Upstox WebSocket `full`, 5-level) Phase 2 se | Rs 0 + VPS | Depth itihas ka sabse sasta aur bot ke apne broker jaisa source; fill model calibration ka asli raasta |
| P0 | Upstox Plus Expired Instruments API test (1-min + OI; NSE_FO, BSE_FO dono check) | Rs 0 (abhi free) | Agar Oct 2024 se data poora mila toh core 2 saal ka 1-min data free mein. Plus sirf data ke liye on karke, trading ke liye Basic par wapas aa sakte hain (24 ghante cooling-off) |
| P1 | **NSE Historical Trade Data (F&O)**, 2 saal (Nov 2024–Oct 2026) | ~Rs 2,20,000 + 18% GST ≈ **Rs 2,60,000** (agar "per annum" = 1 saal ka data) | Har trade, saare strikes, expired bhi, official. Tick se apne 1-min bars, VWAP, trade-through fill rule. **Shart:** licence ki "commercial use" line par NSE se likhit haan |
| P2 | Ek vendor ka 1-min OHLCV+OI (NSE + BSE options, expired, saare strikes) 2–3 saal | Budget cap ~Rs 1,00,000 (quote maangna; public price nahi) | Tez iteration aur NSE data se cross-check; Sensex ke liye khaas zaroori agar Upstox BSE_FO kam pade |
| P3 | **BSE Order Book history** (Equity & Index Derivatives), 2 recent mahine | 2 x 47,000 = 94,000 + GST ≈ **Rs 1,11,000** (agar "per month" = 1 mahine ka data) | Sensex ki depth/fill calibration; NSE ka order book bahut mehenga hai |
| P4 | Sensex trades: BSE Trade Book 3 mahine (sirf agar P0/P2 se Sensex data kam pade) | 3 x 47,000 + GST ≈ Rs 1,66,000 | Sensex tick-level verification |
| Reserve | NSE se 1 mahine ka Order & Trade data ka custom quote (agar bechte hon); storage/compute (AWS S3 Mumbai) | ~Rs 2,00,000–3,00,000 | Nifty/BankNifty depth ka ek official namuna; delivery cloud par hoti hai |

**Kul (P0–P4): lagbhag Rs 6–7 lakh**, baaki buffer. Sab number andaza hain; har vendor se likhit quote, saal/mahine ka matlab aur licence terms lene ke baad hi kharidna.

**Kharidne se pehle NSE (marketdata@nse.co.in, +91-22-2659 8385) se poochna:**
1. "Per annum/site" ka matlab: ek saal ka data ya ek saal ki subscription?
2. Kaun se saal milte hain; kya F&O "Snapshots" folder (5 order-book snapshots/din) ab bhi milta hai?
3. Undertaking ki "commercial purposes / financial gains" aur "virtual trading or simulation" lines: kya apne paise se trading bot ka internal backtest allowed hai?
4. Kya 1–2 mahine ka Order & Trade data alag se milta hai?

### Depth history na mile toh fill model kaise approximate hoga
1. **Sirf 1-min OHLCV ho toh:** buy limit tabhi fill maano jab agle bar ka low ≤ limit − 1 tick ho ("touch is not fill"; ek tick trade-through chahiye). Fill price = limit (ya bar ka close + half-spread andaza, jo bura ho). Order qty bar ke volume ka chhota hissa ho (participation cap, jaise ≤10%: andaza). Volume 0 wala bar = koi fill nahi.
2. **Tick trades ho toh (NSE Historical Trade Data):** har trade ka sequence dikhta hai; limit tabhi fill jab us price par ya behtar trade ho aur us price par humse pehle khade qty (andaza) ke barabar volume nikal chuka ho. Bid-ask bounce se spread ka andaza (Roll-type estimator) nikal sakte hain, par yeh andaza hi hai.
3. **Spread/depth parameter** time bucket, moneyness, DTE aur expiry-din ke hisaab se table mein rakho; shuruaat section 3 ke conservative andaze se.
4. **Paper stage mein calibrate:** asli recorded book par simulated fill vs model fill milao; parameter fit karo.
5. **Stage 2 (1 lot asli) mein calibrate:** asli fill price/time vs model; agar model achha nikle (zyada umeed) toh parameter turant pessimistic karo. Model se behtar fill par kabhi bharosa mat karo.

---

## 7. Verify nahi hua (saaf list)

1. BSE Sensex options transaction charge ka **BSE ka apna notice** (site 403 deti hai). 0.0325% broker pages aur Business Standard (Sep 2024) se hai. May 2026 mein BSE ke charge kam karne ka ek secondary daawa (pulse.bot, "Rs 5 per Rs 1 lakh") khul nahi saka; Upstox/Zerodha pages (10 Nov 2026) abhi bhi 0.0325% dikhate hain.
2. Upstox API Rs 10/order **31 Dec 2026 ke baad**; brokerage-charges page aur trading-api page ki tarikhon mein takraav; Upstox Plus ki "free initially" ke baad ki fees.
3. Upstox ka exercised/expired contract par brokerage; "per executed order" mein partial fills ka niyam.
4. GST base mein SEBI fee shamil hai ya nahi (Zerodha haan, Upstox chup). Farak paise ka hai.
5. Sensex lot **25** (Jan 2027 contracts) ka BSE notice; BankNifty lot 30→35 kab hua.
6. 1 Oct 2024 se pehle ke STT (0.0625%) aur NSE txn (0.0495%) rate: sirf secondary (Zerodha bulletin).
7. NSE/BSE historical tariff mein "per annum"/"per month" ka asli matlab, kaun se saal milte hain, aur NSE licence ki commercial-use pabandi bot par lagti hai ya nahi.
8. Upstox expired data kitna purana (6 mahine? Oct 2024 se?) aur BSE_FO support; Upstox API data terms.
9. TrueData, GDFL, Accelpix ke bulk historical options data ke daam (public nahi); GDFL ka 2021 forum price purana hai.
10. Dhan Data API ka exact daam/period aur BSE support; ICICI Breeze mein expired options intraday.
11. ATM spread ke asli number (koi rigorous study nahi mili); exchange OI update frequency.
12. 9 Nov / 24 Nov 2026 holiday ki wajah (sirf bhavcopy expiry dates se nikala hai).
13. niftyindices par purane monthly constituents files abhi bhi download hote hain ya nahi; Sensex constituents itihas ka source.
14. NSE website archives ko automatic download karne ki terms.
15. Sensex launch ki exact tarikh (15 May 2023 sirf Business Standard URL se).

---

## 8. Sources (sab dekha: 10 Nov 2026)

**Primary / official**
- NSE circular NSE/FATAX/73524, 31 Mar 2026 (STT, Finance Act 2026): https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf
- NSE circular NSE/FA/73061, 27 Feb 2026 (Transaction charges + IPFT, lagu 1 Mar 2026): https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- NSE investor page, SEBI fee/Stamp/GST/STT (updated 17/04/2026): https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies
- NSE investor page, Stamp Duty (updated 03/10/2023): https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes
- NSE market lots file (last-modified 30 Oct 2026): https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv
- NSE circular NSE/FAOP/70616, 3 Oct 2025 (lot revision): https://nsearchives.nseindia.com/content/circulars/FAOP70616.pdf
- NSE circular NSE/FAOP/64625, 18 Oct 2024 (lot revision, SEBI 1 Oct 2024 circular): https://nsearchives.nseindia.com/content/circulars/FAOP64625.pdf
- NSE F&O bhavcopy 06 Nov 2026: https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20261106_F_0000.csv.zip
- NSE participant OI 06 Nov 2026: https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_06112026.csv
- NSE Data & Analytics page (tariff link, updated 24/04/2026): https://www.nseindia.com/nse-data-and-analytics/data-information-vending
- NSE tariff PDF (Domestic, lagu 1 Apr 2026): https://nsearchives.nseindia.com//web/mediaattachment/2026-04/Download_Pricing_file_-_Domestic_clients_20260424122229.pdf
- NSE paid historical data page (updated 02/09/2026): https://www.nseindia.com/market-data/eod-historical-data-subscription
- NSE Historical Order & Trade spec v1.19 (3 Aug 2026): https://nsearchives.nseindia.com//web/mediaattachment/2026-09/NSE_Hist_Order_Trade_Data_1.19_20260902144045.pdf
- NSE F&O Trade Data spec: https://nsearchives.nseindia.com/content/press/Data_Details_F_n_O.pdf
- NSE F&O sample files: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Download%20Sample%20Files%20for%20F%26O.zip
- NSE Historical Trade Undertaking: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NDAL-v.2024-Historical%20Trade%20Undertaking.doc
- BSE Information Products Domestic Tariff Sheet (Feb 2025): https://www.bseindia.com/downloads1/Information_Products_Pricing_Sheet.pdf
- SEBI circular 1 Oct 2024 (index derivatives framework): https://www.sebi.gov.in/legal/circulars/oct-2024/measures-to-strengthen-equity-index-derivatives-framework-for-increased-investor-protection-and-market-stability_87208.html (page khud nahi khola; NSE circular FAOP64625 isko quote karta hai)

**Broker (Upstox aur doosre)**
- Upstox brokerage charges: https://upstox.com/brokerage-charges/
- Upstox trading API (Rs 10/order till 31 Dec 2026, APIs free, rate limits): https://upstox.com/trading-api/
- Upstox Plus T&C: https://upstox.com/help-center/what-are-the-terms-and-conditions-for-upstox-plus-264073/
- Upstox community, Rs 10 extension till Mar 2026 (31 Dec 2025): https://community.upstox.com/t/stay-ahead-of-the-curve-we-re-extending-10-order-api-pricing-till-march-2026/13277
- Upstox Historical Candle V3: https://upstox.com/developer/api-documentation/v3/get-historical-candle-data/
- Upstox Expired Historical Candle: https://upstox.com/developer/api-documentation/get-expired-historical-candle-data/
- Upstox Expired Instruments announcement: https://upstox.com/developer/api-documentation/announcements/expired-instruments-api/
- Upstox Market Data Feed V3: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- Upstox community, expired data availability (May 2025): https://community.upstox.com/t/historical-availability-retrieval-limit-per-query-for-expired-options-contract/9245
- Upstox community, Sensex earliest expiry 2024-10-04: https://community.upstox.com/t/getting-historical-f-o-data-before-first-expiry-2024-10-04/9491
- Upstox public instrument masters (8 Nov 2026): https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz , https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz
- Zerodha charges: https://zerodha.com/charges/
- Dhan expired options data: https://dhanhq.co/docs/v2/expired-options-data/ ; https://dhanhq.co/trading-apis
- ICICI Breeze: https://api.icicidirect.com/apiuser/home
- Kite forum (expired options): https://kite.trade/forum/discussion/7294/historical-data-for-expired-option-contracts

**Vendors**
- TrueData price: https://www.truedata.in/price
- Global Datafeeds products/shop: https://globaldatafeeds.in/products/ , https://globaldatafeeds.in/shop/
- Accelpix: https://accelpix.com/

**Secondary (kamzor; sirf sanket ke liye)**
- onetradejournal, broker API comparison (checked 13–14 Oct 2026): https://onetradejournal.com/trading-apis/algo-trading-charges , https://onetradejournal.com/trading-apis/historical-data-api-india
- onetradejournal, bid-ask spread (19 Jun 2026): https://onetradejournal.com/glossary/bid-ask-spread
- Navia, bid-ask spread: https://navia.co.in/blog/what-is-bid-ask-spread/
- Business Standard, BSE txn fee Sep 2024: https://www.business-standard.com/markets/stock-market-news/nse-and-bse-revise-their-transaction-fees-to-comply-with-sebi-circular-124092701207_1.html
- Business Standard, Sensex expiry change Jan 2025: https://www.business-standard.com/markets/stock-market-news/sensex-bankex-sensex-50-expiry-days-to-change-from-january-1-bse-124112801317_1.html
- Business Standard, Sensex/Bankex relaunch May 2023: https://www.business-standard.com/markets/news/bse-relaunches-sensex-bankex-derivatives-contracts-to-boost-trading-123051501206_1.html
- Moneylife, expiry Tue/Thu from 1 Sep 2025: https://moneylife.in/article/nse-equity-fo-contracts-to-expire-on-tuesdays-bse-on-thursdays-from-1st-september/77434.html
- Angel One, Nov 2024 lot table (BSE notice 20241021-13): https://www.angelone.in/announcements/market/revision-in-market-lot-for-index-derivatives-contracts
- Zerodha bulletin, Budget-day session 1 Feb 2026: https://zerodha.com/marketintel/bulletin/439957/special-live-trading-session-on-sunday-february-1-2026
- Zerodha bulletin, Oct 2024 txn/STT revision: https://zerodha.com/marketintel/bulletin/391488/revision-in-transactions-charges-from-1st-october-2024
- BSE earnings call transcript (4 Nov 2026, "charging lower than other participants"): https://uk.investing.com/news/stock-market-news/earnings-call-transcript-bse-posts-strong-h1-2027-growth-as-shares-slip-93CH-4957188
