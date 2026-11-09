#!/usr/bin/env python3
"""Synthetic tick generator (seeded). Throw-away benchmark, production code nahi.

Likhta hai (data/ folder mein):
  meta.bin      498 instruments x 24 bytes  '<BBBBIdQ'
                kind(0 spot,1 fut,2 opt), idx(0 BN,1 NIFTY,2 SENSEX), otype(0 CE,1 PE,9 none),
                exp(0/1), lot(u32), strike(f64), expiry_ns(u64)
  ticks.bin     N x 62 bytes packed little-endian
                id u16, ts_ns u64, ltp f64, ltq u32, bid f64, ask f64, bq u32, aq u32, oi u64, vol u64
  ticks.ndjson  same ticks, ek JSON object per line (decode cost dikhane ke liye)

Instrument id: 0..2 spot, 3..5 futures, option = 6 + idx*164 + exp*82 + k*2 + t  (k 0..40, t 0 CE/1 PE)
"""
import argparse, datetime, os, struct
import numpy as np

N_IDX, N_EXP, N_K = 3, 2, 41
N_INST = 6 + N_IDX * N_EXP * N_K * 2          # 498
BASE_SPOT = [52000.0, 24500.0, 80500.0]
STEP = [100.0, 50.0, 100.0]
LOT = [30, 75, 20]
BASE_IV = [0.14, 0.12, 0.13]
R = 0.065
YEAR_NS = 365.0 * 86400e9

TICK_DT = np.dtype([('id', '<u2'), ('ts', '<u8'), ('ltp', '<f8'), ('ltq', '<u4'), ('bid', '<f8'),
                    ('ask', '<f8'), ('bq', '<u4'), ('aq', '<u4'), ('oi', '<u8'), ('vol', '<u8')])
assert TICK_DT.itemsize == 62


