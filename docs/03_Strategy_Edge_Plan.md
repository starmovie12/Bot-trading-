# 03: Strategy Edge Plan (profit zyada, loss kam: sabit karne ka tareeka)

**Tarikh:** 10 Nov 2026 · **Kisne:** Claude Code · **Status:** Prastaavit · **Saboot:** `docs/research/R_c_Compliance.md` (SEBI studies), `R_d_Costs_Data.md` (kharche, data), `scratch/risk_sim/` (Monte Carlo)

## Saar (10 line)
1. **Profit ki guarantee koi nahi de sakta.** SEBI ki Aug 2026 study: FY26 mein 87.7% individual F&O traders haare; option buyers mein ~90% loss-makers the.
2. **Is bot ka goal:** kharche ke baad positive Net Expectancy **sabit** karna. Sabit na ho toh live nahi jaana.
3. **Kharcha:** Nifty50 1 Lot round-trip ~Rs 80.5 (Rs 20/order brokerage, STT 0.15% 1 Apr 2026 se). Iske upar Slippage. 1 Lot par sabse bada kharcha brokerage hai.
4. **Data:** core data Nov 2024 ke baad ka hai (naya lot, BankNifty weekly band, Sep 2025 se naye expiry din). Sabse kaam ki kharid NSE Historical Trade Data hai (~Rs 2.6 lakh, 2 saal, licence ki pushti ke baad). Depth ka itihas sasta nahi milta, isliye khud record karna hai.
5. **Backtest:** event-driven, live wala hi code, depth/trade se realistic fill, latency injection, Walk-Forward, Out-of-Sample, parameter stability, multiple-testing correction, Monte Carlo, aur regime-wise nateeje.
6. **Risk ka sach (Monte Carlo):** "poora balance = Lot" niyam mein achhe edge (+7.3%/trade) ke saath bhi Rs 52,000 se 250 trade mein **~60% Risk of Ruin** aata hai. Hisse wale niyam (Vikalp A, 25%) mein lagbhag 0% hai. Ek Stop-Loss = equity ka 21 se 25%, jabki `Daily_Loss_Risk_Limit` 3% hai.
7. **Ganit:** ek trade ka sigma ~37% hai. Isliye +3.6% edge sabit karne ke liye ~300 trade chahiye, aur +7.3% ke liye ~74.
8. **Ablation:** har check aur har Data Family ko hata kar dekhna ki kaun sach mein edge deta hai. Shadow se Active sirf data se.
9. **Stage Gates** Confidence Interval par hain, sirf ausat par nahi. Live band karne ki 4 kasauti hain.
10. **Pre-mortem:** 15 tareeke jinse bot fail ho sakta hai, aur har ek ka bachav.

---

## 0. Seedhi baat pehle

Option khareedna aaj ke Indian bazaar mein zyada tar retail logon ke liye nuksan ka khel raha hai:

| SEBI study | Kya mila | Source |
|---|---|---|
| Jan 2023 (FY22) | 89% individual traders haare | [SEBI PR 22/2024](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727086965496.pdf) mein zikr (`R_c` Section 4) |
| Sep 2024 (FY22-FY24) | 93% haare; average ~Rs 2 lakh nuksan; transaction cost FY22-24 mein ~Rs 50,000 crore | [SEBI PR 22/2024](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727086965496.pdf) |
| Jul 2025 (FY25) | ~91% ko net nuksan; FY25 net nuksan Rs 1,05,603 crore (baad mein revise) | [SEBI PR 39/2025](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900802566.pdf) |
| Aug 2026 (FY25-FY26) | FY26 mein 87.7% haare; kul nuksan Rs 91,685 crore; **option buyers mein ~90% loss-makers**; algo aur non-algo dono individual groups ka gross P&L minus mein | [Profitability study](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf), [Behaviour study](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233601328.pdf) |

