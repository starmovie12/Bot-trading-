# R-e: Benchmark: Python vs Rust vs C++ vs Go (synthetic tick replay)

**Tarikh:** 10 Nov 2026. **Kisne:** benchmark subagent. **Code:** `scratch/bench/` (throw-away, production code nahi).
**Data:** sirf synthetic (seeded). Koi broker, network, key ya token use nahi hua.

## Saar (10 line)
1. Ek jaisa logic 5 tarah chalaya: plain Python, Python+NumPy, Python+Numba, Rust, C++, Go. Sabka checksum match hua.
2. Plain Python ek tick (decode + candles + EMA/RSI/ATR) ~2 µs (p50) mein, ~21 µs (p99.9) mein karta hai.
3. Python throughput ~3.6 lakh ticks/sec hai. Burst 30,000 ticks/sec ka yeh ~12 guna hai.
4. Sabse busy second mein Python CPU sirf ~9% busy raha (binary). JSON (stdlib) decode ke saath ~22%.
5. 1-second evaluation (492 options ka IV + delta, ~135 shortlisted strikes par 50 checks) Python mein ~2.4 ms (p50), p99.9 ~4-7 ms.
6. Yani `Evaluation_Gati_Samay` (1 second) ka 1% se kam istemal. Headroom ~150 guna.
7. Rust/C++ tick par ~35 guna aur eval par ~23 guna tez hain. Par Python ko is load par itni speed ki zaroorat nahi dikhi.
8. Asli khatra average speed nahi, Python ka GC pause hai: growing objects ke saath ek pause 217-234 ms tak gaya.
9. `gc.freeze()` + `gc.disable()` se max tick time ~2.2 ms aur max lag ~6 ms rah gaya. Isliye GC discipline zaroori hai.
10. Nateeja: is synthetic load par Python kaafi hai. Rust mein tab badlo jab neeche likhe measurable trigger live/paper mein toot jaayein.

## Machine
Yeh shared 4 vCPU cloud sandbox hai, dedicated machine nahi. Doosre VM ka load results ko hila sakta hai.

| Cheez | Value |
|---|---|
| CPU | Intel Xeon Processor @ 2.10GHz (KVM guest), 4 vCPU, 1 thread/core |
| Cache | L2 8 MiB (4 instances), L3 260 MiB |
| RAM | 15 GiB, swap nahi |
| OS / kernel | Ubuntu 24.04.5 LTS, Linux 6.18.44-fc-v310, clocksource `tsc` |
| Steal time | benchmark ke dauraan ~0.4% (/proc/stat se andaza) |
| Toolchains | Python 3.13.18, NumPy 2.5.3, Numba 0.68.1, orjson 3.13.0, rustc 1.97.0 (serde_json 1.0.154), g++ 13.3.0, go 1.24.7 |
| Timer ka apna kharcha | Python `perf_counter_ns` ~86-89 ns/call, C++ `steady_clock` ~28 ns/call |
| Pinning | har run `taskset -c 2` par, ek ke baad ek (parallel nahi) |

## Method
**Data (gen.py, seed 20261110).** 498 instruments: 3 index spot (BankNifty, Nifty50, Sensex), 3 futures, aur 3 index x 2 expiry x 41 strikes x CE/PE = 492 options.
360 simulated seconds, 2,055,094 ticks. Normal ~3,000 ticks/sec, teen burst (har ek 12 sec) ~30,000 ticks/sec (max second 32,712 ticks).
Tick record fixed 62 bytes: instrument_id u16, ts_ns u64, ltp f64, ltq u32, bid f64, ask f64, bidqty u32, askqty u32, oi u64, volume u64.
Wahi ticks NDJSON (ek JSON object per line) mein bhi likhe, taaki decode ka kharcha dikhe. Upstox ka asli feed protobuf hai; protobuf decode yahan naapa nahi gaya (verify nahi hua).

