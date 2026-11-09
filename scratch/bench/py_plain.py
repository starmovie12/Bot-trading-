#!/usr/bin/env python3
"""Plain Python reference implementation. Throw-away benchmark, production code nahi.

Logic ka spec README.md mein hai. Rust/C++/Go/NumPy versions isi ko copy karte hain.
Usage: python3 py_plain.py --data data --out out/py_plain [--format bin|json] [--json-lib json|orjson] [--gc on|freeze]
"""
import argparse, array, gc, json, math, os, struct, sys, time

N_INST = 498
TF_NS = (60_000_000_000, 180_000_000_000, 900_000_000_000)
RING = 301
R = 0.065
YEAR_NS = 365.0 * 86400e9
A9 = 2.0 / 10.0
A21 = 2.0 / 22.0
INV_SQRT_2PI = 0.3989422804014327
MIN_SCORE = 70
# 50 checks = 16 features x thresholds. check j: feature j%16, threshold BASE+STEP*(j//16)
BASE = [1.0, 1.5, 0.0, 0.0, 0.8, 0.5, 0.0, 0.0, 0.0, 50.0, 50.0, 0.002, 0.0, 0.05, 0.0, 0.0]
STEPS = [0.25, 0.25, 0.002, 0.01, 0.1, 0.05, 0.0005, 0.0005, 0.0005, 5.0, 5.0, 0.001, 0.001, 0.02, 0.1, 0.0002]
DIR = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1]      # 1: green if f > th, 0: green if f < th
CHECKS = [(j % 16, BASE[j % 16] + STEPS[j % 16] * (j // 16), DIR[j % 16], 1 + j % 4, j % 16 == 13)
          for j in range(50)]                                 # (feature, th, dir, weight, is_gate)
TICK = struct.Struct('<HQdIddIIQQ')


def opt_id(i, e, k, t):
    return 6 + i * 164 + e * 82 + k * 2 + t


def ncdf(x):
    z = abs(x)
    k = 1.0 / (1.0 + 0.2316419 * z)
    poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))))
    n = 1.0 - math.exp(-0.5 * z * z) * INV_SQRT_2PI * poly
    return n if x >= 0 else 1.0 - n


def load_meta(path):
    raw = open(path, 'rb').read()
    return [struct.unpack_from('<BBBBIdQ', raw, o * 24) for o in range(N_INST)]


class State:
    def __init__(self):
        n = N_INST
        self.ltp = [0.0] * n; self.last_vol = [0] * n; self.cum_pv = [0.0] * n; self.cum_v = [0] * n
        self.vwap = [0.0] * n; self.bid = [0.0] * n; self.ask = [0.0] * n; self.bq = [0] * n; self.aq = [0] * n
        self.oi = [0] * n; self.oi_open = [-1] * n
        # candles: [tf][inst]
        self.cb = [[-1] * n for _ in range(3)]
        self.co = [[0.0] * n for _ in range(3)]; self.ch = [[0.0] * n for _ in range(3)]
        self.cl = [[0.0] * n for _ in range(3)]; self.cc = [[0.0] * n for _ in range(3)]
        self.cv = [[0] * n for _ in range(3)]
        self.ncl = [[0] * n for _ in range(3)]; self.pclose = [[0.0] * n for _ in range(3)]
        self.ema9 = [[0.0] * n for _ in range(3)]; self.ema21 = [[0.0] * n for _ in range(3)]
        self.atr = [[0.0] * n for _ in range(3)]; self.ag = [[0.0] * n for _ in range(3)]
        self.al = [[0.0] * n for _ in range(3)]; self.rsi = [[50.0] * n for _ in range(3)]
        # rolling 1-second snapshots (ring of 301 seconds) for 30s / 5-min windows
        self.ring_p = [[0.0] * n for _ in range(RING)]; self.ring_v = [[0] * n for _ in range(RING)]
        # checksum accumulators
        self.n_evals = 0; self.n_short = 0; self.n_green = 0; self.n_gate = 0; self.n_signal = 0
        self.score_sum = 0; self.iv_sum = 0.0; self.delta_sum = 0.0; self.feat_sum = 0.0