Nuksan ke kaaran wahi hain jo idea khud maanta hai: theta (samay ke saath premium galna), spread, IV Crush aur kharche. SEBI ka chart yeh bhi dikhata hai ki "algo use karna" apne aap faayda nahi deta (`R_c` Section 4 ka note).

**Is bot ka goal:** kharche aur Slippage ke baad positive Net Expectancy ko itne trades par **sabit** karna ki kismat ka asar alag ho jaaye. Sabit na ho toh Real Money Mode mein poore Lot par nahi jaana (Idea v4 §1 ka `[PRASTAAVIT-CC]` lakshya).

---

## 1. Cost model (official source, 10 Nov 2026; poora: `R_d` Section 1-2)

| Charge | Rate | Kis par | Lagu tarikh | Source |
|---|---|---|---|---|
| Brokerage (Upstox) | Rs 20 / executed order (API order Rs 10 offer "31 Dec 2026 tak"; do pages mein tarikh alag) | Har order | page par tarikh nahi | [upstox.com/brokerage-charges](https://upstox.com/brokerage-charges/), [trading-api](https://upstox.com/trading-api/) |
| STT | **0.15%** sell premium (31 Mar 2026 tak 0.10%); exercise par 0.15% intrinsic | Sell | 1 Apr 2026 | NSE circular NSE/FATAX/73524 |
| NSE transaction | 0.03553% premium (IPFT shaamil) | Dono side | 1 Mar 2026 | NSE/FA/73061 |
| BSE transaction (Sensex) | 0.0325% premium | Dono side | 1 Oct 2024 | Broker pages (BSE notice verify nahi hua) |
| SEBI fee | 0.0001% | Dono side | — | NSE investor page |
| Stamp duty | 0.003% | Buy side | 1 Jul 2020 | NSE investor page |
| GST | 18% | Brokerage + txn (+SEBI fee, conservative) | — | NSE / Upstox |
| Auto square-off (broker kare toh) | Rs 75 + GST | Har aisa case | — | Upstox brokerage page |

**Round-trip, 1 Lot, Rs 20 brokerage (script `R_d`):**

| Udaharan | Kul kharcha | Premium ka % | Breakeven (premium points) |
|---|---|---|---|
| Nifty50 (Lot 65) 200 → 220 | Rs 80.52 | 0.62% | +1.20 (24 tick) |
| BankNifty (Lot 30) 300 → 280 | Rs 67.39 | 0.75% | +2.29 (46 tick) |
| Sensex (Lot 20) 200 → 240 | Rs 57.91 | 1.45% | +2.83 (57 tick) |

**Slippage:** koi pakki public study nahi mili (`R_d` Section 3). Shuruaati andaza: Nifty 2 tick/side, BankNifty aur Sensex 4 tick/side; expiry dopahar, event aur 9:15-9:20 par 2 se 5 guna. **Backtest ko 1, 2, 4, 10 tick/side ki poori grid par chalana hai.** Jo strategy sirf 0-1 tick par kamaati hai, use kamzor maano.

**Model ke niyam:**
- Rates **tarikh ke hisaab se** (purane trade par purana STT). 1 Oct 2024 se pehle ke rate primary se verify nahi hue.
- Kharcha_Filter ko % nahi, **rupaye** mein dekhna chahiye, kyunki 1 Lot par brokerage fixed hai.
- Har cancel-reprice ya slice alag executed order ho sakta hai, isliye uski brokerage alag gino.

---

## 2. Data plan (poora: `R_d` Section 4-6)

**Data quality model se zyada zaroori hai.** Ek galat expiry tarikh, ek galat Lot, ya "touch hua toh fill" maanna poore backtest ko jhootha bana deta hai.

### 2.1 Kya chahiye, kahan se, kitne ka

| Priority | Data | Srot | Kharcha (andaza) | Kyun |
|---|---|---|---|---|
| P0 | Bhavcopy, Participant OI, fo_mktlots, India VIX, index closes, constituents, circulars | NSE/BSE/niftyindices (free) | Rs 0 | Calendar, Lot, expiry, EOD OI aur breadth ki neev |
| P0 | **Apna live depth record** (Upstox WS `full`, 5 level) | Phase 2 se khud | Rs 0 + VPS | Fill model ka sabse sasta aur asli calibration |
| P0 | Upstox Expired Instruments API (1-min + OI) test | Upstox Plus (abhi free) | Rs 0 | Mil gaya toh core 2 saal free |
| P1 | **NSE Historical Trade Data (F&O)**, Nov 2024 se Oct 2026 | NSE | ~Rs 2,60,000 (GST ke saath) | Har trade, saare strikes, expired bhi. **Shart:** "commercial use" wali licence line par NSE ka likhit jawab (Sawal 140) |
| P2 | Ek vendor ka 1-min OHLCV + OI (NSE + BSE) 2-3 saal | TrueData / GDFL / Accelpix (public price nahi) | cap ~Rs 1,00,000 | Cross-check; Sensex ke liye |
| P3 | BSE Order Book history, 2 mahine | BSE | ~Rs 1,11,000 | Sensex ka depth calibration |
| Reserve | Custom NSE depth sample; storage/compute | NSE / cloud | ~Rs 2-3 lakh | Nifty/BankNifty depth ka ek official namuna |

**Kul (P0-P3 + reserve): ~Rs 6-7 lakh**, 10 lakh budget ke andar. NSE Order & Trade (depth) data ~Rs 12.5 lakh/saal hai, isliye budget se bahar (`R_d`). Har kharid se pehle likhit quote, "per annum" ka matlab aur licence terms.

### 2.2 Quality ki dikkatein aur jaanch

| Dikkat | Jaanch |
|---|---|
| Lot size kai baar badla; Sensex Jan 2027 se 25 (verify nahi hua) | Har din ka Lot contract master/bhavcopy se; kabhi hard-code nahi |
| Expiry weekday 2025 mein badla; chhutti par khisakti hai (Nifty 9 Nov 2026 Somvaar) | Expiry sirf contract master se |
| Missing strikes, illiquid strikes ke stale prints | Har minute ke liye "aakhri trade kitna purana" column; purana print = no-quote |
| Crossed book (bid > ask), galat timestamp (NSE sample mein mila) | Crossed/out-of-order rows gino aur hatao; ginti report mein |
| OI der se update hota hai | OI ka apna timestamp; OI checks ko OI ki umar ke saath test karo |
| Expired contracts ka gayab hona | Survivorship check: har expiry ke saare strikes maujood |
| Index constituents badle (BankNifty ki ginti) | Har mahine ki official suchi |
| Holidays/special session (Muhurat, Budget Sunday) | Calendar se; aise din alag tag |
| Bazaar ke naye samay (3:40 PM, 7 Dec 2026 se 3:45 PM) | Session-aware candles; purane aur naye din alag |

### 2.3 Fill model (depth itihas na ho toh)
1. **Sirf 1-min bar:** buy limit tabhi fill jab agle bar ka low ≤ limit − 1 tick ho ("touch is not fill"). Order qty bar volume ka chhota hissa (≤ 10%, andaza). Volume 0 = fill nahi.
2. **Tick trades:** limit tabhi fill jab us bhav ya behtar par trade ho, aur humse pehle khadi qty (andaza) nikal chuki ho.
3. Spread aur depth ke parameter: samay, moneyness, expiry tak ke din aur expiry din ke hisaab se table.
4. **Paper mein calibrate** (asli recorded book par simulated vs model fill) aur **Stage2 mein** (asli fill vs model). Model asli se achha nikle toh turant pessimistic karo. Model ke behtar fill par kabhi bharosa nahi.

---

## 3. Backtest design

| Hissa | Design |
|---|---|
| **Event-driven, live wala code** | Wahi Dimaag aur Haath, sirf `BacktestBroker` (02 §C5). Ek bhi alag "backtest-only" niyam nahi |
| **Realistic fill** | §2.3 ka model; Slippage grid 1/2/4/10 tick/side; partial fill; reject (price band) simulate |
| **Latency injection** | Har order par deri: feed lag + faisla + network + broker (hop 1-12, 02 §A1), shuru mein median 300 ms aur tail 2 s (andaza), Stage2 ke naap se badlo. Deri ke dauran bhav khiskta hai |
| **Walk-Forward** | Train 6 mahine → test 1 mahina, phir 1 mahina aage khisko. Har window ke parameter record |
| **Out-of-Sample** | Aakhri 6 mahine (`Backtest_Min_Avadhi`) shuru se band (lock). Sirf ek baar, aakhir mein, kholna |
| **Parameter stability** | Har mukhya number ±20% par Net Expectancy ka "plateau" chahiye, "chotiyan" nahi (`Parameter_Stability_Paimana`) |
| **Multiple-testing correction** | Har aazmaya config ek register mein (ginti zaroori). Chuni hui config ka Out-of-Sample result is ginti ke saath judge ho: Holm-Bonferroni (hypotheses par) aur White Reality Check ya SPA jaisa bootstrap test (configs par). Kitne config aazmaaye, report mein likhna zaroori |
| **Monte Carlo** | (a) Trade bootstrap (din ke blocks mein, taaki ek din ke trade saath rahein); (b) kram badal kar sabse buri girawat ka distribution; (c) Slippage aur deri ko random badal kar |
| **Regime-wise nateeje** | Trending, Sideways (Shadow Trade se), Ulta-Palat, expiry din, event din, gap din, aur samay ke khaane. Regime ka label do tarah: bot ka apna (live jaisa) aur baad mein data se (sach). Dono milao (H-12) |
| **Look-ahead se bachav** | Har check sirf us samay tak ka data dekhe; band candle; swing ki pushti ke baad (`smart-money-concepts` wali galti nahi, `R_b`) |
| **Replay test** | Live/Paper ka recorded din backtest mein chalao; faisle bit-for-bit mile |

**Kitne trade chahiye (ganit, `scratch/risk_sim/ruin_mc.py`):**

| Edge ka scenario | Net Expectancy / trade (stake ka %) | Sigma / trade | Ek-taraf 95% bharose ke liye trade |
|---|---|---|---|
| Thoda edge (jeet 45%) | +3.58% | 37.8% | ~302 |
| Achha edge (jeet 50%) | +7.28% | 38.1% | ~74 |
| Barabar (jeet 40%) | −0.12% | 37.2% | kabhi nahi |

Isliye `Backtest_Min_Trade_Ginti` = 300 hai. Gates sakht hain, toh roz shayad 0.5 se 1 trade hi bane (andaza). 18 mahine mein ~190 se 375 trade, aur Out-of-Sample 6 mahine mein ~60 se 125. Agar Out-of-Sample mein 100 trade na bane, toh **nateeja "sabit nahi" hai**, chahe ausat achha dikhe.

---

## 4. Check Ablation plan (kaun sa check sach mein edge deta hai)

1. **Baseline:** pehle version ke saare checks, Walk-Forward par.
2. **Ek-ek hatao:** har Score check aur har Gate ko hata kar dobara chalao. Har ke liye ΔNet Expectancy, ΔProfit Factor aur trade ginti ka badlaav. Same signals par paired bootstrap se Confidence Interval.
3. **Family hatao:** Data Family (v4 §7 table) ko poora hata kar. Agar ek family hatane se nateeja nahi badalta, toh woh family nakli bharosa de rahi thi.
4. **Correlation:** har check ke GREEN/RED ka aapas mein correlation. Jo checks ek saath chalte hain, unke liye `Data_Family_Max_Score_Hissa`.
5. **Gates ka hisaab:** har Gate ne kitne signal roke, aur un rukay signals ka Shadow Trade nateeja. Agar Gate ke roke trade kharche ke baad bhi munafe mein the, toh Gate mehenga hai.
6. **Vazan:** ablation ke baad vazan sirf malik badlega (Idea §15). Naya vazan Out-of-Sample par dobara parkha jaayega.
7. **Shadow → Active niyam:** `Shadow_Se_Active_Min_Signal` (100) signal, aur check jodne par Net Expectancy ka nichla Confidence Interval upar khiske, Walk-Forward ki zyada tar windows mein. Phir malik ki manzoori.

---

## 5. Risk engineering

### 5.1 Ek Stop-Loss banam `Daily_Loss_Risk_Limit`
Nifty50 premium Rs 200, Lot 65 → 1 Lot = Rs 13,000. Stop-Loss 25-30% → ek nuksan ~Rs 3,250 se 3,900, kharche aur gap alag. Agar account mein Rs 15,000 hai, toh **ek Stop-Loss = equity ka ~24%**. `Daily_Loss_Risk_Limit` 3%, `Weekly_Loss_Risk_Limit` 6-8%, `Monthly_Loss_Risk_Limit` 15% hai. Matlab **pehla hi nuksan teeno seemayein tod deta hai**, aur bot mahine bhar ke liye ruk jaata hai (F-03). Saath hi, malik ke udaharan ka Rs 14,000 Nifty50 ke 1 Lot aur 10% buffer (Rs 14,300) ke liye bhi kam hai.

### 5.2 Monte Carlo: Risk of Ruin (`scratch/risk_sim/ruin_mc.py`, nateeje `results.md`)
**Maanyatayein (andaza):** premium Rs 200, Lot 65; jeet par +45% (0.5x se 1.5x), haar par −28% (0.8x se 1.2x) aur 5% haar mein gap (+20%); kharcha + Slippage Rs 93.5/Lot; 250 trade; 20,000 path; naya paisa nahi daala. "Ruin" = 1 Lot + buffer ka paisa na bachna.

| Shuruaati equity | Scenario | Malik ka niyam (poora balance) | Vikalp A (25% stake) | Vikalp C (Worst-Case ≤ 5% equity) |
|---|---|---|---|---|
| Rs 15,000 | Achha edge (+7.3%/trade) | Ruin **90.9%**; median 2 trade | Trade hi nahi (1 Lot 25% se bada) | Trade hi nahi |
| Rs 52,000 | Thoda edge (+3.6%) | Ruin **92.8%**; median ant/shuru 0.25 | Ruin 0%; 89.5% "niyam se ruka" (Lot bada) | Trade hi nahi |
| Rs 52,000 | Achha edge (+7.3%) | Ruin **59.7%**; median maxDD 95% | Ruin 0%; 77.6% ruka | Trade hi nahi |
| Rs 1,30,000 | Barabar (−0.1%) | Ruin **99.5%** | Ruin 0%; equity < 50%: 60.6% | Ruin 0%; median 0.79 |
| Rs 1,30,000 | Thoda edge (+3.6%) | Ruin **87.6%**; median 0.10 | Ruin 0%; median **2.56**; equity < 50%: 13.8% | Ruin 0%; median **1.56**; median maxDD 29% |
| Rs 1,30,000 | Achha edge (+7.3%) | Ruin **44.3%**; median 1.26; maxDD 98% | Ruin 0%; median 23.8 (sirf ganit, edge sach mein itna hona mushkil) | Ruin 0%; median 4.52 |

**Seekh:**
1. **Positive edge ke saath bhi poora balance lagana balance ko doobata hai.** Kelly Hissa thode edge par ~27% aur achhe edge par ~56% hai. Poore balance ka Lot stake ko 85-95% par rakhta hai, jo Kelly se kai guna zyada hai. Isse lambe samay ki badhotri negative ho jaati hai.
2. **Chhote account mein Nifty50 ka Lot hi bada hai.** Hisse wala niyam (A ya C) chhote balance par trade karne hi nahi deta. Yeh "kamzori" nahi, ganit ki sachchai hai: Rs 13,000 ke Lot ke liye 25% niyam par ~Rs 52,000 aur Vikalp C par ~Rs 1,04,000 chahiye.
3. **Malik ke Fund Request model mein "ruin" ka matlab** hai: har nuksan ke baad naya paisa daalna padta hai. Asli jokhim kul daala hua paisa hai. Report mein "kul daala paisa vs kul nikla paisa" alag dikhna chahiye.
4. **`Ulta_Palat_Aur_Drawdown_Lot_Cut` 1 Lot par nahi lagta**, aur poore balance mein aksar 1 Lot hi hota hai. Isliye drawdown par Lot cut asal mein kabhi chalta hi nahi (F-74).

### 5.3 Behtar sizing ke Prastaav (malik ka niyam overwrite nahi; Idea v4 §9)
- **Vikalp A (H-09):** stake ≤ `Fractional_Stake_Hissa` (25%) aur Backtest ke Kelly Hissa ka aadha. Jo Lot isse bada ho, woh trade skip.
- **Vikalp B (H-10):** seemayein Stop-Unit mein: din 1, hafta 2, mahina 4. Isse seema aur Lot ek ikai mein aate hain.
- **Vikalp C:** ek trade ka Worst-Case Nuksan ≤ malik ki rupaye wali seema (`Prati_Trade_Max_Nuksan_Rupaye`).
- **Test:** wahi Monte Carlo, par Backtest ke **asli** trade distribution par (bootstrap), na ki upar ke andaze par. Malik ke saamne table: Risk of Ruin, p95 girawat, median badhotri, aur "kitna paisa chahiye".

---

## 6. Entry/Exit sudhaar ke Hypotheses (har ek: hypothesis, test, success metric)

| ID | Hypothesis | Test | Success metric |
|---|---|---|---|
| H-01 | IV/RV kam aur IVP neeche hone par Net Expectancy zyada | Trades ko IV/RV ke 4 khaanon mein baanto | Sabse sasta khaana sabse mehenge se zyada; farak ka 90% CI 0 se upar |
| H-02 | Spread-aware Limit Order (beech se shuru, ek sudhaar) Slippage ghatata hai | Paper aur Stage2 mein A/B (din ke hisaab se badal kar) | Median Slippage kam, fill-dar ≥ `Entry_Fill_Dar_Min` (80%) |
| H-03 | Kuch samay ke khaane kharche ke baad lagatar nuksan dete hain | Har 30 minute ke khaane ki Net Expectancy | Khaane ka 90% CI poora 0 se neeche, aur Walk-Forward ki zyada tar windows mein |
| H-04 | Expiry subah current expiry ka trade kamzor hai | Expiry subah ke trades alag | Net Expectancy aam din se kam aur gap-fill zyada |
| H-05 | Stop-Unit ke guna par partial profit % se behtar | Dono exit niyam ek hi signals par | Net Expectancy barabar ya zyada, sigma kam |
| H-06 | Cap se door stop par trade skip karna behtar | "Cap par stop" vs "skip" | Skip mein Net Expectancy/trade zyada, kul P&L kam na ho |
| H-07 | Theta-aware Time-Stop behtar | Time-Stop ko expiry tak ke din ke hisaab se | Time-Stop wale trades ka nuksan kam |
| H-08 | Shock mein munafe wale trade ko trail karna behtar | Shock events par dono | Shock trades ki Net Expectancy zyada, Slippage kam |
| H-09 | Vikalp A Risk of Ruin ko bahut ghatata hai | §5 Monte Carlo, asli trades par | Ruin < 1%, p95 girawat malik ki seema ke andar |
| H-10 | Stop-Unit wali Risk Limit seemaon ko asal mein lagu karti hai | Monte Carlo | Seema toote toh sirf utni hi, jitni tay |
| H-11 | Ablation se kuch checks bekaar niklenge; family cap nakli signal ghatata hai | §4 | Hatane par Net Expectancy na gire; family cap par Out-of-Sample sudhre |
| H-12 | "Trending" tag agle ghante ki ek-disha chaal pehchanta hai | Tag vs baad mein data se nikla regime | Tag ke baad trend ki sambhavna base rate se saaf zyada |
| H-13 | Event window nuksan bachata hai | Event ke paas ke Shadow Trades | Window ke andar ke Shadow Trades ki Net Expectancy negative |
| H-14 | Futures par breakout Spot se jaldi aur saaf | Dono par signal | Futures signal ki deri kam aur Net Expectancy barabar ya zyada |
| H-15 | Feed atakne par broker se bhav maangna turant MPP exit se sasta | Fault injection + Stage2 ke asli atkaav | Atkaav wale trades ka Slippage kam, koi Critical niyam nahi toota |
| (extra) | Tick wale checks har tick par (1 s timer ke bajay) | Paper mein A/B | Entry deri ~500 ms kam, Chase reject kam (02 §A2) |

**Event bachav:** H-13 ke liye event calendar official srot se (RBI MPC schedule, MoSPI calendar, Budget) aur malik ki file se. Har event ka type aur samay record.

---

## 7. Stage Gates (Prastaavit numbers; Idea v4 §16 aur §18)

| Stage | Pass karne ki shart | Fail par |
|---|---|---|
| **Backtest** | Walk-Forward ≥ 18 mahine, aakhri 6 mahine Out-of-Sample; ≥ 300 trade (OOS mein ≥ 100); OOS Net Expectancy ka ek-taraf 95% nichla CI > 0; Profit Factor ≥ 1.3 (kharche + Slippage grid ke 2 tick par); ±20% par stable; multiple-testing correction ke baad bhi significant; koi regime akela poora munafa na de; Monte Carlo p95 girawat malik ki seema ke andar | Paper shuru nahi. Strategy dobara socho (naye config aazmaane se pehle register mein likho) |
| **Paper** (`Paper_Gate_CC`) | ≥ 40 trading din aur ≥ 60 trade; Net Expectancy Backtest ke 90% daayre mein; simulated vs recorded-book fill farak median ≤ 1 tick; saare fault tests pass; koi Critical niyam nahi toota | Fill model ya niyam sudhaaro; Paper dobara |
| **Stage2** (1 Lot asli, `Stage2_Gate_CC`) | ≥ 60 asli trade; asli Net Expectancy ka ek-taraf 90% nichla CI > 0; asli vs Paper fill farak median ≤ `Paper_Asli_Fill_Farak_Hadd` aur p90 ≤ uska 2 guna; Pehredaar, shared token, Kill Latch, Broker Stop ka asli test pass | 120 trade tak sabit na ho toh **ruk kar dobara design** |
| **Poora Lot** | Stage2 pass; malik ka likhit faisla sizing vikalp par (Sawal 118); Lot dheere badhe: har 20 trade par +1 Lot, jab tak limit na toote (andaza) | Wapas Stage2 Lot |

**Live band karne ki kasauti (`Live_Kill_Paimana`), koi ek bhi:**
1. Deposit-Adjusted girawat > Backtest ki p95 sabse buri girawat ka 1.5 guna.
2. Pichle 30 trade ki Net Expectancy Backtest ke 5% wale nichle daayre se neeche.
3. Pichle 20 trade ka median Slippage model ka 2 guna se zyada.
4. Koi Critical niyam toota: net short, `Entry_Ke_Baad_Broker_Stop_Samay` se zyada bina Broker Stop, dohra order, Lease ke bina hukm.
5. (extra) Regulator ya broker ka niyam badla aur jaanch nahi hui: pause.

---

## 8. Pre-mortem: "Yeh bot kab aur kaise fail hoga" (top 15)

| # | Kaise fail hoga | Bachav |
|---|---|---|
| 1 | **Asli edge hai hi nahi**; backtest mein dikha kyunki 100 config aazmaaye | Config register, Holm/Reality Check, locked OOS, Stage Gates CI par |
| 2 | **Poore balance ka Lot** ek bure hafte mein account khatam karta hai | Vikalp A/B/C (H-09, H-10); Monte Carlo malik ko dikhana |
| 3 | **Slippage model se zyada**; kaagaz par munafa, asli mein nuksan | Slippage grid; khud ka depth record; Stage2 calibration; kill criteria 3 |
| 4 | **Bot aur Pehredaar ek saath exit**, account net short | Lease, "Pehredaar ne control liya", invariant tests, fault injection |
| 5 | **Shared token kaam nahi karta** (F-76) ya Pehredaar order cancel nahi kar sakta | Real Money se pehle asli test; fail par design badlo |
| 6 | **Feed chupchaap atakta hai**, purane bhav par faisla | Do timestamp wali taazgi, `Ghadi_Skew_Sakht_Hadd`, heartbeat RED, Pehredaar ka apna milaan |
| 7 | **Dohra order** timeout ke baad | Entry kabhi bina pushti dobara nahi; unique Order Tag; Intent Log |
| 8 | **Expiry din gamma**: stop kood jaata hai | Worst-Case Nuksan se risk, H-04, expiry subah Lot cut vikalp |
| 9 | **Niyam ya bazaar badla** (samay, STT, lot, expiry din) aur bot purane niyam par | Roz Instrument Master + timing jaanch; Tarikh wali baatein ki mahine ki review |
| 10 | **Gates itne sakht ki trade hi na bane**; malik niyam dheele karta hai (overfitting) | `Trade_Kam_Din_Ginti`; Shadow Trade se Gate ki keemat; badlaav sirf OOS + Paper ke baad |
| 11 | **Dashboard hack**, nakli hukm | Signed hukm, 2FA, Pehredaar sirf Kill maane, Dashboard par token nahi |
| 12 | **Supply-chain**: dependency mein malicious code chaabi churaye | Hash-lock, audit, kam dependencies, TLS grep, egress allowlist |
| 13 | **Static IP ya token din mein band**; bot andha, trade khula | Broker Stop hamesha broker par; token-band par entry band + alert; IP kabhi din mein nahi badlo |
| 14 | **Malik ka haath ka trade** bot ke trade se mil jaata hai | Foreign Position wale instrument mein bot trade nahi (F-11) |
| 15 | **Revenge / override**: bure din malik Stage Override ya niyam dheela karta hai | Override sirf 1 Lot + likhit pushti; niyam-file sirf agle din se; kill criteria par malik ki likhit jaanch |

---

## Self-check (Deliverable 3)

| Check | Nateeja |
|---|---|
| "Profit ki guarantee nahi" pehle, SEBI study ke source ke saath | PASS (§0) |
| Cost model official source aur tarikh ke saath | PASS (§1; BSE notice verify nahi hua, likha hai) |
| Data plan: srot, kharcha, quality, 10 lakh mein kya | PASS (§2) |
| Backtest: event-driven, live code, depth fill, latency, WF, OOS, stability, multiple-testing, Monte Carlo, regime | PASS (§3) |
| Ablation aur Shadow → Active ka data-based niyam | PASS (§4) |
| Risk-of-ruin hisaab, Daily limit vs SL, Lot cut/drawdown simulation, sizing vikalp bina overwrite | PASS (§5; script `scratch/risk_sim/`) |
| Har hypothesis ka test aur success metric | PASS (§6) |
| Stage Gates (CI ke saath) aur kill criteria | PASS (§7) |
| Pre-mortem top 15 | PASS (§8) |
| "Profit pakka" / "100% safe" nahi | PASS |
| Andaze saaf "andaza" likhe | PASS (Monte Carlo ke saare inputs andaza hain; asli trades se dobara chalana hai) |
