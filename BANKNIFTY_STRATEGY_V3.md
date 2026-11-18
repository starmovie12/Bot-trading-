# BANKNIFTY STRATEGY V3 — "ADAPTIVE SNIPER" (malik ki strategy, backtest + sudhaar ke liye)

**File:** BANKNIFTY_STRATEGY_V3.md · **Version:** 3.0 (V1, V2 ki jagah) · **Tarikh:** 19 Nov 2026 · **Malik:** Ail
**Ek line:** Bank Nifty ke Call/Put sirf khareedna. Entry candle, futures volume aur HDFC+ICICI ki sahmati par. Exit 4-gear trailing Stop-Loss se, munafe par koi upari seema nahi. T1 mein 3 lot (cap ke andar); risk ke hisaab se size R8 mein test hoga. Kharcha asli. Har trade chart se milane layak.

**Yeh file akeli kaafi hai.** Srot tag ([S], [B] ...) sirf yeh batate hain ki niyam kahan se aaya. Agent ke paas woh files nahi hain, aur unki zaroorat bhi nahi. Har niyam aur har number isi file mein poora likha hai.

**Srot tag:**
- **[S]** malik ki Sniper file (strategy ka mool, T1)
- **[B]** malik ki Bot_Idea v4
- **[O]** options spec
- **[P]** Intraday PRD v1.1
- **[C]** Crypto PRD v2.3
- **[RES]** agent ki purani research (`results/*.md`)
- **[NEW]** Claude ka sudhaar
- **[AUD]** V2 ke teen audit (MASTER, Master, Part 1–4)

**Status label:**

| Label | Matlab |
|---|---|
| PAKKA | Malik ka final niyam. Kabhi nahi badlega. |
| PAKKA (jab chune) | Woh roop chuna jaaye toh number pakka. |
| DEFAULT | Malik ka number, T1 mein yahi. AI sirf §12.1 ki range mein, §13 ke tareeke se badle. |
| SUJHAAV | [NEW] ka tunable number. Test se pehle pakka nahi. |
| FIXED | Constant. Tune nahi hoga (§12.2). |
| SHADOW | Sirf record. Faisle mein kabhi nahi. |
| NA | Data nahi. Na GREEN, na RED. |
| SAWAL | Malik ka jawab chahiye (§18). Tab tak default. |

**Takraav ka kram:** §2 > §6 > §7 > §12 > baaki. §0A sirf samjhane ke liye tasveer hai. Kaun sa module kis roop mein chalu hai, woh sirf §7.0 ki table batati hai.

---

## §0. AGENT KE LIYE 12 NIYAM

1. Yeh **pehle se likhi strategy** hai. Naya strategy-family nahi dhoondhna. Isi ko test karo aur §13 ke tareeke se sudhaaro.
2. **Kram:** §13.0 ke saare tests pass → Step 0 (§5.7) → R0. R0 mein **T1-P mukhya test** hai. T1-RAW aur T1 sirf tulna ke liye hain.
3. Har badlaav §12.1 ki range ke andar. Round ka grid pehle `PLAN.md` mein commit. `tools/preflight.py` (§13.1) har run se pehle.
4. Har fit (har window, har combo) runner khud `trials.jsonl` mein likhega. Haath se ginti mana.
5. Kharcha: BASE asli (§5). STRESS alag check. Kharche ki series (§5.5) beech mein badli toh R0 se dobara.
6. Fill aur bar ke niyam (§6) har test mein same. SL sirf bar close par badalta hai, live mein bhi (§6.3).
7. Har trade aur har signal (liya ya chhoda) CSV mein (§15). Bina record ka number report mein nahi.
8. Holdout sirf R10 ke final candidate par, ek baar (§14.2).
9. Naya data nahi. Jo data se nahi banta, woh `NA` (§4.4). `STATE.md` ya data na mile toh HALT card. Tool na mile toh §13 ke spec se likho, aur `DECISIONS.md` mein likho.
10. Phase 4 (bot code) band, jab tak STRATEGY PASS card aur malik ka "build bot" na aaye.
11. Malik se beech mein mat poochho. Har faisla `DECISIONS.md` mein. Ruko sirf §13.9 par. Har round ke baad 8–12 line ka card (§15.6).
12. Har command `set -euo pipefail`. Assert fail ho toh pehle theek karo. Adhoore round ka kuch bhi `results/` mein commit nahi. Progress sirf `STATE.md` / `wip/` mein.

---

## §0A. STRATEGY EK NAZAR MEIN (sirf tasveer; asli niyam §2, §6, §7, §12)

1. **09:15–09:20:** bot dekhta hai. Levels ka naksha banta hai: pichhle din ka high/low, opening range, VWAP, round number, OI deewar (§8).
2. **Din ki jaanch:** IVP 65 se kam ho aur shock na ho [T1-P]. Bazaar mein jaan ho (DEAD nahi) aur baar-baar VWAP ke aar-paar na ho (CHOP nahi) [sirf R4 test].
3. **Signal:** mazboot 1-minute candle (breakout, ya pullback ke baad uchhal), futures volume uchhla hua, aur HDFC + ICICI saath [T1].
4. **Jagah:** agli OI deewar SL se 2 guna door ho [T1-P]. Har level tak 1.5 guna jagah ho [sirf R4 test].
5. **Strike aur size:** ₹300–420 ka premium, ₹350 ke paas. 3 lot, agar cap (₹35,700) ijaazat de [T1]. Risk ke hisaab se 1–3 lot [R8 test].
6. **Exit:** −15 point SL → kharcha nikalte hi breakeven → "teen kadam peeche" trail → bade uchhal par kas jaata hai. Koi upari target nahi. SL har minute ke close par khiskta hai [T1].
7. **Din ke niyam:** max 4 trade (R9 mein 15 tak test). Lagatar 2 ghaate par din band. 15:10 par sab band [T1].
8. **Imaandaari:** yahi exit random entry par 2000 baar chalega. Strategy random se saaf behtar nahi nikli, toh pass nahi [§14].

## §0B. EDGE KI KAHANI (data isse jaanchega)

- **Kaun haarta hai:** level tootne par der se ghusne wale, aur galat taraf phanse traders. Badi chaal tab jab bade banks aur futures volume saath hon.
- **Payoff:** chhote ghaate (−15 pt, jaldi breakeven), kabhi-kabhi bade jeet (gear 3).
- **Ganit:** jeet = `net_base > 0`. p = jeet ki dar, R = ausat net jeet ÷ ausat net haar. Munafe ke liye **p > 1 ÷ (1 + R)** chahiye. R 1.8 par p > 36%; R 2.3 par p > 30%.
- **Data mein dikhna chahiye:** munafa trend din mein zyada ho, CHOP din mein kam. Diagnosis (§13.6) har baat alag naapega. Kahani galat nikle toh card mein seedha likho.

---

## §1. GALTIYON KA REGISTER (dobara nahi honi chahiye)

| # | Galti | Rok |
|---|---|---|
| E1 | Malik ka tareeka kabhi test nahi; AI ne 415 apne ideas aazmaaye [RES] | T1 = malik ki strategy, sabse pehle |
| E2 | Exit galat size ke (−30% / +60% premium; ~850 index pt), 24 mein 18 trade zero par band [RES] | Exit premium points mein, option ki ATR se (§7.6) |
| E3 | Kharcha double-stress; ATM par asli ~₹130/lot ko ₹217 maana [RES] | BASE asli; STRESS alag (§5) |
| E4 | 09:15–09:30 kabhi trade nahi [RES] | Faisla 09:20 se (§7.1) |
| E5 | Lot hamesha 30 maana [RES] | Lot har contract ka apna (§5.4) |
| E6 | R15-a ke trades save nahi [RES] | Har trade + signal CSV (§15) |
| E7 | 415 trials ki khudai [RES] | Seemit rounds; har fit runner gine (§13.2) |
| E8 | "Momentum ghaata deta hai" galat exit se nikla [RES] | Purane nateeje sach nahi maane jaayenge |
| E9 | 26 setups ka portfolio usi data par chuna [RES] | Ek strategy; portfolio mana |
| E10 | Assert fail par chain chupchaap ruki [RES] | §0 niyam 12 |
| E11 | Beech mein rukkar malik se poocha [RES] | §13.9 |
| E12 | 1-min bar mein high/low ka kram pata nahi; backtest aur live alag chal sakte hain | SL sirf bar close par, live mein bhi; intrabar sensitivity report (§6.3) [AUD] |
| E13 | Spot index ka volume 0 | VWAP futures se (§4.3) |
| E14 | [S] ka lock "+2": ₹350 par 3 lot −₹5.26, 1 lot −₹33.22, 3 lot stress −₹68.14 | Lock = asli breakeven (FIX-1) |
| E15 | Lookahead: adhoori 3m/15m bar, shaam wala daily metric | Feature registry + leak test (§4.2, T04–T06) [AUD] |
| E16 | Holdout pehle bhi ek baar khula tha (A1+b1) | `HOLDOUT_REUSED` label, sirf R10 final par, 1 baar, fail → ruko; pass ke baad paper phase (§14.2–14.3) [AUD] |
| E17 | Entry ka hunar random se nahi naapa | NULL-RANDOM gate (§13.5) |
| E18 | CE aur PE ko ek jaisa maana | Har report CE/PE alag; N15 |
| E19 | V2: FIX-3/4/6 ki paribhasha nahi | FIX table (§7.1) [AUD] |
| E20 | V2: "3 lot" ka daava cap se takraaya (lot 35 par ₹350 = ₹36,888 > ₹35,700) | `size_at_fill()` har fill par, `lots_reason` (§7.5) [AUD] |
| E21 | V2: N17 ke formula mein brokerage 3 baar gina | Asli `risk(n)` (§10.2) [AUD] |
| E22 | V2: stale bars par 15:10/13:30 ka exit atak sakta tha | Ghadi wale exit stale par bhi (§6.4), overnight assert [AUD] |
| E23 | V2: gear 1 aur 2 ke beech "dead zone" | FIX-6: time-stop gear se (§7.6) [AUD] |
| E24 | V2: R7/R10 ke andar ke fits gine nahi gaye; PE Delta negative; t+2 purana fill | §13.2, `abs(Delta)`, sirf t+1 [AUD] |

---