def close_candle(st, tf, i):
    c = st.cc[tf][i]; h = st.ch[tf][i]; l = st.cl[tf][i]
    if st.ncl[tf][i] == 0:
        st.ema9[tf][i] = c; st.ema21[tf][i] = c; st.atr[tf][i] = h - l
        st.ag[tf][i] = 0.0; st.al[tf][i] = 0.0
    else:
        st.ema9[tf][i] = st.ema9[tf][i] + A9 * (c - st.ema9[tf][i])
        st.ema21[tf][i] = st.ema21[tf][i] + A21 * (c - st.ema21[tf][i])
        pc = st.pclose[tf][i]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        st.atr[tf][i] = (st.atr[tf][i] * 13.0 + tr) / 14.0
        chg = c - pc
        g = chg if chg > 0 else 0.0
        ls = -chg if chg < 0 else 0.0
        st.ag[tf][i] = (st.ag[tf][i] * 13.0 + g) / 14.0
        st.al[tf][i] = (st.al[tf][i] * 13.0 + ls) / 14.0
    ag = st.ag[tf][i]; al = st.al[tf][i]
    if al == 0.0:
        st.rsi[tf][i] = 100.0 if ag > 0.0 else 50.0
    else:
        st.rsi[tf][i] = 100.0 - 100.0 / (1.0 + ag / al)
    st.pclose[tf][i] = c
    st.ncl[tf][i] += 1


def update(st, i, ts, p, ltq, bid, ask, bq, aq, oi, vol):
    dv = vol - st.last_vol[i]
    st.last_vol[i] = vol
    st.ltp[i] = p
    st.cum_pv[i] += p * dv
    st.cum_v[i] += dv
    st.vwap[i] = st.cum_pv[i] / st.cum_v[i] if st.cum_v[i] > 0 else p
    st.bid[i] = bid; st.ask[i] = ask; st.bq[i] = bq; st.aq[i] = aq; st.oi[i] = oi
    if st.oi_open[i] < 0:
        st.oi_open[i] = oi
    for tf in (0, 1, 2):
        b = ts // TF_NS[tf]
        cb = st.cb[tf]
        if b != cb[i]:
            if cb[i] >= 0:
                close_candle(st, tf, i)
            cb[i] = b
            st.co[tf][i] = p; st.ch[tf][i] = p; st.cl[tf][i] = p; st.cc[tf][i] = p; st.cv[tf][i] = dv
        else:
            if p > st.ch[tf][i]: st.ch[tf][i] = p
            if p < st.cl[tf][i]: st.cl[tf][i] = p
            st.cc[tf][i] = p
            st.cv[tf][i] += dv


def make_update_hist(st):
    """GC test: naive bot jaisa poore din ki tick history list mein rakhna (objects badhte rehte hain)."""
    st.hist = [[] for _ in range(N_INST)]
    def update_hist(st, i, ts, p, ltq, bid, ask, bq, aq, oi, vol):
        update(st, i, ts, p, ltq, bid, ask, bq, aq, oi, vol)
        st.hist[i].append([ts, p, vol])           # list = GC-tracked object
    return update_hist


