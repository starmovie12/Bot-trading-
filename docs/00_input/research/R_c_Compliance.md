# R-c: SEBI / NSE / BSE / Upstox niyam (Compliance research)

**Tarikh:** 10 Nov 2026 (aaj NSE aur BSE par chhutti hai: Diwali-Balipratipada).
**Kisne likha:** research subagent (R-c). Sirf research. Koi Upstox account, key ya token use nahi hua.
**Kaise padhein:** har claim ke saath source ka ID hai, jaise [S3] ya [U5]. Poora URL Section 10 mein hai. **Saare sources 10 Nov 2026 ko dekhe gaye** (dekha: 10 Nov 2026). "Primary" matlab SEBI, NSE, BSE ya Upstox ka apna page/PDF. "Secondary" matlab news, blog ya forum.
**Kanooni salah nahi:** yeh sirf facts hain. Kanoon aur tax ke faisle CA/vakil se confirm karne hain (Section 8).

## Saar (10 line)
1. SEBI retail algo framework (circular 4 Feb 2025 [S1]) **1 April 2026 se sab brokers par poori tarah lagu** hai (SEBI circular 30 Sep 2025, para 8 [S2]). Idea ki yeh baat sahi hai.
2. NSE/BSE standard: client ki API se aaya **har order "algo" order** maana jaata hai. **10 orders per second (OPS) per exchange** tak exchange registration nahi chahiye, broker generic Algo ID (NSE par "99999") lagata hai. 10 OPS se upar algo exchange par register karna padta hai [S3][S4][S7][S8].
3. Static IP: **ek primary + ek optional secondary**, **calendar week mein ek baar se zyada nahi badal sakte**. Har API session roz agle trading din se pehle logout hona chahiye. OAuth + 2FA zaroori hai, open API band hai [S1][S3][S7].
4. Naya khatra jo idea mein nahi hai: NSE standard A.4 kehta hai ki client ke paas kai API keys hon toh **bina registration wala algo sirf ek pehle se tay API key se chalega** [S3][S7]. Pehredaar ka alag Upstox app (alag API key) isse takra sakta hai. Upstox aur CA/vakil se confirm karna zaroori hai.
5. Exchange par **algo market order allowed nahi** [S7]. Upstox market order ko sirf `market_protection` (MPP) ke saath leta hai, 0 dene par reject [U5][U8]. **Options par SL-M exchange 27 Sep 2021 se reject karta hai** [S19]. Broker Stop ke liye SL (limit) hi rasta hai.
6. Bada badlav: **3 Aug 2026 se F&O 3:40 PM tak** chalta hai (cash market mein Closing Auction Session aaya) [S12][U19]. **7 Dec 2026 se index F&O 3:45 PM tak, par expiry ke din expire hone wale index contract 3:30 PM par band** [S13]. Expiry settlement ka tareeka bhi badla hai.
7. Expiry din (10 Nov 2026 ko sahi): Nifty weekly **Tuesday**, BankNifty sirf monthly (**aakhri Tuesday**), Sensex weekly **Thursday** [S10][S11][S18]. Lot: Nifty 65, BankNifty 30, Sensex 20 [S16][S18]. Freeze (2 Nov 2026 se): Nifty 1800, BankNifty 900 [S17].
8. Upstox: order APIs (place, modify, cancel, multi, GTT milakar) **10/sec, 500/min, 2000/30 min**; token **agle din 3:30 AM** tak; **F&O auto square-off 3:25 PM** (3:24 PM ke baad naya intraday order nahi); **X-Algo-Name header sirf exchange-approved algo ke liye zaroori** [U1][U10][U21][U22][U5].
9. Upstox ne **TOTP + PIN se token lene ka official API** diya hai [U10]. Idea mein likha "Upstox login automatic karne ki salah nahi deta" ab purana hai. Par iska security aur compliance faisla abhi baaki hai (Section 8).
10. SEBI ki latest study (Aug 2026): FY26 mein **87.7%** individual F&O traders haare, kul nuksan **₹91,685 crore**. **Option buyers mein ~90% loss-makers** the [S24][S25]. Isliye profit ki koi guarantee nahi di ja sakti.

---

## (1) SEBI / NSE / BSE retail algo framework