## §2. MALIK KE PAKKE NIYAM (kabhi nahi badlenge)

1. Sirf **BANKNIFTY** index options. [B][mission]
2. Sirf **CE ya PE khareedna**. Bechna, spread, hedge nahi. [B][O]
3. **Lots 1, 2 ya 3.** Kabhi 3 se zyada nahi. [malik]
4. Ghaate wale trade mein lots nahi jodna. [B]
5. SL entry ke saath tay. Sirf munafe ki disha mein khiskta hai, kabhi dheela nahi. [B][O][P]
6. **Intraday only.** 15:10 tak sab band. Koi position raat ko nahi. [B][mission]
7. **Lagatar 2 ghaate (net_base < 0) → us din naye entry band.** [B][P][S]
8. Ek waqt mein **ek hi khula trade.** [B]
9. **Expiry din:** current expiry ka trade **13:30** tak band. Expiry ki subah strike ka Delta 0.55–0.65. [B] Entry ki aakhri faisla-bar 12:59 (FIXED [NEW]; §7.2).
10. **IVP > 65 → naya buy nahi (K03).** **Agli OI deewar ≥ 2 × index risk door (K05).** [B] R1 se har test mein, aur R0 ke T1-P mein. Sirf T1-RAW aur T1 (tulna) inke bina.
11. SL kabhi entry premium ke 30% se door nahi. [B]
12. Har fill par: F × qty + round-trip charges ≤ `MAX_TRADE_LOSS_RS` (₹35,700) aur ≤ `CAPITAL_RS`. Warna lots kam (`size_at_fill`, §7.5); 1 lot bhi na aaye toh skip. Sasta strike chunkar fit karna mana. [B][mission]
13. Long ITM option expiry close tak kabhi nahi. [O]
14. Naya data nahi. Phase 4 band. Gates dheele nahi. [malik]

---

## §3. AAJ KA DATA SACH (19 Nov 2026, repo se) [RES][NEW]

| Baat | Nateeja | Matlab |
|---|---|---|
| DESIGN / HOLDOUT | [RES] ke hisaab se DESIGN 362 din (2024-11-21 → 2026-07-03), HOLDOUT ~90 din (uske baad). Pakka `STATE.md` se | §14 ki ginti inhi se |
| ₹300–420 premium wale strike ka Delta | median **0.33** (10%–90%: 0.22–0.52) | Premium band aur Delta 0.45–0.65 takraate hain |
| ATM premium, DTE se | DTE 3–7: ~₹349 · 8–15: ~₹575 · 16+: ~₹804 | ₹350 par ATM sirf aakhri hafte |
| ₹350 strike ki 1-min range (ATR5) | median ~10.6 pt; 09:20 par 30–45 pt | Khulne par fixed 15-pt SL shor mein kat sakta hai |
| `half_spread_PROXY` | ₹350 strike par ~1.75 | Asli bid-ask nahi; STRESS mein gina (§5.3) |
| Round-trip kharcha (₹350, BASE, Apr 2026 ke baad) | 1 lot ₹114.14 · 3 lot ₹248.03 | |
| Spot-vol rishta | Chadhte bazaar mein IV aksar girta hai | CE ko kam fayda (N15) |

**Imaandaar note:** upar ke numbers 21 sample din se hain. Inmein 3 din (2026-07-10, 08-13, 09-17) DESIGN ke baad ke the, yaani shayad holdout ke. Wahan sirf bazaar ka swabhav naapa gaya (Delta, premium, range, spread). Koi strategy ka P&L nahi. Phir bhi holdout ko `REUSED` hi maana gaya hai (§14.2).

---

## §4. DATA

### 4.1 Tables (data repo `store/`; mission ke data niyam wahi)
- `spot_1m`, `fut_1m`, `opt_1m` + `opt_wide_1m` (union), `vix_1m`, `stock_1m`
  - Columns: `ts_open, ts_close, o, h, l, c, v, oi, is_stale, expiry_date, strike, option_type`
  - In tables mein `available_from_ts` nahi hai; available = `ts_close`.
- `iv_greeks_1m`: `close, v, oi, is_stale, iv_DERIVED, delta_DERIVED, theta_DERIVED, half_spread_PROXY, volume_baseline_same_dte_DERIVED, baseline_same_dte_status, available_from_ts`
- `chain_1m`: `strike, ce_close_DERIVED, ce_v_DERIVED, ce_oi_DERIVED, ce_is_stale, pe_..., available_from_ts`
- `chain_metrics_1m`: `pcr_DERIVED, call_oi_wall_DERIVED, put_oi_wall_DERIVED, max_pain_DERIVED, gex_proxy_PROXY, gamma_flip_PROXY, atm_iv_DERIVED, available_from_ts`
- `bars_3m`, `bars_15m`: `o_DERIVED, h_DERIVED, l_DERIVED, c_DERIVED, is_partial, available_from_ts`
- `daily_metrics_DERIVED`: `version, rv20_DERIVED, ivp_vix_PROXY, ivp_status, available_from_ts`
- `xcheck_csv/fii_dii_daily.csv`
- `stock_1m` mein 12 banks: AUBANK, AXISBANK, BANKBARODA, CANBK, FEDERALBNK, HDFCBANK, ICICIBANK, IDFCFIRSTB, INDUSINDBK, KOTAKBANK, PNB, SBIN.

Mission ke data niyam wahi rahenge:
- Sirf `PRICE_READY` din; special session (jaise Sunday Muhurat) bahar.
- Cumulative files ka de-dup.
- Option P&L sirf monthly-expiry daur mein.
- DESIGN aur HOLDOUT ki baant `STATE.md` se.

### 4.2 Feature registry aur lookahead ka niyam [AUD]
- Faisla-bar `t` (ts_open) ka **decision_ts = t + 1 min**.
- Har feature row tabhi use ho jab `available_from_ts` (ya `ts_close`) ≤ decision_ts.
- **3m/15m bars:** sirf `is_partial == False` aur `available_from_ts ≤ decision_ts`. Udaharan: 09:20 ki faisla-bar (decision 09:21) par 3m ki aakhri bar 09:18–09:21. Aaj ki pehli 15m bar 09:30 se pehle nahi; tab tak pichhle din ki.
- **Daily metrics:** sirf `version == "INTRADAY_PREV_CLOSE"` (09:15 par pata). `EOD_INCLUSIVE` kabhi nahi.
- **K06 baseline:** `baseline_same_dte_status != "OK"` → K06 = NA.
- Code mein ek `features.yaml`: har feature ka table, column aur availability niyam. Test T04–T06 (§13.0).

### 4.3 Paribhasha
- **Din ka futures:** 09:15–09:19 mein jiska volume zyada, woh poore din. [B]
- **VWAP:** din ke futures ka, 09:15 se, typical (h+l+c)/3 aur `v` se. **σ** = volume-weighted std of typical price. U1/U2 = VWAP + 1σ/2σ, D1/D2 neeche. "Trend upar" = futures close > futures VWAP. [FIX-3]
- **Basis:** futures close − spot close. Futures ka level spot mein = level − basis.
- **EMA9, EMA21 (spot close):** pichhle din ki bars se warm-up.
- **ATR10 (spot):** pichhli 10 bars ki (h−l) ka ausat.
- **Option_ATR5:** trade wale strike ki pichhli 5 non-stale bars ki (h−l) ka ausat.
- **Disha:** UP = bhav VWAP, EMA9, EMA21 ke upar aur EMA21 ka 5-bar slope upar. DOWN ulta. Warna FLAT. [B]
- **DTE** = expiry_date − trading_date.
- **F** = asli entry fill (§6.1). **PEAK** = entry ke baad ka sabse ooncha option bar high (bar close par update). **GAIN** = PEAK − F.
- **Index risk** = SL point ÷ **abs(Delta)** (entry ka Delta). Udaharan: 15 ÷ 0.33 ≈ 45 index point. [AUD: PE Delta negative]
- **COST_PER_UNIT_1LOT** = `SPREAD_FULL_RS` + 2 × `SLIP_RS` + (1 lot ke round-trip charges ÷ lot_size). ₹350 par ≈ ₹3.80. (K21, K28)
- **DAY_STATE** (sirf diagnosis; EOD data se, faisle mein kabhi nahi): TREND = din ka |close − open| ≥ 0.6 × din ki range **aur** EOD ADX14(3m) ≥ 25 · CHOP = din bhar futures-VWAP crossings ≥ 12 · DEAD = din ki range < 0.6 × pichhle 20 din ki ausat range · warna NORMAL.

### 4.4 Shuruaati bars (EARLY_BARS)
- ATR10 aur futures volume ka 10-bar ausat: aaj ki bars se. Aaj ki 10 se kam hon toh jitni hain (kam se kam 5).
- K27 (30 bars) 09:45 se pehle NA. P3 (15-bar high) 09:30 se pehle nahi.

### 4.5 Data mein nahi → `NA`
Market depth/asli bid-ask · ticks · Nifty50/Sensex · GIFT Nifty · macro · economic calendar · agli expiry ke options (25 din chhod kar) · Iceberg, Rate_Update, Tick_Heartbeat · LLM/AI ki raay.

---

## §5. KHARCHA (asli, paise tak)

### 5.1 Charges ke rate (`tools/bn_economics.py side_charges()` se mel, **×1.5 nahi**)
| Charge | 1 Oct 2024 – 28 Feb 2026 | 1 Mar 2026 – 31 Mar 2026 | 1 Apr 2026 se | Kab |
|---|---|---|---|---|
| Brokerage | ₹20/order | ₹20 | ₹20 | dono |
| STT (premium) | 0.10% | 0.10% | **0.15%** (NSE/FATAX/73524) | sirf sell |
| Exchange | 0.03503% | **0.03553%** (NSE/FA/73061) | 0.03553% | dono |
| IPFT | 0.0005% (₹50/crore) | ₹0.01/crore (NSE/FA/73061) | ₹0.01/crore | dono |
| SEBI | 0.0001% | 0.0001% | 0.0001% | dono |
| Stamp | 0.003% | 0.003% | 0.003% | sirf buy |
| GST | 18% × (brokerage + exchange + IPFT + SEBI) | same | same | — |

- Har component bina round kiye. **Total ek baar paise tak round** (half-up).
- ₹10 API offer nahi ginna.

