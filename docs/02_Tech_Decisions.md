# 02: Tech Decisions (Phase 1, sirf faisle, code nahi)

**Tarikh:** 10 Nov 2026 · **Kisne:** Claude Code · **Status:** Prastaavit (malik ki pushti baaki) · **Research ke saboot:** `docs/research/R_a` se `R_e` · Har number ke saath source ya "andaza" likha hai.

## Saar (10 line)
1. **Speed ka sach:** tick se broker ack tak asli samay broker ke andar (lagbhag 30 se 45 ms, Upstox staff ka daawa) aur bot ke apne design mein jaata hai: har 1 second ka evaluation aur band candle ka intezaar. Hamare code ka hissa microseconds se kuch milliseconds hai.
2. **Language:** Dimaag (feed, candle, checks, scoring, order manager, backtest) **Python** mein. Benchmark mein Python ka 1-second evaluation p99.9 ~5 ms aaya, budget ka 1% se kam. Asli khatra GC pause tha (228 ms), jo `gc.freeze` se ~2 ms par aaya.
3. **Pehredaar Go mein** (alag runtime, ek static binary). Dashboard frontend TypeScript mein. C/C++ nahi. Rust tabhi jab measure kiya hua trigger toote.
4. **Sabse bada design badlaav (F-76):** Upstox mein ek user ka sirf ek chalu API app hai. Isliye Bot aur Pehredaar **ek hi app ka roz ek hi token** share karenge, encrypted raste se. Shared token ka asli test Real Money se pehle zaroori hai.
5. **Architecture:** Bot machine par 3 process hain: Dimaag, Haath (akela broker ko hukm dene wala), Recorder. Har input ek event hai, aur Backtest, Paper aur Live mein ek hi code chalta hai. Bot ka broker par haq Lease se bandha hai.
6. **VPS (malik ka budget ₹1,500/mahina, 10 Nov 2026):** Bot = AWS Lightsail Mumbai $12 plan (2 vCPU, 2 GB, static IP shaamil; Upstox ke server bhi AWS Mumbai mein). Pehredaar aur Dashboard = Oracle Cloud Always Free. Kul ~₹1,330 GST ke saath (D8). Asli paise se pehle Pehredaar paid server par (Plan B, wahi ~₹1,330). Badi machine wali D7 salah ab sirf budget badhne par.
7. **Khareedne se pehle:** sasti machines par ek hafte ka probe (~₹330) chalega, aur Upstox se 3 sawaal confirm karne hain. Bachat ki keemat: burstable CPU, kam RAM, aur Oracle Free machine ke idle hone par delete hone ka khatra (D8).
8. **Repos:** sirf official Upstox SDK ka REST hissa (pinned + hash-locked). Iska WebSocket feeder TLS jaanch band rakhta hai, isliye feeder khud likhenge. openalgo (AGPL) aur NseIndiaApi (GPL) nahi lenge.
9. **Security:** chaabi sirf cloud ke secrets store mein, Dashboard par kabhi nahi. Dashboard par 2FA, signed hukm aur audit log. Har dependency hash-locked.
10. **Compliance:** SEBI algo framework 1 Apr 2026 se lagu hai. 10 OPS se neeche registration nahi chahiye. 15 sawaal CA, vakil aur Upstox se poochne hain. Bot doosron ke liye hua toh empanelment, RA registration aur broker-hosting lagenge.

---

## A. Speed ka sach: tick se order ack tak latency budget

**Seedhi baat:** yeh bot microsecond ki race nahi jeet sakta, aur use jeetni bhi nahi hai. Bot breakout ke baad 15 second se 2 minute tikav dekhta hai, aur chart checks band candle par chalte hain. Isliye asli sawaal "kitna tez" nahi, "kitna **tika hua** (stable p99.9) aur **sahi**" hai.

### A1. Hop by hop (ek entry order ka raasta)