| # | Baat | Kis tarikh tak sahi | Source | Primary/Secondary |
|---|---|---|---|---|
| 1.1 | SEBI circular **SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013**, 4 Feb 2025, "Safer participation of retail investors in Algorithmic trading". Asli lagu tarikh 1 Aug 2025 thi (para 7b). | 10 Nov 2026 tak lagu | [S1] | Primary |
| 1.2 | 29 Jul 2025 ke circular se tarikh 1 Oct 2025 hui. Phir **SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/132, 30 Sep 2025**: taiyar brokers 1 Oct 2025 se live; baaki ke liye milestones (31 Oct 2025 apply, 30 Nov 2025 registration, 3 Jan 2026 mock); milestone chhootne par 5 Jan 2026 se naye retail API algo client nahi. **Para 8: 1 April 2026 se framework sab brokers par lagu.** | 1 Apr 2026 se lagu; 10 Nov 2026 tak koi aur extension nahi mila | [S2] | Primary |
| 1.3 | Broker principal hai, algo provider uska agent (para 5.I.a). Broker **open API allow nahi karega**; access sirf "unique vendor client specific API key aur broker ki whitelist ki hui static IP" se. **Sirf OAuth** authentication, baaki band. **2FA** zaroori. Broker sirf empanelled algo providers se deal karega. | 10 Nov 2026 tak | [S1] para 5.I.d | Primary |
| 1.4 | Khud likha algo (tech-savvy retail investor) exchange par **sirf tab register karna hai jab OPS threshold paar ho**. Registered algo sirf **family** (khud, pati/patni, dependent bachche, dependent maa-baap) ke liye use ho sakta hai, doosron ke liye nahi. | 10 Nov 2026 tak | [S1] para 5.I.c | Primary |
| 1.5 | NSE implementation standards: **NSE/INVG/67858, 5 May 2025**. BSE ne wahi standards **Notice 20250506-3, 6 May 2025** ke annexure mein diye (annexure ka text NSE jaisa mila). | 10 Nov 2026 tak (NSE ne 30 Apr 2026 ke consolidated circular mein shaamil kiya) | [S3][S8][S7] | Primary |
| 1.6 | **OPS threshold (TOPS): "not exceeding 10 orders per second" per exchange** (section F mein "per exchange/segment"). Isse neeche client ko algo registration nahi chahiye. Threshold **broker server ki calendar clock second** par ginta hai. Exchange notice dekar ise badal sakta hai. Broker client ke liye isse kam limit rakh sakta hai. Limit se upar wale order broker reject karega. | 10 Nov 2026 tak | [S3] B.2, B.5, F; [S7] 8.3.2.2 | Primary |
| 1.7 | **Modify aur cancel OPS mein gine jaate hain?** NSE/BSE ke text mein yeh saaf nahi likha (sirf "orders per second"). Upstox apni seema mein place, modify, cancel, multi aur GTT ko milakar ginta hai. | Exchange ki baat: **verify nahi hua**. Upstox wali baat 10 Nov 2026 tak sahi | [S3][U1] | Primary (Upstox), exchange par saaf likha nahi mila |
| 1.8 | 10 OPS se upar: algo **har us exchange par register** karna hoga jahan chalega. Broker details exchange ko bhejta hai, exchange registration ID (Algo ID) deta hai. Logic badle toh re-registration. | 10 Nov 2026 tak | [S3] C.1-C.2; [S7] | Primary |
| 1.9 | **Algo-ID tagging:** sab algo orders (threshold ke upar aur neeche) par exchange ka unique identifier. NSE: client API ka bina-registration algo (10 OPS ke andar) **sirf ek pehle se tay API key** se chalega, aur broker Algo ID field mein **"99999"** aur NNF ID ka 13th digit **"0"** bhejta hai. Client Direct API ka NNF ID "444444444444" se shuru hota hai. | 10 Nov 2026 tak | [S4] para 2.1, 8.2.4; [S7] 8.4.6; [S6] Q7-Q8 | Primary |
| 1.10 | **Kai API keys:** client ko kai API keys mil sakti hain. Har key same primary/secondary IP ya alag IP se map ho sakti hai. **"Non-registered algos are run only through one of the predefined API keys. Other API keys can be used only for registered algos."** | 10 Nov 2026 tak | [S3] A.3-A.4; [S7] | Primary |
| 1.11 | **Static IP:** client ek primary IP de sakta hai, ya redundancy ke liye ek secondary bhi. IP **calendar week mein ek baar se zyada nahi** badal sakta (khaas haalat mein broker se baat). Ek static IP ek samay ek hi client se jud sakta hai (family ke saath share ho sakta hai). | 10 Nov 2026 tak | [S3] A.1-A.7; [S8] | Primary |
| 1.12 | Static IP **sirf "Tech-savvy" client** (khud API se order bhejne wala) ke liye zaroori. Vendor platform broker ke server par ho toh broker ke server ki IP lagti hai. Yeh bot "tech-savvy" category mein aata hai, isliye **static IP chahiye**. | 10 Nov 2026 tak | [S6] Q3, Q6, Q10; [S7] 8.4 note | Primary |
| 1.13 | **Daily logout:** "All API sessions shall be compulsorily logged out every day before the start of the next trading day." | 10 Nov 2026 tak | [S3] A.8 | Primary |
| 1.14 | **White box vs black box:** white box = logic user ko pata aur dohraya ja sake (Execution, TWAP, VWAP). Black box = logic user ko pata nahi (Arbitrage, Alpha seeking, HFT, Scalping, Others). **Black box provider ko SEBI Research Analyst (RA) banna padega** aur har algo ki detailed research report rakhni hogi. Logic badle toh naya algo register. Registered black box mein modification allowed nahi. | 10 Nov 2026 tak | [S1] para 5.V; [S4] 2.4.5, 2.7, 9.9 | Primary |
| 1.15 | **Hosting:** algo provider ke saare strategies **broker ke server par** chalne chahiye. Par **tech-savvy client apni static IP wali machine par** apna algo chala sakta hai. | 10 Nov 2026 tak | [S6] Q4-Q5; [S4] para 14 | Primary |
| 1.16 | **Algo market order:** "Algo orders with order type as Market Order are not permitted." (Cash market ke Closing Auction Session mein algo market order ki chhoot hai, par yeh F&O options ke liye nahi.) | 10 Nov 2026 tak | [S7] 8.1.12; [S6] Q11; [S20b] | Primary |
| 1.17 | **Monthly mock:** registered algos ko har mahine mock session mein aana hai, par **individual tech-savvy client ko nahi**. | 10 Nov 2026 tak | [S7] p.21; [S6] Q9 | Primary |
| 1.18 | Broker ko API orders ka **audit trail kam se kam 5 saal** rakhna hai (asli user aur user-id ke saath). | 10 Nov 2026 tak | [S3] I.a | Primary |
| 1.19 | Exchange kisi "rogue algo" ko **kill** kar sakta hai. Broker algo fees/API fees brokerage ke upar le sakta hai. | 10 Nov 2026 tak | [S3] J.2-J.3 | Primary |
| 1.20 | NSE ka naya **consolidated NNF circular NSE/INVG/73992, 30 Apr 2026** ne purana NSE/MSD/67753 badla. Retail algo ke upar wale niyam usmein shaamil hain. | 10 Nov 2026 tak | [S7] | Primary |
| 1.21 | BSE ki retail algo FAQ (3 Nov 2025) maujood hai, par maine use khol kar nahi padha. | **verify nahi hua** | rhnvrm circular index (secondary) | Secondary |

**Bot ke design par asar (meri samajh, CA/Upstox se confirm karna hai):**
- Bot "tech-savvy, within OPS threshold" category mein hai. Exchange registration nahi chahiye agar bot aur Pehredaar milakar 10 OPS se neeche rahein. Threshold **client aur exchange** ke hisaab se ginta hai, app ke hisaab se nahi.
- Pehredaar ka alag Upstox app = alag API key. Rule 1.10 ke hisaab se bina-registration algo sirf ek tay API key se chal sakta hai. **Kya Pehredaar ke exit orders doosri key se allowed hain? Verify nahi hua.** (Section 8, sawal 1.)

---

## (2) Bot doosron ke liye ho toh kya badlega

Abhi bot sirf malik ke apne account ke liye hai. Agar baad mein doosron ko diya gaya, toh yeh niyam lagu ho sakte hain (sab Primary, dekha: 10 Nov 2026; kis tarikh tak sahi: 10 Nov 2026):

| # | Kya badlega | Source |
|---|---|---|
| 2.1 | **Family ki chhoot khatam:** khud ka algo sirf family (khud, pati/patni, dependent bachche, dependent maa-baap) ke liye. Doosre logon ke liye nahi. | [S1] 5.I.c |
| 2.2 | **Algo Provider empanelment** har exchange (NSE, BSE) ke saath. NSE criteria: individual/firm/LLP/company; promoter/director ka **2 saal securities market experience**; **ISO 27001:2022** (empanelment ke 3 mahine mein); pichhle 3 saal ke cyber incident ka declaration; **half-yearly VAPT** CERT-In empanelled auditor se; financial details (CA/CS certified net worth); undertaking. | [S5] Annexure 2; [S4] |
| 2.3 | **Har algo ka exchange registration broker ke zariye**, auditor report aur auditor certificate ke saath. Logic badle toh re-approval. | [S4] 8.2.5; [S3] E.2 |
| 2.4 | **Hosting broker ke server par** (provider ki apni machine se nahi). | [S6] Q4-Q5; [S4] para 14 |
| 2.5 | **Broker ke saath agreement** (commercial/technical). Broker exchanges ko batayega aur due diligence karega. Fees share ho sakti hai, par client ko poori fees ka khulasa. | [S1] 5.III; [S3] E.3-E.5 |
| 2.6 | **Black box ho toh SEBI Research Analyst registration** + har algo ki research report. Black box algo mein baad mein modification nahi. Multiple third-party RA ke black box ek provider host nahi kar sakta. | [S1] 5.V; [S6] Q4; [S4] 9.9 |
| 2.7 | Registered algos ka **monthly mock** zaroori. | [S7] p.21 |
| 2.8 | **Performance/return ka daava (past ya future) karna mana** (SEBI 2 Sep 2022 circular, NSE circular 6 Sep 2022). SEBI ne March 2026 mein aise daavon par kuch brokers par penalty lagayi. | NSE COMP53555 [O1] (primary, maine khola nahi; search snippet), Moneylife [O3] (secondary) - **text verify nahi hua** |
| 2.9 | Kisi aur ka paisa/account chalana (PMS, Investment Adviser) ya doosre ka login use karna: in par alag SEBI niyam ho sakte hain. **Verify nahi hua**, vakil se poochna hai. | - |

---

## (3) F&O measures, expiry, lot, freeze, samay, chhutti