### 5.2 Lot size
Har trade ka lot us contract ka apna (expiry se), instrument data ya NSE circular se.
Cross-check: Jan–Jun 2025 expiry = 30 · Jul–Dec 2025 expiry = 35 · Jan 2026 se = 30 (NSE/FAOP/70616). Nov–Dec 2024 ke contracts circular se pakka karo. CSV mein `lot_size`.

### 5.3 Spread aur slippage (fill price ke andar)
- **BASE:** `SPREAD_FULL_RS` ₹1.00 (aadha har side), `SLIP_RS` ₹0.20 har side.
- **STRESS:** aadha spread = max(2 × BASE ka aadha, entry bars ke `half_spread_PROXY` ka median). Slippage × 2. Charges × 1.0. [AUD]
- **Malik ka naap aane par:** BASE = naapa hua median (time bucket se), aur STRESS = 2 × BASE. PROXY tab sirf jaankari.
- **PROXY column:** har bar ka `half_spread_PROXY` aadha spread.
- Stale bar par exit: spread × 2.

### 5.4 Har trade ke teen net
`net_base`, `net_stress`, `net_proxy`. Pass ki shart base aur stress par (§14).

### 5.5 Kharche ki series (immutable)
- Har kharcha-setting ka ek `series_id` (rates + spread + slip ka hash).
- Spread ya koi rate badla → nayi series, R0 se dobara. Do series ke trial kabhi ek saath nahi gine jaayenge. [AUD]

### 5.6 Kharche ka curve
- Final candidate aur T1-P ka net, full spread ₹0.50 / 1.00 / 1.50 / 2.00 / 2.50 / 3.00 / 3.50 / 4.00 par.
- Card mein: **"spread ₹x se upar hua toh strategy zero par."**

### 5.7 Step 0: haath se jaancho (code ka nateeja inse ₹0.01 tak mile)
- **A** (Apr 2026 ke baad): 3 lot, qty 90, open 350.00 → F = 350.70. Exit level 388.40 → fill 387.70.
  - Gross ₹3,330.00
  - Charges ₹128.43: brokerage 40.00, exchange 23.61, STT 52.34, GST 11.46, stamp 0.95, SEBI 0.07, IPFT ~0.00
  - **Net ₹3,201.57**
- **B** (Apr 2026 ke baad): wahi entry, SL = F − 15 = 335.70 → fill 335.00.
  - Charges ₹119.32
  - **Net −₹1,532.32**
- **C** (2026-02-10): 2 lot, qty 60, F = 350.70, exit fill 387.70.
  - Charges ₹89.72: brokerage 40.00, exchange 15.52, STT 23.26, GST 10.04, stamp 0.63, IPFT 0.22, SEBI 0.04
  - **Net ₹2,130.28**
- **D** (T1-RAW lock, Apr 2026 ke baad, F = 350.70, exit level 352.70):
  - 3 lot −₹5.26 · 1 lot −₹33.22 · 3 lot STRESS (aadha spread 1.00, slip 0.40) −₹68.14

---

## §6. FILL AUR BAR KE NIYAM

### 6.1 Entry fill
- Signal bar `t` band → bar `t+1` ke open par buy: F = open + aadha spread + slippage.
- `t+1` stale → `NO_FILL_STALE`. **t+2 nahi.** [AUD]
- F par dobara jaancho:
  - (i) T1/T1-P mein F ≤ `PREMIUM_MAX`, warna `NO_FILL_BAND`.
  - (ii) `size_at_fill()` (§7.5).
  - (iii) K03, K05 (jin roop mein chalu hon).
  - Koi fail → skip, wajah ke saath.
- Tick 0.05 par round (buy upar, sell neeche). [O]

### 6.2 Har non-stale bar `b` par kram
1. **Gap:** `b.open ≤ SL` → exit `b.open` par (− aadha spread − slippage). `GAP_SL`. [O]
2. **Stop:** `b.low ≤ SL` → exit SL par. Reason = jis niyam ne SL rakha: `SL_G0 / SL_G1_LOCK / TRAIL_G2 / TRAIL_G3 / CLIMAX_LOCK`.
3. **Pakka target (sirf X-B, N3):** `b.high ≥ target` → exit target par. Step 2 pehle; dono ek bar mein hon toh SL maano.
4. **Bar close ke checks:** time-stop, aur jo module chalu hon: structure stop (N7), reason-reversal (N12). Inke saath shock, expiry, force-flat. Koi sach → exit agli bar ke open par.
5. `PEAK = max(PEAK, b.high)`.
6. Naya SL §7.6 se, **agli bar se** lagu. Naya SL ≥ `b.close` ho → exit agli bar ke open par (wahi gear reason).

### 6.3 SL sirf bar close par (backtest = live) [AUD F2.1; NEW]
- **Niyam:** SL ek minute ke andar nahi badalta. Har 1-min bar ke close par ek baar badalta hai. **Live bot bhi bilkul aisa hi karega** (§17). Tab backtest aur live ek hi system hain, aur ek bar ke andar ke kram ka shak khatam.
- **Sensitivity report** (gate nahi; T1-P aur final candidate ke liye):
  - `PATH` = hari bar O→L→H→C; laal ya doji bar O→H→L→C. SL H par badle aur usi bar mein jaancha jaaye.
  - `WORST` = har bar O→H→L→C.
  - Card par teeno ka net. Agar PATH ya WORST mein `net_base` < 0, toh label **INTRABAR-SENSITIVE**. Matlab live bot ko bar-close niyam se bilkul nahi hatna.

### 6.4 Stale bars aur ghadi wale exit [AUD]
- **Stale bar par:** step 1–3 nahi (bhav asli nahi). Step 5 nahi (PEAK nahi badhta). Bar counter (time-stop) chalta rehta hai.
- **Ghadi wale exit** (15:10 force-flat, 13:30 expiry, shock) stale bar par bhi us minute lagte hain:
  - Fill = pichhli non-stale bar ka min(low, close) − 2 × (aadha spread + slippage).
  - Flag `STALE_FORCED`.
- **Lagatar 3 stale bars:** `ILLIQUID_EXIT`, agli bar par. Woh bhi stale ho toh upar wala fill.
- **Assert:** har din 15:11 par khule trade = 0. Expiry din 13:31 par current-expiry trade = 0.

### 6.5 Exit fill
- Exit = level − aadha spread − slippage. Stale exit par spread × 2.
- Force-flat 15:10 bar ke open par.

---

## §7. T1 — ADAPTIVE SNIPER (malik ki [S] strategy + zaroori sudhaar)

### 7.0 Roop aur module (sirf yeh table batati hai kya chalu hai)
| Module | T1-RAW | T1 | T1-P | R1+ base |
|---|---|---|---|---|
| Asli breakeven lock (FIX-1) | – (lock F+2) | ✓ | ✓ | ✓ |
| Strike skip, ITM1 nahi (FIX-2) | – (ITM1) | ✓ | ✓ | ✓ |
| Baaki FIX (3, 4, 5, 6, 7, 8) | ✓ | ✓ | ✓ | ✓ |
| K03 IVP gate, K05 OI-deewar gate | – | – | ✓ | ✓ |
| K25–K28 filters, N2–N17, P3 | – | – | – | Sirf apne round mein |
| §2 ke baaki pakke niyam | ✓ | ✓ | ✓ | ✓ |

**T1-P mukhya test hai.** T1-RAW aur T1 sirf tulna ke liye; inka koi pass/fail ya holdout nahi.

### 7.1 FIX table
| FIX | Niyam | Kyun |
|---|---|---|
| FIX-1 | Gear 1 lock = BE_LEVEL (asli breakeven, §7.6); trigger = F + max(5, be_pts + 2.5) | "+2" lock ₹350 par ghaata deta hai (§5.7 D) |
| FIX-2 | Band mein strike na mile → `NO_STRIKE_IN_BAND` | [S] ka "ATM mehenga → ITM1" ulta; ITM1 aur mehenga hota hai |
| FIX-3 | VWAP futures se (§4.3) | Spot ka volume 0 |
| FIX-4 | Bar niyam §6 (SL bar close par, gap, stale) | 1-min data mein yahi imaandaar |
| FIX-5 | Pehli faisla-bar 09:20 | P1 ko aaj ki 5 bars chahiye |
| FIX-6 | Gear 2 tab, jab GAIN ≥ `G2_START`. Gear 3 tab, jab GAIN ≥ `G3_START`. Time-stop: 20 bars aur max gear < 2 | V2 ka gear 1–2 "dead zone" band [AUD] |
| FIX-7 | Re-entry: agli bar ka open > PEAK + 1 + step → nahi | Bhaage bhav ke peeche nahi |
| FIX-8 | Din band: lagatar 2 `net_base < 0`. [S] mein "2 Gear-0 ghaate" tha | [B][P] ka pakka niyam bada hai |

T1-RAW mein ITM1 = ATM − `STRIKE_STEP` (CE) ya ATM + `STRIKE_STEP` (PE). ATM = spot ke sabse paas ka strike. `STRIKE_STEP` = chain mein ATM ke paas strikes ka farak (aam taur par 100).

### 7.2 Samay
- Faisla-bars (ts_open): **09:20–11:29** aur **13:15–14:44**. Fill ek minute baad.
- **Entry ts_open sirf 09:21–11:30 aur 13:16–14:45 mein.** Assert: 11:31–13:15 mein koi entry nahi. [AUD]
- Gear 2/3 wale trade 15:10 tak.
- Expiry din: aakhri faisla-bar 12:59. Dopahar window (13:15 se) expiry din khaali rahegi. Exit 13:30.

### 7.3 Entry signal ((a), (b), (c) teeno sach)
**(a) Trend + Heavyweights** [S]
- CE: futures close > futures VWAP · spot close > EMA9 · HDFCBANK aur ICICIBANK dono ka pichhli 3 bars ka return > 0.
- PE: sab ulta.

**(b) Pattern (koi ek)** [S]
- **P1 Ignition (CE):**
  - spot close > pichhli 5 bars ka sabse ooncha high
  - body ≥ 0.60 × range
  - close range ke upar wale 25% mein
  - 0.5 × ATR10 ≤ range ≤ 2.2 × ATR10
  - PE ulta.
