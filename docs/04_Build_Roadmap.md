# 04: Build Roadmap (Phase 2 se aage ka plan)

**Tarikh:** 10 Nov 2026 · **Kisne:** Claude Code · **Status:** Prastaavit · **Shart:** Phase 2 malik ke "go" ke bina shuru nahi hoga.

## Saar (10 line)
1. Kaam 11 milestones (M0 se M10) mein hai. Har milestone ke saath acceptance tests hain; test pass hue bina agla milestone nahi.
2. **Critical path:** M0 → M1 (data record jaldi shuru) → M2 → M3 → M4 (Backtest Gate) → M5 → M6 → M8 (Paper) → M9 (Stage2, asli 1 Lot).
3. **Sabse lambe intezaar:** NSE data licence ka jawab, data kharid, aur Upstox se 3 pushtiyan (shared token, Pehredaar ka cancel, kill switch par IP). Yeh aaj se shuru hon.
4. **Backtest Gate fail hua toh M5 aage nahi.** Bina edge ke order code banana paisa aur samay ki barbaadi hai.
5. Test ki 6 parat: unit, property-based, deterministic replay, fault injection, conformance (Bot aur Pehredaar ka exit), aur Paper vs Live reconciliation.
6. **12 invariants** kabhi nahi tootne chahiye, jaise Net Quantity Guard, Broker Stop qty = fill qty, aur Lease ke bina hukm nahi. Har ek ka test aur live alarm hai.
7. **Fault injection** mein yeh sab nakli broker par chalenge: disconnect, aadha fill, token band, purana data, dohra order, 429, Broker Stop ka aadha fill, network toot-na, ghadi ki galti, nakli Dashboard hukm.
8. Risk register mein 16 jokhim hain, har ek ka maalik, trigger aur bachav ke saath.
9. Runbook 10 haalaat ke liye hai: crash, token band, halt, Kill-Switch, feed atakna, Pehredaar takeover, IP, broker band, Dashboard band, din ka ant.
10. Ant mein agle Claude Code sessions ke liye 8 ready-to-paste prompts hain, har milestone ka ek.

---

## 1. Milestones aur acceptance tests