### 3a. SEBI ke index-derivatives niyam

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 3.1 | SEBI circular **SEBI/HO/MRD/TPD-1/P/CIR/2024/132, 1 Oct 2024**. Lagu tarikh: **upfront option premium** buyer se 1 Feb 2025; expiry din calendar spread fayda khatam 1 Feb 2025; **intraday position limit monitoring** 1 Apr 2025; **contract size ₹15-20 lakh** 20 Nov 2024; **ek exchange, ek benchmark index ki weekly expiry** 20 Nov 2024; **expiry din short options par extra 2% ELM** 20 Nov 2024. | 10 Nov 2026 tak lagu | [S9] | Primary |
| 3.2 | Bot ke liye matlab: option khareedne se pehle **poora premium account mein** hona chahiye. Extra 2% ELM sirf **short** (bechne wale) options par hai, buyer par nahi. | 10 Nov 2026 | [S9] 5.1, 5.6 | Primary |
| 3.3 | SEBI **SEBI/HO/MRD/MRD-TPD-1/P/CIR/2025/76, 26 May 2025**: har exchange ke saare equity derivatives ki expiry **Tuesday ya Thursday** mein se ek din. Har exchange ki **ek weekly benchmark index option**. Baaki sab contracts kam se kam 1 mahine ke, mahine ke aakhri hafte ke chune hue din expire. | 10 Nov 2026 tak | [S10] | Primary |
| 3.4 | NSE ne **Tuesday** chuna: 1 Sep 2025 ya baad expire hone wale contracts Tuesday ko; monthly **aakhri Tuesday**. BSE ne **Thursday** chuna. | 10 Nov 2026 tak | NSE: [S11] Primary. BSE: Business Standard/Moneylife (Secondary) + Upstox instrument file [S18] mein Sensex expiry Thursday | NSE Primary, BSE Secondary |
| 3.5 | Intraday position limit (entity level, index options): net ₹5,000 cr, gross ₹10,000 cr (SEBI circular 1 Sep 2025). End-of-day: net ₹1,500 cr, gross ₹10,000 cr (29 May 2025 circular). Yeh bade players ke liye hai, is bot ke size se bahut upar. | 10 Nov 2026 (exact lagu tarikh mein sources alag) | taxguru, Moneylife [O2] | Secondary, **circular text verify nahi hua** |

### 3b. Expiry din, lot, freeze (10 Nov 2026 ki sthiti)

| Index | Weekly expiry | Monthly expiry | Agli expiries (Upstox instrument file, aaj download) | Lot | Freeze limit |
|---|---|---|---|---|---|
| **Nifty 50** (NSE) | Tuesday | Aakhri Tuesday | 17 Nov (Tue), **23 Nov (Mon, monthly; 24 Nov chhutti)**, 1 Dec, 8 Dec, 29 Dec (monthly), **25 Jan 2027 (Mon; 26 Jan chhutti)** | **65** (NSE/FAOP/70616; weekly 6 Jan 2026 se, monthly 27 Jan 2026 se) [S16] | **1800** w.e.f. 2 Nov 2026 (NSE/FAOP/77189) [S17]. Upstox file mein freeze_quantity **1755** (= 27 lot) [S18] |
| **BankNifty** (NSE) | Nahi (sirf monthly) | Aakhri Tuesday | **23 Nov (Mon)**, 29 Dec (Tue), 25 Jan 2027 (Mon) | **30** [S16] | **900** w.e.f. 2 Nov 2026 [S17] |
| **Sensex** (BSE) | Thursday | Aakhri Thursday | 12, 19 Nov, 26 Nov (monthly), 3, 10, 17, 24, 31 Dec (monthly) | **20** (Dec 2026 tak). Upstox file mein **28 Jan 2027 aur aage ke contracts ka lot 25** dikha [S18]. **BSE ka notice verify nahi hua** | Upstox file mein **1000** [S18]. **BSE ka primary source verify nahi hua** |

- 9 Nov 2026 (Mon) ko Nifty weekly expiry hui kyunki 10 Nov chhutti thi (Upstox file mein "09 NOV 26" contract dikha) [S18][S14].
- Chhutti par expiry pichhle trading din par aati hai. Yeh Upstox file ki tarikhon se match karta hai [S18]. Bot ko roz instrument file se expiry lena chahiye, weekday ginkar nahi.

### 3c. Order types, price band

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 3.6 | **SL-M (stop loss market) index aur stock options mein 27 Sep 2021 se band**; exchange reject karta hai ("Function Not Available"). SL (limit) chalu hai. | 10 Nov 2026 tak (koi palat circular nahi mila) | [S19] NSE/FAOP/49677 | Primary |
| 3.7 | **Algo market order allowed nahi** (Section 1.16). | 10 Nov 2026 | [S7] | Primary |
| 3.8 | **Options price band / LPP:** Limit Price Protection = reference price ke dono taraf range. OPTIDX: reference price **≤₹50 par ±₹20**, **>₹50 par ±40%**. LPP se bahar ka limit order reject. Yeh Operating Price Range (OPR) ke upar ek extra check hai. LPP range din bhar badalti hai aur exchange broadcast karta hai. | FAQ version 3.0, Nov 2024; 10 Nov 2026 tak naya version nahi mila | [S20] | Primary |
| 3.9 | NSE (18 Mar 2026): CAS ke baad bhi **options price band ya LPP ka tareeka 9:00 AM se 3:40 PM tak nahi badla**. | 10 Nov 2026 | [S20b] NSE/CMTR/73362 para 3.2.2 | Primary |
| 3.10 | OPR (operating range) index options ke liye kaise banti hai, iska poora formula maine nahi padha. | **verify nahi hua** | - | - |

### 3d. Bazaar ka samay (F&O)

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 3.11 | **Cash pre-open:** 9:00-9:15 AM (order entry 9:00-9:10, random close 9:08-9:10). Continuous trading 9:15 AM se. | 7 Sep 2026 se lagu; 10 Nov 2026 tak | [S12] para 5 | Primary |
| 3.12 | **F&O pre-open sirf futures ke liye** (8 Dec 2025 se). Options ke pre-open ka koi zikr nahi mila. | 10 Nov 2026 | [U27] (broker doc). NSE circular **verify nahi hua** | Secondary-ish |
| 3.13 | **3 Aug 2026 se:** cash market mein F&O stocks ke liye Closing Auction Session (CAS) 3:15-3:35 PM. **Equity derivatives 3:40 PM tak** chalte hain. Post-close 3:50-4:00 PM. | 3 Aug 2026 se **6 Dec 2026 tak** | [S12] para 4.2; [U19] | Primary |
| 3.14 | **Abhi (6 Dec 2026 tak) index option ka expiry settlement:** index ka closing price, jo constituents ke closing price (CAS se) par bana hai. Yaani idea ka "3:00-3:30 PM ausat" abhi lagu **nahi**. | 3 Aug 2026 se 6 Dec 2026 tak | [S12] para 4.9 | Primary |
| 3.15 | **7 Dec 2026 se (SEBI 15 Oct 2026):** CAS 3:30-3:40 PM. **Index derivatives 3:45 PM tak**, par **expiry din expire hone wale index contracts 3:30 PM par band**. Stock derivatives 3:45 PM tak (expiry din bhi). **Index settlement = constituents ke last 30 minute CTS (yaani 3:00-3:30 PM) ke VWAP se bana index value.** Exchange yeh indicative value live dikhayega. | 7 Dec 2026 se lagu (aaj se 27 din baad) | [S13] para 4.2.4, 4.2.5, 4.9, 6.1 | Primary |
| 3.16 | NSE/BSE ka 7 Dec 2026 wala implementation circular maine nahi dekha. | **verify nahi hua** | - | - |