- **P2 Pullback Bounce (CE):**
  - Pichhli 1–3 bars mein kam se kam ek bar ka low pichhli bar ke low se neeche (asli dip).
  - Un bars ka sabse neecha low `EMA9 − 0.3 × ATR10` se `EMA9 + 0.1 × ATR10` ke beech, **ya** futures VWAP ke 0.2 × ATR10 ke andar (spot mein badal kar).
  - Un bars mein koi futures close VWAP ke neeche nahi.
  - Abhi ki bar: close > pichhli bar ka high, close > open, body ≥ 0.50 × range, close range ke upar wale 40% mein.
  - PE ulta.

**(c) Volume** [S]
- Din ke futures ka 1-min volume ≥ 1.25 × 10-bar ausat (§4.4).
- Volume gayab ho toh: spot range ≥ 0.8 × ATR10.

CE aur PE dono sach → koi trade nahi (`CALL_PUT_TAKRAAV`).

### 7.4 Strike
- **T1:** nearest expiry. Signal bar ke close par, jis non-stale strike ka premium ₹300–420 ke beech ho aur ₹350 ke sabse paas.
- **Expiry din (DTE 0):** Delta 0.55–0.65 wala strike.
- `delta_at_entry` har trade mein.

### 7.5 Lots: `size_at_fill(F)` (har fill par: pehla entry, re-entry, STEP, TRAIL_BUY) [AUD]
1. n = mode ke hisaab se lots (T1: 3; §10.2).
2. Jab tak `F × lot_size × n + charges_roundtrip(n)` > `MAX_TRADE_LOSS_RS` ya > `CAPITAL_RS`: n = n − 1.
3. Din ki seema (§7.8): jab tak `din ka net_base − risk(n)` < −`DAY_MAX_LOSS_RS`: n = n − 1.
4. n = 0 → skip (`MAX_LOSS_CAP` / `DAY_LOSS_ROOM`). CSV mein `lots_reason` (`MODE / CAP / DAY / RISK`).

**Asar** (malik dhyaan de):
- 3 lot tabhi jab F ≤ ₹395.96 (lot 30) ya F ≤ ₹339.40 (lot 35).
- Jul–Dec 2025 (lot 35) mein ₹350 par T1 asal mein 2 lot lega (3 lot = ₹36,888).

### 7.6 Exit engine: 4 gear (bina upari seema)
Har bar close par (§6.2 kadam 6):

```
step      = clamp(0.6 × Option_ATR5, 4, 9)                        [S]
be_pts    = sabse chhota x jisse exit level F + x par net_base ≥ 0
            (is trade ke lots, bhav, spread, charges se;
             ₹350 par: 1 lot 3.15 · 2 lot 2.35 · 3 lot 2.10)
BE_LEVEL  = F + be_pts + 0.5                                      [FIX-1]
G1_TRIG   = F + max(5, be_pts + 2.5)                              [S; FIX-1]

Gear 0:   SL = F − SL_INIT_PTS (15), par F × 0.70 se neeche kabhi nahi  [S][§2 #11]
Gear 1:   jab PEAK ≥ G1_TRIG:          SL = max(SL, BE_LEVEL)         [FIX-1]
Gear 2:   jab GAIN ≥ G2_START (10):    SL = max(SL, PEAK − step)       [S][FIX-6]
Gear 3:   jab GAIN ≥ G3_START (25):    SL = max(SL, PEAK − 0.6 × step) [S][FIX-6]
Climax:   option bar (close − open) ≥ 20 → SL = max(SL, close − 2)    [S]
Time-stop: 20 bars poore aur max gear < 2 → exit agli bar open par    [S][FIX-6]
Target:   koi nahi (X-A)                                               [malik]
```
- T1-RAW: lock F + 2, trigger F + 5.
- Record: `max_gear, peak, mfe_pts, mae_pts, bars_held`.

### 7.7 Second-wave re-entry [S]
- Trade Gear 1 lock par band ho, aur agli 3 bars mein us strike ka high ≥ PEAK + 1, aur (a) aur (c) sach → **ek baar** re-entry, agli bar ke open par.
- Re-entry par wahi saare fill-checks (§6.1): band, `size_at_fill`, K03/K05 (jahan chalu).
- FIX-7 lagu. Re-entry ko naye pattern (b) ki zaroorat nahi. "Naye signal bar" niyam ka yahi akela apwaad hai. Din ki ginti mein gini jaati hai.

### 7.8 Din ke niyam (sab `net_base` par)
- Max **4 trade** (re-entry milakar). [S]
- **Ghaata** = `net_base < 0` (lock exit ka −₹5 bhi). `net_base ≥ 0` → lagatar ginti reset. **Lagatar 2 ghaate → din band.**
- Ghaate ke baad 10 min cool-off. [S]
- Har naya trade naye signal bar se (re-entry chhod kar).
- **Din ki seema:** `STOP_UNIT_RS` = `RISK_PER_TRADE_RS` (₹1,600). `DAY_MAX_LOSS_RS` = 2.5 × ₹1,600 = **₹4,000**. Naya entry tabhi jab `din ka net_base − risk(n)` ≥ −₹4,000; warna n kam (§7.5).
  - risk(n) = SL lage toh is trade ka nuksan (§10.2 formula).
  - Gap ka asli nuksan isse bada ho sakta hai; card mein `GAP_SL` ki ginti aur sabse bura gap. [AUD]
- **Profit Lock:** din ka sabse ooncha net_base ≥ 4% × `CAPITAL_RS` → floor = 0.70 × din ka sabse ooncha net (upar hi khiskega).
  - Naya entry tabhi jab `din ka net − risk(n)` ≥ floor.
  - Kisi exit ke baad net ≤ floor → din band. [B]
- Hafte/mahine ki Risk Limit: sirf ginti, lagu nahi. [B]

### 7.9 Safety exits
- **Shock:** spot ka 5-min move > 1% aur VIX ka 5-min uchhal > 8% → entry band, khula trade agli bar band. Bandish tab tak, jab VIX apne peak se 5% neeche aakar 10 min tike. [B]
- Expiry 13:30, force-flat 15:10 (§6.4).

### 7.10 Ek poora nakli trade (sirf samjhane ke liye)
**Setup:**
- 10:14 bar: P1 CE. Strike 57,500 CE @ ₹352. 3 lot (qty 90). Kharcha Apr 2026 ke baad wala.
- ATR5 = 10 → step 6.0 (udaharan mein same maana).
- F = 352.70 · SL 337.70 · BE_LEVEL 355.30 · G1_TRIG 357.70.

| Bar | O / H / L / C | Kya hua (bar-close niyam) | Agli bar ka SL | Gear |
|---|---|---|---|---|
| 10:15 | 352.0 / 356.5 / 349.0 / 355.5 | SL nahi laga; PEAK 356.5 | 337.70 | 0 |
| 10:16 | 356.0 / 359.0 / 354.0 / 358.5 | PEAK 359 ≥ 357.70 | 355.30 | 1 |
| 10:17 | 358.5 / 364.5 / 356.0 / 364.0 | GAIN 11.8 | 358.50 | 2 |
| 10:18 | 364.0 / 371.0 / 360.5 / 370.5 | GAIN 18.3 | 365.00 | 2 |
| 10:19 | 370.0 / 380.0 / 367.0 / 379.0 | GAIN 27.3 | 376.40 | 3 |
| 10:20 | 379.0 / 391.0 / 377.5 / 390.0 | PEAK 391 | 387.40 | 3 |
| 10:21 | 390.0 / 402.0 / 388.0 / 401.0 | PEAK 402 | 398.40 | 3 |
| 10:22 | 401.0 / 404.0 / 397.5 / 398.0 | low ≤ 398.40 → **exit** | — | `TRAIL_G3` |

**Ek hi trade, alag niyam se:**
- **Bar-close niyam (T1, live bhi aisa):** exit 398.40 → fill 397.70 → **net ₹3,919.76**.
- **PATH:** 10:22 laal bar, pehle high 404 → SL 400.40 → low lagi → **net ₹4,099.42**.
- **WORST:** 10:16 mein pehle high 359 → lock 355.30 → low 354 lagi → **net ₹48.21**. Isliye live bot bhi SL sirf minute ke close par badlega (§6.3).
- **X-B (+30 target):** 10:20 par 382.70 → **net ₹2,509.48**.
- **10:15 par hi palat jaata:** SL 337.70 → **net −₹1,532.75**.

---

## §8. LEVEL MAP AUR BAZAAR KA HAAL (filters sirf R4 mein; T1 mein shadow)

| Level | Kya | Kab pata |
|---|---|---|
| PDH, PDL, PDC | Pichhle din ka spot high, low, close | 09:15 |
| ORH, ORL | 09:15–09:29 ki bars ka spot high/low | 09:30 se |
| VWAP, U1/U2, D1/D2 | §4.3 | Har bar |
| ROUND | Har `ROUND_STEP` (500) ka spot level | Hamesha |
| WALL_C, WALL_P | `call_oi_wall_DERIVED`, `put_oi_wall_DERIVED` | `available_from_ts` |

- **Resistance (CE)** = sab levels jo spot close se 0.1 × ATR10 se zyada upar hon. **Support (PE)** ulta.
- **K25 STRETCH:** CE: futures close > U2 → RED (sirf P1). PE ulta.
- **K26 ROOM:** agli resistance tak doori ≥ `ROOM_MULT` (1.5) × index risk → GREEN. (V2 ka "3%" clause hataya; 500 ka round level hamesha paas hota hai.)
- **K27 CHOP:** pichhli 30 bars mein futures close ne VWAP ≥ 4 baar paar kiya → RED (P1/P2). 09:45 se pehle NA.
- **K28 DEAD:** spot ATR10 × abs(Delta) < 2.0 × COST_PER_UNIT_1LOT → RED.
- **K29 LEVEL_BREAK:** P1 ki bar ne isi bar mein PDH, ORH, ROUND ya U1 paar kiya (PE: PDL, ORL, ROUND, D1) → GREEN (score +2).

---

## §9. CHECK LIBRARY (shadow: har signal par record; faisla sirf jahan §7.0 kahe)