| # | Hop | Samay | Source / bharosa |
|---|---|---|---|
| 1 | Exchange par saude se Upstox feed server tak | **verify nahi hua** | Upstox docs mein feed ka update interval nahi mila (R-c 5.16) |
| 2 | Upstox feeder (`wsfeeder-api.upstox.com`, AWS Mumbai) se Bot VM (AWS Mumbai) tak ka network | ~0.5 se 2 ms (andaza) | AZ "within 100 km" aur "~1 ms round-trip per 100 km" ka rule ([AWS blog](https://aws.amazon.com/blogs/industries/lower-access-latency-for-your-apps-with-aws-wavelength-and-our-telco-partners/)); probe se naapna hai |
| 3 | WebSocket frame + protobuf decode | Python mein ~2 se 20 µs prati message (andaza) | Benchmark mein JSON decode p50 4.8 µs (stdlib) aur 2.7 µs (orjson) mila; protobuf decode naapa nahi gaya |
| 4 | Instrument state + 3 timeframe candle update | Python p50 1.9 µs, p99.9 ~20 µs; Rust 54 ns | `docs/research/R_e_Benchmark.md` (synthetic, shared 4 vCPU) |
| 5 | **Evaluation ka intezaar** (`Evaluation_Gati_Samay` = 1 s) | **ausat 500 ms, sabse bura 1 s** | Idea ka apna design; yeh sabse bada hissa hai |
| 6 | **Chart check ke liye band candle ka intezaar** | breakout candle band hone tak 0 se 3 minute | Idea ka design (`Breakout_Candle_Timeframe`) |
| 7 | 50 checks + scoring (~135 strikes, 492 options ka IV/Delta) | Python plain p99.9 ~5 se 7 ms; NumPy ~2.4 ms; Numba ~0.7 ms; Rust ~0.3 ms | `R_e_Benchmark.md` |
| 8 | Intent Log likhna (durable, fsync) | ~1 se 5 ms (andaza, cloud disk) | verify nahi hua; Phase 2 mein naapna |
| 9 | Order build + rate limiter + REST call (TLS keep-alive) Bot se `api-hft.upstox.com` | network ~1 se 2 ms (andaza) | probe ki pass kasauti: TCP connect p50 ≤ 2 ms (`R_a` Section 6) |
| 10 | Upstox ke andar se exchange ack tak | **~30 se 45 ms** (Upstox staff ka daawa) | [Upstox community, 9 Jun 2025](https://community.upstox.com/t/re-9351107-clarification-on-achieving-45ms-latency-with-upstox-api/9453/2); Place Order V3 response mein `metadata.latency` field hai ([docs](https://upstox.com/developer/api-documentation/v3/place-order/)) |
| 11 | Fill ki khabar wapas (portfolio stream) | **verify nahi hua** | [Portfolio stream docs](https://upstox.com/developer/api-documentation/get-portfolio-stream-feed/) mein number nahi |
| 12 | Broker Stop lagana (ek aur round trip) | ~35 se 50 ms (andaza = hop 9 + 10) | `Entry_Ke_Baad_Broker_Stop_Samay` (2 s) ke andar aaram se |

### A2. Asli samay kahan jaata hai
- **Design ki cadence:** hop 5 aur 6 (500 ms se minutes tak) baaki sab se bade hain. Agar tez entry chahiye, toh pehle yeh dekho, language nahi. Prastaav: tick wale checks har naye tick par chalein aur 1 second ka timer sirf Dashboard ke liye ho. Isse ausat 500 ms bachega. Yeh `H-02` jaisa hi Paper Stage mein test ho.
- **Broker ka hissa:** hop 10 (~30 se 45 ms) hamare haath mein nahi. Bot ko Mumbai mein rakhna isliye zaroori hai ki network hop chhota rahe.
- **Hamara code:** hop 3, 4, 7, 8 milakar Python mein bhi ~10 ms se kam (p99.9). Rust se yeh ~1 ms ho jaata, par hop 5 aur 10 ke saamne farak chhota hai.
- **Tail ka khatra:** Python GC pause benchmark mein **228 ms** tak gaya (jab objects badhte rahe). `gc.freeze()` + `gc.disable()` ke baad max ~2.2 ms raha. Isliye v1 ka pehla niyam: hot path mein naye objects mat banao, pehle se bana memory reuse karo, aur GC ko control karo.
- **Naapne ka plan (Phase 2):** har event par 6 timestamp: exchange ka samay, receive, decode ke baad, faisla, order bheja, ack. Inse har hop ka p50/p99/p99.9 Dashboard aur roz ki report mein dikhe.

---

## B. Language faisla

### B1. Kasauti aur vazan

| Kasauti | Vazan | Kyun |
|---|---|---|
| Latency ka tikav (p99, p99.9) | 15 | Upar dikha ki budget bada hai; tail matter karta hai, ausat nahi |
| Correctness aur memory-safety | 25 | Asli paisa; ek galti = net short ya dohra order |
| Upstox ka official SDK aur libraries | 15 | Official SDK sirf Python, Node.js, Java, PHP, .NET mein hain; Rust, Go, C++ mein nahi (`R_b` Section 3) |
| Dev-speed | 10 | Malik non-programmer hai; aage ke AI sessions ko tez aur saaf likhna hai |
| Testability (property tests, replay, fault injection) | 15 | Invariants sabit karne hain |
| Maintenance (kam language, kam dependencies) | 10 | Har nayi language = naya toolchain, naya supply-chain khatra |
| Ops-risk (deploy, crash, debug) | 10 | Ek static binary vs bada runtime |

### B2. Candidates ka score (1 se 5; vazan ke saath kul 500 mein se)

| Language | Tikav | Correct/safe | SDK/libs | Dev-speed | Testability | Maint. | Ops | **Kul** |
|---|---|---|---|---|---|---|---|---|
| Python (asyncio + NumPy, GC control) | 3 | 3 | 5 | 5 | 5 | 5 | 3 | **400** |
| Rust | 5 | 5 | 2 | 2 | 4 | 3 | 5 | **390** |
| Go | 4 | 4 | 2 | 4 | 4 | 4 | 5 | **380** |
| TypeScript (Node) | 3 | 3 | 4 | 4 | 4 | 3 | 3 | **340** |
| Java/Kotlin | 4 | 4 | 4 | 3 | 4 | 3 | 3 | **370** |
| C++ | 5 | 1 | 1 | 2 | 3 | 2 | 3 | **230** |

(Score andaza hai. Tikav ka score `R_e_Benchmark.md` se, SDK ka `R_b` se, baaki engineering raay. Python aur Rust mein sirf 10 ka farak hai: Python SDK, dev-speed aur ek-code-replay se jeet-ta hai, Rust safety aur tikav se. Isliye trigger tootne par agla qadam Rust hai. Go Pehredaar ke liye chuna gaya, kyunki wahan SDK ki zaroorat nahi aur ek static binary ka ops faayda bada hai.)

### B3. Shuruaati soch ko saboot se challenge

| Shuruaati soch | Saboot | Nateeja |
|---|---|---|
| "C/C++ nahi" | Benchmark mein C++ sabse tez tha (tick p50 53 ns), par Rust bhi utna hi tez (54 ns) aur memory-safe hai. Upstox ka C++ SDK nahi hai | **Sahi.** C++ ka koi faayda nahi jo Rust na de |
| "Dimaag pehle Python mein" | Plain Python 30k ticks/s burst ka ~12 guna sambhal leta hai. Sabse busy second mein CPU 9 se 22%. Eval p99.9 ~5 ms vs 1000 ms budget | **Sahi**, shart ke saath: GC control aur hot path mein allocation nahi. Data synthetic hai; asli Upstox tick rate verify nahi hua |
| "Jo hissa p99 budget tode, sirf wahi Rust mein" | Abhi koi hissa budget ke paas nahi. Pehle sasta upay: NumPy (eval 2.4 ms), Numba (0.7 ms), orjson | **Sahi.** Trigger neeche table mein |
| "Pehredaar alag language aur runtime mein" | Ek bug dono ko na maare, yeh sahi hai. Par exit ka kram (Broker Stop cancel, confirm, broker ki net quantity, exit) do jagah likhna padega, aur do code ka alag hona bhi khatra hai | **Sahi, ek shart ke saath:** exit kram ka ek likhit spec ho aur ek hi "conformance test suite" (nakli broker par scenarios) dono implementations par chale |
| "Pehredaar ke liye Go ya Rust static binary" | Upstox ka Go/Rust official SDK nahi; Pehredaar ko sirf ~6 REST calls chahiye (positions, orders, cancel, exit order, kill switch, exit-all). Go mein HTTP + TLS standard library mein hai (andaza; code review mein pakka) | **Go.** Rust bhi chalega, par Go se jaldi aur saaf likha jaayega, aur Pehredaar ko latency nahi chahiye |
| "Order state machine ke liye Rust ki strong typing" | Fayda asli hai (har state ka match compiler jaanchta hai). Par Python mein strict type check + `match` + `assert_never` + model-based property tests se bhi har state jaanchi ja sakti hai. Rust ke liye alag process ya FFI chahiye, aur backtest ke saath ek code nahi rahega | **Abhi Python**, sakht typing aur model-based tests ke saath. Trigger neeche |

### B4. Har hisse ki final language aur "kab badlenge"

| Hissa | v1 language | Wajah | Kab badlenge (measurable trigger) |
|---|---|---|---|
| Tick ingest (WebSocket + protobuf) | Python (asyncio + uvloop + official `.proto` se bana decoder), **apna feeder, TLS jaanch ON** | SDK feeder TLS jaanch band rakhta hai (`R_b`); Python decode budget mein | Asli feed par decode+state p99.9 > 5 ms, ya burst mein lag p99.9 > 50 ms → ingest alag Rust process mein |
| Candle builder | Python (incremental, bina pandas) | Benchmark: p99.9 ~20 µs | Upar wala hi trigger |
| Check engine | Python + NumPy (strikes par vectorised); Numba vikalp | Eval p99.9 2.4 ms (NumPy) | Eval p99 > 200 ms, ya busiest second CPU > 50% → Numba, phir Rust |
| Scoring | Python (pure function) | Deterministic, test mein aasaan | Nahi badlega |
| Order manager + state machine ("Haath") | Python, strict typing, model-based tests, akela broker ko hukm dene wala | Ek hi code backtest/paper/live mein | Fault tests mein state machine ka koi invariant tootna jo typing pakad sakti thi, ya Pehredaar ke saath code share karna ho → Rust |
| Pehredaar + Exit Hissa | **Go** (static binary, alag machine, alag provider) | Alag runtime; bot ka bug ise na maare | Nahi badlega |
| Backtester | Python (wahi Dimaag aur Haath, nakli broker ke saath) | Deterministic replay; ek hi code | 18 mahine ka run > 8 ghante → pehle din-wise parallel run, phir hot hissa Rust |
| Dashboard backend | Python (FastAPI jaisa), read-only state + signed command queue | Bot ke data models reuse | Nahi badlega |
| Dashboard frontend | TypeScript (static build, kam dependencies, sakht CSP) | Browser ki zaroorat | Nahi badlega |
| Data store | Intent Log + order/position events: SQLite (WAL, durable writes). Raw ticks: din-wise append-only compressed files, phir research ke liye Parquet | Ek machine, kam ops; replay ke liye seedha | Ek din ka raw data > 20 GB, ya Dashboard ko kai users → event stream ke liye alag store |
| Alerts | Bot: Python; Pehredaar: Go. Dono **seedha** Telegram Bot API par HTTPS ([docs](https://core.telegram.org/bots/api)) + email | Library ki zaroorat nahi (`R_b`) | Nahi badlega |

### B5. Benchmark ka saar (`docs/research/R_e_Benchmark.md`)

Synthetic data: 498 instruments, ~2.05 million ticks, normal ~3k/s aur burst ~30k/s. Har second 492 options ka IV aur Delta, phir ~135 strikes par 50 checks. Har variant 3 baar chala, median liya. Saare variants ka checksum Python se match hua.

| Variant | Tick p50 / p99.9 / max | Eval p50 / p99.9 / max | Ticks/s |
|---|---|---|---|
| C++ | 53 ns / 234 ns / 109 µs | 107 / 187 / 201 µs | 9.17M |
| Rust | 54 ns / 229 ns / 1.0 ms | 105 / 282 / 342 µs | 8.42M |
| Go | 66 ns / 219 ns / 245 µs | 160 / 291 / 314 µs | 7.13M |
| Python + Numba eval | 1.8 / 19.4 µs / 2.6 ms | 0.39 / 0.73 / 0.74 ms | 454k |
| Python + NumPy eval | 1.9 / 20.0 µs / 2.7 ms | 0.88 / 2.38 / 2.89 ms | 441k |
| Python plain, GC on | 1.9 / 22.0 µs / 4.0 ms | 2.45 / 6.91 / 7.95 ms | 367k |
| Python plain + badhta history, GC on | 2.1 / 31.7 µs / **228 ms** | 2.47 / 5.99 / 6.21 ms | 293k |
| Python plain + badhta history, `gc.freeze` | 2.1 / 23.7 µs / 2.2 ms | 2.45 / 4.95 / 5.53 ms | 328k |

**Caveats:** machine shared 4 vCPU thi, dedicated nahi. Data synthetic tha. Upstox ka asli tick rate aur protobuf decode naapa nahi gaya. Network, asyncio aur logging benchmark mein nahi the. Isliye Phase 2 mein asli feed record karke yahi benchmark dobara chalega.

---

## C. Architecture

### C1. Teen machine, kaun kya karta hai

| Machine | Kaam | Broker token? | Inbound port |
|---|---|---|---|
| **Bot** (AWS Mumbai) | Dimaag, Haath, Recorder; roz ka login; Primary Static IP | Haan (memory mein) | **Koi nahi** |
| **Pehredaar** (GCP Mumbai) | Bot ki dhadkan aur Lease; apna broker milaan; Exit Hissa; Kill-Switch; apne alerts; Secondary Static IP | Haan, Bot se encrypted raste se (F-76) | Sirf Bot ke private tunnel se |
| **Dashboard** (AWS, alag AZ) | Dikhana; malik ke hukm lena (signed queue) | **Kabhi nahi** | Sirf 443 |

Machines ke beech raasta: Bot ↔ Pehredaar aur Bot/Pehredaar → Dashboard, ek private encrypted tunnel (jaise WireGuard) se, dono taraf ki pehchaan ke saath. Bot aur Pehredaar khud Dashboard se data aur hukm lene jaate hain. Dashboard unke andar kuch push nahi kar sakta.

### C2. Bot machine ke process

```
 Upstox WS feed ──► [Dimaag process]  (ek thread, deterministic)
                     feed decode → instrument state → candles → checks → score
                     │ Intent (Signal ID, strike, qty, max bhav, config hash)
                     ▼
 Upstox REST ◄──── [Haath process]   (broker ko hukm dene wala AKELA process)
 portfolio stream ─► Order Baari + rate limiter → state machine → Intent Log (durable)
                     Broker Stop manager · reconcile · Lease agent ◄──► Pehredaar
                     │ har event
                     ▼
                    [Recorder process] → append-only event log + SQLite → backup → Dashboard sync
```

- **Dimaag** kabhi broker ko seedha nahi bulata. Woh sirf Intent bhejta hai.
- **Haath** hi akela broker ko hukm deta hai. Isse Order Baari, rate limit aur Net Quantity Guard ek jagah rehte hain.
- Process ke beech bounded queues hain. Market data par per-instrument conflation hota hai (sirf aakhri tick); Intent aur order events **kabhi drop nahi** hote. Queue bhari toh naye entry band aur alert.

### C3. Order state machine (Haath)

**Order states:** `INTENT_LIKHA → BHEJA → BROKER_MANJOOR → AADHA_FILL → POORA_FILL` | `CANCEL_BHEJA → CANCELLED` | `REJECTED` | `ANJAAN` (jawab nahi aaya) `→ MILAAN_HUA`.

**Trade (position) states:**
```
FLAT → ENTRY_PENDING → OPEN_BINA_STOP → OPEN_SURAKSHIT (Broker Stop qty = fill qty, broker se confirm)
     → EXIT_SHURU (Broker Stop cancel bheja) → STOP_HATA (cancel confirm, net qty broker se padhi)
     → EXIT_ORDER_LIVE → FLAT (net qty 0 confirm)
Har state se: → PEHREDAAR_KE_HAATH (Lease khatam ya "Pehredaar ne control liya")
```

**Niyam jo code mein "assert" honge (invariants, dekho `04_Build_Roadmap.md`):**
1. Net quantity kabhi 0 se neeche nahi (Net Quantity Guard).
2. `OPEN_SURAKSHIT` mein Broker Stop qty = broker ki confirmed fill qty.
3. `OPEN_BINA_STOP` mein `Entry_Ke_Baad_Broker_Stop_Samay` se zyada nahi.
4. Ek Signal ID par ek hi entry order.
5. Lease ke bina broker ko koi hukm nahi.
6. Kill Latch laga ho toh koi entry Intent nahi.
7. Exit order ki qty = cancel confirm ke baad broker ki net qty (F-09).

### C4. Intent Log aur idempotency
- Har Intent ka ek **unique Order Tag** (kabhi dohraya nahi). Upstox ke tag ki lambai ki seema verify nahi hui; Phase 2 mein docs se pakka karna hai.
- Intent pehle durable likha jaata hai, phir order jaata hai. Crash ke baad har `BHEJA`/`ANJAAN` Intent ka broker se tag se milaan hota hai (F-36).
- **Entry kabhi bina pushti dobara nahi** (F-10). Exit tabhi dobara jaata hai jab broker position khuli dikhaye.

### C5. Event-sourcing aur deterministic replay
- Har input ek event hai: tick, Option Chain snapshot, depth, order update, malik ka hukm, **aur ghadi** (timer bhi event). Har event par sequence number aur do timestamp (exchange ka, receive ka) hote hain.
- Dimaag ek **pure function** hai: (state, event) → (naya state, Intents). Woh khud wall-clock nahi padhta.
- **Ek hi code teen mode mein:** `LiveBroker`, `PaperBroker` (asli live depth par fill simulate), `BacktestBroker` (recorded/khareede data par fill model). Sirf broker adapter badalta hai.
- **Replay test:** kal ka event log dobara chalao; har Intent bit-for-bit wahi aana chahiye (F-49). Farak = bug.

### C6. Config-as-data
- Saare numbers (Numbers ki list) ek versioned niyam-file mein. File ka hash har faisle aur har trade ke saath record hota hai.
- Niyam-file sirf malik ki manzoori se badalti hai (git commit + Badlaav-suchi). Bot chalte hue file nahi badalti; naya version agle din se lagu.
- Har number ka type, unit aur range file mein. Galat range par Taiyari Fail.

### C7. Observability
- **Metrics:** har hop ka latency histogram, feed lag, queue depth, GC pause, CPU steal, chrony offset, rate-limit headroom, open positions, Broker Stop umar.
- **Logs:** structured (JSON), har line par Signal ID, Order Tag, config hash. **Token ya chaabi kabhi log mein nahi** (log likhne wale par filter + test).
- **Alert rules:** feed lag > `Data_Purana_Hadd`, Lease ke paas, Broker Stop missing, rate-limit 80% par, disk 80% par.
- Dashboard par har dabbe ke saath data ki umar.

### C8. Crash recovery (Bot)
1. Process ko system ka service manager restart karta hai (`Restart=on-failure` + watchdog, `R_b`).
2. Start par: snapshot + event log replay → state.
3. Broker se positions, orders (tag se) aur funds padho. Intent Log ke adhoore irade milao.
4. Bina Broker Stop ki position mile → pehle Broker Stop, warna exit (Idea §5).
5. Pehredaar se Lease lo. "Pehredaar ne control liya" nishan ho toh us din broker ko hukm nahi.
6. Jab tak 1 se 5 poore na hon, naya entry nahi.

### C9. Login aur token (F-76 ke baad)
- Roz login **sirf Bot machine** karti hai (ek jagah se). Tareeka malik chunega (Sawal 139): phone manzoori wala semi-automatic rasta, ya official TOTP rasta.
- Token sirf memory mein rehta hai. Pehredaar ko private tunnel se, mutual pehchaan ke saath, ek baar bheja jaata hai. Pehredaar bhi use sirf memory mein rakhta hai.
- Pehredaar kabhi khud naya login **nahi** karta, kyunki naya token Bot ka token band kar dega. Bot mar jaaye aur token chahiye ho, toh Pehredaar subah wala token hi use karta hai (din ke ant tak valid).
- Static IP badalne par saare token band hote hain (F-65). Isliye IP kabhi din mein nahi badla jaata.
- **Verify nahi hua (Real Money se pehle test):** ek token do IP (Primary aur Secondary) se ek saath chalta hai ya nahi.

---

## D. VPS aur network (poora research: `docs/research/R_a_VPS_Network.md`)

### D1. Upstox ke server kahan hain (10 Nov 2026 ko jaancha)
- `api-hft.upstox.com` (order) aur `wsfeeder-api.upstox.com` (market-data WebSocket) dono **AWS Mumbai (ap-south-1) ke load balancer** par hain. Yeh teen tareeke se confirm hua: DNS, [AWS ip-ranges](https://ip-ranges.amazonaws.com/ip-ranges.json) aur [ARIN RDAP](https://rdap.arin.net/registry/ip/13.232.55.50).
- `api.upstox.com` (login, kill switch, portfolio stream) Cloudflare ke peeche hai. Uska asli server kahan hai, verify nahi hua.
- **Nateeja:** Bot ke liye AWS Mumbai sabse paas hai. Kisi cloud se Upstox tak ka asli latency public mein nahi mila (verify nahi hua), isliye probe se khud naapna hai.

### D2. Static IP niyam (Upstox official)
Har user ko 1 Primary aur 1 Secondary IP milta hai, chahe token kisi bhi app ne banaya ho. IP hafte mein ek baar hi badal sakta hai, aur badalte hi saare token band ho jaate hain ([docs](https://upstox.com/developer/api-documentation/update-app-static-ips/), [announcement](https://upstox.com/developer/api-documentation/announcements/algo-trading-circular/)). Exit-all aur kill switch par static IP lagta hai ya nahi, verify nahi hua. **Faisla:** Bot = Primary (AWS Elastic IP), Pehredaar = Secondary (GCP static IP). IPv6 egress band rakho, taaki koi order bina-registered IPv6 se na nikle.

### D3. Shortlist (7 option dekhe; kimat 10 Nov 2026, USD, GST alag)

| # | Provider / region | Upstox se doori | Instance | vCPU | $/mahina | Note |
|---|---|---|---|---|---|---|
| 1 | **AWS Mumbai** | Same region | `c8g.xlarge` 4 vCPU, 8 GiB | Graviton4, 1 vCPU = 1 physical core | 78.81 | Precision clock (PHC); Elastic IP doosri machine par shift ho jaata hai |
| 2 | **GCP Mumbai** | Alag provider, same shahar | `c4a-standard-2` 2 vCPU, 8 GiB | Axion, "each vCPU is an entire core" | 68.17 | Ek machine ka SLA 99.9% |
| 3 | **Azure Central India** | **Pune** (Mumbai nahi) | `D2ps_v6` 2 vCPU, 8 GiB | Cobalt 100, physical core | 33.73 | Sasta; doori thodi zyada (andaza) |
| 4 | **E2E Networks** | Delhi/Chennai DC (**Mumbai nahi**) | `SDC3-4.30GB` 4 dedicated vCPU | Dedicated | 72.43 | Bot ke liye door |
| 5 | **Akamai (Linode) Mumbai** | Alag provider, same shahar | Dedicated 4GB | Dedicated | 36.00 | IPv4, backup, NTP ki baatein verify nahi hui |
| 6 | **DigitalOcean BLR1** | Bangalore (**Mumbai region nahi**) | `c-2` | Dedicated | 42.00 | Door |
| 7 | **Oracle OCI Mumbai** | Alag provider | E5.Flex 1 OCPU | 1 OCPU = 1 core | 33.58 | Kai details verify nahi hui |

Sources: [AWS EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/), [AWS CPU options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/cpu-options-supported-instances-values.html), [GCP machine types](https://docs.cloud.google.com/compute/docs/general-purpose-machines), [Akamai pricing](https://www.akamai.com/cloud/pricing/cpu); baaki `R_a` Section 9 mein. Public IPv4 AWS, GCP aur Azure par $0.005/ghanta (~$3.65/mahina) ([AWS VPC pricing](https://aws.amazon.com/vpc/pricing/), [GCP network pricing](https://cloud.google.com/vpc/network-pricing)).

| Kasauti | AWS | GCP | Azure (Pune) |
|---|---|---|---|
| Uptime SLA | Ek machine 99.5%, alag AZ 99.99% ([SLA](https://aws.amazon.com/compute/sla/)) | Ek machine 99.9% ([SLA](https://cloud.google.com/compute/sla)) | Premium SSD ke saath 99.9% |
| DDoS (default) | Shield Standard, bina extra kharche ([Shield](https://aws.amazon.com/shield/)) | verify nahi hua | Infrastructure-level default |
| Clock sync | Time Sync + PHC ([docs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configure-ec2-ntp.html)) | Metadata NTP ([docs](https://docs.cloud.google.com/compute/docs/instances/configure-ntp)) | Host PTP |
| Snapshot | $0.05/GB-mahina | $0.052/GiB-mahina | verify nahi hua (do rate dikhe) |

### D4. Mahine ka kharcha (3 machine, 10 Nov 2026; ₹ ECB rate ₹93.94/USD se andaza)

| Combo | Bot | Pehredaar | Dashboard | Kul |
|---|---|---|---|---|
| **(ii-A) Salah:** Bot+Dashboard AWS, Pehredaar GCP | AWS `c8g.xlarge` $86.70 | GCP `c4a-standard-2` $74.52 | AWS `t4g.small` $14.65 | **~$176 ≈ ₹16,500** (AWS par 18% GST alag) |
| (i) Sab AWS, alag AZ | $86.70 | AWS `c8g.large` $45.88 | $14.65 | ~$147 ≈ ₹13,830 |
| (ii-B) Pehredaar Azure | $86.70 | Azure `D2ps_v6` $44.26 | $14.65 | ~$146 ≈ ₹13,680 |

Har machine ke kharche mein compute, IPv4, disk aur ek snapshot shaamil hai (`R_a` Section 4). Trial probe: ~$46 (≈ ₹4,300) ek hafte ka.

### D5. Settings (har ek ki wajah)

| Setting | Kya | Kyun |
|---|---|---|
| OS | Ubuntu 24.04 LTS minimal ([release cycle](https://ubuntu.com/about/release-cycle)) | Lamba security support, parkha hua |
| Ghadi | UTC system clock. AWS: `server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4` + PHC (`refclock PHC /dev/ptp_ena`). GCP: sirf `metadata.google.internal` | `Ghadi_Skew_Sakht_Hadd` (50 ms) se bahut neeche rehna; leap smear wale aur bina smear source mix nahi |
| SSH | Sirf key; password aur root login band; behtar: public SSH port band, cloud console tunnel | Bahar se login ka darwaza nahi |
| Firewall | Default-deny inbound. Bot par **koi** inbound port nahi. Dashboard par sirf 443 | Kam darwaze, kam khatra |
| Updates | Security updates automatic, **automatic reboot band**; reboot sirf market ke baad | Bazaar ke beech reboot nahi |
| IPv6 | Egress band | Order bina-registered IP se na nikle |
| CPU pinning | Core 0: OS, IRQ, ghadi. Core 1: feed reader. Core 2: Dimaag + Haath. Core 3: Recorder. Kernel: `isolcpus=domain,managed_irq,1-2 nohz_full=1-2 rcu_nocbs=1-2 irqaffinity=0` ([kernel docs](https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt)); service par `CPUAffinity` | Hot path par kernel aur doosre process ki bheed nahi (asar probe se naapna) |
| Swap | Band | Memory disk par gayi toh latency achanak badhti hai |
| Tuned profile | `network-latency` ([tuned](https://github.com/redhat-performance/tuned/tree/master/profiles)) | Ek jaisa network response; Ubuntu par poora lagu hota hai ya nahi, verify nahi hua |
| NIC IRQ | Core 0 par; `irqbalance` band ya isolated cores ban | Interrupt hot core ko na roke |
| DNS | Local caching resolver, TTL ka izzat | Load balancer ka IP badle toh bot naye IP par jaaye |
| Machine roles | Bot par web server nahi; Dashboard par token nahi | Website hack ho toh bhi order na lage |

### D6. Khareedne se pehle: probe (design, abhi code nahi)
- **3 trial VM, 5 trading din:** V1 AWS `c8g.xlarge` (Bot ka candidate; 2 din ek AZ, 3 din doosre), V2 GCP `c4a-standard-2` (Pehredaar), V3 Azure `D2ps_v6` ya Akamai (Plan B).
- **Har 10 second**, 09:00 se 15:30 IST, teen host (`api-hft`, `wsfeeder-api`, `api.upstox.com`) ke har IP par: DNS time (cache aur bina cache), TCP connect, **sirf** TLS handshake (koi HTTP request, token ya login nahi), ghadi ka offset, CPU steal.
- CSV columns aur din ka summary (p50, p90, p99, p99.9, max, error rate) `R_a` Section 6 mein.
- **Pass kasauti (andaza, pehle hafte ke baad final):** Bot VM par TCP connect p50 ≤ 2 ms, p99 ≤ 5 ms, p99.9 ≤ 20 ms; TLS p99 ≤ 15 ms; error ≤ 0.1%; ghadi offset p99 ≤ 1 ms (PHC ke saath ≤ 100 µs); steal p99 ≤ 1%.
- Probe chalane se pehle Upstox se pooch lo ki 10 second ka TLS handshake theek hai (verify nahi hua).

### D7. Bada budget hota toh: "Yeh khareedo, yeh wajah, yeh plan B" (ab D8 dekho)

| Machine | **Yeh khareedo** | Wajah | Plan B |
|---|---|---|---|
| **Bot** | AWS Mumbai `c8g.xlarge` (precision-time placement), **Elastic IP = Upstox Primary**, AZ probe se | Upstox ke order aur feed server isi region mein; 4 physical core; PHC ghadi; Elastic IP doosre AZ ki nayi machine par shift ho jaata hai, isliye Upstox par IP nahi badalna padta (F-65) | x86 chahiye toh `c7i.xlarge` ($130.31) ya `c6a.xlarge` ($68.25) |
| **Pehredaar** | GCP Mumbai `c4a-standard-2` + static IP = **Upstox Secondary** | Alag company aur alag account: billing, account lock ya ops ki galti dono ko ek saath nahi girayegi | Azure Central India `D2ps_v6` ($44.26) ya Akamai Mumbai Dedicated 4GB ($36) |
| **Dashboard** | AWS `t4g.small` teesre AZ mein, **token ke bina**, sirf 443, malik login + 2FA | Latency zaroori nahi; sasta; Bot se alag | GCP `e2-small` |

**Dhyan rahe:** AWS Mumbai poora band ho, toh Upstox ke order server bhi wahin hain, toh shayad woh bhi band honge (andaza). Isliye alag provider ka asli faayda account aur ops ki galti se bachav hai, region outage se nahi. Bot aur Pehredaar dono **ARM (Graviton/Axion)** hain; har dependency ka ARM build Phase 2 ke pehle din jaanchna hai.

### D8. Malik ka niyam (10 Nov 2026): teeno server ₹1,500 mahina ke andar

**Malik ki baat:** pehle ek Mumbai server (Bot) khareedo, baaki hisse free ya ~₹500 wale server par. **Yeh theek hai**, aur hamara apna benchmark bhi kehta hai ki D7 wali badi machine zaroori nahi thi: Python ne sabse busy second mein bhi ek core ka sirf 9-22% liya (`R_e`). D7 ki salah ab sirf tab hai jab budget badhe.

**Ganit:** $1 = ₹93.94 (ECB, 9 Nov 2026; andaza). AWS India par 18% GST lagta hai (`R_a` S61). Doosre providers par GST verify nahi hua, isliye 18% maan kar likha (conservative).

**Plan A (salah; Paper Stage ke liye):**

| Machine | Kya khareedo | $/mahina | ₹/mahina (18% GST ke saath, andaza) |
|---|---|---|---|
| Bot | **AWS Lightsail Mumbai, Linux $12 plan:** 2 vCPU, 2 GB RAM, 60 GB SSD, CPU baseline 20% prati vCPU; **static IP plan mein shaamil** | 12 | ~₹1,330 |
| Pehredaar | **Oracle Cloud Always Free** AMD micro (`VM.Standard.E2.1.Micro`: 1/8 OCPU + burst, 1 GB, 1 public IP, 50 Mbps), home region Mumbai | 0 | ₹0 |
| Dashboard | Oracle Always Free, doosra AMD micro (token ke bina) | 0 | ₹0 |
| **Kul** | | **12** | **~₹1,330** (₹170 bachat) |

**Plan B (asli paise / Stage2 se pehle; agar Paper mein Bot 1 GB aur 10% CPU mein fit ho):**

| Machine | Kya khareedo | $/mahina | ₹/mahina (andaza) |
|---|---|---|---|
| Bot | Lightsail Mumbai Linux $7: 2 vCPU, 1 GB, 40 GB, baseline 10% prati vCPU, static IP shaamil | 7 | ~₹776 |
| Pehredaar | Vultr Mumbai `vc2-1c-1gb` (1 vCPU, 1 GB, 25 GB) | 5 | ~₹554 (GST maan kar) |
| Dashboard | Oracle Always Free AMD micro | 0 | ₹0 |
| **Kul** | | **12** | **~₹1,330** |

**Plan C (sabse sasta):** Bot Lightsail $7 + Pehredaar aur Dashboard Oracle Free = ~₹776.

**Sources (dekha: 10 Nov 2026):** [Lightsail pricing](https://aws.amazon.com/lightsail/pricing/) (bundle, static IP "Included in all Lightsail plans", Mumbai region), [Lightsail baseline CPU](https://docs.aws.amazon.com/lightsail/latest/userguide/baseline-cpu-performance.html) ($7 = 10%, $12 = 20% prati vCPU), [OCI Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [Vultr plans API](https://api.vultr.com/v2/plans) (`bom` = Mumbai; $5 aur $10 plan), [Akamai types API](https://api.linode.com/v4/linode/types) (Nanode 1 GB $5, Plan B ka vikalp). AWS EC2 ka sabse sasta vikalp `t4g.micro` $0.0056/ghanta (Mumbai price file, 7 Nov 2026) + public IPv4 $3.65 + disk se ~$8.65 banta hai, isliye Lightsail (IP shaamil) sasta pada.

**Kyun Lightsail:** yeh usi AWS Mumbai region mein hai jahan Upstox ke order aur feed server hain (D1), isliye network hop wahi rehta hai. Static IP shaamil hai. Bot ka server badalna pade, toh **wahi static IP nayi Lightsail machine par le jao**, Upstox par IP mat badlo; badalne se saare token band hote hain aur hafte mein ek hi baar badal sakte hain (F-65). Static IP ko doosri machine par le jaane ka exact tareeka Lightsail docs se pakka karna baaki hai (verify nahi hua).

**Is bachat ki keemat (saaf-saaf):**

| Kya gaya | Khatra | Bachav |
|---|---|---|
| Dedicated core (ab burstable CPU) | Burst khatam hone par CPU baseline par dabta hai; p99.9 latency bigad sakti hai, khaas kar expiry din | Lightsail ke burst capacity metric par alarm. Prastaav: burst capacity bahut kam ho toh naye entry band. Paper mein roz ka CPU aur burst record karo |
| 4 GB+ RAM (ab 1-2 GB) | Python process badhe toh memory khatam ho sakti hai (benchmark mein RAM naapi nahi gayi) | Plan A (2 GB) se shuru; Paper mein RAM naapo; swap band, memory alarm |
| PHC precise ghadi | Lightsail par PHC aur Amazon Time Sync chalta hai ya nahi, verify nahi hua | Chrony se offset naapo; `Ghadi_Skew_Sakht_Hadd` (50 ms) ke liye NTP kaafi hona chahiye (andaza) |
| Pehredaar ki pakki machine (Plan A mein) | Oracle Free: 7 din tak CPU p95, network (aur A1 par memory) 20% se kam ho toh machine **delete** ho sakti hai; Pehredaar aksar idle rehta hai. Home region zaroori; "out of host capacity" bhi aata hai | Bot Pehredaar ki dhadkan dekhta hai aur na mile toh naye entry band karta hai (F-16, F-79). Pehredaar ka IP badle toh Upstox par Secondary IP sirf market ke baad. **Asli paise se pehle Plan B** (paid Pehredaar). Pay-As-You-Go upgrade se delete se bachne ki baat sirf community post mein mili, official verify nahi hua |
| Vultr/Oracle ke IPv4 aur GST | Vultr plan mein IPv4 shaamil hai ya nahi; Oracle ka public IP machine dobara banane par badalta hai ya nahi | Khareedne se pehle unke page par pakka karo (verify nahi hua) |

**Probe:** D6 wala probe ab sirf chuni hui sasti machines par, ek hafta. Lightsail $12 ka ek hafta ~$3 (~₹330 GST ke saath) hai, Oracle free hai. Lightsail par pinning ke kernel settings (D5) bekaar hain, kyunki 2 burstable vCPU hain; baaki hardening wahi rahegi.

---

## E. Tayyar repo review (poora: `docs/research/R_b_Repos_Licence.md`, jaanch 10 Nov 2026)

| Repo | Licence | Aakhri commit | Stars | Security padhai mein kya mila | **Faisla** |
|---|---|---|---|---|---|
| `upstox/upstox-python` | MIT | 9 Nov 2026 (v2.30.0) | 193 | WebSocket feeder TLS jaanch band (`CERT_NONE`, `check_hostname: False`), usi par token; `uuid` dependency purana PyPI package | **REST ke liye use** (pinned + hash-locked). **Feeder khud likho**, TLS ON, official `.proto` pin |
| `bukosabino/ta` | MIT | 18 Mar 2026 (PyPI 0.11.0, 2023) | 5.3k | Sirf ganit; VWAP rolling hai | **Khud likho**; repo ki `test/data` CSV se test vector |
| `joshyattridge/smart-money-concepts` | MIT | 3 Apr 2026 | 2.2k | Swing mein aage ki candles (`shift(-n)`) = lookahead bias | **Khud likho** (sirf concept padho) |
| `vollib/py_vollib` | MIT | 30 Apr 2026 (PyPI 1.0.12, tag sirf v1.0.10 tak) | 446 | PyPI aur GitHub tag mel nahi khaate | **Khud likho**; `tests/test_data.json` se milao |
| `marketcalls/openalgo` | **AGPL-3.0** | 6 Nov 2026 | 3.0k | Advisory GHSA-4vvw-xw2w-38g8 (SMTP TLS off); Upstox stream mein bhi TLS off; AI agent bahar call karta hai | **Use nahi, copy nahi** |
| `BennyThadikaran/NseIndiaApi` | **GPL-3.0** | 30 Oct 2026 | 162 | Unofficial NSE website rasta | **Use nahi**; Upstox official API se |
| `ranaroussi/yfinance` | Apache-2.0 | 7 Nov 2026 | 25.9k | Yahoo data "personal use only" | **Bot mein nahi**; sirf alag research jagah mein |
| `Supervisor/supervisor` | BSD-derived | 21 Dec 2025 | 9.2k | Purane CVE fixed | **Zaroorat nahi**; systemd `Restart=` + `WatchdogSec=` |
| `python-telegram-bot/python-telegram-bot` | GPL-3 / LGPL-3 | 9 Nov 2026 | 29.6k | Theek | **Zaroorat nahi**; seedha Bot API HTTPS |

**Licence ka asar (vakil se confirm karna; main vakil nahi hoon):**
- **Sirf malik ke apne account ke liye (private, kisi ko nahi diya):** GNU FAQ ke hisaab se GPL code ko badal kar privately use karna allowed hai, bina source release ke. AGPL mein bhi asar tab aata hai jab doosre log network se use karein ([GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html)).
- **Doosron ke liye (becha, diya, ya SaaS):** GPL library import ki toh poora combination GPL ki shart mein. AGPL Section 13: network par use karne wale har user ko source dena padega ([AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html)). MIT/Apache/BSD mein sirf notice aur licence copy rakhni hai.
- **Hamara plan** (khud likho + MIT official SDK) dono haalat mein AGPL aur GPL ke khatre se bachata hai.

**Behtar vikalp:** Upstox ke official SDK sirf Python, Node.js, Java, PHP, .NET mein hain. Rust ke liye sirf third-party `upstox-rust-sdk` (MPL-2.0, 1 star), Go ke liye koi official nahi, isliye Pehredaar ka chhota REST client khud likhna hai. Indicators ke liye doosra vikalp `TA-Lib/ta-lib` (BSD). `pandas-ta` 10 Nov 2026 ko 404 de raha tha, bharosa nahi. Chhutti ki suchi Upstox `/v2/market/holidays` se aur NSE circular se milao.

---

## F. Security

| Hissa | Faisla | Kyun |
|---|---|---|
| **Secrets store** | Bot: AWS Secrets Manager / SSM Parameter Store (KMS ke saath). Pehredaar: GCP Secret Manager. Dashboard: **koi broker ya Telegram chaabi nahi**. Machine ki IAM role se padhna; disk par plain file nahi | Chaabi ek jagah, access ka audit |
| **Roz ka token** | Agle din 3:30 AM par khud khatam ([docs](https://upstox.com/developer/api-documentation/get-token/)). Sirf memory mein; Pehredaar ko private tunnel se. Log mein token filter + test | Leak ho toh bhi ek din ka |
| **Login ka tareeka** | Malik chunega (Sawal 139). TOTP rasta chuna toh TOTP secret aur PIN secrets store mein, sirf login process ko access | TOTP secret chori = poora account; isliye vakil se bhi poochna |
| **Lambi chaabi rotation** | API secret aur Telegram bot token har 90 din, aur kisi bhi shak par turant | Purani chaabi ka khatra kam |
| **IP allowlist** | Upstox: sirf 2 registered IP. Cloud firewall: Bot par koi inbound nahi; Pehredaar par sirf private tunnel; Dashboard 443 | Bahar se koi rasta nahi |
| **Dashboard login** | Ek user (malik). Password + **2FA (passkey/WebAuthn ya TOTP)**. Session chhota. Real Money controls par doosra step (Idea §13) | Internet par khula hai |
| **Dashboard hardening** | Rate-limit (login aur hukm), CSRF token, sakht CSP, HTTPS only (HSTS), kam dependencies, WAF/proxy | Aam web hamle |
| **Hukm ki suraksha** | Har hukm signed, ek-baar ka number, `Command_Max_Umar`; Bot aur Pehredaar khud hukm lene jaate hain; Pehredaar sirf Kill-Switch maanta hai (F-17) | Dashboard hack ho toh bhi trade na lage |
| **Audit log** | Har login, hukm, niyam-file badlaav: kisne, kab, kahan se. Append-only, alag account ke backup mein | Baad mein sach dikhe |
| **Supply chain** | Exact version pin + hash-lock (`pip --require-hashes` / `uv lock`, Go `go.sum`). Har release se pehle `pip-audit` / OSV scan aur `govulncheck`. CI mein grep: `CERT_NONE`, `verify=False`, `check_hostname=False` mile toh fail. Broker chaabi wale process mein dependencies kam se kam ([pip secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/), [pip-audit](https://github.com/pypa/pip-audit)) | Misaal: OSV MAL-2026-2144 (LiteLLM ke kuch versions malicious, `R_b`) |
| **TLS** | Har bahari connection par certificate jaanch ON; Upstox `.proto` ka sha256 pin | SDK feeder ki galti dobara na ho |
| **Backup** | Event log, SQLite, niyam-file, audit log: roz encrypted backup, alag account ke versioned + object-lock bucket mein, `Record_Rakhne_Avadhi` (8 saal) tak | Tax aur broker record; ransomware se bachav |
| **Disaster recovery** | Infrastructure-as-code se nayi machine 30 minute mein (lakshya); Elastic IP shift (Upstox par IP nahi badalna); snapshot se restore; runbook (`04_Build_Roadmap.md`) | Machine mare toh bhi IP aur token bachein |
| **RPO / RTO lakshya** | Trading ke dauran: RPO 0 (Intent Log durable), RTO: khula trade Broker Stop par 2 s ke andar surakshit, bot 5 minute mein wapas (lakshya) | Asli paisa |

---

## G. Compliance checklist (poora: `docs/research/R_c_Compliance.md`)

**Main vakil ya CA nahi hoon. Yeh sirf facts ki suchi hai; har baat professional se confirm karni hai.**

| # | Niyam | Bot ke liye matlab | Kis tarikh tak sahi | Source |
|---|---|---|---|---|
| 1 | SEBI retail algo framework | 1 Apr 2026 se poori tarah lagu | 10 Nov 2026 | [SEBI 4 Feb 2025](https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html), [SEBI 30 Sep 2025](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/1759232056254.pdf) |
| 2 | API se aaya har order algo order | 10 orders/sec/exchange tak exchange registration nahi; broker aam Algo-ID lagata hai | 10 Nov 2026 | [NSE/INVG/67858](https://nsearchives.nseindia.com/content/circulars/INVG67858.pdf) |
| 3 | Static IP (Primary + Secondary), hafte mein ek baar badlaav | Bot = Primary, Pehredaar = Secondary | 10 Nov 2026 | NSE/INVG/67858; [Upstox](https://upstox.com/developer/api-documentation/announcements/algo-trading-circular/) |
| 4 | Roz login, OAuth + 2FA; open API band | Roz subah login; token 3:30 AM khatam | 10 Nov 2026 | SEBI 4 Feb 2025; Upstox token docs |
| 5 | Bina registration algo sirf ek pehle se tay API key se (A.4) | Upstox ka "ek user, ek app" (F-76) ke saath ek hi key; Pehredaar shared token | 10 Nov 2026 | NSE/INVG/67858; [Upstox community 27 Mar 2026](https://community.upstox.com/t/important-new-sebi-exchange-mandates-for-api-trading-effective-1st-april-2026/14822) |
| 6 | Exchange par algo ka market order nahi; options par SL-M nahi | Broker Stop = SL (limit); MPP ke liye `market_protection` | 10 Nov 2026 | [NSE/FAOP/49677](https://nsearchives.nseindia.com/content/circulars/FAOP49677.pdf); [Upstox place order](https://upstox.com/developer/api-documentation/v3/place-order/) |
| 7 | Upstox rate limit | Order APIs 10/s, 500/min, 2000/30 min (bina registration); idea ki `Order_Prati_Second_Seema` (8/400/1800) iske andar | 10 Nov 2026 | [Upstox rate limits](https://upstox.com/developer/api-documentation/rate-limiting/) |
| 8 | Algo Name header (`X-Algo-Name`) | Docs: sirf exchange-approved algo ke liye zaroori | 10 Nov 2026 | Upstox place order docs |
| 9 | F&O samay | 3 Aug 2026 se 3:40 PM; 7 Dec 2026 se 3:45 PM (expiry din expire hone wale index contract 3:30 PM) | 10 Nov 2026 | [SEBI 15 Oct 2026](https://www.sebi.gov.in/legal/circulars/oct-2026/review-of-certain-aspects-of-the-closing-auction-session-market-timings-and-settlement-methodology-f) |
| 10 | Upstox auto square-off F&O | 3:25 PM; 3:24 PM ke baad naya intraday order nahi; broker ke square-off par charge | 10 Nov 2026 | [Upstox announcement](https://upstox.com/announcements/revised-timings/important-update-intraday-square-off-timings-are-changing/) |
| 11 | Record | Broker audit trail kam se kam 5 saal (NSE); naye broker regulations mein 8 saal (secondary); tax books 7 tax years (draft Rule 46, secondary) → bot ka record 8 saal | 10 Nov 2026 | `R_c` Section 6 |
| 12 | Performance ya return ka daawa | Bot ke baare mein kabhi return ka daawa nahi (khaas kar doosron ke liye) | 10 Nov 2026 | NSE COMP53555 (text verify nahi hua) |

**Bot doosron ke liye hua toh kya badlega** (`R_c` Section 2): family ki chhoot khatam; har exchange ke saath Algo Provider empanelment (2 saal experience, ISO 27001, half-yearly VAPT); har algo ka exchange registration auditor report ke saath; algo broker ke server par host; broker ke saath agreement; black box ho toh SEBI Research Analyst registration; monthly mock; aur AGPL/GPL code bilkul nahi (Section E).

**CA / vakil / Upstox se poochne ki suchi:**
1. Shared token (Primary + Secondary IP, ek app) se Pehredaar ka exit order NSE A.4 ke andar hai? (Upstox + vakil)
2. 10 OPS ki ginti mein modify aur cancel aate hain? Bot aur Pehredaar milakar gine jaate hain? (Upstox/NSE)
3. Is category mein kya Upstox ko koi form ya declaration chahiye? `X-Algo-Name` bhejna hai? (Upstox)
4. TOTP + PIN se roz automatic login SEBI ke OAuth + 2FA niyam ke andar hai? TOTP secret server par rakhna allowed hai? (Upstox + vakil)
5. Options par SL-M bheja toh Upstox kya karta hai? `market_protection=-1` ka options par asli percent? (Upstox)
6. Machine kharab ho aur hafte ka IP badlaav ho chuka ho, toh emergency rasta? (Upstox)
7. Exit-all aur kill switch par static IP lagta hai? (Upstox)
8. Bot doosron ko diya toh hum "Algo Provider" hain? White box ya black box? PMS/Investment Adviser niyam? (vakil)
9. Family ke account par bot chalana bina registration allowed? (vakil)
10. F&O option buying ki income business income (non-speculative)? Kaunsa ITR? (CA)
11. Naye Income-tax Act 2025 mein F&O turnover kaise ginein, aur tax audit (Section 63) kab? (CA)
12. Books kitne saal (Rule 46)? Bot ke electronic logs ka India mein roz backup zaroori? (CA)
13. F&O nuksan ka carry-forward aur set-off ke naye niyam? (CA)
14. NSE ke purane data ki licence: apne paise ke bot ka internal backtest "commercial use" mein aata hai? (NSE)
15. API order par ₹10 brokerage ki aakhri tarikh: 31 Dec 2025 ya 31 Dec 2026? (Upstox)

---

## Self-check (Deliverable 2)

| Check | Nateeja |
|---|---|
| Latency budget hop by hop, har number ke saath source ya "andaza" | PASS (A1) |
| Har hisse ki language + "kab badlenge" trigger | PASS (B4) |
| Shuruaati soch ko saboot se challenge kiya | PASS (B3) |
| Python vs Rust vs C++ (aur Go) benchmark p50/p99.9 | PASS (B5; p99 `R_e` mein) |
| Architecture: process, queue, state machine, Intent Log, idempotency, event-sourcing, replay, config, observability, crash recovery, 3 machine | PASS (C1-C9) |
| VPS: 5+ option, official pricing tarikh ke saath, exact instance, settings, probe design, "yeh khareedo + plan B", Dashboard bot machine par nahi | PASS (D1-D7; 7 option) |
| Repo: licence, aakhri commit, security padhai, faisla, behtar vikalp, AGPL/GPL asar | PASS (E) |
| Security: secrets, token rotation, IP allowlist, Dashboard 2FA/rate-limit/audit, supply chain, backup/DR | PASS (F) |
| Compliance: tarikh + source, CA/vakil list, "doosron ke liye" | PASS (G) |
| Koi key, token, password nahi; "100% safe" nahi | PASS |
| Verify nahi hua wali baatein saaf likhi | PASS (feed interval, shared token do IP se, Cloudflare origin, protobuf decode cost, kill switch par IP, Upstox tag ki lambai) |