### 3e. Chhutti aur Muhurat (2026)

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 3.17 | NSE F&O 2026 ki bachi chhuttiyan (10 Nov ke baad): **24 Nov 2026 (Tue) Guru Nanak Dev Prakash Gurpurb**, **25 Dec 2026 (Fri) Christmas**. 10 Nov 2026 (Tue, aaj) Diwali-Balipratipada. | Circular 12 Dec 2025; exchange badal sakta hai | [S14] NSE/FAOP/71777 | Primary |
| 3.18 | **Muhurat Trading: Sunday 8 Nov 2026** (ho chuka). Timing alag circular mein aani thi; maine woh circular nahi dekha. | 8 Nov 2026 | [S14] | Primary (timing verify nahi hua) |
| 3.19 | BSE list mein bhi 10 Nov, 24 Nov, 25 Dec 2026 chhutti. | 10 Nov 2026 | [S15] (BSE page, search ke zariye dekha; page khud nahi khola) | Primary-ish |
| 3.20 | CAS ke baad special trading session (jaise Muhurat) ka F&O close: CAS khatam hone ke 10 minute baad (Jan 2026 circular); 7 Dec 2026 se 5 minute baad. | 10 Nov 2026 | [S12] 4.2.5; [S13] 4.2.7 | Primary |
| 3.21 | 2027 ki chhutti list abhi nahi dekhi. 25 Jan 2027 (Mon) monthly expiry dikhti hai, iska matlab 26 Jan (Tue) chhutti maani gayi hai [S18]. | **2027 list verify nahi hua** | - | - |

---

## (4) SEBI ke F&O retail loss studies

| Study | Kya mila (exact numbers) | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| **Jan 2023** (FY19-FY22, top-10 brokers) | FY22 mein **89%** individual traders haare. Average nuksan **~₹1.1 lakh**; active traders mein 90% haare, average ₹1.25 lakh. | Study ki tarikh 25 Jan 2023 | 89%: SEBI PR 22/2024 [S21] (Primary). ₹1.1 lakh aur ₹1.25 lakh: Moneylife/Business Standard [S26] (Secondary; original PDF nahi khola) | Mixed |
| **Sep 2024** (FY22-FY24, PR No. 22/2024, 23 Sep 2024) | **93%** of 1 crore se zyada individual traders ko teen saal mein average **~₹2 lakh** nuksan (transaction cost milakar). Kul nuksan **₹1.8 lakh crore se zyada**; FY24 mein ~₹75,000 crore. Top 3.5% loss-makers (~4 lakh) ka average **₹28 lakh**. Sirf **1%** ne ₹1 lakh se zyada kamaya. Transaction cost: FY24 mein **₹26,000 per person**; FY22-24 mein **~₹50,000 crore** (51% brokerage, 20% exchange fees). FPI aur prop profits ka 97% aur 96% algo trading se. 75% loss-makers ne trading jaari rakhi. | 23 Sep 2024 | [S21] | Primary |
| **Jul 2025** (FY25, PR No. 39/2025, top-13 brokers ~96 lakh traders) | **~91%** individual traders ko FY25 mein net nuksan. Net nuksan **₹1,05,603 crore** (FY25) vs ₹74,812 crore (FY24), transaction cost ke baad. | 7 Jul 2025 (baad mein FY25 figure revise hua, neeche dekho) | [S23] | Primary |
| **Aug 2026** (FY25-FY26 profitability) | Active individual traders **106.2 lakh → 87.5 lakh** (-18%). Loss-makers **90.9% (FY25) → 87.7% (FY26)**. Kul net nuksan **₹91,685 crore** (FY26) vs revised **₹1.12 lakh crore** (FY25; sample 13 se 15 brokers). Average nuksan per person **₹1.13 lakh → ₹1.17 lakh**. Loss-makers ka average nuksan **₹1.47 lakh**, profit-makers ka average profit ₹1.22 lakh. **Options = 92% nuksan**; options mein 87.7% loss-makers, futures mein 66%. Transaction cost ~**₹25,000 crore** har saal (FY25, FY26); STT ₹4,920 cr → ₹6,645 cr. FY22-FY26 transaction cost ~₹1 lakh crore, aadha brokerage. Index options turnover ka **59%** expiry ke din (0DTE) (FY25 mein 70%). FPI aur prop profit ka **99%** "algo entities" se. | Aug 2026 | [S24] | Primary |
| **Aug 2026** (Trading behaviour, ~5,050 traders ka random sample, "indicative") | **97%** individual traders mainly option buyers. **Option buyers mein ~90% loss-makers**, kul nuksan ka 55-65%. "Only Options Buyers" ka average nuksan per loss-maker **₹1.3 lakh**. Experience se fayda nahi: pehle saal ~91% loss-makers, 4+ saal wale 95% se zyada. 100+ din trade karne wale 42% traders = 87% nuksan. | Aug 2026 | [S25] | Primary |

Note: SEBI ke chart mein individuals ke "algo" aur "non-algo" dono groups ka gross P&L minus mein hai (FY25-FY26) [S24, Chart 20]. Matlab algo use karna apne aap faayda nahi deta.

---