| M | Naam | Kya banega | Acceptance tests (sab pass) | Kis par tika |
|---|---|---|---|---|
| **M0** | Neev | Repo dhaancha, toolchain, CI (lint, sakht type check, tests), hash-locked lockfile, dependency audit, CI mein TLS-off grep, niyam-file ka schema (Numbers ki list ki har row) | CI green; lockfile `--require-hashes` se install; niyam-file loader har row ka type/unit/range jaanchta hai aur galat file par fail; koi network call nahi | — |
| **M1** | Data aur Recorder | Apna Upstox feed client (TLS ON, official `.proto` pin + sha256), instrument master, holiday aur timing sync, Recorder (raw events + do timestamp), read-only login flow; D2 ka probe | 5 trading din ka raw data bina gap ke (ya gap ki report); probe report (p50/p99/p99.9); order wale endpoint code mein hain hi nahi (test se); token kahin log ya disk par nahi | Malik ka roz login; trial VM |
| **M2** | Market state | Instrument state, 3 timeframe candles, EMA/RSI/ATR/ADX/VWAP (din-bhar), Black-Scholes/Black-76 IV aur greeks (khud likhe), Replay harness | Indicator test vectors pass (`ta` ki CSV, `vollib` ki JSON, `R_b`); replay do baar = bit-for-bit same; property tests (candle OHLC niyam, VWAP monotonic volume); look-ahead test (future data hatane par result same) | M1 ka data |
| **M3** | Check engine | Pehle version ke saare checks, scoring, Gates, Confidence, NA-Data/NA-Lagu-Nahi, Shadow Mode, Data Family tags, reject wajah | Har check ke golden scenarios (GREEN, RED, NA-Data, NA-Lagu-Nahi, Put ulta); F-01 test (aam din manipulation Gate trade na roke); group cap aur `Maximum_Score_Threshold_Cap` ke boundary tests; ek hi input par Dashboard dabba = order faisla | M2 |
| **M4** | Backtester | `BacktestBroker` + fill model (`03` §2.3), date-aware cost model, latency injection, Walk-Forward runner, config register, Monte Carlo, regime report, Ablation runner | Cost model `R_d` ke 3 udaharan rupaye-paise tak mile; ek din ka backtest = us din ka replay; config register mein har run; **Backtest Gate report** (`03` §7) | Data kharid (P1), NSE licence jawab |
| **M5** | Haath (Order manager) | Order/trade state machine, Intent Log (durable), Order Baari + rate limiter, Broker Stop manager, reconcile, `PaperBroker`, nakli broker (fault injection ke liye) | Saare invariants ke property tests (§3); fault suite (§2.4) pass; restart test (har state par process maaro, wapas aao, invariant bane rahe) | **M4 ka Backtest Gate pass** |
| **M6** | Pehredaar | Go binary: Lease, haalat wali dhadkan, apna broker milaan, Exit Hissa, Kill Latch, apne alerts, shared token lena (private tunnel) | **Conformance suite** (ek hi scenario file) Bot ke Haath aur Pehredaar dono par pass; chaos tests: Bot maaro, Bot dheema karo, network todo, dono ek saath exit karein → kabhi net short nahi | M5 |
| **M7** | Dashboard + Alerts | Read-only state, signed command queue, 2FA, audit log, Kill-Switch → Pehredaar; Telegram + email (seedha API) | Security tests: bina 2FA login nahi; CSRF; rate-limit; purana/dohraya hukm reject; Dashboard host par koi broker/Telegram chaabi nahi (scan); alert do raste se | M3 (parallel M5/M6) |
| **M8** | Paper Stage | Teen machine (D2 §D7), live data + `PaperBroker`, roz ki report, Shadow Trades, reconciliation | `Paper_Gate_CC` (`03` §7); simulated vs recorded-book fill farak ≤ 1 tick (median); 0 Critical invariant breach; har din ka replay match | M5, M6, M7; VPS kharid |
| **M9** | Stage2 (asli 1 Lot) | Real Money, `Test_Stage2_Live_Lot`; pehle asli broker tests | **Pehle din (bina trade ke):** shared token do IP se, Pehredaar se cancel/exit, broker Kill Switch, IP par 3 Upstox pushtiyan likhit mein. Phir `Stage2_Gate_CC` | Upstox ke jawab (Sawal 117, 136, 141); malik ka sizing faisla (Sawal 118) |
| **M10** | Poora Lot | Sizing vikalp ke hisaab se dheere Lot badhna | `Live_Kill_Paimana` kabhi nahi toota; har 20 trade par review | M9 pass |

### 1.1 Critical path aur lambe intezaar
```
M0 ─► M1 ─► M2 ─► M3 ─► M4 ══(Backtest Gate)══► M5 ─► M6 ─► M8 ─► M9 ─► M10
              └──────────────► M7 (parallel) ───────┘
Lambe intezaar (aaj se shuru):  NSE licence jawab → data kharid → M4
                                Upstox pushtiyan (Sawal 117/136/141) → M9
                                Malik ke faisle (Sawal 118, 119, 120-123) → M3/M5/M9
```
- **M1 jaldi kyun:** apna depth aur tick record jitna jaldi shuru ho, utna lamba asli data milega (fill model ke liye).
- **Gate:** M4 ka Backtest Gate fail ho toh M5 ke bajay strategy par wapas (naye config register mein likh kar).

---

## 2. Test strategy

### 2.1 Unit
Har function ke chhote tests: indicator, IV, cost model, Tick Size rounding (kharid upar, bech neeche), Circuit-limit clamp, Signal ID, Order Tag ka unique hona.

### 2.2 Property-based
- Candle: high ≥ open/close ≥ low; volume kabhi ghatta nahi.
- Scoring: kisi bhi Group ka hissa `Ek_Group_Maximum_Score_Hissa` se zyada nahi; Gate RED → hamesha skip.
- State machine: random event kram (fill, aadha fill, reject, timeout, cancel, disconnect) par saare invariants (§3) sach.
- Rate limiter: kisi bhi kram mein per-second/minute/30-minute seema nahi tootti.