| ID | Check [B naam] | Input | GREEN (CE; PE ulta) | Number | Status | Family |
|---|---|---|---|---|---|---|
| K01 | Din_Ka_Mausam | bars_3m (pichhla din + aaj, §4.2) | ADX14 ≥ 25. ≤ 20 = RED. Beech = MIXED (NA) | 25/20 | DEFAULT | Disha |
| K02 | Bada_Gap | spot | Gap < 1%. ≥ 1% → 09:45 tak entry nahi | 1% | DEFAULT | — |
| K03 | IVP (Gate) | `ivp_vix_PROXY`, INTRADAY_PREV_CLOSE | ≤ 65. Card par label: "IVP = VIX par PROXY" | 65 | **PAKKA** | IV |
| K04 | IV_Overpriced | `atm_iv_DERIVED`, `rv20_DERIVED` | ATM IV ≤ 1.5 × RV20 | 1.5 | DEFAULT | IV |
| K05 | OI_Deewar (Gate) | oi_wall | Deewar ≥ 2 × index risk door, ya deewar ka OI 5 min mein ghata | 2× | **PAKKA** | OI |
| K06 | Strike_Volume | `v`, baseline | 5-min volume ≥ 1.5 × baseline (status OK na ho → NA) | 1.5 | DEFAULT | Volume |
| K07 | Fake_Spike | chain_1m | ±2 ke 4 strikes mein ≥ 3 usi disha | 3/4 | DEFAULT | Liquidity |
| K08 | Chase_Guard | opt_1m | 5 bars mein premium ≤ 15% badha, ya 0.5 × ATR5 pullback ke baad chala | 15% | DEFAULT | Breakout |
| K09 | Lambi_Wick | spot | Ulti wick ≤ 50% range | 50% | SUJHAAV | Breakout |
| K10 | Premium_Tezi | opt_1m | Is bar ka % badlaav ≥ 3 × pichhle 5 min ka ausat | 3× | SUJHAAV | Volume |
| K11 | Volume_Uchhal | fut_1m | Volume ≥ 3 × ausat aur futures > VWAP | 3× | DEFAULT | Volume |
| K12 | Trap_Detection | spot | Breakout ki agli bar level ke andar band nahi | 1 bar | DEFAULT | Breakout |
| K13 | Range_Breakout | bars_3m | Close pichhle 30 min (10 bars) ke high ke upar | 30 min | DEFAULT | Breakout |
| K14 | Timeframe_Match | bars_15m, 3m | Dono ki Disha trade ki taraf | — | DEFAULT | Disha |
| K15 | EMA_Slope | spot | — | — | SHADOW | Disha |
| K16 | RSI | bars_3m | RSI14 > 60 (PE < 40) | 60/40 | DEFAULT | Disha |
| K17 | OI_Short_Covering | chain_1m | Upar ki call deewar ka OI 5 min mein ghata, neeche put OI badha | 5 min | DEFAULT | OI |
| K18 | PCR_Trend | chain_metrics | PCR 15 min mein badha (PE ghata) | 15 min | DEFAULT | OI |
| K19 | Breadth | stock_1m | 12 mein ≥ 7 ka 5-min return trade ki taraf. ≥ 7 ulte = RED | 7/12 | DEFAULT | Stocks |
| K20 | VIX_Gati | vix_1m | CE: VIX 5 min mein na badhe. PE: badhe | 5 min | DEFAULT | IV |
| K21 | Kharcha_Filter | chain_metrics | (deewar tak doori × abs(Delta)) ≥ 3 × COST_PER_UNIT_1LOT | 3× | DEFAULT | OI |
| K22 | Max_Pain/GEX/Gamma_Flip | chain_metrics | — | — | SHADOW | OI |
| K23 | FII_DII | csv | — | — | SHADOW | — |
| K24 | Teeno_Index, Macro, GIFT, Event | — | — | — | NA | — |
| K25–K29 | §8 | §8 | §8 | §8 | SUJHAAV | Levels |

R7 mein ek family se max 2 checks.

---

## §10. SCORECARD AUR SIZE

### 10.1 Scorecard [B]
- **Order-Flow:** K10 = 2, K11 = 2, K12 = 3
- **Technical:** K13 = 3, K14 = 3, K16 = 1, K29 = 2
- **Directional:** K17 = 5, K18 = 2
- **Sentiment:** K19 = 5, HDFC+ICICI = 3, K20 = 2

Pass: har group mein ≥ 1 GREEN, kul ≥ 5 GREEN, score ≥ 10, ek group se max 5 point. NA = 0 point.

### 10.2 Lots ke roop (R8)
- **L1:** 3 (T1).
- **L2:** score ≥ 15 → 3, 10–14 → 2, < 10 → 1.
- **L3:** score pass Gate, phir L2.
- **N17 RISK** [P][AUD]:
  - `risk(n)` = n × lot_size × (SL point + aadha spread + slippage) + charges_roundtrip(n, F, F − SL).
  - lots = sabse bada n ≤ 3 jiska risk(n) ≤ `RISK_PER_TRADE_RS` (₹1,600). risk(1) bhi zyada → skip `RISK_TOO_BIG`.
  - Jaanch (F 350.70): lot 30 · SL 15 → 3 lot (₹1,532.32) · SL 18 → 2 (₹1,216.93) · SL 25 → 1 (₹841.66) · lot 35, SL 15 → 2 (₹1,202.29).
- **RISK + L2:** dono ka chhota.
- **Kat:**
  - K01 MIXED din → lots aadhe.
  - Equity (CAPITAL_RS + kul net_base) apne peak se 5% neeche → lots aadhe.
  - Aadha karne par neeche round, kam se kam 1.
- Har roop ke baad `size_at_fill()` (§7.5) lagta hai.
- Size tabhi badhe jab edge ho. Ghaate ko size se bachana mana.

---

## §11. MODULES (sab off, sirf apne round mein on; flag §12.3)

| ID | Module | Niyam | Kyun |
|---|---|---|---|
| N2 | ATR SL | Gear 0 SL = clamp(k × ATR5, 12, 30), k ∈ {1.0, 1.5}; 30% cap | Khulne par range 30–45 pt |
| N3 | Runner | 2–3 lot par GAIN ≥ 30 → 1 lot becho, baaki bina target | "30 par fix nahi" |
| N4 | Entry engines [C] | **STEP:** signal ke baad 2 bars mein option high ≥ open + 3 → (open + 3) par entry. **TRAIL_BUY:** 3 bars tak low ka intezaar → low + 3 par buy, ya open + 10 (FOMO). Fill-checks §6.1 | Galat signal par entry kam |
| N5 | Mausam gate | Sirf K01 GREEN (ya GREEN + MIXED) | [B] |
| N6 | Delta floor | Band + Delta ≥ 0.30. Kam ho toh ek strike andar (premium ≤ ₹500), warna skip | DTE 20+ par Delta ~0.22 |
| N7 | Structure stop | **P1:** spot close < breakout level − 0.1 × ATR10. **P2:** < pullback low − 0.1 × ATR10. **P3:** > trap high + 0.1 × ATR10. Exit agli bar open | Jis wajah se ghuse, woh tooti |
| N8 | Kharcha gate | K21 zaroori | [B] |
| N9 | Samay ke khaane | Har aadhe ghante ka net; khaana hatana = trial | [B] |
| N10 | Khulne ki bandish | Pehli faisla-bar 09:30 | [B] |
| N11 | P3 Trap Reversal | Neeche | [B]; [RES] diagnosis mein fade ka gross plus |
| N12 | Reason-reversal | Sirf gear 0/1. CE: futures close < VWAP aur HDFC, ICICI dono ka 3-bar return < 0, lagatar 2 bars → exit agli bar open | [B] Ulta_Check |
| N13 | Adaptive gears | G1 = max(be_pts + 2.5, 0.5 × ATR5). G2_START = clamp(1.0 × ATR5, 6, 15). G3_START = clamp(2.5 × ATR5, 15, 40). ATR5 entry ka | "Adaptive"; DTE ke saath swabhav alag |
| N14 | Level tighten | Gear 2 mein spot agli resistance ke 0.3 × ATR10 andar → turant gear 3 wala SL | Level par chaal rukti hai |
| N15 | Side-split | CE: Delta 0.45–0.55 strike. PE: premium band | Chadhte bazaar mein IV girta hai |
| N16 | Futures signal | Patterns futures 1-min bars par | Futures mein asli saude |
| N17 | Risk lots | §10.2 | [P] |

**N11 · P3 Trap Reversal (PE roop; CE ulta):**
1. 09:30 ke baad (§4.4). Spot ki ek bar ne key level (PDH, ORH, ROUND, ya pichhli 15 bars ka high) ke upar close kiya, kam se kam 0.2 × ATR10 se.
2. Agli 1–3 bars mein ek laal bar level ke neeche band hui; body ≥ 0.50 × range.
3. Us bar par futures volume ≥ 1.25 × ausat.
4. HDFC aur ICICI dono ka 3-bar return < 0.
5. Entry: PE, agli bar ke open par (fill-checks §6.1). Stop N7 (P3). Gears wahi.

**Exit ke roop:**
- **X-A:** bina target (T1).
- **X-B:** + pakka target +30.
- **X-C:** N3.
- **X-D:** SL −15% premium; +10% par BE_LEVEL; +20% se trail ₹15 peeche; target +30% [O].
- [O] ka "target 5%, SL 20%" test **nahi**: usmein kharche se pehle 80% jeet chahiye.

---

## §12. REGISTRY (har number yahin; code `config/strategy_v3.toml` se padhe)

**Niyam:**
- Strategy code ka har number isi registry se aaye.
- Test T02: code ke har numeric constant ka naam yahan ho.
- Naya number → pehle yahan, `DECISIONS.md` mein wajah ke saath.