## (5) Upstox API niyam

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 5.1 | **Static IP:** "API orders must originate from a registered Static IP"; bina registered IP ke order reject. Lagu: **1 April 2026**. Yeh Place, Modify, Cancel, Multi Order, Cancel Multi, GTT, Exit All par lagta hai. Holdings, positions, funds, historical candle par nahi. | 1 Apr 2026 se; 10 Nov 2026 tak | [U2] | Primary |
| 5.2 | **Har user ke 2 IP (Primary + Secondary), user-level** ("regardless of which OAuth client issued the token"). Ek IP sirf ek customer se jud sakti hai. IPv4 ya IPv6. | 10 Nov 2026 | [U2][U3] | Primary |
| 5.3 | IP **calendar week mein ek baar** badal sakti hai. **Badalte hi purane access tokens band** ho jaate hain. My Apps UI ya `GET/PUT /v2/user/ip` API se (10 Apr 2026 se). Galat IP par error **UDAPI1154**. | 10 Nov 2026 | [U2][U3][U4][U5] | Primary |
| 5.4 | **Algo Name header: `X-Algo-Name`.** Place Order V3 aur Multi Order page: "X-Algo-Name header is **optional and only required if you have an exchange-approved algo strategy**". Value app settings ke Algo name se match honi chahiye. Galat naam par **UDAPI1156**. Announcement page kehta hai "include X-Algo-Name for order tracking" (thoda alag). | 10 Nov 2026; **do pages mein farak hai**, Upstox se confirm karna | [U5][U7][U2] | Primary |
| 5.5 | **Algo ID kaun deta hai:** exchange. Upstox: 10 OPS se upar algo exchange par register ho, exchange Algo ID de, user use Algo App settings mein daale. **10 OPS se kam par registration nahi.** (Upstox likhta hai "registered with SEBI", jabki NSE text "exchange registration" kehta hai.) | 10 Nov 2026 | [U2][S3] | Primary |
| 5.6 | **Rate limit, order APIs (place, modify, cancel, multi, GTT milakar), bina registration algo:** **10/sec, 500/min, 2000/30 min**. SEBI-registered algo: 50/sec, 500/min, 2000/30 min. Baaki standard APIs: 50/sec, 500/min, 2000/30 min. Limit per-API, per-user. Paar karne par "temporary suspension" ho sakta hai. | 10 Nov 2026 | [U1] | Primary |
| 5.7 | **Multi Order:** ek request mein max **10 orders**. Rate limit ke liye page rate-limit page ki taraf bhejta hai, jahan multi order alag number ke saath nahi, combined limit mein hai. BUY pehle, SELL baad mein execute. | 10 Nov 2026 | [U7][U1] | Primary |
| 5.8 | **Ek order kitni baar modify:** Upstox docs mein koi number nahi mila. Dec 2024 community jawab: "no maximum", sirf rate limit. (25 baar wali seema Zerodha Kite forum ki hai.) | **verify nahi hua** (official) | [U25] | Secondary |
| 5.9 | **Access token:** agle din **3:30 AM** tak valid, chahe kabhi bhi banaya ho. Authorization code ek hi baar chalta hai. | 10 Nov 2026 | [U10] | Primary |
| 5.10 | **Ek app, ek token:** "If the app already has an active access token, that token is revoked and a new one is issued" (TOTP section mein likha). Refresh token ka koi zikr docs mein nahi. | 10 Nov 2026 | [U10] | Primary |
| 5.11 | **Extended token:** "primarily for read-only access". **Analytics Token** (20 Mar 2026): 1 saal valid, sirf GET. 6 Jun 2026 se static IP ke saath account APIs (positions, orders, funds, P&L) bhi padh sakta hai. Order nahi laga sakta. Ek account mein ek active analytics token. | 10 Nov 2026 | [U10][U12] | Primary |
| 5.12 | **Login flow:** OAuth 2.0 authorization code. "All logins are handled by upstox.com". 2FA ke liye SMS OTP ya TOTP. **Semi-automated:** Access Token Request API se request, malik phone/WhatsApp par approve kare, token notifier webhook par aata hai. | 10 Nov 2026 | [U9][U11] | Primary |
| 5.13 | **TOTP login API:** `POST /v2/totp-login/authorization/token`, header `x-api-key`, body mein user ka **6-digit TOTP aur 6-digit PIN**. Sirf "individual" apps ke liye. Purana token band hota hai. Rate limit: 1/sec, 10/min, 60/30 min. | 10 Nov 2026 | [U10][U1] | Primary |
| 5.14 | **Logout API** hai (session aur token band karta hai). | 10 Nov 2026 | [U26] Login page | Primary |
| 5.15 | **Market Data Feed V3:** WebSocket + **Protobuf**. Modes: **ltpc, option_greeks, full (5 depth), full_d30 (30 depth)**. Normal: **2 connections per user**; ek mode mein LTPC 5000, Option Greeks 3000, Full 2000 instrument keys; kai modes milakar 2000/2000/1500. **Upstox Plus:** 5 connections, Full D30 50 keys per connection. Pehla message market status, doosra snapshot, phir live ticks. CAS fields (iep, rp, ieq) aur India VIX bhi. | 10 Nov 2026 | [U13][U14] | Primary |
| 5.16 | Feed ki **update frequency / snapshot interval** docs mein nahi mili. | **verify nahi hua** | [U13] | - |
| 5.17 | **Portfolio stream feed:** WebSocket par order, gtt_order, position, holding updates; doosre platform (app/web) se lage order ke update bhi aate hain. | 10 Nov 2026 | [U15] | Primary |
| 5.18 | **Option Chain API** (`/v2/option/chain`, instrument + expiry). **Option Greek API** (`/v3/market-quote/option-greek`), ek request mein **max 50 instruments**. Naye Market Info APIs (OI, PCR, Max Pain, FII/DII) 11 May 2026 se. | 10 Nov 2026 | [U16][U17][U26] | Primary |
| 5.19 | **Order types:** MARKET, LIMIT, SL, SL-M. **Market order bina protection ke reject** (UDAPI1158). `market_protection`: **-1 = auto (default), 1-25 = % custom, 0 = reject**. Sirf Market aur SL-M par lagta hai (11 Mar 2026 se, "Beta"). Exchange options par SL-M reject karta hai [S19]; Upstox options SL-M ko kaise sambhalta hai, **verify nahi hua**. | 10 Nov 2026 | [U5][U8] | Primary |
| 5.20 | **Auto-slicing:** `slice: true` bhejne par Upstox freeze quantity ke hisaab se order tod deta hai; har tukde ka correlation_id `_1`, `_2`... Default false. | 10 Nov 2026 | [U5] | Primary |
| 5.21 | **GTT** API hai, trailing stop loss ke saath (30 Jun 2025 se). Static IP GTT par bhi lagu. | 10 Nov 2026 | [U26][U2] | Primary |
| 5.22 | Place Order API **5:30 AM se 12:00 AM** tak hi chalta hai (UDAPI100074). | 10 Nov 2026 | [U5] | Primary |
| 5.23 | **Kill Switch API** (10 Apr 2026): segment band karne par us segment ke open orders cancel aur naye orders block. **Pehle saari open positions band karni padti hain.** | 10 Nov 2026 | [U20] | Primary |
| 5.24 | **Intraday auto square-off (F&O): 3:25 PM** (4 Sep 2026 announcement: 3:20 se 3:25). Help center: Equity Derivatives mein **3:24 PM ke baad naya intraday order nahi**. Upstox square-off kare toh **₹88.5 (₹75+GST) basic plan / ₹59 Plus** charge. Volatility mein samay badal sakta hai. | 4 Sep 2026 se; 10 Nov 2026 tak | [U21][U22] | Primary |
| 5.25 | **Sandbox:** sirf Place, Place V3, Multi, Modify, Modify V3, Cancel, Cancel V3 orders ka payload test. Token **30 din**. **Ek user ek sandbox app.** Sandbox token se live order nahi. Docs ke hisaab se yeh payload/integration test ke liye hai; asli market depth ya fill simulate karta hai, aisa nahi likha. Paper Mode ke liye bot ka apna simulator chahiye. | 10 Nov 2026 | [U18] | Primary |
| 5.26 | **CAS (3 Aug 2026 se):** NSE_FO/BSE_FO ka NORMAL_CLOSE **3:40 PM**. CAS ke niyam (SL order nahi, slicing nahi) sirf CAS-eligible cash stocks par; NSE_FO mein CAS nahi. | 3 Aug 2026 se; 7 Dec 2026 se samay badlega [S13] | [U19] | Primary |
| 5.27 | **API charge:** "API Subscription Charges: Free". **API order brokerage ₹10/order**: brokerage page par "Valid till 31 Dec 2025", Trading API page par "Valid till 31st Dec 2026" (dono pages mein farak). Normal F&O options brokerage: **flat ₹20 per executed order**. Detail kharcha R-d agent dekhega. | 10 Nov 2026; **API rate ki aakhri tarikh mein farak** | [U23][U24] | Primary |

---

## (6) Record aur tax facts (sirf facts; CA se confirm)

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 6.1 | Broker ko API orders ka audit trail **kam se kam 5 saal**. | 10 Nov 2026 | [S3] I.a | Primary |
| 6.2 | **SEBI (Stock Brokers) Regulations, 2026** 7 Jan 2026 ko notify, 1992 wale regulations ki jagah. Broker ke books aur records **8 saal** (pehle 5). | 7 Jan 2026 se | KPMG flash [T1] | Secondary (SEBI ka text **verify nahi hua**) |
| 6.3 | **Income-tax Act, 2025: 1 April 2026 se lagu.** Income-tax Rules, 2026 20 Mar 2026 ko notify (secondary). FY 2025-26 ki income par purana 1961 Act (secondary). | 1 Apr 2026 se | incometaxindia.gov.in page (search mein dikha, kholne par 403) + Deccan Herald [T2] | Secondary |
| 6.4 | Books of account: naya **Section 62** (purana 44AA ki jagah). **Rule 46** (purana Rule 6F ki jagah): books aur documents **7 tax years** tak rakhne (tax year khatam hone se), reopen case mein uske khatam hone tak. Electronic books ka roz backup India ke server par. Article draft rules (7 Feb 2026) ka hai. | Final notified Rule 46 ka text **verify nahi hua** | [T3] | Secondary |
| 6.5 | Tax audit: naya **Section 63** (purana 44AB). Turnover **₹1 crore** se upar audit; cash receipts/payments 5% ya kam ho toh **₹10 crore**. Ek source profit-test (presumptive) bhi batata hai. | **verify nahi hua** (official text nahi padha) | [T4] | Secondary |
| 6.6 | F&O income ko business income (non-speculative) maana jaata hai aur F&O "turnover" ICAI guidance note ke hisaab se ginte hain: maine is session mein verify nahi kiya. | **verify nahi hua** | - | - |