### 2.3 Deterministic replay
- Har din ka event log dobara chalao → har Intent aur faisla bit-for-bit same.
- Backtest ka ek din = Paper ka wahi din (same data par) → same faisle.
- CI mein ek "golden day" replay har commit par.

### 2.4 Fault injection (nakli broker par)

| # | Fault | Umeed (pass ki shart) |
|---|---|---|
| F1 | Broker disconnect (WS aur REST) beech trade | Naye entry band; Broker Stop broker par; reconnect par `Reconnect_Taza_Tick_Ginti` ke baad hi data; reconcile |
| F2 | Entry ka aadha fill | Bacha cancel; Broker Stop qty = fill qty; < 1 Lot par band |
| F3 | Broker Stop ka aadha fill exit ke beech | Exit qty = cancel confirm ke baad broker ki net qty; net short nahi (F-09) |
| F4 | Token band (401) din ke beech | Entry band; Critical Alert; naye login ke baad reconcile phir entry |
| F5 | Feed chupchaap atka (ticks band, connection zinda) | Tick_Heartbeat RED; khule trade par broker se bhav (H-15) ya MPP; alert |
| F6 | Order ka jawab nahi (timeout) | Entry dobara nahi bheji; tag se poochha; dohra trade nahi (F-10) |
| F7 | 429 (bahut zyada request) | Order Baari dheemi; exit aur Broker Stop pehle; entry band |
| F8 | Bot dheema (GC jaisa 5 s pause) | Lease khatam; Bot ne koi hukm nahi bheja; Pehredaar ne control liya; net short nahi (F-05) |
| F9 | Bot aur Pehredaar ke beech network toota, dono zinda | Sirf ek ne broker ko hukm diya |
| F10 | Ghadi `Ghadi_Skew_Sakht_Hadd` se zyada khiski | Taiyari Fail / naye entry band (F-07) |
| F11 | Kill-Switch jab bot zinda | Kill Latch; bot naya entry nahi leta; Pehredaar naye entry order cancel karta hai (F-04) |
| F12 | Nakli/purana Dashboard hukm | Reject + audit log + alert (F-17) |
| F13 | Expiry shift ke second par exit aur entry | Entry sirf net qty 0 aur paisa padhne ke baad (F-12) |
| F14 | Foreign Position usi instrument mein | Bot us instrument mein trade nahi; uski qty nahi chhooi (F-11) |
| F15 | Broker Stop modify reject (do baar) | Trade band (Idea §5) |
| F16 | Process crash har state par | Restart ke baad invariants sach; adhoora Intent milaya (F-36) |
| F17 | Halt / circuit / bid gayab | Entry band; Broker Stop khula; Critical Alert; khulte hi MPP |
| F18 | Dashboard band | `Dashboard_Band_Hadd` ke baad naye entry band (F-47) |

### 2.5 Conformance (Bot ka Haath aur Pehredaar)
Ek hi scenario file (YAML jaisa data) jismein broker ki taraf se events aur umeed wale hukm likhe hon. Dono implementations (Python Haath, Go Pehredaar) par chalti hai. Exit kram ka koi bhi farak = fail.

### 2.6 Paper vs Live reconciliation
- Roz: har asli order ka (bhav, samay, qty) vs usi samay ka Paper simulation. Farak ka median aur p90 report mein.
- Broker ke contract note/trade book se bot ke record ka milaan (kharche bhi). Farak > Rs 1 = alert.
- `Paper_Asli_Fill_Farak_Hadd` toote toh fill model pessimistic.

---

## 3. Invariants (kabhi nahi tootne chahiye)