**Per tick.** Decode, phir ltp, volume delta, running VWAP, bid/ask/qty/OI update.
Phir 1-min, 3-min, 15-min candles (timestamp bucket). Candle close par incremental EMA(9), EMA(21), RSI(14 Wilder), ATR(14 Wilder).

**Har simulated second (evaluation).** Har instrument ka ltp/volume 301-second ring buffer mein. Har index ke liye breadth, PCR, spot momentum.
Har option (492) ka implied volatility (3 Newton steps, Black-Scholes), phir delta. Shortlist: CE delta 0.25..0.65 ya PE delta -0.65..-0.25, ltp >= 2.
Shortlisted (~135 per second) par 16 features: premium raftaar 30s vs 5-min, volume spike vs baseline, +-2 neighbour strikes se fake spike, OI change, PCR, breadth, 3 timeframe EMA gap, RSI, ATR, VWAP distance, spread, depth imbalance, spot momentum.
Unpar 50 threshold checks (vazan 1-4), ek spread gate, score >= 70 par signal. Checks aur thresholds synthetic hain, idea ke asli numbers nahi.

**Checksum.** Integer counts exact match (359 evals, 48,544 shortlisted, 1,024,020 green checks, 9,209 signals, score sum 2,497,585).
Float sums (IV, delta, features, indicators) relative 1e-9 tak match. Rust aur C++ bit-for-bit Python jaise; Go, NumPy, Numba mein ~1e-15 ka farq (exp/log library ka farq).

**Naap.** Per-tick latency = decode + update (eval ka time ghata ke). Per-eval latency alag. Har variant 3 runs; table mein har statistic ka median of 3.
Queue simulation: har tick apne timestamp par aata hai, single-thread bot. Lag = kaam khatam hone ka samay - aane ka samay. Isme 1-second eval ke peeche ruke ticks bhi dikhte hain.
GC: `gc on` (default, callback se pause naapa) vs `gc freeze` (`gc.freeze()` + `gc.disable()`). `hist` variant har tick ko list mein rakhta hai (naive bot jaisa), taaki GC ka asli asar dikhe.

## Results (median of 3 runs)

| Language / variant | per-tick p50 / p99 / p99.9 / max | per-eval p50 / p99 / p99.9 / max | Throughput (ticks/s) | Checksum OK |
|---|---|---|---|---|
| C++ (-O2 -march=native), bin | 53 ns / 86 ns / 234 ns / 109 µs | 107 µs / 155 µs / 187 µs / 201 µs | 9,165,280 | haan |
| Rust (--release), bin | 54 ns / 100 ns / 229 ns / 1.00 ms | 105 µs / 157 µs / 282 µs / 342 µs | 8,416,539 | haan |
| Go, bin | 66 ns / 95 ns / 219 ns / 245 µs | 160 µs / 240 µs / 291 µs / 314 µs | 7,125,278 | haan |
| Python + Numba eval, bin | 1.8 µs / 4.0 µs / 19.4 µs / 2.59 ms | 394 µs / 649 µs / 727 µs / 744 µs | 453,937 | haan |
| Python + NumPy eval, bin | 1.9 µs / 3.8 µs / 20.0 µs / 2.71 ms | 877 µs / 1.42 ms / 2.38 ms / 2.89 ms | 440,533 | haan |
| Python plain, bin, gc on | 1.9 µs / 4.5 µs / 22.0 µs / 4.02 ms | 2.45 ms / 4.05 ms / 6.91 ms / 7.95 ms | 367,176 | haan |
| Python plain, bin, gc freeze | 2.0 µs / 4.6 µs / 20.9 µs / 2.13 ms | 2.40 ms / 3.77 ms / 4.27 ms / 4.31 ms | 362,350 | haan |
| Python plain, bin, hist, gc on | 2.1 µs / 6.4 µs / 31.7 µs / **228 ms** | 2.47 ms / 4.36 ms / 5.99 ms / 6.21 ms | 292,627 | haan |
| Python plain, bin, hist, gc freeze | 2.1 µs / 5.8 µs / 23.7 µs / 2.24 ms | 2.45 ms / 3.84 ms / 4.95 ms / 5.53 ms | 327,524 | haan |
| Rust, JSON (serde_json) | 418 ns / 859 ns / 3.7 µs / 2.12 ms | 109 µs / 166 µs / 192 µs / 193 µs | 1,926,791 | haan |
| Go, JSON (encoding/json) | 2.4 µs / 8.1 µs / 25.3 µs / 6.73 ms | 165 µs / 239 µs / 777 µs / 1.02 ms | 358,412 | haan |
| Python plain, JSON (orjson) | 2.7 µs / 6.4 µs / 24.4 µs / 7.10 ms | 2.43 ms / 4.04 ms / 4.45 ms / 4.56 ms | 284,536 | haan |
| Python plain, JSON (stdlib json) | 4.8 µs / 12.1 µs / 34.1 µs / 3.54 ms | 2.45 ms / 3.99 ms / 4.31 ms / 4.33 ms | 171,152 | haan |