Bot ke liye matlab: har order, fill, Intent Log aur P&L ka record **kam se kam 8 saal** rakhne ka plan theek rahega (broker 8 saal aur tax 7 saal mein jo bada ho). Yeh sirf andaza hai, CA confirm kare.

---

## (7) Jane Street case: update (10 Nov 2026 tak)

| # | Baat | Kis tarikh tak sahi | Source | P/S |
|---|---|---|---|---|
| 7.1 | SEBI **interim order 3 Jul 2025** (WTM/AN/MRD/MRD-SEC-3/31516/2025-26, Whole Time Member Ananth Narayan G.). Aarop: BankNifty index manipulation. **₹4,843,57,70,168 (≈₹4,843.57 crore)** impound, escrow account. | 3 Jul 2025 | [S27] | Primary |
| 7.2 | Jane Street ne escrow mein paisa jama kiya; SEBI ne **21 Jul 2025** ko market access ki rok hatayi (investigation jaari). | 21 Jul 2025 | ThePrint/Outlook [S30] | Secondary |
| 7.3 | SAT mein Oct 2026 mein documents (order logs, SEBI-NSE ki correspondence, surveillance report) ki maang par sunwai hui. SEBI ka kehna: 10 GB se zyada data diya, order logs par bharosa nahi kiya. **21 Oct 2026 ko SAT ne order reserve kiya.** Yeh documents ki arzi hai, manipulation ka final faisla nahi. | 21 Oct 2026 | Business Standard 8 Oct 2026 [S28]; Newsbytes/Lapaas Voice [S29] | Secondary |
| 7.4 | 21 Oct 2026 ke baad (Nov 2026 tak) SAT ka faisla ya koi nayi khabar **nahi mili**. Jane Street aaropon ko nahi maanta. | 10 Nov 2026 | Search (koi result nahi) | **verify nahi hua** |

---

## (8) CA / vakil / Upstox se confirm karne ki list (sawal)

1. Pehredaar ka **alag Upstox app (alag API key)** se exit order bhejna kya NSE standard A.4 ("non-registered algos sirf ek predefined API key se") ke khilaf hai? Kya dono apps ko ek hi "API key" maana jaayega, ya Pehredaar ke liye registration chahiye? (Upstox + vakil)
2. 10 OPS threshold mein **modify aur cancel** gine jaate hain ya nahi? Bot aur Pehredaar ke orders milakar ginte hain na? (Upstox/NSE)
3. Bot "tech-savvy within OPS" category mein hai: kya Upstox ko koi form, declaration ya "Algo Trading App" approval chahiye? Kya X-Algo-Name bhejna hai ya nahi? (Upstox)
4. **TOTP + PIN API** se roz automatic login karna SEBI ke "OAuth + 2FA" niyam ke andar hai? TOTP secret server par rakhna kitna safe aur allowed hai? Ya semi-automated (malik phone par approve) hi rakhein? (Upstox + vakil)
5. Upstox options par **SL-M** order lene par kya karta hai (reject ya SL-limit mein badalta hai)? `market_protection=-1` ka asli percentage options ke liye kya hai? (Upstox)
6. Static IP badalne par sab tokens band hote hain: Primary machine kharab ho toh IP badalna padega. Hafte mein ek baar ki seema mein emergency ka kya rasta hai? (Upstox)
7. Agar bot doosron (family ke bahar) ko diya: kya hum "Algo Provider" banenge? Bot white box hai ya black box (RA registration)? PMS/Investment Adviser niyam lagenge? (vakil)
8. Family ke liye bot: pati/patni ya dependent maa-baap ke account par chalana bina extra registration allowed hai? (vakil)
9. F&O options buying ki income: business income (non-speculative) hai na? ITR form, presumptive (44AD/naya section) lena chahiye ya nahi? (CA)
10. Naye Income-tax Act 2025 mein F&O **turnover** kaise ginein aur tax audit (Section 63) kab lagega? Profit kam ho ya nuksan ho toh audit chahiye? (CA)
11. Books of account kitne saal rakhne hain (Rule 46: 7 tax years?) aur bot ke electronic logs ka India mein roz backup zaroori hai? (CA)
12. Nuksan carry-forward ke liye ITR samay par bharna, aur F&O nuksan ko salary se set-off na karna: naye Act mein kya niyam hai? (CA)
13. Sensex ka lot 25 (Jan 2027 contracts se) aur Sensex freeze limit: BSE ka official notice kaunsa hai? (broker/BSE)
14. 7 Dec 2026 se expiry din index options 3:30 PM par band: NSE/BSE ka implementation circular kab aaya aur Upstox ka square-off samay badlega? (Upstox)
15. API order brokerage ₹10 ki aakhri tarikh: 31 Dec 2025 ya 31 Dec 2026? (Upstox)

---

## (9) Idea file ke "Tarikh wali baatein" ke 6 points: kya sahi, kya badla, kya verify nahi hua

| Point | Sahi nikla | Badla / purana | Verify nahi hua |
|---|---|---|---|
| **1. SEBI Retail Algo Niyam** | 1 Apr 2026 se poori tarah lagu [S2]; static IP ek ya do [S3]; roz login/2FA, refresh-token nahi [S1][S3][U10]; 10 orders/sec/exchange/client, upar registration [S3]; IP hafte mein ek baar se zyada nahi [S3]. Ab source primary hai (pehle sirf broker blog). | "Har algo order par exchange ki di Algo-ID": 10 OPS se neeche **broker generic ID "99999"** lagata hai, client ko apni ID nahi chahiye [S4]. "Market order MPP mein badal jaata hai": sirf tab jab `market_protection` -1 ya 1-25 ho; 0 par reject; exchange par algo market order allowed nahi [U5][S7]. **Naya:** kai API keys par rule A.4 (Pehredaar ke liye khatra) [S3]. | Modify/cancel exchange ke OPS mein gine jaate hain ya nahi. |
| **2. Expiry weekday aur settlement** | Nifty weekly Tuesday, Sensex weekly Thursday, BankNifty monthly aakhri Tuesday, aakhri Tuesday ko NSE ke saare F&O ek saath [S10][S11][S18]. Sensex monthly aakhri Thursday [S18]. Nov 2026: Nifty 9 Nov (Mon), monthly 23 Nov (Mon) [S14][S18]. | **Settlement "3:00-3:30 PM ausat"**: 3 Aug se 6 Dec 2026 tak **lagu nahi** (CAS closing price se) [S12]; **7 Dec 2026 se phir constituents ka 3:00-3:30 PM VWAP** [S13]. **F&O close ab 3:40 PM**, 7 Dec 2026 se 3:45 PM aur expiry din expire hone wale index contract 3:30 PM [S12][S13]. Naya: 25 Jan 2027 monthly (Mon) [S18]. | BSE ka Thursday wala notice khud nahi padha (secondary + Upstox file). |
| **3. Lot, Freeze, Market-Stop** | Nifty 65, BankNifty 30 [S16]; Sensex 20 (Dec 2026 tak) [S18]; freeze Nifty 1800, BankNifty 900 w.e.f. 2 Nov 2026 (NSE/FAOP/77189) [S17]; options par SL-M band (NSE/FAOP/49677, 27 Sep 2021) [S19]. | **Sensex lot Jan 2027 contracts se 25** (Upstox file) [S18]. Upstox file mein Nifty freeze **1755** (27 lot) dikhta hai. Sensex freeze Upstox file mein **1000** [S18]. | Sensex 25 lot aur 1000 freeze ka BSE notice; 5 Oct 2026 wali purani limits (3,510 / 1,440) maine primary se nahi dekhin. |
| **4. Khaas Trading Din** | Muhurat 8 Nov 2026 (Sunday) [S14]. | Bachi 2026 chhuttiyan: 24 Nov, 25 Dec [S14]. CAS ke baad special session mein F&O ka band hone ka samay alag niyam se [S12][S13]. | Budget day 2027 ki tarikh/session; Muhurat ka timing circular. |
| **5. Jane Street** | 3 Jul 2025 order, ₹4,843.57 crore impound [S27]; 21 Oct 2026 SAT ne document arzi par order reserve kiya, final faisla nahi [S28][S29]. | Joda: 21 Jul 2025 ko escrow ke baad trading rok hati [S30]. | 21 Oct 2026 ke baad koi nayi khabar nahi mili. |
| **6. Upstox seemayein, token, square-off** | 10/sec, 500/min, 2000/30 min [U1]; token 3:30 AM [U10]; naya token purana band [U10]; extended token read-only [U10]. | **Square-off ka takraav hal: F&O 3:25 PM** (4 Sep 2026), 3:24 PM ke baad naya intraday order nahi [U21][U22]. **"Har order par Algo Name zaroori"**: docs kehte hain sirf exchange-approved algo ke liye zaroori [U5]. **"Multi-order 4/sec"**: abhi ke page par alag number nahi, combined limit [U1][U7]. **TOTP login API officially hai** [U10]. Naya: IP badalne par token band [U4]; Analytics Token 1 saal [U12]; Kill Switch API [U20]. | **"25 modify per order"**: Upstox docs mein nahi mila; community kehti hai limit nahi [U25]. Feed update frequency. |