| # | Invariant | Test (offline) | Live alarm |
|---|---|---|---|
| I-1 | Kisi instrument ki net qty kabhi 0 se neeche nahi (Net Quantity Guard) | Property test + F3, F8, F9 | Har reconcile par; tootne par Critical + kill criteria 4 |
| I-2 | `OPEN_SURAKSHIT` mein Broker Stop qty = broker ki confirmed fill qty | Property + F2, F3 | Reconcile; farak par Critical |
| I-3 | Koi position `Entry_Ke_Baad_Broker_Stop_Samay` se zyada bina Broker Stop nahi | F1, F2, F16 | Pehredaar ka apna milaan (F-16) |
| I-4 | Ek Signal ID par ek hi entry order | Property + F6 | Order Tag ginti |
| I-5 | Lease ke bina broker ko koi hukm nahi | F8, F9 | Haath ka guard; log audit |
| I-6 | Kill Latch laga ho toh koi entry nahi | F11 | Pehredaar dekhe; mile toh cancel + Critical |
| I-7 | Exit qty = cancel confirm ke baad broker ki net qty | F3 | Exit se pehle assert |
| I-8 | Order traffic `Order_Prati_Second_Seema` ke andar | Rate limiter property | Rate-limit headroom metric |
| I-9 | Har bhav Tick Size par aur Circuit-limit ke andar | Unit + property | Reject ki wajah gino |
| I-10 | Foreign Position wale instrument mein bot ka order nahi | F14 | Order se pehle assert |
| I-11 | Raat ko koi khuli position nahi | Backtest/Paper har din | `Auto_Square_Off_Samay` ke baad check; broker square-off charge alert |
| I-12 | Token, chaabi kabhi log, disk ya Dashboard mein nahi | Log filter tests; disk scan | Roz scan |

---

## 4. Risk register

| # | Jokhim | Sambhavna | Asar | Bachav | Trigger | Maalik |
|---|---|---|---|---|---|---|
| R1 | Strategy mein asli edge nahi | Zyada (SEBI data) | Bahut bada | Backtest Gate, OOS lock, multiple-testing | Gate fail | Malik + Claude |
| R2 | Poore balance sizing se ruin | Zyada (`03` §5) | Bahut bada | Vikalp A/B/C | Malik ka faisla (Sawal 118) | Malik |
| R3 | Shared token do IP se na chale / Pehredaar cancel na kar sake | Madhyam | Bada | M9 se pehle test; design B (Pehredaar sirf Kill Switch + alert) | Upstox jawab | Claude |
| R4 | NSE A.4 / single-app niyam ka galat arth | Madhyam | Bada (account rok) | Upstox + vakil likhit | Jawab | Malik |
| R5 | Slippage model se zyada | Madhyam | Bada | Grid, khud ka depth record, Stage2 | Kill criteria 3 | Claude |
| R6 | Data licence se kharid atke | Madhyam | Madhyam | Upstox expired API, vendor | NSE jawab | Malik |
| R7 | Bazaar/broker niyam badle (samay, STT, lot) | Zyada | Madhyam | Roz timing/master sync; mahine ki review | Circular | Claude |
| R8 | Net short / dohra order bug | Kam (tests ke baad) | Bahut bada | Invariants, fault suite, conformance | Koi breach | Claude |
| R9 | Feed chupchaap atakna | Madhyam | Bada | Do timestamp, heartbeat, Pehredaar milaan | Feed lag alarm | Claude |
| R10 | GC/latency tail | Kam | Madhyam | `gc.freeze`, allocation-free hot path, trigger par Rust | p99.9 trigger (`02` §B4) | Claude |
| R11 | Dashboard hack | Kam | Bada | 2FA, signed hukm, Pehredaar sirf Kill | Audit alert | Claude |
| R12 | Supply-chain attack | Kam | Bahut bada | Hash-lock, audit, kam deps, egress allowlist | Advisory | Claude |
| R13 | Cloud machine ya AZ band | Kam | Madhyam | Elastic IP shift, IaC, runbook | Health check | Claude |
| R14 | Malik ka override (revenge) | Madhyam | Bada | Override sirf 1 Lot + likhit; niyam agle din se | Override log | Malik |
| R15 | Tax/record galti | Madhyam | Madhyam | 8 saal record, roz tax file, CA review | CA jawab | Malik |
| R16 | Upstox API offer/charges badle (Rs 10 → Rs 20) | Zyada (31 Dec 2026) | Chhota | Cost model date-aware | Brokerage page | Claude |

---

## 5. Runbook (kya karna hai, kram se)