NumPy/Numba eval time mein har second list state ko numpy array mein badalne ka kharcha bhi shaamil hai. Numba ka JIT compile time timing se bahar hai.
Per-tick numbers mein timer ka apna kharcha shaamil hai (compiled mein ~28 ns, yani asli kaam ~25-35 ns).
"max" column zyada tar OS/VM noise hai: Rust ke teen runs ka max 0.2 ms, 1.0 ms, 2.1 ms aaya. Python (bina GC collection) ka max 3-9 ms.

### Queue simulation (tick apne timestamp par aata hai)

| Variant | lag p50 | lag p99 | lag p99.9 | lag max | Sabse busy second |
|---|---|---|---|---|---|
| C++ bin | 53 ns | 88 ns | 259 ns | 202 µs | 0.2% |
| Rust bin | 54 ns | 101 ns | 259 ns | 1.00 ms | 0.3% |
| Rust JSON | 418 ns | 881 ns | 11.8 µs | 2.12 ms | 2.1% |
| Python + Numba bin | 1.8 µs | 4.8 µs | 40.8 µs | 2.59 ms | 7.2% |
| Python plain bin, gc on | 2.0 µs | 6.2 µs | 1.97 ms | 7.96 ms | 9.4% |
| Python plain bin, gc freeze | 2.0 µs | 6.2 µs | 1.81 ms | 4.33 ms | 8.6% |
| Python plain JSON orjson | 2.7 µs | 9.8 µs | 2.04 ms | 7.10 ms | 14.8% |
| Python plain JSON stdlib | 4.8 µs | 22.4 µs | 2.01 ms | 4.81 ms | 22.2% |
| Python plain bin, hist, gc on | 2.1 µs | 656 µs | **168 ms** | **228 ms** | 31.1% |

Python ka lag p99.9 ~2 ms isliye hai ki ~2.4 ms ka eval chalte waqt aane wale ticks line mein rukte hain. Numba/NumPy se eval chhota hua, toh yeh lag bhi gira.

### GC ka asar (Python)
Is design mein hot loop ke objects turant free ho jaate hain. Isliye normal runs mein GC collection 0 rahe aur gc on/freeze mein farq chhota tha.
`hist` variant (har tick list mein jodna) mein har run mein 937 gen0, 85 gen1, 6 gen2 collections hue. Max pause 217-234 ms tha.
Yahi pause burst ke beech aaye toh hazaaron ticks ~0.2 second late hote hain (lag p99.9 168 ms). `gc.freeze()` + `gc.disable()` se max tick time ~2.2 ms aur max lag ~6 ms (eval samet) rah gaya.
orjson runs mein 3 gen0 collections (~46-51 ms) report hue, par per-tick max mein nahi dikhe. Shayad loop ke bahar hue; jaanch nahi ki.
`gc.disable()` ka nuksan: cycle wala kachra apne aap saaf nahi hota. Isliye bade growing objects se bacho, ya shant samay par khud `gc.collect()` chalao (Phase 2 mein jaanchna).

