# scratch/bench: Python vs Rust vs C++ vs Go (synthetic tick replay)

Yeh throw-away benchmark hai, production code nahi. Koi broker, network, key ya token nahi.
Sirf synthetic (nakli, seeded) data. Result: `docs/research/R_e_Benchmark.md`.

## Chalana

```bash
cd scratch/bench
./run_all.sh            # build + data (agar nahi hai) + har variant 3 runs (taskset -c 2) + analyze
RUNS=1 ./run_all.sh     # jaldi check ke liye
```

Zaroorat: python3 (numpy, numba, orjson optional), cargo/rustc, g++, go (optional).
`data/` aur `out/` git mein nahi jaate (`.gitignore`).

## Files

| File | Kaam |
|---|---|
| `gen.py` | Seeded generator. `data/meta.bin`, `data/ticks.bin` (62-byte fixed record), `data/ticks.ndjson` (same ticks JSON mein) |
| `py_plain.py` | Plain Python reference. Spec isi file mein hai. Flags: `--format bin/json`, `--json-lib json/orjson`, `--gc on/freeze`, `--keep-history` |
| `py_numpy.py` | Tick path plain Python; 1-second eval NumPy vectorised (`--engine numpy`) ya Numba JIT (`--engine numba`) |
| `rust/` | Rust port (`--release`, `target-cpu=native`), JSON ke liye serde_json |
| `cpp/main.cpp` | C++ port (`-O2 -march=native -ffp-contract=off`), sirf binary format |
| `go/main.go` | Go port, JSON ke liye `encoding/json` |
| `analyze.py` | Percentiles, median of 3 runs, checksum match, queue simulation |
| `run_all.sh` | Sab kuch ek saath |

## Data

- 498 instruments: 3 index spot + 3 futures + 3 index x 2 expiry x 41 strikes x CE/PE (492 options).
- 360 simulated seconds, ~2.05M ticks. Normal ~3,000 ticks/s, teen burst (12 s each) ~30,000 ticks/s.
- Tick record: id u16, ts_ns u64, ltp f64, ltq u32, bid f64, ask f64, bidqty u32, askqty u32, oi u64, volume u64.

## Logic (sab languages mein bilkul same)

Per tick: decode -> ltp, volume delta, running VWAP, bid/ask/qty/OI -> 1m/3m/15m candles (ts bucket).
Candle close par incremental EMA(9), EMA(21), RSI(14, Wilder), ATR(14, Wilder).

Har simulated second (pehla tick jo naye second mein aaye, us se pehle) evaluation:
1. Har instrument ka ltp aur volume 301-second ring buffer mein snapshot (30s aur 5-min windows).
2. Har index: breadth (kitne options 30s pehle se upar), PCR per expiry, spot momentum.
3. Har option (492): implied volatility (3 Newton steps, Black-Scholes, A&S normal CDF), phir delta.
4. Shortlist: CE delta 0.25..0.65 ya PE delta -0.65..-0.25, aur ltp >= 2.
5. Har shortlisted option par 16 features (premium raftaar 30s vs 5-min, volume spike, +-2 neighbour
   strikes ke against fake-spike, OI change, PCR, breadth, EMA gap 3 timeframe, RSI, ATR, VWAP distance,
   spread, depth imbalance, spot momentum) aur unpar 50 threshold checks (vazan 1..4), spread wala gate.
6. Score >= 70 (max 123) = signal.

Checksum: integer counts (evals, shortlisted, green checks, gate pass, signals, score sum) exact match;
float sums (IV, delta, features, final indicators) relative 1e-9 tak match. Reference = `py_plain` bin.

## Measure kya hota hai

- `tick_ns`: ek tick ka decode + update time (eval time isme se ghata diya). Timer call ka apna kharcha shaamil.
- `eval_ns`: ek 1-second evaluation ka time (NumPy/Numba mein list->array conversion bhi shaamil).
- Queue simulation (`analyze.py`): tick apne timestamp par aata hai, single thread bot. Lag = kaam khatam - arrival.
- Python GC: `--gc on` (default, callback se pause naapte hain) vs `--gc freeze` (`gc.freeze()` + `gc.disable()`).
  `--keep-history` har tick ko list mein rakhta hai (naive bot jaisa), taaki GC ka asli asar dikhe.

## Seemayein

Shared 4 vCPU sandbox (dedicated nahi). Synthetic data. Asli Upstox feed rate aur protobuf decode cost
verify nahi hue. Network, asyncio, logging, order placement is benchmark mein nahi hain.