| Haalat | Pehchaan | Kadam |
|---|---|---|
| **Bot crash** | Pehredaar ki dhadkan chhooti; alert | 1. Pehredaar ne control liya? Dashboard dekho. 2. Broker par har position ka Broker Stop dekho (Upstox app). 3. Bot ka service manager restart karta hai; bot us din broker ko hukm nahi dega (nishan). 4. Shaam ko log aur replay se wajah. |
| **Token band / login fail** | 401; "Taiyari Fail" | 1. Naye entry band (auto). 2. Malik naya login kare (sirf Bot machine se, kabhi Pehredaar se nahi). 3. Bot reconcile kare, phir hi entry. 4. 3 koshish ke baad din band. |
| **Exchange halt / circuit** | Broker_Exchange_Gadbad RED; Critical | 1. Kuch mat karo; Broker Stop khula rahe. 2. Khulte hi bot MPP se nikle (auto). 3. Malik Upstox app tayyar rakhe. |
| **Kill-Switch dabaana** | Malik ka faisla | 1. Dashboard par Kill-Switch + confirm. 2. "Ho gaya" dikhe tak dekho. 3. Fail dikhe toh Upstox app se haath se band karo. 4. Kill Latch agle din Start tak. 5. Shaam ko wajah likho. |
| **Feed atka** | Warning-light; Tick_Heartbeat RED | 1. Naye entry band (auto). 2. Khule trade broker ke bhav par (H-15) ya MPP. 3. Probe/metrics dekho: Upstox ya hamara network? |
| **Pehredaar ne control liya** | Critical (Pehredaar ke raste se) | 1. Positions zero hain? Upstox app se pakka karo. 2. Bot ko us din wapas mat chalao. 3. Agle din Start se pehle wajah samjho. |
| **Static IP / Algo reject** | Reject wajah, Critical | 1. Naye entry band (auto). 2. **Din mein IP mat badlo** (sab token band ho jaayenge). 3. Upstox support. |
| **Broker/Upstox band** | Saare API fail | 1. Broker Stop broker par hain (umeed). 2. Upstox app/phone se position dekho. 3. Bot naye entry nahi lega. |
| **Dashboard band** | Bot Dashboard se jud nahi pa raha | 1. Naye entry band (auto, F-47). 2. Upstox app aapat rasta. 3. Dashboard machine restart/restore. |
| **Din ka ant** | `Auto_Square_Off_Samay` | 1. Saari positions zero (I-11). 2. Roz ki report, tax file, backup. 3. Agle din ka calendar file aur timing check. |

---

## 6. Agle Claude Code sessions ke liye ready-to-paste prompts

Har prompt Phase 2 ke liye hai aur tabhi chalana hai jab malik "go" de. Har session `docs/PROGRESS.md` padh kar shuru kare aur khatam hone par use update kare.

### Prompt M0: Neev
```
# PHASE 2 / M0: NEEV (repo, CI, niyam-file). Asli broker connection NAHI.
Tum is project ke Principal Engineer ho. Simple Hinglish, technical shabd English mein.
Pehle padho: docs/PROGRESS.md, docs/02_Tech_Decisions.md (B4, C, F), docs/04_Build_Roadmap.md (M0).
Kaam:
1. Python project ka dhaancha (Dimaag, Haath, Recorder alag packages) aur Go module (Pehredaar) ka khaali dhaancha.
2. CI: lint, sakht type check, tests, lockfile --require-hashes, pip-audit/OSV, govulncheck,
   aur grep jo CERT_NONE / verify=False / check_hostname=False milne par fail ho.
3. Niyam-file schema: docs/01_Bot_Idea_v4.md ki Numbers list ki HAR row ka naam, type, unit, range, status.
   Loader galat file par fail kare. Malik ke "Andaza"/"Prastaavit"/"Tay nahi" status bhi file mein rahein.
Niyam: koi key/token/password na maango, na likho. Kisi broker ya Telegram se connect nahi. Har library ka
version aur licence internet se verify karo ("verify nahi hua" likho jahan na ho). Pehle chhota plan, phir kaam.
Har kaam ke baad commit. Ant mein self-check aur M0 ke acceptance tests ka nateeja dikhao. Phir ruko.
```

