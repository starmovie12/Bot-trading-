#!/usr/bin/env python3
"""Results analyse karta hai: har variant ke 3 runs -> percentiles -> median of 3.
Throw-away benchmark, production code nahi.

Usage: python3 analyze.py out [data]
Reads out/<variant>/run<k>/{tick_ns,eval_ns,eval_at}.u64 + result.json
Prints markdown tables (stdout) aur out/summary.json likhta hai.
"""
import glob, json, os, sys
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
DATA = sys.argv[2] if len(sys.argv) > 2 else 'data'
INT_KEYS = ['n_evals', 'n_short', 'n_green', 'n_gate', 'n_signal', 'score_sum']
FLT_KEYS = ['iv_sum', 'delta_sum', 'feat_sum', 'final_sum']
PCT = [50, 99, 99.9]

TICK_DT = np.dtype([('id', '<u2'), ('ts', '<u8'), ('ltp', '<f8'), ('ltq', '<u4'), ('bid', '<f8'),
                    ('ask', '<f8'), ('bq', '<u4'), ('aq', '<u4'), ('oi', '<u8'), ('vol', '<u8')])
ts = np.fromfile(os.path.join(DATA, 'ticks.bin'), TICK_DT)['ts'].astype(np.int64)
arr = ts - ts[0]
sec_of_tick = arr // 1_000_000_000


def queue_sim(service):
    """Single-thread bot: tick apne ts par aata hai, pichhla kaam khatam hone tak wait karta hai.
    lag = finish - arrival (ns). Python loop slow hai, isliye numba agar ho."""
    try:
        from numba import njit
        @njit(cache=True)
        def sim(a, s):
            lag = np.empty(len(a), np.int64); fin = 0
            for i in range(len(a)):
                st = a[i] if a[i] > fin else fin
                fin = st + s[i]; lag[i] = fin - a[i]
            return lag
        return sim(arr, service)
    except ImportError:
        lag = np.empty(len(arr), np.int64); fin = 0
        for i in range(len(arr)):
            st = max(arr[i], fin); fin = st + int(service[i]); lag[i] = fin - arr[i]
        return lag


def one_run(d):
    tick = np.fromfile(os.path.join(d, 'tick_ns.u64'), np.uint64).astype(np.int64)
    ev = np.fromfile(os.path.join(d, 'eval_ns.u64'), np.uint64).astype(np.int64)
    at = np.fromfile(os.path.join(d, 'eval_at.u64'), np.uint64).astype(np.int64)
    res = json.load(open(os.path.join(d, 'result.json')))
    service = tick.copy(); service[at] += ev
    lag = queue_sim(service)
    busy = np.bincount(sec_of_tick, weights=service.astype(float))   # ns of work per simulated second
    r = {'tick': list(np.percentile(tick, PCT)) + [tick.max()], 'eval': list(np.percentile(ev, PCT)) + [ev.max()],
         'lag': list(np.percentile(lag, PCT)) + [lag.max()], 'tput': res['n_ticks'] / res['wall_s'],
         'peak_busy': busy.max() / 1e9, 'checksum': res['checksum'], 'gc': res.get('gc')}
    return r


def ok_vs(ref, c):
    for k in INT_KEYS:
        if ref[k] != c[k]:
            return False
    for k in FLT_KEYS:
        if abs(ref[k] - c[k]) > 1e-9 * max(1.0, abs(ref[k])):
            return False
    return True


def fmt_ns(x):
    if x < 1e3: return f'{x:.0f} ns'
    if x < 1e6: return f'{x / 1e3:.1f} µs'
    return f'{x / 1e6:.2f} ms'


def main():
    variants = sorted(os.path.basename(p) for p in glob.glob(os.path.join(OUT, '*')) if os.path.isdir(p))
    variants = [v for v in variants if glob.glob(os.path.join(OUT, v, 'run*'))]
    allres = {}
    for v in variants:
        runs = [one_run(d) for d in sorted(glob.glob(os.path.join(OUT, v, 'run*')))]
        med = {}
        for key in ('tick', 'eval', 'lag'):
            med[key] = [float(np.median([r[key][i] for r in runs])) for i in range(4)]
        med['tput'] = float(np.median([r['tput'] for r in runs]))
        med['peak_busy'] = float(np.median([r['peak_busy'] for r in runs]))
        med['checksum'] = runs[0]['checksum']
        med['checksum_runs_equal'] = all(r['checksum'] == runs[0]['checksum'] for r in runs)
        med['gc'] = [r['gc'] for r in runs]
        med['n_runs'] = len(runs)
        allres[v] = med
    ref_name = 'py_plain_bin_gc-on' if 'py_plain_bin_gc-on' in allres else variants[0]
    ref = allres[ref_name]['checksum']
    print(f'Reference checksum ({ref_name}): {json.dumps(ref)}\n')
    print('| variant | runs | tick p50 | tick p99 | tick p99.9 | tick max | eval p50 | eval p99 | eval p99.9 | eval max | throughput (ticks/s) | checksum OK |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for v, m in allres.items():
        ok = ok_vs(ref, m['checksum']) and m['checksum_runs_equal']
        m['checksum_ok'] = ok
        t, e = m['tick'], m['eval']
        print(f"| {v} | {m['n_runs']} | {fmt_ns(t[0])} | {fmt_ns(t[1])} | {fmt_ns(t[2])} | {fmt_ns(t[3])} | "
              f"{fmt_ns(e[0])} | {fmt_ns(e[1])} | {fmt_ns(e[2])} | {fmt_ns(e[3])} | {m['tput']:,.0f} | {'haan' if ok else 'NAHI'} |")
    print('\nQueue simulation (tick apne timestamp par aata hai; single thread; lag = processing khatam - arrival):\n')
    print('| variant | lag p50 | lag p99 | lag p99.9 | lag max | sabse busy second (CPU busy fraction) |')
    print('|---|---|---|---|---|---|')
    for v, m in allres.items():
        l = m['lag']
        print(f"| {v} | {fmt_ns(l[0])} | {fmt_ns(l[1])} | {fmt_ns(l[2])} | {fmt_ns(l[3])} | {m['peak_busy'] * 100:.1f}% |")
    print('\nGC info (sirf gc-on Python runs):')
    for v, m in allres.items():
        if m['gc'] and isinstance(m['gc'][0], dict):
            print(f"- {v}: " + '; '.join(f"collections={g['collections']} max_pause={fmt_ns(g['max_pause_ns'])}" for g in m['gc']))
    json.dump(allres, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()