### 12.1 Tunable (sirf R-rounds mein, isi range mein)
| Naam | T1 | Range | Status |
|---|---|---|---|
| `DECISION_START` | 09:20 | {09:20, 09:30} (N10) | DEFAULT |
| `MORNING_END` (aakhri faisla-bar) | 11:29 | {10:59, 11:29, 11:44} | DEFAULT |
| `AFTERNOON_START` | 13:15 | {13:15, 13:30} | DEFAULT |
| `LAST_ENTRY` (aakhri faisla-bar) | 14:44 | {14:14, 14:44} | DEFAULT |
| `SIGNAL_SRC` | SPOT | {SPOT, FUT} (N16) | DEFAULT |
| `BREAKOUT_LOOKBACK` | 5 | {3, 5, 8} | DEFAULT |
| `BODY_MIN_P1` | 0.60 | {0.5, 0.6, 0.7} | DEFAULT |
| `RANGE_MAX_ATR` | 2.2 | {1.8, 2.2, 2.6} | DEFAULT |
| `HW_RET_BARS` | 3 | {3, 5} | DEFAULT |
| `FUT_VOL_MULT` | 1.25 | {1.0, 1.25, 1.5, 2.0} | DEFAULT |
| `STRIKE_MODE` | PREMIUM_BAND | {PREMIUM_BAND, DELTA_BAND, N6, N15} | DEFAULT |
| `LOT_MODE` | L1 | {L1, L2, L3, RISK, RISK+L2} | DEFAULT |
| `RISK_PER_TRADE_RS` | 1,600 | {1,000, 1,600, 2,500} | SUJHAAV |
| `SL_INIT_PTS` | 15 | {12, 15, 18}; N2 k {1.0, 1.5} | DEFAULT |
| `G1_TRIGGER_PTS` | 5 | {5, 8, 12} | DEFAULT |
| `G2_START` / `G3_START` | 10 / 25 | {8, 10, 15} / {20, 25, 35}; N13 | DEFAULT |
| `STEP_MULT` | 0.6 | {0.5, 0.6, 0.8} | DEFAULT |
| `G3_MULT` | 0.6 | {0.5, 0.6, 0.8} | DEFAULT |
| `TIME_STOP_BARS` | 20 | {15, 20, 30} | DEFAULT |
| `CLIMAX_PTS` | 20 | {20, 25} | DEFAULT |
| `EXIT_MODE` | X-A | {X-A, X-B, X-C, X-D} | DEFAULT |
| `RUNNER_BOOK_PTS` | 30 | {25, 30, 40} | SUJHAAV |
| `REENTRY_MAX` | 1 | {0, 1} | DEFAULT |
| `MAX_TRADES_DAY` | 4 | {4, 6, 10, 15} | DEFAULT |
| `LOSS_COOLDOWN_MIN` | 10 | {10, 20} | DEFAULT |
| `PROFIT_COOLDOWN_MIN` | 0 | {0, 5} | DEFAULT |
| `DAY_LOSS_SU` | 2.5 | {2.0, 2.5, 3.0} | SUJHAAV |
| `ROOM_MULT` | 1.5 | {1.0, 1.5, 2.0} | SUJHAAV |
| `CHOP_CROSSES` | 4 | {3, 4, 6} | SUJHAAV |
| `DEAD_MULT` | 2.0 | {1.5, 2.0, 3.0} | SUJHAAV |
| `DELTA_FLOOR` | 0.30 | {0.25, 0.30, 0.35} | SUJHAAV |
| `LEVEL_NEAR_ATR` | 0.3 | {0.2, 0.3, 0.5} | SUJHAAV |
| `ENTRY_ENGINE` | INSTANT | {INSTANT, STEP, TRAIL_BUY} | DEFAULT |

### 12.2 FIXED / PAKKA (tune nahi)
- **Time:**
  - `FORCE_FLAT` 15:10 · `EXPIRY_EXIT` 13:30 (PAKKA)
  - `EXPIRY_LAST_DECISION` 12:59 (FIXED)
  - `OR_BARS` 09:15–09:29
  - `K02_WAIT` 09:45 · `K27_START` 09:45 · `P3_START` 09:30
- **Indicators:**
  - `EMA_FAST` 9 · `EMA_SLOW` 21 · `EMA_SLOPE_BARS` 5
  - `ATR_SPOT_N` 10 · `ATR_OPT_N` 5 · `FUT_VOL_SMA` 10 · `EARLY_MIN_BARS` 5
- **P1:** `CLOSE_ZONE_P1` 0.25 · `RANGE_MIN_ATR` 0.5
- **P2:**
  - `P2_MAX_BARS` 3 · `P2_LOW_ATR` 0.3 · `P2_HIGH_ATR` 0.1 · `P2_VWAP_ATR` 0.2
  - `BODY_MIN_P2` 0.50 · `CLOSE_ZONE_P2` 0.40
- **(c):** `VOL_FALLBACK_ATR` 0.8
- **Strike:**
  - `PREMIUM_MIN/MAX/TARGET` 300/420/350 (DEFAULT)
  - `DELTA_BAND` 0.45–0.65 (PAKKA jab chune) · `EXPIRY_DELTA` 0.55–0.65 (PAKKA)
  - `CE_DELTA_BAND` (N15) 0.45–0.55 · `N6_PREMIUM_CAP` 500
  - `STRIKE_STEP` = data se
- **Exit:**
  - `STEP_CLAMP` 4–9 · `BE_BUFFER_PTS` 0.5 · `G1_EXTRA_PTS` 2.5 · `CLIMAX_GAP` 2
  - `SL_MAX_PCT` 30% (PAKKA)
  - `N2_CLAMP` 12–30
  - `N7_OFFSET_ATR` 0.1 · `N12_BARS` 2
  - `N13_G1_ATR` 0.5 · `N13_G2_ATR` 1.0 · `N13_G2_CLAMP` 6–15 · `N13_G3_ATR` 2.5 · `N13_G3_CLAMP` 15–40
  - `TRAP_MIN_ATR` 0.2 · `TRAP_BARS` 3 · `TRAP_LOOKBACK` 15
  - `REENTRY_BARS` 3 · `REENTRY_ABOVE_PEAK` 1
- **Stale:** `STALE_EXIT_BARS` 3 · `STALE_SPREAD_MULT` 2
- **Day:**
  - `CONSEC_LOSS_STOP` 2 (PAKKA) · `MAX_LOTS` 3 (PAKKA)
  - `MAX_TRADE_LOSS_RS` 35,700 (PAKKA) · `CAPITAL_RS` 2,00,000 (SAWAL)
  - `STOP_UNIT_RS` = `RISK_PER_TRADE_RS`
  - `PROFIT_LOCK_TRIG` 4% CAPITAL · `PROFIT_LOCK_KEEP` 70%
  - `DD_CUT` 5% → lots × 0.5
- **Shock:**
  - `SHOCK_MOVE` 1% / 5 min · `SHOCK_VIX` 8% / 5 min
  - Bandish khulne ki shart: VIX peak se 5% neeche aur 10 min tike
- **Levels:** `ROUND_STEP` 500 · `LEVEL_IGNORE_ATR` 0.1
- **Checks:** §9 ke numbers. `IVP_MAX` 65 (PAKKA), K05 2× (PAKKA). Baaki FIXED, sirf on/off R7 mein.
- **Score:** weights §10.1 · `MIN_SCORE` 10 · `MIN_GREENS` 5 · `GROUP_CAP` 5 · L2 thresholds 15/10
- **Entry engines:** `STEP_PTS` 3 · `STEP_BARS` 2 · `TRAIL_REV` 3 · `FOMO_PTS` 10 · `TRAIL_BARS` 3
- **Cost:** `SPREAD_FULL_RS` 1.00 · `SLIP_RS` 0.20 · `TICK` 0.05 · rates §5.1
- **Stats:**
  - `WF_BLOCKS` 5 · `MIN_TRADES_OOS` 150 · `MIN_TRADES_WINDOW` 25
  - `BOOT_BLOCK_DAYS` 5 · `BOOT_N` 1,000 · `NULL_SEEDS` 2,000 · `PBO_BLOCKS` 16
  - `NEFF_CORR` 0.5 · `PBO_MAX` 0.25 · `DSR_MIN` 0.95 · `SEED` 20261119
  - `HOLDOUT_MIN_TRADES` 20 · `PAPER_MIN_TRADES` 60

### 12.3 Module flags (T1-P mein sab OFF, sirf §7.0 wale ON)
`FLAG_K25..K28`, `FLAG_N2..N17`, `FLAG_P3`, `FLAG_REENTRY` (T1 mein ON).

---

## §13. BACKTEST AUR SUDHAAR KA TAREEKA

### 13.0 Pehle yeh tests pass hon (R0 se pehle; fail = aage nahi)
| Test | Kya jaanchta hai |
|---|---|
| T01 | Har `FIX-n` ki is file mein theek ek paribhasha (§7.1) |
| T02 | Code ka har numeric constant §12 mein (registry diff khaali) |
| T03 | §5.7 ke A, B, C, D ₹0.01 tak |
| T04 | Bars t+1…t+15 (har table) bigaado → bar t ke saare features hoobahu same |
| T05 | 09:20 faisla-bar par 3m ki aakhri bar 09:18–09:21; aaj ki 15m bar 09:30 se pehle nahi |
| T06 | Daily metric sirf `INTRADAY_PREV_CLOSE` |
| T07 | PE Delta −0.35 par index risk > 0; K05 ka fail case pakda jaaye |
| T08 | 15:05–15:29 sab stale, trade khula → 15:10 par `FORCE_FLAT_1510` + `STALE_FORCED`; 15:11 par khule = 0 |
| T09 | Expiry din: 13:01 signal skip; 13:25 ke baad stale par bhi 13:30 exit |
| T10 | N13, ATR5 = 20 → G2_START = clamp(20, 6, 15) = 15; PEAK GAIN 12; 21vi bar → `TIME_STOP` |
| T11 | R0 ke T1-RAW/T1/T1-P mein `STRUCTURE_STOP, REASON_REVERSAL, NO_ROOM, CHOP, DEAD, STRETCH` = 0; T1-RAW/T1 mein `GATE_IVP, GATE_OI_WALL` = 0 |
| T12 | `size_at_fill`: lot 30 F 401 → 2 lot; lot 35 F 350.70 → 2 lot (`CAP`); har trade F × qty + charges ≤ 35,700 |
| T13 | N17: §10.2 ki chaaron jaanch; RISK ₹500, SL 15 → `RISK_TOO_BIG` |
| T14 | Din ka net −₹3,000 + agla trade 3 lot (risk ₹1,532) → 1 lot (`DAY`) |
| T15 | Lock exit −₹5.26 ghaata gina jaaye; net ≥ 0 lock par ginti reset |
| T16 | Re-entry F 401 (lot 30) → 2 lot; IVP 70 par re-entry nahi (T1-P) |
| T17 | Signal premium 415, t+1 open 425 → `NO_FILL_BAND`; t+1 stale → `NO_FILL_STALE` (t+2 nahi) |
| T18 | Koi entry ts_open 11:31–13:15 mein nahi; sabse jaldi 09:21, sabse der 14:45 |
| T19 | §7.10 replay: bar-close → 10:22 `TRAIL_G3` ₹3,919.76; WORST → 10:16 ₹48.21; PATH → ₹4,099.42 |
| T20 | NULL: K03 skip ginti > 0; day niyam lage; random-PnL strategy par percentile ~50 |
| T21 | `preflight`: trials.jsonl ki ek row hatao → abort; PLAN.md commit run ke baad → abort |
| T22 | Holdout ki tarikhein §14.2 se pehle ek baar bhi nahi padhi gayi (access log = 0); doosra holdout run → abort |
| T23 | Wahi config + seed → wahi trades.csv hash |
| T24 | Spread badla → naya `series_id`; purani series ke trial alag |
| T25 | 09:20 bar par ATR10 aur volume ausat aaj ki 5 bars se; K27 09:45 se pehle NA; P3 09:30 se pehle nahi |