def evaluate(st, meta, t_ns):
    n = st.n_evals
    slot = n % RING
    st.ring_p[slot] = st.ltp[:]            # 1-second snapshot
    st.ring_v[slot] = st.last_vol[:]
    p30 = st.ring_p[max(n - 30, 0) % RING]; p300 = st.ring_p[max(n - 300, 0) % RING]
    v30 = st.ring_v[max(n - 30, 0) % RING]; v300 = st.ring_v[max(n - 300, 0) % RING]
    ltp = st.ltp
    for ix in range(3):
        S = ltp[ix]
        if S <= 0.0:
            continue
        base = 6 + ix * 164
        up = 0; oi_ce = [0, 0]; oi_pe = [0, 0]
        for o in range(base, base + 164):
            if ltp[o] > p30[o]:
                up += 1
            e = (o - base) // 82
            if (o - base) % 2 == 0:
                oi_ce[e] += st.oi[o]
            else:
                oi_pe[e] += st.oi[o]
        breadth = up / 164
        pcr = [oi_pe[0] / (oi_ce[0] + 1), oi_pe[1] / (oi_ce[1] + 1)]
        spot_mom = (st.ema9[0][ix] - st.ema21[0][ix]) / S
        # 30s % change for every option of this index (neighbour check ke liye)
        ch30 = [((ltp[o] - p30[o]) / p30[o]) if p30[o] > 0.0 else 0.0 for o in range(base, base + 164)]
        for e in range(2):
            for k in range(41):
                for t in range(2):
                    o = base + e * 82 + k * 2 + t
                    p = ltp[o]
                    if p <= 0.0:
                        continue
                    K = meta[o][5]
                    T = (meta[o][6] - t_ns) / YEAR_NS
                    sq = math.sqrt(T)
                    disc = K * math.exp(-R * T)
                    lnsk = math.log(S / K)
                    sig = 0.20
                    for _ in range(3):           # IV: 3 Newton steps
                        d1 = (lnsk + (R + 0.5 * sig * sig) * T) / (sig * sq)
                        d2 = d1 - sig * sq
                        if t == 0:
                            price = S * ncdf(d1) - disc * ncdf(d2)
                        else:
                            price = disc * ncdf(-d2) - S * ncdf(-d1)
                        vega = S * math.exp(-0.5 * d1 * d1) * INV_SQRT_2PI * sq
                        if vega < 1e-8:
                            break
                        sig = sig - (price - p) / vega
                        if sig < 0.01: sig = 0.01
                        if sig > 3.0: sig = 3.0
                    d1 = (lnsk + (R + 0.5 * sig * sig) * T) / (sig * sq)
                    delta = ncdf(d1) if t == 0 else ncdf(d1) - 1.0
                    st.iv_sum += sig
                    st.delta_sum += delta
                    if t == 0:
                        ok = 0.25 <= delta <= 0.65
                    else:
                        ok = -0.65 <= delta <= -0.25
                    if not ok or p < 2.0:
                        continue
                    # ---- shortlisted: 16 features ----
                    st.n_short += 1
                    f = [0.0] * 16
                    f[0] = (abs(p - p30[o]) / 30) / (abs(p - p300[o]) / 300 + 0.01)
                    f[1] = ((st.last_vol[o] - v30[o]) / 30) / ((st.last_vol[o] - v300[o]) / 300 + 1)
                    s = 0.0; cnt = 0
                    for d in (-2, -1, 1, 2):
                        kk = k + d
                        if 0 <= kk <= 40:
                            s += ch30[e * 82 + kk * 2 + t]; cnt += 1
                    f[2] = ch30[e * 82 + k * 2 + t] - s / cnt
                    f[3] = (st.oi[o] - st.oi_open[o]) / (st.oi_open[o] + 1)
                    f[4] = pcr[e]
                    f[5] = breadth
                    f[6] = (st.ema9[0][o] - st.ema21[0][o]) / p
                    f[7] = (st.ema9[1][o] - st.ema21[1][o]) / p
                    f[8] = (st.ema9[2][o] - st.ema21[2][o]) / p
                    f[9] = st.rsi[0][o]
                    f[10] = st.rsi[1][o]
                    f[11] = st.atr[0][o] / p
                    f[12] = (p - st.vwap[o]) / st.vwap[o]
                    f[13] = (st.ask[o] - st.bid[o]) / p
                    f[14] = (st.bq[o] - st.aq[o]) / (st.bq[o] + st.aq[o] + 1)
                    f[15] = spot_mom if t == 0 else -spot_mom
                    fs = 0.0
                    for x in f:
                        fs += x
                    st.feat_sum += fs
                    # ---- 50 checks ----
                    score = 0; greens = 0; gate_ok = True
                    for fi, th, dr, w, gate in CHECKS:
                        green = (f[fi] > th) if dr else (f[fi] < th)
                        if green:
                            score += w; greens += 1
                        elif gate:
                            gate_ok = False
                    st.n_green += greens
                    if gate_ok:
                        st.n_gate += 1
                        st.score_sum += score
                        if score >= MIN_SCORE:
                            st.n_signal += 1
    st.n_evals += 1


def final_sum(st):
    s = 0.0
    for tf in range(3):
        for i in range(N_INST):
            s += st.ema9[tf][i] + st.ema21[tf][i] + st.rsi[tf][i] + st.atr[tf][i]
    for i in range(N_INST):
        s += st.vwap[i]
    return s


