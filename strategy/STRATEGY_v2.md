# Strategy v2.3: "Pehle Mauka, Phir Premium" (option BUYING, 1 lot)

**Tarikh:** 11 Nov 2026 · **Kisne:** Claude Code · **Haalat:** 3 audit round ke baad (v2 → v2.1 → v2.2 → v2.3). Round ki report: `strategy/AUDIT_ROUNDS.md`.

> **Saaf baat (pehle padho):** profit ki koi guarantee nahi. SEBI ki study ke hisaab se FY25 mein ~91% individual F&O traders nuksan mein the.
> Bharat ke research ke hisaab se option ka implied volatility aam taur par asli chaal se zyada hota hai (variance risk premium),
> yani option **khareedne wala aam taur par zyada daam deta hai**. Isliye yeh strategy tabhi chalegi jab **apne data par backtest + paper** mein
> kharche ke baad munafa **sabit** ho. Sabit na ho toh Real Money nahi. Neeche ke saare "setup" **parikalpana (hypothesis)** hain, sach nahi.

## 1. 2026 ka market (yeh badla, purana plan galat tha)

| Baat | Ab (dekha 11 Nov 2026) | Asar |
|---|---|---|
| Nifty 50 weekly expiry | **Tuesday** (1 Sep 2025 se); monthly = aakhri Tuesday | Nifty trade: Tue expiry |
| Sensex weekly expiry | **Thursday**; monthly = aakhri Thursday | Sensex trade: Thu expiry |
| Bank Nifty | **Weekly band (Nov 2024 se)**, sirf monthly | Monthly ATM ~₹15-27k/lot: **₹15k capital mein aksar nahi aata** |
| Lot size | Nifty **65**, Bank Nifty **30**, Sensex **20** (Dec 2025/Jan 2026 se) | Kharcha aur risk ginti badli |
| STT (option bechne par) | **0.15%** premium ka (1 Apr 2026 se; pehle 0.10%) | Har trade mehenga |
| Brokerage (Upstox) | ₹20/order | 2 order = ₹40 + GST |
| Exchange charge, SEBI fee, stamp | **verify nahi hua** (code mein andaza, `CostModel.unverified()`) | Real Money se pehle contract note se pakka |
| Chhutti par expiry shift | **verify nahi hua** (list nahi jaanchi) | Bot roz broker ki instrument list se expiry lega |

**Faisla:** trade sirf **Nifty 50 aur Sensex** (weekly). **Bank Nifty sirf signal/breadth** ke liye (code: `SPECS["BankNifty"].tradable = False`).

## 2. Edge kahan se aa sakta hai (aur kahan se nahi)
- **Nahi:** roz kuch na kuch khareedna. VRP ke kaaran lambe samay mein yeh ghaate ka khel hai.
- **Shayad (test karna hai):**
  1. **Trend wale din** ki tez chaal pakadna, jab asli chaal implied se badi ho.
  2. **Intraday momentum:** US research mein pehle aadhe ghante ka return aakhri aadhe ghante ko batata hai (Gao et al.). Doosre markets mein mila-jula natija. Nifty par test karna hai.
  3. **Kam samay hold karna** (theta ka nuksan kam).
- Opening Range Breakout par khula backtest (GitHub) Nifty options mein positive dikhata hai. Par author ne khud lookahead bug maana, aur ek doosre test mein stocks par ORB random se behtar nahi tha. **Isliye ORB bina filter ke nahi.**

## 3. Strategy ki 5 parat (layers)

### Parat 0: No-trade (koi bhi ek sach ho toh aaj/abhi entry nahi)
- Din ki nuksan seema tay nahi (Settings) ya poori ho gayi; lagatar 2 haar; aaj 2 entry ho chuki.
- Pehle se ek position khula hai: **ek samay par sirf 1 lot** (Nifty aur Sensex dono saath nahi; dono ek hi taraf chalte hain, risk double ho jata).
- India VIX din mein **≥ 8%** uchhla (dar ka mahaul).
- **Event din:** RBI policy, Budget, US Fed, bade results (HDFC Bank, Reliance, ICICI, Infosys, TCS). Calendar bot ko roz subah chahiye (source tay karna baaki).
- Data purana (`Data_Purana_Hadd`), feed toota, token khatam, ghadi galat.
- Gap > 1% wala din: pehle 30 min koi entry nahi.
- **Expiry din 13:30 ke baad** naya entry nahi.
- Pehle 15 min (9:15-9:30) entry nahi.