### 13.1 Preflight (`tools/preflight.py`, har run se pehle)
- Round ka grid `PLAN.md` mein commit ho, aur commit ka samay pehle run se pehle ka ho.
- `trials.jsonl` ki rows = runner calls = result files.
- `series_id` aur `config_hash` sahi hon.
- Koi bhi fail → abort.

### 13.2 Trial ginti
- Naya program: trial ID `S3-` se, 0 se.
- **Runner har fit khud likhega.** Har window, har combo, R7 ka har step, R10 ki har window ka har chunaav. Haath se ginti nahi.
- Purane 415 trials report mein dikhte rahenge.
- **N_eff (DSR ke liye):** saare S3 trials ke din-wise net ka correlation lo. Hierarchical clustering karo (distance 1 − ρ, average linkage, `NEFF_CORR` 0.5 par kaato). Clusters ki ginti = N_eff. Card par raw-N DSR bhi.
- T1-P ek pehle se likha niyam hai, data se nahi nikla, isliye uska faisla N = 1 par.
- Imaandaar note: malik ke niyam isi daur ke trading anubhav se bane hain. Isliye NULL aur holdout zaroori hain.

### 13.3 Rounds (grid pehle `PLAN.md` mein commit)
- R1 se base T1-P.
- Har round ka jeeta roop agle round ka base banta hai, sirf training window ke chunaav se (nested).

| Round | Kya | Configs (cap) |
|---|---|---|
| **R0** | Tests (§13.0), Step 0, T1-RAW + T1 (tulna), **T1-P (mukhya)**. Nulls, diagnosis, intrabar sensitivity | 3 |
| **R1** | G1 {5, 8, 12} × SL {12, 18} × {X-A, X-B}; + N13 | 13 |
| **R2** | Strike: DELTA_BAND, N6, N15 | 3 |
| **R3** | Exit: X-C, X-D, N2 (k 1.0), N2 (k 1.5), N7, N12, N14 | 7 |
| **R4** | Filters: K25, K26, K27, K28 (akele), phir sabse achhe do ka jod | 6 |
| **R5** | Entry: STEP, TRAIL_BUY, K12, N10, N16 | 5 |
| **R6** | P3: (a) sab windows (b) sirf jab us bar par K27 CHOP (c) sirf 13:15 ke baad | 3 |
| **R7** | Ablation: K01–K21 + K29 (on/off sirf, number nahi), forward selection training window par, family se max 2, max 6 kadam | har fit gina |
| **R8** | Size: L1, L2, L3, RISK, RISK+L2 | 5 |
| **R9** | MAX_TRADES {4, 6, 10, 15} × cool-off {10, 20}; N9 | 10 |
| **R10** | Combination: har training window mein R1–R9 ka chunaav dobara | har fit gina |
| R11–R12 | Agent ke ideas: **sirf** §12.1 ke params ke 2-way jod, ya §11 ke do modules ka jod | 10 har round |

Configs ka jod (R0–R9, R11–R12) = 75. R7 aur R10 ke fits runner gine. Kul ginti card par.

### 13.4 Nested walk-forward
- DESIGN ko 5 chronological block mein baanto.
- Expanding window: train blocks 1..k → test block k+1 → **4 OOS windows** (blocks 2–5).
- **Har candidate (T1-P bhi) ka nateeja inhi 4 windows par.** Ek jaisi tulna.
- Runner: repo mein maujood nested runner, agar woh ek chhote fixture par §13.4 jaisa nateeja de. Warna `tools/nested_wf.py` isi spec se likho. `DECISIONS.md` mein likho.
- Har round ke baad PBO (CSCV, 16 blocks) aur DSR (N_eff).

### 13.5 Nulls (entry ka hunar) [AUD]
**NULL-RANDOM:**
- Unhi dino par, utni hi entries jitni candidate ne li.
- Random faisla-bar, sirf un bars mein jahan candidate ke disha-rahit filter pass hon (samay, K03, K27/K28 agar chalu hon).
- Random CE/PE. K05 random side ke liye jaancho; fail → dobara chuno.
- Strike niyam, `size_at_fill`, lot roop, exit engine, re-entry, din ke niyam aur kharcha: sab wahi.
- 2,000 seed (`SEED` se). p = (k + 1) ÷ (2,000 + 1), jahan k = jitne seed candidate ke barabar ya behtar.

**NULL-FLIP:** wahi signal-samay, ulti disha.

**EXIT-CHECK:** wahi entries, fixed 10/20/30 bar exit (gear engine kitna jodta hai).

### 13.6 Diagnosis (trial nahi)
- MFE/MAE. Kitne % trade +5, +10, +25, +30 tak pahunche.
- **MFE capture** = jeete trades ka ausat exit-gain ÷ ausat MFE.
- Exit reason ki ginti. `GAP_SL` aur `STALE_FORCED` ki ginti aur sabse bura.
- Net alag-alag:
  - CE banam PE
  - DTE (0–2, 3–7, 8–15, 16+)
  - aadhe ghante ke khaane
  - P1/P2/P3
  - DAY_STATE (§4.3)
  - VIX half
  - lot daur (30/35)
  - `lots_reason`
- p aur R, aur §0B ki shart.
- Kharche ka curve (§5.6). Intrabar sensitivity (§6.3).
- 10 trade ki chart table (§15.5).

### 13.7 AI kya badal sakti hai / kya kabhi nahi
- **Haan:**
  - §12.1 ki range ke numbers.
  - §9 ke checks on/off (R7).
  - §10 ke lot roop.
  - §11 ke modules aur exit roop.
  - Ek round mein ek tarah ka badlaav.
- **Kabhi nahi:**
  - §2.
  - Kharcha BASE se kam.
  - §6.
  - §12.2 ke FIXED number.
  - Naya data ya instrument.
  - Option bechna.
  - Holdout tuning mein.
  - Bina preflight run.
  - Purane 31 rounds ke families.

### 13.8 Seekh ka niyam [P]
- Final report mein T1-P aur final candidate saath-saath.
- T1-P ghaate mein ho aur sirf filters plus banayein → card mein saaf likho. Aisa candidate §14 ki saari shartein OOS mein poori kare tabhi aage.

### 13.9 Kab rukna hai
1. **STRATEGY PASS** (§14) → card, ruko.
2. **Holdout fail** → STRATEGY FAIL card, ruko. Doosra candidate holdout par nahi.
3. **R12 khatam**, koi pass nahi → FINAL card (sabse achha `PAPER CANDIDATE`, kya fail hua, kaun sa naap ya niyam madad karega). Ruko.
4. `STATE.md` ya data na mile → HALT card.
5. Paisa, token ya live wala faisla.

**Auto-continue:**
- Usage/context khatam → `STATE.md` mein progress likho, commit + push, phir khud ko "continue" schedule karo (agar tool ho).
- Bina koi round poora kiye **lagatar 3 auto-continue** → HALT card (kahin atka hai).

---

## §14. PASS KI SHARTEIN, HOLDOUT, PAPER

### 14.1 DESIGN par (sab 4 OOS windows, blocks 2–5, par) [AUD]
Card par pehle: `DESIGN_DAYS` (`STATE.md` se), trade/din, aur kya gate 6 mumkin hai.
- `DESIGN_DAYS × MAX_TRADES_DAY` < 150 → `INSUFFICIENT` (FAIL nahi).
- `DESIGN_DAYS` < 80 → tuned pass mumkin nahi (sirf PAPER).

Shartein:
1. `net_base` per trade > 0, kul > 0.
2. `net_stress` ≥ 0 (§5.3 ka STRESS).
3. 4 mein se ≥ 3 window positive, har window mein ≥ 25 trade.
4. Best 5 trade hatakar bhi `net_base` > 0.
5. Dono VIX half mein `net_base` ≥ 0.
6. ≥ 150 OOS trade.
7. Day-block bootstrap (5 din ke block, 1,000 baar, `SEED`), ek-taraf p < 0.05. Tuned ke liye saath mein DSR (N_eff) ≥ 0.95 aur PBO ≤ 0.25.
8. E12 ≥ DD95.
   - E12 = OOS ka ausat din-net × 250.
   - DD95 = 250 din ke 5-din-block bootstrap paths (1,000) ka 95th percentile max drawdown (₹).
9. NULL-RANDOM p ≤ 0.05.

### 14.2 HOLDOUT (label `HOLDOUT_REUSED`) [AUD]
- **Kyun REUSED:** purane program ne yeh din ek baar A1+b1 par dekhe the, aur §3 ke 3 calibration din bhi shayad inme the. Naya, anchhua data bacha hi nahi. Isliye holdout ka pass nirnayak nahi; sirf ek aur jaanch.
- `STATE.md` mein `holdout_uses` log (tarikh, candidate hash, nateeja). Is program mein **max 1**.
- **Sirf R10 ka final candidate** (T1-RAW/T1 kabhi nahi). Woh pehle §14.1 ki saari shartein paas kare. Candidate aur shartein pehle commit.
- **Pass** = holdout par:
  - `net_base` > 0 aur `net_stress` ≥ 0
  - ≥ 20 trade
  - bootstrap p < 0.10
  - NULL-RANDOM ≥ 90th percentile (holdout dino par)