def ncdf(x):
    # Abramowitz-Stegun 26.2.17 (same formula as the benchmark code)
    z = np.abs(x)
    k = 1.0 / (1.0 + 0.2316419 * z)
    poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))))
    n = 1.0 - np.exp(-0.5 * z * z) * 0.3989422804014327 * poly
    return np.where(x >= 0, n, 1.0 - n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
    ap.add_argument('--seconds', type=int, default=360)
    ap.add_argument('--seed', type=int, default=20261110)
    ap.add_argument('--no-json', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)

    # 10 Nov 2026 09:15 IST = 03:45 UTC
    t0 = int(datetime.datetime(2026, 11, 10, 3, 45, tzinfo=datetime.timezone.utc).timestamp()) * 1_000_000_000
    exp_ns = [t0 + int((1 * 86400 + 6.25 * 3600) * 1e9), t0 + int((8 * 86400 + 6.25 * 3600) * 1e9)]

    # ---- instruments ----
    kind = np.zeros(N_INST, np.uint8); idx = np.zeros(N_INST, np.uint8); otype = np.full(N_INST, 9, np.uint8)
    expi = np.zeros(N_INST, np.uint8); lot = np.zeros(N_INST, np.uint32); strike = np.zeros(N_INST)
    expns = np.zeros(N_INST, np.uint64); weight = np.zeros(N_INST)
    for i in range(3):
        kind[i], idx[i], weight[i] = 0, i, 3.0
        kind[3 + i], idx[3 + i], lot[3 + i], weight[3 + i] = 1, i, LOT[i], 2.0
        expns[3 + i] = t0 + int(20 * 86400e9)
    for i in range(N_IDX):
        atm = round(BASE_SPOT[i] / STEP[i]) * STEP[i]
        for e in range(N_EXP):
            for k in range(N_K):
                for t in range(2):
                    o = 6 + i * 164 + e * 82 + k * 2 + t
                    kind[o], idx[o], otype[o], expi[o], lot[o] = 2, i, t, e, LOT[i]
                    strike[o] = atm + (k - 20) * STEP[i]
                    expns[o] = exp_ns[e]
                    weight[o] = np.exp(-abs(k - 20) / 8.0) * (2.0 if e == 0 else 1.0)
    with open(os.path.join(a.out, 'meta.bin'), 'wb') as f:
        for o in range(N_INST):
            f.write(struct.pack('<BBBBIdQ', kind[o], idx[o], otype[o], expi[o], lot[o], strike[o], int(expns[o])))

    # ---- timestamps: normal ~3000/s, bursts 30000/s ----
    bursts = [(60, 72), (180, 192), (300, 312)]
    ts_parts = []
    for s in range(a.seconds):
        rate = 30000 if any(b0 <= s < b1 for b0, b1 in bursts) else 3000
        n = int(rate * rng.uniform(0.9, 1.1))
        ts_parts.append(t0 + s * 1_000_000_000 + rng.integers(0, 1_000_000_000, n))
    ts = np.sort(np.concatenate(ts_parts)).astype(np.uint64)
    N = len(ts)
    p = weight / weight.sum()
    ids = rng.choice(N_INST, size=N, p=p).astype(np.uint16)
    # first tick of every instrument early (so state exists), just overwrite first 498 ids
    ids[:N_INST] = rng.permutation(N_INST)

    # ---- spot path on 10 ms grid ----
    steps = a.seconds * 100 + 1
    sd = 0.15 * np.sqrt(0.01 / (252 * 22500.0))
    spot_grid = np.zeros((N_IDX, steps))
    sec_of_step = np.arange(steps) // 100
    in_burst = np.zeros(steps, bool)
    for b0, b1 in bursts:
        in_burst |= (sec_of_step >= b0) & (sec_of_step < b1)
    for i in range(N_IDX):
        z = rng.standard_normal(steps) * sd * np.where(in_burst, 4.0, 1.0)
        z += np.where(in_burst, rng.choice([-1.0, 1.0]) * sd * 0.8, 0.0)   # burst me trend
        spot_grid[i] = BASE_SPOT[i] * np.exp(np.cumsum(z))
    gi = ((ts - np.uint64(t0)) // np.uint64(10_000_000)).astype(np.int64)
    ix = idx[ids].astype(np.int64)
    S = spot_grid[ix, gi]

    # ---- prices ----
    k_of = np.zeros(N_INST); k_of[6:] = [((o - 6) % 82) // 2 for o in range(6, N_INST)]
    price = np.empty(N)
    kd = kind[ids]
    m0 = kd == 0; m1 = kd == 1; m2 = kd == 2
    price[m0] = S[m0]
    price[m1] = S[m1] * (1 + R * 20 / 365) * (1 + rng.normal(0, 2e-5, m1.sum()))
    o = ids[m2].astype(np.int64)
    K = strike[o]
    T = (expns[o].astype(np.float64) - ts[m2].astype(np.float64)) / YEAR_NS
    iv = np.array(BASE_IV)[ix[m2]] + 0.004 * np.abs(k_of[o] - 20) + 0.01 * expi[o]
    sq = np.sqrt(T)
    d1 = (np.log(S[m2] / K) + (R + 0.5 * iv * iv) * T) / (iv * sq)
    d2 = d1 - iv * sq
    disc = K * np.exp(-R * T)
    ce = S[m2] * ncdf(d1) - disc * ncdf(d2)
    pe = disc * ncdf(-d2) - S[m2] * ncdf(-d1)
    opt_price = np.where(otype[o] == 0, ce, pe) * (1 + rng.normal(0, 0.002, len(o)))
    price[m2] = opt_price
    ltp_p = np.maximum(np.round(price / 0.05) * 5, 5).astype(np.int64)        # paise, multiple of 5
    ltp_p[m0] = np.round(S[m0] * 100).astype(np.int64)                          # index: 0.01 tick
    m1b = rng.integers(1, 5, N); m2b = rng.integers(1, 5, N)
    bid_p = np.maximum(ltp_p - 5 * m1b, 5); ask_p = ltp_p + 5 * m2b
    bid_p[m0] = ltp_p[m0]; ask_p[m0] = ltp_p[m0]
    ltq = (lot[ids].astype(np.int64) * rng.integers(1, 11, N)).astype(np.uint32)
    ltq[m0] = 0
    bq = (lot[ids].astype(np.int64) * rng.integers(1, 200, N)).astype(np.uint32)
    aq = (lot[ids].astype(np.int64) * rng.integers(1, 200, N)).astype(np.uint32)
    bq[m0] = 0; aq[m0] = 0

    # cumulative volume / oi per instrument (vectorised group cumsum)
    order = np.argsort(ids, kind='stable')
    sid = ids[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sid)) + 1]
    grp = np.repeat(np.arange(len(starts)), np.diff(np.r_[starts, N]))
    def group_cumsum(x):
        c = np.cumsum(x[order])
        base = np.r_[0, c[starts[1:] - 1]]
        out = np.empty(N, np.int64); out[order] = c - base[grp]
        return out
    vol_open = (lot.astype(np.int64) * rng.integers(0, 100000, N_INST))
    vol = vol_open[ids] + group_cumsum(ltq.astype(np.int64))
    oi_open = (lot.astype(np.int64) * rng.integers(1000, 50000, N_INST))
    oi = oi_open[ids] + group_cumsum(lot[ids].astype(np.int64) * rng.integers(-3, 5, N))
    vol[m0] = 0; oi[m0] = 0; oi[m1] = oi[m1]  # index ka volume/oi nahi

    rec = np.empty(N, TICK_DT)
    rec['id'] = ids; rec['ts'] = ts; rec['ltp'] = ltp_p / 100.0; rec['ltq'] = ltq
    rec['bid'] = bid_p / 100.0; rec['ask'] = ask_p / 100.0; rec['bq'] = bq; rec['aq'] = aq
    rec['oi'] = np.maximum(oi, 0).astype(np.uint64); rec['vol'] = vol.astype(np.uint64)
    rec.tofile(os.path.join(a.out, 'ticks.bin'))
    print(f'ticks={N} seconds={a.seconds} instruments={N_INST} bin_bytes={N * 62}')

    if not a.no_json:
        with open(os.path.join(a.out, 'ticks.ndjson'), 'w') as f:
            cols = [rec[c].tolist() for c in ('id', 'ts', 'ltp', 'ltq', 'bid', 'ask', 'bq', 'aq', 'oi', 'vol')]
            lines = []
            for i, t, l, q, b, k, x, y, z, v in zip(*cols):
                lines.append(f'{{"i":{i},"t":{t},"ltp":{l!r},"ltq":{q},"b":{b!r},"a":{k!r},'
                             f'"bq":{x},"aq":{y},"oi":{z},"v":{v}}}\n')
                if len(lines) >= 100000:
                    f.write(''.join(lines)); lines.clear()
            f.write(''.join(lines))
        print('json written', os.path.getsize(os.path.join(a.out, 'ticks.ndjson')), 'bytes')


if __name__ == '__main__':
    main()