### Parat 1: Din ka mausam (regime)
Har 5 min par: (a) opening range (9:15-9:30) ki chaudai vs pichhle 10 din ka average; (b) futures VWAP ke upar/neeche; (c) EMA 9/21 (5 min) ka jhukav; (d) breadth: vazan mein top 10 stocks mein se kitne usi taraf.
- **Trend-up / Trend-down:** b, c, d teeno ek taraf, aur d ≥ 7/10. Sirf isi mein entry.
- **Range:** baaki sab. Koi entry nahi (yahi sabse bada bachav hai).

### Parat 2: Setup (har setup alag parikalpana, alag backtest)
| ID | Setup | Entry | Underlying SL |
|---|---|---|---|
| S1 | ORB + retest | 5-min candle range ke bahar **band** ho, agli candle(s) mein retest hold ho, VWAP usi taraf. **Entry agli candle par** (lookahead se bachav) | Range ke andar wapas band |
| S2 | VWAP pullback | Trend din mein daam VWAP/EMA21 tak aaye aur trend ki taraf band ho | VWAP ke paar band |
| S3 | Dopahar momentum | 9:15-9:45 ka return aur 13:30 tak ka trend ek taraf ho, toh 13:30-14:45 mein S2 jaisa entry | Pichhla swing |
| S4 | Expiry momentum | **Sirf paper**, tab tak jab tak alag se sabit na ho | — |

### Parat 3: Option chunna (code: `bot/strategy/selection.py`)
- Weekly, sabse paas wali expiry. Expiry din par S4 ke alawa koi nahi.
- Strike: **1-step ITM, phir ATM.** OTM kabhi nahi.
- SL: 25% premium SL aur **chart (underlying) SL × delta**, dono mein jo paas ho. Chart SL door ho toh nuksan seema se upar jaata hai, isliye SKIP (Round 4).
- Har candidate ke liye chaar jaanch:
  1. Spread ≤ 1% (ask ke hisaab se).
  2. OI ≥ 50,000.
  3. 1 lot + kharcha ≤ capital ka 90%.
  4. **SL lagne par nuksan (kharcha samet) ≤ ek-trade ki risk seema.**
- Koi bhi candidate pass na ho toh **SKIP** (wajah log mein). Yahi "premium quality pehle, paisa kam ho toh chupchaap skip" hai.

### Parat 4: Exit (code: `bot/strategy/rules.py`, `on_tick`)
1. **Broker Stop:** entry ke turant baad broker par SL (limit) order (options par SL-M exchange reject karta hai: docs/REGULATORY.md). Ek hi server hai, isliye yeh zaroori hai.
2. **Hard SL:** premium −25% ya underlying SL, jo pehle lage.
3. **Time stop:** 15 minute mein +5% bhi na ho toh nikal jao (theta).
4. **+1R par** SL ko entry par le jao. Uske baad sabse uchi kamai ka 35% wapas jaaye toh exit (trailing).
5. **15:15 hard exit.** Expiry din exercise se bachne ke liye bhi (STT 0.15% exercise par).

### Parat 5: Paisa aur risk (₹15k capital, 1 lot)
- **Risk per trade seema** = min(Settings ki "Din ki nuksan seema" ka 60%, capital ka 6%) → ₹15k par ~₹900.
- Misaal: Nifty ITM premium ₹140 × 65 = ₹9,100. 25% SL par nuksan ~₹2,275, jo ₹900 se **zyada** hai. Is haalat mein:
  - ya underlying SL itna paas ho ki nuksan ₹900 se kam rahe (achhi entry),
  - ya trade **SKIP**.
- **Isliye bahut din trade nahi hoga. Yeh theek hai.**
- Sensex misaal: premium ₹300 × 20 = ₹6,000. 25% SL par ₹1,500. Yahan bhi tight underlying SL chahiye.
- Din: max 2 entry, lagatar 2 haar par band, din ki seema par halt. Kul_Jeb_Nuksan_Seema par bot poori tarah band (malik ka faisla baaki).
- **Kul jeb ka taala (11 Nov 2026, malik: "₹15,000 = ek mahine ki salary, aakhri mauka"):** shuru ke ₹15,000 se kul nuksan
  `Kul_Jeb_Nuksan_Seema` tak pahunche toh bot **hamesha ke liye band**. Din badalne par apne-aap nahi khulta; sirf malik khud kholega.
  Seema tay nahi = koi trade nahi (code: `account_allows_trading`). Claude ka prastaav: **₹4,000** (tab kam se kam ~₹11,000 bachega).
  Faisla malik ka.