- 20 se kam trade → `INSUFFICIENT` → PAPER.
- **Fail** → STRATEGY FAIL card, ruko. Holdout ke baad koi tweak nahi.
- **Pass** → **STRATEGY PASS (REUSED)** card.

### 14.3 PAPER phase (STRATEGY PASS ke baad, live se pehle)
- Holdout reused hai, isliye live paisa sirf tab, jab paper mein ≥ 60 trade ho chuke hon.
- Paper ka `net_base` > 0 ho, aur backtest ke ausat ke 95% band ke andar ho.
- Yeh Phase 4 ka hissa hai; malik ke "build bot" ke baad.

Har number par label: `[BACKTEST·OOS]`, `[HOLDOUT·REUSED]`, `[PAPER]`, PRE-TAX.

---

## §15. OUTPUT

### 15.1 `results/s3_trades.csv`
`series_id, config_hash, code_commit, trial_id, date, signal_ts, pattern(P1/P2/P3/REENTRY), side, expiry, dte, strike, delta_at_entry, premium_at_signal, entry_ts, entry_fill, lots, lots_reason, lot_size, qty, sl_init, be_level, index_risk_pts, room_pts, peak, peak_ts, max_gear, mfe_pts, mae_pts, bars_held, exit_ts, exit_level, exit_fill, exit_reason, stale_forced, gross_rs, brokerage, stt, exchange, gst, sebi, ipft, stamp, spread_slip_rs, net_base, net_stress, net_proxy, net_path, net_worst, score, checks_green, wf_window, vix_half, day_state`

### 15.2 `exit_reason`
`SL_G0, GAP_SL, SL_G1_LOCK, TRAIL_G2, TRAIL_G3, CLIMAX_LOCK, TARGET30, RUNNER_BOOK, TIME_STOP, STRUCTURE_STOP, REASON_REVERSAL, ILLIQUID_EXIT, SHOCK, EXPIRY_1330, FORCE_FLAT_1510, DAY_LOCK`

### 15.3 `results/s3_signals.csv` (liya ya chhoda)
Signal details, K01–K29, score, levels, aur faisla: `TAKEN` ya wajah:
`NO_STRIKE_IN_BAND, NO_FILL_STALE, NO_FILL_BAND, WINDOW, EARLY_BARS, DAY_STOP_2LOSS, DAY_LOSS_ROOM, PROFIT_FLOOR, COOLDOWN, MAX_TRADES, MAX_LOSS_CAP, RISK_TOO_BIG, GATE_IVP, GATE_OI_WALL, NO_ROOM, CHOP, DEAD, STRETCH, CALL_PUT_TAKRAAV, SHOCK, EXPIRY_AFTER_1259`

### 15.4 Reports
`results/s3_nulls.md`, `s3_diagnosis.md`, `s3_cost_curve.md`, `s3_intrabar.md`

### 15.5 Malik ki chart-jaanch
- R0 card ke saath T1-P ke 10 trade: 5 jeet, 5 haar, alag mahinon se.
- Har trade: tarikh, entry/exit samay, strike, CE/PE, bhav, net.
- Malik broker chart par milayega. Farak = bug, pehle theek.

### 15.6 Round card (8–12 line)
- Round, configs/fits, sabse achha candidate.
- Net base/stress per trade, trade per din, OOS windows (+/−).
- Best-5 hatakar, DD95.
- NULL p.
- CE banam PE.
- Intrabar label (agar ho).
- Kya seekha (1 line), aage kya (1 line).

---

## §16. TAKRAAV JO SULJHAAYE

| # | Takraav | Faisla |
|---|---|---|
| 1 | Premium ₹300–420 [S] banam Delta 0.45–0.65 [B] | T1 = premium band; Delta roop R2; expiry din Delta 0.55–0.65 |
| 2 | 09:18 [S] banam pehle 15 min dekhna [B] | 09:20 faisla (FIX-5); 09:30 = N10 |
| 3 | Dopahar band 11:30–13:15 [S] banam 11:45–13:30 [B] | [S] |
| 4 | Aakhri entry 14:45 [S] banam 15:10 [B] | Aakhri faisla-bar 14:44, fill 14:45 |
| 5 | Lock +2 [S] banam asli breakeven [B] | FIX-1 |
| 6 | "ATM mehenga → ITM1" [S] | FIX-2 (T1-RAW mein ITM1, sirf tulna) |
| 7 | Spot VWAP [S] | Futures VWAP (FIX-3) |
| 8 | Max 4 [S] / 1–15 (malik) / 3–4 [B] | 4 se shuru, R9 mein 15 tak |
| 9 | 2 Gear-0 ghaate [S] banam 2 net ghaate [B][P] | FIX-8 |
| 10 | Cool-off 10 [S] banam 20 [B] | 10; R9 mein 20 |
| 11 | +30 target [S] banam "30 par fix nahi" (malik) | X-A; X-B tulna; N3 runner |
| 12 | Time-stop 20 min [S] banam 15 min/5% [B] | [S], gear se (FIX-6) |
| 13 | 3 lot [S] banam score [B] banam fixed risk [P] | T1 = 3 (cap ke andar); baaki R8 |
| 14 | Volume 1.25× [S] banam 3× [B] | 1.25× trigger; 3× = K11 |
| 15 | [O] target 5% / SL 20% | Test nahi |
| 16 | Day loss 3% [B] banam 4–6% [P] | 2.5 × ₹1,600 = ₹4,000 |
| 17 | Force-flat 15:10 banam 15:15 [B] | 15:10 |
| 18 | Event lock [B] | Backtest mein NA |
| 19 | LLM layer [P] | Backtest mein nahi; live mein sirf SHADOW (§17) |
| 20 | Expiry entry 13:30 (V2 §2) banam 13:00 (V2 §7) | Aakhri faisla-bar 12:59; exit 13:30 PAKKA |
| 21 | Auditor ka "hamesha pehle high" (WORST) banam bar-close | Bar-close, live mein bhi; WORST/PATH sirf report (§6.3) |
| 22 | Auditor ka "naya anchhua holdout" | Data nahi bacha; `HOLDOUT_REUSED` + paper phase (§14.2–14.3) |

---

## §17. PAPER/LIVE KE LIYE (abhi code nahi)
- **SL sirf 1-min bar ke close par badlega (pakka; §6.3).** Tick par trailing mana, warna backtest aur live alag system ho jaayenge.
- Agar naya SL bhav se upar ho → turant protected exit.
- Entry Limit order, ask + max ₹1.50. 10 sec mein fill nahi → cancel, peeche nahi bhaagna. [O][B]
- Fill ke 1–2 sec mein broker par SL-Limit (options par SL-M mana). Gap par fill na ho → 5 sec baad protected sell. [O]
- Har level asli fill F se, tick 0.05. [O]
- Paper mein wahi engine, wahi kharcha, gap non-fill ka simulation. [O][C][P]
- **AI/LLM:** live mein sirf SHADOW (log, trade nahi rokta), jab tak 60+ paper/live trade par uska fayda saabit na ho. [P][AUD]
- Live ke baaki niyam (event calendar, kill-switch, static IP, roz login): mission ke hisaab se.

---

## §18. MALIK SE SAWAL (backtest inke bina bhi chalega)
1. **Asli spread (sabse zaroori):** ATM aur ₹350 strike ka bid-ask, 09:20, 11:00, 13:00 aur 15:00 par, 3–5 din.
   - Iske bina STRESS data ke proxy par chalega (₹3.50 full spread, kaafi kada).
   - Naap aate hi STRESS = 2 × asli, aur nayi series.
2. **`MAX_TRADE_LOSS_RS`:** lot 35 ke daur mein ₹350 par 3 lot ₹36,888 ka hai, isliye cap ₹35,700 par 2 lot hi hote hain. 3 lot chahiye toh cap ~₹37,000 karna padega. Yeh tumhara faisla hai.
3. **`CAPITAL_RS` aur `RISK_PER_TRADE_RS`:** asli balance, aur ek trade mein kitna nuksan manzoor hai.

---

## §19. BADLAAV-SUCHI
- **3.0 (19 Nov 2026):** teen audit [AUD] ke findings (2 + 9 P0, saare P1). Har finding ka hisaab `V3_AUDIT_TRACE.md` mein. Mukhya badlaav:
  - **Bar niyam:** SL sirf bar close par, live mein bhi; WORST/PATH sensitivity. Stale bars par ghadi wale exit, overnight assert. Sirf t+1 fill; F par band/cap/gate dobara.
  - **FIX table** FIX-1…8 (FIX-6 = gear dead-zone ka hal). Module ki on/off table (§7.0). §0A ka kram.
  - **Paise ka hisaab:**
    - `size_at_fill()` aur `lots_reason`.
    - N17 ka sahi `risk(n)`.
    - Din ki seema ₹4,000; ghaate ki paribhasha; Profit Lock 70% of max.
    - Rates dated table (STT 73524, exchange+IPFT 73061). Total ek baar round.
    - Step 0 ke A–D sahi numbers. STRESS = max(2 × BASE, PROXY median).
    - Kharche ki series immutable.
  - **Data aur stats:**
    - Feature registry, exact column naam, 3m/15m aur daily metric ka lookahead niyam.
    - `abs(Delta)`, COST_PER_UNIT ki paribhasha, EARLY_BARS, DAY_STATE (sirf diagnosis).
    - Runner har fit gine; N_eff ka tareeka tay. 5 block → 4 OOS windows, ≥ 25 trade har window.
    - DD95/E12 ki paribhasha. NULL ka poora spec (2,000 seed, wahi niyam).
    - Holdout REUSED: sirf R10 final, 1 baar, fail → ruko; pass ke baad paper ≥ 60 trade. LLM sirf shadow.
  - **Engineering:** constants registry (§12.2) + `config/strategy_v3.toml`, 25 tests (§13.0), preflight, auto-continue ki seema, WIP niyam.
  - **Naam:** GAIN/PEAK; galti register E1–E24; source tag [RES]/[NEW]/[AUD]; label table.
  - Strategy ke naye trading idea **nahi** jode: pehle imaandaar R0 nateeja.
- **2.0:** levels, CHOP/DEAD, P3, risk lots, nulls, poora udaharan.
- **1.0:** paanch files se pehli file.