---

## (10) Sources (sab dekhe: 10 Nov 2026)

**SEBI / NSE / BSE (primary)**
- [S1] SEBI circular 4 Feb 2025, SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013: https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html (PDF: https://www.sebi.gov.in/sebi_data/attachdocs/feb-2025/1738665456458.pdf). Dekha: 10 Nov 2026.
- [S2] SEBI circular 30 Sep 2025, SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/132: https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/1759232056254.pdf. Dekha: 10 Nov 2026.
- [S3] NSE/INVG/67858, 5 May 2025 (Implementation Standards): https://nsearchives.nseindia.com/content/circulars/INVG67858.pdf. Dekha: 10 Nov 2026.
- [S4] NSE/INVG/69255, 22 Jul 2025 (Detailed Operational Modalities, zip): https://nsearchives.nseindia.com/content/circulars/INVG69255.zip. Dekha: 10 Nov 2026.
- [S5] NSE/INVG/70309, 19 Sep 2025 (Corrigendum + empanelment criteria, zip): https://nsearchives.nseindia.com/content/circulars/INVG70309.zip. Dekha: 10 Nov 2026.
- [S6] NSE Retail Algo FAQ (3 Nov 2025): https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQ_Retail_Algo_03112025_NSE.pdf. Dekha: 10 Nov 2026.
- [S7] NSE/INVG/73992, 30 Apr 2026 (Consolidated NNF circular, zip): https://nsearchives.nseindia.com/content/circulars/INVG73992.zip. Dekha: 10 Nov 2026.
- [S8] BSE Notice 20250506-3, 6 May 2025: https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20250506-3 (Annexure: https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?id=20250506-3&attachedId=c4703523-fc81-4733-898d-5348602f3074). Dekha: 10 Nov 2026.
- [S9] SEBI circular 1 Oct 2024, SEBI/HO/MRD/TPD-1/P/CIR/2024/132: https://www.sebi.gov.in/legal/circulars/oct-2024/measures-to-strengthen-equity-index-derivatives-framework-for-increased-investor-protection-and-market-stability_87208.html (PDF: https://www.sebi.gov.in/sebi_data/attachdocs/oct-2024/1727786261636.pdf). Dekha: 10 Nov 2026.
- [S10] SEBI circular 26 May 2025, SEBI/HO/MRD/MRD-TPD-1/P/CIR/2025/76: https://www.sebi.gov.in/sebi_data/attachdocs/may-2025/1748266377271.pdf. Dekha: 10 Nov 2026.
- [S11] NSE/FAOP/68589, 17 Jun 2025 (Tuesday expiry): https://nsearchives.nseindia.com/content/circulars/FAOP68589.pdf. Dekha: 10 Nov 2026.
- [S12] SEBI circular 16 Jan 2026, HO/47/11/11(3)2025-MRD-POD2/I/2765/2026 (CAS): https://www.sebi.gov.in/legal/circulars/jan-2026/introduction-of-closing-auction-session-cas-in-the-equity-cash-segment-and-certain-modifications-in-the-pre-open-auction-session_99122.html (PDF: https://www.sebi.gov.in/sebi_data/attachdocs/jan-2026/1768576287344.pdf). Dekha: 10 Nov 2026.
- [S13] SEBI circular 15 Oct 2026, HO/47/11/11(3)2025-MRD-POD2/I/23843/2026 (CAS review, timings, settlement): https://www.sebi.gov.in/legal/circulars/oct-2026/review-of-certain-aspects-of-the-closing-auction-session-market-timings-and-settlement-methodology-for-derivatives-contracts_105293.html (PDF: https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1792079571420.pdf). Dekha: 10 Nov 2026.
- [S14] NSE/FAOP/71777, 12 Dec 2025 (F&O holidays 2026): https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf. Dekha: 10 Nov 2026.
- [S15] BSE trading holidays page: https://beta.bseindia.com/static/markets/marketinfo/listholi.aspx (search result ke zariye). Dekha: 10 Nov 2026.
- [S16] NSE/FAOP/70616, 3 Oct 2025 (index lot revision): https://nsearchives.nseindia.com/content/circulars/FAOP70616.pdf. Dekha: 10 Nov 2026.
- [S17] NSE/FAOP/77189, 30 Oct 2026 (freeze limits w.e.f. 2 Nov 2026): https://nsearchives.nseindia.com/content/circulars/FAOP77189.pdf. Dekha: 10 Nov 2026.
- [S18] Upstox public instrument files (bina login, 10 Nov 2026 ko download): https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz aur https://assets.upstox.com/market-quote/instruments/exchange/BSE.json.gz. Dekha: 10 Nov 2026. (Broker ka data; exchange circular nahi.)
- [S19] NSE/FAOP/49677, 21 Sep 2021 (SL-M options band 27 Sep 2021 se): https://nsearchives.nseindia.com/content/circulars/FAOP49677.pdf. Dekha: 10 Nov 2026.
- [S20] NSE FAQs on Limit Price Protection v3.0 (Nov 2024): https://nsearchives.nseindia.com/web/sites/default/files/inline-files/FAQs_on_Limit_Price_Protection.pdf. Dekha: 10 Nov 2026.
- [S20b] NSE/CMTR/73362, 18 Mar 2026 (CAS SOP; options price band/LPP; algo market orders): https://nsearchives.nseindia.com/content/circulars/CMTR73362.pdf. Dekha: 10 Nov 2026.
- [S21] SEBI PR No. 22/2024, 23 Sep 2024: https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727086965496.pdf. Dekha: 10 Nov 2026.
- [S23] SEBI PR No. 39/2025 aur study (Jul 2025): https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900802566.pdf, https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751900271726.pdf. Dekha: 10 Nov 2026.
- [S24] SEBI study "Profitability of Individual Traders in the Equity Derivatives Segment (FY25-FY26)", Aug 2026: https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf. Dekha: 10 Nov 2026.
- [S25] SEBI study "Trading Behaviour of Individual Traders in the EDS (FY25-FY26)", Aug 2026: https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233601328.pdf. Dekha: 10 Nov 2026.
- [S27] SEBI interim order, Jane Street, 3 Jul 2025: https://www.sebi.gov.in/sebi_data/attachdocs/jul-2025/1751584518593.pdf. Dekha: 10 Nov 2026.

**Upstox (primary, official)**
- [U1] Rate Limits: https://upstox.com/developer/api-documentation/rate-limiting/. Dekha: 10 Nov 2026.
- [U2] Algo Registration & Static IP announcement: https://upstox.com/developer/api-documentation/announcements/algo-trading-circular/. Dekha: 10 Nov 2026.
- [U3] My Apps / Static IPs: https://upstox.com/developer/api-documentation/appendix/my-apps-support-for-algo-trading-circular/. Dekha: 10 Nov 2026.
- [U4] Update Static IPs API: https://upstox.com/developer/api-documentation/update-app-static-ips/. Dekha: 10 Nov 2026.
- [U5] Place Order V3: https://upstox.com/developer/api-documentation/v3/place-order/. Dekha: 10 Nov 2026.
- [U6] Modify Order V3: https://upstox.com/developer/api-documentation/v3/modify-order/. Dekha: 10 Nov 2026.
- [U7] Place Multi Order: https://upstox.com/developer/api-documentation/place-multi-order/. Dekha: 10 Nov 2026.
- [U8] Market Protection (MPP): https://upstox.com/developer/api-documentation/announcements/market-protection/. Dekha: 10 Nov 2026.
- [U9] Authentication: https://upstox.com/developer/api-documentation/authentication/. Dekha: 10 Nov 2026.
- [U10] Get Token (TOTP section ke saath): https://upstox.com/developer/api-documentation/get-token/. Dekha: 10 Nov 2026.
- [U11] Access Token Request: https://upstox.com/developer/api-documentation/access-token-request/. Dekha: 10 Nov 2026.
- [U12] Analytics Token + Static IP: https://upstox.com/developer/api-documentation/announcements/analytics-token-static-ip/. Dekha: 10 Nov 2026.
- [U13] Market Data Feed V3: https://upstox.com/developer/api-documentation/v3/get-market-data-feed/. Dekha: 10 Nov 2026.
- [U14] Websocket Plus: https://upstox.com/developer/api-documentation/announcements/websocket-plus/. Dekha: 10 Nov 2026.
- [U15] Portfolio Stream Feed: https://upstox.com/developer/api-documentation/get-portfolio-stream-feed/. Dekha: 10 Nov 2026.
- [U16] Put/Call Option Chain: https://upstox.com/developer/api-documentation/get-pc-option-chain/. Dekha: 10 Nov 2026.
- [U17] Option Greek: https://upstox.com/developer/api-documentation/option-greek/. Dekha: 10 Nov 2026.
- [U18] Sandbox: https://upstox.com/developer/api-documentation/sandbox/. Dekha: 10 Nov 2026.
- [U19] Closing Auction Session support: https://upstox.com/developer/api-documentation/announcements/closing-auction-session/. Dekha: 10 Nov 2026.
- [U20] Kill Switch API: https://upstox.com/developer/api-documentation/announcements/kill-switch-api/. Dekha: 10 Nov 2026.
- [U21] Square-off timings change (4 Sep 2026): https://upstox.com/announcements/revised-timings/important-update-intraday-square-off-timings-are-changing/. Dekha: 10 Nov 2026.
- [U22] Help center, auto square-off: https://help.upstox.com/support/solutions/articles/252251-what-is-auto-square-off-and-what-is-the-auto-square-off-timings-for-different-segments. Dekha: 10 Nov 2026.
- [U23] Trading API page: https://upstox.com/trading-api/. Dekha: 10 Nov 2026.
- [U24] Brokerage charges: https://upstox.com/brokerage-charges/. Dekha: 10 Nov 2026.
- [U26] Announcements index aur Login page: https://upstox.com/developer/api-documentation/announcements/, https://upstox.com/developer/api-documentation/login/. Dekha: 10 Nov 2026.
- [U27] NSE pre-open for futures (Upstox): https://upstox.com/developer/api-documentation/announcements/nse-pre-open-session/. Dekha: 10 Nov 2026.

**Secondary**
- [U25] Upstox community thread (modify limit): https://community.upstox.com/t/is-there-any-limit-on-order-price-modifications-through-api-call/7640. Dekha: 10 Nov 2026.
- [S26] Jan 2023 study ke numbers: https://www.moneylife.in/article/90-percentage-individual-traders-in-equity-fo-segment-incurred-losses-sebi-research/69634.html, https://www.business-standard.com/amp/article/markets/sebi-study-suggests-89-retail-traders-in-equity-f-o-suffered-losses-123012501466_1.html. Dekha: 10 Nov 2026.
- [S28] Business Standard, 8 Oct 2026: https://www.business-standard.com/markets/news/jane-street-accuses-sebi-of-shifting-goalposts-in-sat-hearing-on-documents-126100801282_1.html. Dekha: 10 Nov 2026.
- [S29] SAT order reserved (21 Oct 2026): https://www.newsbytesapp.com/news/business/sat-reserves-order-in-jane-street-document-disclosure-case/story, https://lapaasvoice.com/sat-reserves-order-in-jane-street-case-as-firm-seeks-more-sebi-documents. Dekha: 10 Nov 2026 (search snippet; newsbytes page 403).
- [S30] Jane Street trading rok hati (21 Jul 2025): https://theprint.in/economy/sebi-lifts-trading-ban-on-jane-street-after-rs-4843-cr-deposit-in-escrow-account/2697696. Dekha: 10 Nov 2026.
- [T1] KPMG flash, SEBI Stock Brokers Regulations 2026: https://www.in.kpmg.com/taxflashnews/KPMG-Flash-News-SEBI-Notifies-Stock-Brokers-Regulations-2026-and-modification-of-Technical-Glitch-Framework.pdf. Dekha: 10 Nov 2026.
- [T2] Income-tax Act 2025 lagu: https://www.incometaxindia.gov.in/w/income-tax-act-2025-comes-into-force-from-1st-april-2026 (403 mila), https://www.deccanherald.com/business/centre-notifies-income-tax-act-2025-law-to-come-into-effect-from-april-1-2026-3693171. Dekha: 10 Nov 2026.
- [T3] Rule 46 (draft) retention: https://www.patronaccounting.com/blog/books-of-account-rules-2026-rule-46-section-62-income-tax. Dekha: 10 Nov 2026.
- [T4] Tax audit Section 63: https://taxguru.in/income-tax/provisions-related-tax-audit-income-tax-act-2025-faqs.html. Dekha: 10 Nov 2026.
- [O1] NSE circular COMP53555 (6 Sep 2022, algo performance claims): https://archives.nseindia.com/content/circulars/COMP53555.pdf (search se; khola nahi). Dekha: 10 Nov 2026.
- [O2] SEBI intraday position limits (1 Sep 2025) summary: https://taxguru.in/sebi/sebi-tightens-intraday-position-limits-derivatives.html. Dekha: 10 Nov 2026.
- [O3] Moneylife (SEBI penalty, TradeTron-linked brokers, Mar 2026): https://moneylife.in/article/sebi-cracks-down-on-tradetronlinked-brokers-slaps-16-lakh-penalties-over-assured-returns-claims/80053.html. Dekha: 10 Nov 2026.