def checksum(st):
    return {'n_evals': st.n_evals, 'n_short': st.n_short, 'n_green': st.n_green, 'n_gate': st.n_gate,
            'n_signal': st.n_signal, 'score_sum': st.score_sum, 'iv_sum': st.iv_sum,
            'delta_sum': st.delta_sum, 'feat_sum': st.feat_sum, 'final_sum': final_sum(st)}


def load_ticks(data, fmt):
    if fmt == 'bin':
        return open(os.path.join(data, 'ticks.bin'), 'rb').read()
    with open(os.path.join(data, 'ticks.ndjson'), 'rb') as f:
        return f.read().split(b'\n')[:-1]


def run(args, evaluate_fn=evaluate, label='py_plain'):
    meta = load_meta(os.path.join(args.data, 'meta.bin'))
    st = State()
    raw = load_ticks(args.data, args.format)
    n_ticks = len(raw) // 62 if args.format == 'bin' else len(raw)
    tick_ns = array.array('Q', bytes(8 * n_ticks))
    eval_ns = array.array('Q'); eval_at = array.array('Q')
    gc_info = {'collections': [0, 0, 0], 'max_pause_ns': 0}
    if args.gc == 'freeze':
        gc.collect(); gc.freeze(); gc.disable()
    else:
        t_gc = [0]
        def cb(phase, info):
            if phase == 'start':
                t_gc[0] = time.perf_counter_ns()
            else:
                d = time.perf_counter_ns() - t_gc[0]
                gc_info['collections'][info['generation']] += 1
                if d > gc_info['max_pause_ns']: gc_info['max_pause_ns'] = d
        gc.callbacks.append(cb)
    if args.format == 'json':
        loads = json.loads
        if args.json_lib == 'orjson':
            import orjson
            loads = orjson.loads
    unpack = TICK.unpack_from
    now = time.perf_counter_ns
    cur_sec = -1
    upd = make_update_hist(st) if args.keep_history else update
    wall0 = now()
    for n in range(n_ticks):
        t0 = now()
        if args.format == 'bin':
            i, ts, p, ltq, bid, ask, bq, aq, oi, vol = unpack(raw, n * 62)
        else:
            d = loads(raw[n])
            i = d['i']; ts = d['t']; p = d['ltp']; ltq = d['ltq']; bid = d['b']; ask = d['a']
            bq = d['bq']; aq = d['aq']; oi = d['oi']; vol = d['v']
        sec = ts // 1_000_000_000
        if sec != cur_sec:
            if cur_sec >= 0:
                e0 = now()
                evaluate_fn(st, meta, (cur_sec + 1) * 1_000_000_000)
                e1 = now()
                eval_ns.append(e1 - e0); eval_at.append(n)
                t0 += e1 - e0
            cur_sec = sec
        upd(st, i, ts, p, ltq, bid, ask, bq, aq, oi, vol)
        tick_ns[n] = now() - t0
    wall = (now() - wall0) / 1e9
    if args.gc == 'freeze':
        gc.enable(); gc.unfreeze()
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, 'tick_ns.u64'), 'wb') as f: tick_ns.tofile(f)
    with open(os.path.join(args.out, 'eval_ns.u64'), 'wb') as f: eval_ns.tofile(f)
    with open(os.path.join(args.out, 'eval_at.u64'), 'wb') as f: eval_at.tofile(f)
    res = {'impl': label, 'format': args.format, 'gc': args.gc, 'keep_history': args.keep_history, 'n_ticks': n_ticks, 'wall_s': wall,
           'checksum': checksum(st)}
    if args.gc != 'freeze': res['gc'] = {'mode': 'on', **gc_info}
    with open(os.path.join(args.out, 'result.json'), 'w') as f: json.dump(res, f, indent=1)
    print(json.dumps(res))


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data'); ap.add_argument('--out', default='out/py_plain')
    ap.add_argument('--format', default='bin', choices=['bin', 'json'])
    ap.add_argument('--json-lib', default='json', choices=['json', 'orjson'])
    ap.add_argument('--gc', default='on', choices=['on', 'freeze'])
    ap.add_argument('--keep-history', action='store_true')
    ap.add_argument('--engine', default='numpy', choices=['numpy', 'numba'])   # sirf py_numpy.py ke liye
    return ap.parse_args(argv)


if __name__ == '__main__':
    run(parse_args())