### JSON decode ka kharcha (per tick p50, binary se upar)
Python stdlib `json` ~+2.8 µs, `orjson` ~+0.7 µs, Rust `serde_json` ~+0.36 µs, Go `encoding/json` ~+2.3 µs.
Python mein decode sabse bada hissa ban sakta hai. Asli Upstox protobuf decode ka kharcha verify nahi hua.

## Interpretation: kya Python tik paata hai?
**Tick burst.** 30,000 ticks/sec par har tick ka average budget ~33 µs hai. Plain Python ka p99.9 ~21 µs (binary) aur ~34 µs (stdlib JSON) hai.
Throughput ~3.6 lakh/sec (binary) aur ~1.7 lakh/sec (stdlib JSON) hai. Yani burst ka ~12 guna aur ~5.7 guna headroom.
Sabse busy second mein CPU 9-22% busy raha. Single core par bhi kaafi jagah bachi hai.

**Evaluation budget.** Plain Python eval p99.9 ~4-7 ms hai, 1 second budget ka 1% se kam. NumPy se ~2.4 ms, Numba se ~0.7 ms (p99.9).
Asli checks agar 10 guna bhaari hon, tab bhi plain Python ~50-70 ms par hoga (yeh andaza hai, naapa nahi).

**Asli khatra.** (a) GC pause jab objects badhte rahein. (b) Eval ke dauraan ticks ka rukna (abhi ~2 ms, eval bhaari hua toh badhega).
(c) Network, asyncio, logging, DB/dashboard writes jo is benchmark mein nahi hain.
Inke liye Rust zaroori nahi: GC discipline, NumPy/Numba eval, aur decode ko alag process mein rakhna pehle aazmao.

## Caveats
- Shared 4 vCPU VM, dedicated nahi. Max/p99.9 numbers mein VM noise hai. Asli VPS par dobara naapna padega.
- Data synthetic hai. Strike distribution, burst ka roop aur price process asli market jaisa hone ki guarantee nahi.
- Upstox feed ki asli tick rate (aam din aur expiry din) verify nahi hui. 3,000 aur 30,000 ticks/sec sirf maan kar liye.
- Upstox feed protobuf hai. Protobuf decode (Python mein) naapa nahi gaya; JSON sirf proxy hai.
- Network receive, WebSocket, asyncio event loop, logging, order placement, dashboard push shaamil nahi.
- 50 checks synthetic hain. Idea ke asli checks (jaise order-flow, iceberg) zyada bhaari ho sakte hain.
- Single thread design naapa gaya. Multi-process design naapa nahi gaya.

## Kab Rust mein badlein: measurable trigger
Phase 2 (paper mode) mein bot inhi metrics ko log kare: per-tick time, per-eval time, queue lag, sabse busy second, GC pause.
Inme se koi bhi trigger kuch din lagataar toote, aur Python wale upay (gc.freeze, NumPy/Numba, orjson/fast protobuf, alag decode process) aazmaane ke baad bhi toote, tab hot path Rust mein le jao:
1. Main loop ka sabse busy second > 50% CPU (abhi synthetic par 9-22%).
2. Tick lag p99.9 > 50 ms, ya koi bhi lag > 250 ms (aaj binary Python ~2 ms p99.9).
3. Eval p99 > 200 ms, yani `Evaluation_Gati_Samay` budget ka 20% (aaj ~4 ms).
4. GC freeze ke baad bhi koi pause > 20 ms.
5. Load scale > 5 guna: jaise > ~2,500 instruments ya > ~1.5 lakh ticks/sec sustained (aaj headroom ~12 guna; aadha safety ke liye).
Beech ka raasta (naapa nahi): sirf hot path (decode + candles + eval) Rust mein PyO3 module, baaki bot Python mein.

## Dobara chalana
`cd scratch/bench && ./run_all.sh` (build, data, har variant 3 runs `taskset -c 2` par, `analyze.py`). Poori table `scratch/bench/out/report.md` mein banti hai.
`data/` aur `out/` git mein nahi jaate.