### Prompt M1: Data aur Recorder
```
# PHASE 2 / M1: APNA FEED CLIENT + RECORDER + PROBE. Sirf market data padhna, ORDER NAHI.
Pehle padho: docs/PROGRESS.md, docs/02_Tech_Decisions.md (A, C2, C9, D6), docs/research/R_b (upstox-python feeder TLS).
Kaam:
1. Upstox market feed V3 ka client khud likho: TLS certificate jaanch ON, official MarketDataFeed.proto pin
   (sha256 record), reconnect, do timestamp (exchange + receive). Order wale endpoint code mein hon hi nahi.
2. Instrument master, holidays aur market timings roz sync (hard-code nahi).
3. Recorder: har raw event append-only file mein + gap report.
4. Probe script (02 D6) ka code: sirf DNS/TCP/TLS handshake, koi HTTP request ya token nahi.
Login: malik khud karega; token sirf memory mein, kabhi log/disk par nahi (test likho).
Niyam: chaabi kabhi chat ya file mein nahi. Upstox docs internet se verify karo. Pehle plan, phir kaam, har kadam commit.
Acceptance (04 M1) dikhao. Phir ruko.
```

### Prompt M2: Market state aur indicators
```
# PHASE 2 / M2: CANDLES, INDICATORS, IV/GREEKS, REPLAY HARNESS.
Pehle padho: docs/PROGRESS.md, docs/01_Bot_Idea_v4.md (Naam-Suchi, Numbers), docs/research/R_b (test vectors).
Kaam: 3 timeframe candles (incremental), EMA/RSI/ATR/ADX, DIN-BHAR ka VWAP (rolling nahi), Black-Scholes/Black-76
IV + greeks khud likho. Test vectors: bukosabino/ta ki test/data CSV aur vollib ki tests/test_data.json
(licence notice ke saath). Replay harness: wahi event log do baar = bit-for-bit same.
Look-ahead test zaroori: swing/pivot sirf pushti ke baad.
GC niyam: hot path mein naye objects nahi; gc.freeze ka asar naapo (docs/research/R_e).
Pehle plan, phir kaam, har kadam commit. Acceptance (04 M2) dikhao. Phir ruko.
```

### Prompt M3: Check engine
```
# PHASE 2 / M3: CHECK ENGINE + SCORING + GATES (pehle version ke checks).
Pehle padho: docs/01_Bot_Idea_v4.md (Section 6, 7, 8 + saare [PRASTAAVIT-CC]), docs/01b_Audit_Findings.md.
Kaam: har pehle-version check ek pure function: (state) -> GREEN/RED/NA-Data/NA-Lagu-Nahi + wajah.
Put ke liye ulti shartein (F-39). Group cap, Confidence, Maximum_Score_Threshold_Cap, Shadow Mode, Data Family tag.
Har check ke golden scenarios (GREEN, RED, NA-Data, NA-Lagu-Nahi, Put). F-01 test: aam din manipulation Gate trade na roke.
Jo number "Tay nahi" hai, use code mein guess MAT karo: niyam-file mein khaali rakho aur check ko Shadow/NA rakho,
aur docs/PROGRESS.md mein sawal likho. Malik ka likha kabhi overwrite nahi.
Pehle plan, phir kaam, commit. Acceptance (04 M3). Phir ruko.
```

### Prompt M4: Backtester aur Backtest Gate
```
# PHASE 2 / M4: BACKTESTER + COST MODEL + WALK-FORWARD + BACKTEST GATE.
Pehle padho: docs/03_Strategy_Edge_Plan.md (poora), docs/research/R_d_Costs_Data.md.
Kaam: BacktestBroker + fill model (touch is not fill, participation cap), date-aware cost model (R_d ke 3 udaharan
paise tak milao), latency injection, Walk-Forward, LOCKED Out-of-Sample, config register (har run likho),
Monte Carlo (din ke blocks), regime report, Ablation runner. Data: sirf malik ka manzoor kiya hua data.
Seedhi baat: profit ki guarantee nahi. Gate fail ho toh saaf "FAIL" likho, numbers ghuma kar pass mat dikhao.
Report: Net Expectancy + CI, Profit Factor, maxDD, Slippage grid (1/2/4/10 tick), kitne config aazmaaye.
Pehle plan, phir kaam, commit. Backtest Gate report (03 §7) dikhao. Phir ruko.
```