## 4. Ganit (kitna jeetna zaroori)
Round-trip kharcha (Nifty, ₹140 premium, 65 qty): ~₹60-75 (andaza; exchange charge verify nahi hua).
Agar risk R = ₹900 aur jeet par +2R, toh breakeven jeet-dar ≈ (1 + kharcha/R) / 3 ≈ **36%**.
Time-stop ke chhote nuksan (−0.3R jaise) yeh dar thoda badalte hain. Backtest mein asli vitaran (distribution) se ginna hai.

## 5. Sabit kaise karenge (Gates)
1. **Data:** M1 recorder se har din Nifty/Sensex index + option chain (ATM ±5) ke 1-min/tick record.
   Historical intraday option data muft nahi milta. Upstox ka expired-instrument history kaam aayega ya nahi: **verify nahi hua**.
2. **Backtest Gate:**
   - ≥ 200 trade (setup-wise alag).
   - Kharche ke baad Profit Factor ≥ 1.3.
   - Max drawdown ≤ capital ka 20%.
   - Walk-forward (6 mahine seekho, 1 mahina jaancho), out-of-sample mein girawat ≤ 30%.
   - Parameters ≤ 6 per setup (overfitting se bachav).
   - Entry hamesha signal candle ke **baad** (lookahead test).
3. **Paper Gate:** live paper mein ≥ 60 trade aur ≥ 3 mahine. Natija backtest ke 70% ke andar ho.
4. **Stage2 Gate:** Real Money mein 1 lot, 1 mahina. Kul nuksan Kul_Jeb seema ke 50% se kam.
5. Koi gate fail: wapas paper. **Malik ka likhit "go" bina Real nahi.**

## 6. Ek server (₹1,500/mahina)
Lightsail Mumbai $12 (~₹1,330). Bot aur Pehredaar usi par, alag service mein (`deploy/`). Bachav broker par SL se hai. Doosra server munafa aane ke baad hi.

## Sources (dekhe 11 Nov 2026)
- Expiry ke din: [Business Standard](https://www.business-standard.com/markets/news/nse-bids-adieu-to-thursday-expiry-as-dates-swap-come-into-effect-explained-125082800635_1.html), [Zerodha support](https://support.zerodha.com/category/trading-and-markets/trading-faqs/f-otrading/articles/weekly-expiries-discontinued-for-certain-index-derivatives), [Angel One](https://www.angelone.in/news/market-updates/why-nifty-expiry-changed-to-tuesday)
- Lot size: [Angel One](https://www.angelone.in/news/market-updates/nse-revises-lot-sizes-for-index-derivatives-from-december-2025-nifty-lot-size-to-reduce-to-65), [Upstox](https://upstox.com/announcements/updates/important-update-changes-in-lot-size-of-derivative-contracts), [Kotak Neo](https://www.kotakneo.com/bulletins/lot-size-changes-in-index-derivatives-effective-december-30-2025/)
- STT 0.15%: [Business Standard](https://www.business-standard.com/markets/news/markets-fm-hikes-stt-on-fo-trades-surprise-move-126020100888_1.html), [ICICI Direct](https://www.icicidirect.com/ilearn/futures-and-options/articles/stt-changes-in-budget-2026-what-f-o-traders-should-know)
- Brokerage: [Upstox help](https://help.upstox.com/support/solutions/articles/248665-what-are-the-brokerage-charges-on-upstox-)
- SEBI FY25 nuksan: [Business Standard](https://www.business-standard.com/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html)
- VRP (India): [Manipal research listing](https://researcher.manipal.edu/en/publications/dynamics-of-variance-risk-premium-evidence-from-india/), [IIM Calcutta WP 688](https://studentlive.iimcal.ac.in/sites/all/files/pdfs/wps_688.pdf)
- Intraday momentum: [Gao et al. (PDF)](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf), [Jin et al. 2020 (RePEc)](https://econpapers.repec.org/RePEc:wly:jfutmk:v:40:y:2020:i:4:p:632-650)
- ORB backtests (sabak): [VKHirehalli/trading-research](https://github.com/VKHirehalli/trading-research), [systronics/nifty200-breakout-backtest](https://github.com/systronics/nifty200-breakout-backtest)