### Prompt M5: Haath (Order manager)
```
# PHASE 2 / M5: ORDER MANAGER + STATE MACHINE + INTENT LOG + PAPER BROKER + FAULT SUITE.
Shart: M4 ka Backtest Gate PASS (docs/PROGRESS.md mein likha ho). Na ho toh ruk jao aur batao.
Pehle padho: docs/02_Tech_Decisions.md (C2-C8), docs/04_Build_Roadmap.md (2.4, 3), docs/01_Bot_Idea_v4.md Section 5, 10, 11.
Kaam: state machine (02 C3), durable Intent Log, unique Order Tag, Order Baari + rate limiter, Broker Stop manager
(min khiskaav, modify bajat), reconcile, Lease guard, Kill Latch guard, PaperBroker, aur nakli broker jispar
fault F1-F18 chalein. Invariants I-1 se I-12 ke property tests. Asli broker par koi order NAHI.
Pehle plan, phir kaam, commit. Fault suite aur invariants ka nateeja dikhao. Phir ruko.
```

### Prompt M6: Pehredaar
```
# PHASE 2 / M6: PEHREDAAR (Go static binary) + LEASE + CONFORMANCE SUITE.
Pehle padho: docs/01_Bot_Idea_v4.md Section 5 (F-04, F-05, F-16, F-76), docs/02_Tech_Decisions.md C9, docs/04 2.5.
Kaam: Lease dena/lena, haalat wali dhadkan, apna broker milaan, Exit Hissa (Broker Stop cancel → confirm →
broker ki net qty → exit), Kill Latch, apne alerts (seedha Telegram API + email), shared token private tunnel se
lena (sirf memory). Pehredaar KABHI khud login nahi karega. Conformance suite: ek scenario file, Bot ke Haath aur
Pehredaar dono par pass. Chaos: bot maaro/dheema/network todo → kabhi net short nahi.
Koi chaabi na maango na likho; asli broker par kuch nahi. Pehle plan, phir kaam, commit. Nateeja dikhao. Phir ruko.
```

### Prompt M7-M8: Dashboard aur Paper Stage
```
# PHASE 2 / M7 + M8: DASHBOARD (2FA, signed hukm) + PAPER STAGE ki taiyari.
Pehle padho: docs/01_Bot_Idea_v4.md Section 13, 14 (F-17, F-47), docs/02_Tech_Decisions.md D7 aur F.
Kaam M7: read-only Dashboard, sirf malik login + 2FA, signed ek-baar hukm (Command_Max_Umar), Kill-Switch → Pehredaar,
audit log, rate-limit, CSRF, CSP. Dashboard host par koi broker/Telegram chaabi nahi (scan test).
Kaam M8: teen machine ka infra-as-code (D7 ka plan, malik ki manzoori ke bina kuch khareedna NAHI), Paper Mode
live data par, roz ki report, Shadow Trades, reconciliation. Paper_Gate_CC ka tracker.
Kharcha karne se pehle malik se poochho. Pehle plan, phir kaam, commit. Acceptance dikhao. Phir ruko.
```

---

## Self-check (Deliverable 4)

| Check | Nateeja |
|---|---|
| Milestones M0 se aage, har ek ke acceptance tests | PASS (M0-M10) |
| Critical path aur lambe intezaar | PASS (1.1) |
| Test strategy: unit, property, replay, fault injection (disconnect, aadha fill, token, stale data, dohra order), paper vs live | PASS (2.1-2.6; F1-F18) |
| Invariants (Net Quantity Guard, Broker Stop qty = fill qty, aur aage) + test plan | PASS (I-1 se I-12) |
| Risk register | PASS (R1-R16) |
| Runbook (crash, token fail, halt, Kill-Switch + aur) | PASS (10 haalaat) |
| 6-8 ready-to-paste prompts, har milestone ka ek, isi style mein | PASS (8 prompts) |
| Koi key/token nahi; profit guarantee nahi | PASS |
