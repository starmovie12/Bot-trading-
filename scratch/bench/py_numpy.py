#!/usr/bin/env python3
"""Python tick path (same as py_plain) + vectorised NumPy (ya Numba) evaluation.
Throw-away benchmark, production code nahi.

Usage: python3 py_numpy.py --data data --out out/py_numpy [--engine numpy|numba] [--gc on|freeze]
Har 1-second eval mein list state -> numpy array conversion bhi time mein shaamil hai.
"""
import math
import numpy as np
import py_plain as P

OPT = np.arange(6, P.N_INST)
IDX_O = (OPT - 6) // 164
E_O = ((OPT - 6) % 164) // 82
K_O = ((OPT - 6) % 82) // 2
T_O = (OPT - 6) % 2
CE = T_O == 0
FI = np.array([c[0] for c in P.CHECKS]); TH = np.array([c[1] for c in P.CHECKS])
DIRS = np.array([c[2] for c in P.CHECKS], bool); W = np.array([c[3] for c in P.CHECKS], np.int64)
GATES = np.array([c[4] for c in P.CHECKS], bool)
CNT = np.array([sum(1 for d in (-2, -1, 1, 2) if 0 <= k + d <= 40) for k in range(41)], float)


def ncdf(x):
    z = np.abs(x)
    k = 1.0 / (1.0 + 0.2316419 * z)
    poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))))
    n = 1.0 - np.exp(-0.5 * z * z) * P.INV_SQRT_2PI * poly
    return np.where(x >= 0, n, 1.0 - n)


class Ctx:
    def __init__(self, meta):
        self.K = np.array([meta[o][5] for o in OPT])
        self.EXP = np.array([meta[o][6] for o in OPT], np.int64)
        self.ring_p = np.zeros((P.RING, P.N_INST)); self.ring_v = np.zeros((P.RING, P.N_INST), np.int64)


def snapshot(st):
    """List state -> numpy arrays (yeh cost bhi eval ka hissa hai)."""
    a = np.array
    return dict(L=a(st.ltp), V=a(st.last_vol, np.int64), OI=a(st.oi, np.int64), OI0=a(st.oi_open, np.int64),
                VWAP=a(st.vwap), BID=a(st.bid), ASK=a(st.ask), BQ=a(st.bq, np.int64), AQ=a(st.aq, np.int64),
                EMA9=a(st.ema9), EMA21=a(st.ema21), RSI=a(st.rsi), ATR0=a(st.atr[0]))


def eval_numpy(st, ctx, t_ns):
    n = st.n_evals
    s = snapshot(st)
    L, V = s['L'], s['V']
    ctx.ring_p[n % P.RING] = L; ctx.ring_v[n % P.RING] = V
    P30 = ctx.ring_p[max(n - 30, 0) % P.RING]; P300 = ctx.ring_p[max(n - 300, 0) % P.RING]
    V30 = ctx.ring_v[max(n - 30, 0) % P.RING]; V300 = ctx.ring_v[max(n - 300, 0) % P.RING]
    p = L[6:]; S = L[IDX_O]
    valid = (p > 0) & (S > 0)
    with np.errstate(all='ignore'):
        T = (ctx.EXP - t_ns).astype(np.float64) / P.YEAR_NS
        sq = np.sqrt(T); disc = ctx.K * np.exp(-P.R * T); lnsk = np.log(S / ctx.K)
        sig = np.full(len(p), 0.20); active = valid.copy()
        for _ in range(3):
            d1 = (lnsk + (P.R + 0.5 * sig * sig) * T) / (sig * sq); d2 = d1 - sig * sq
            price = np.where(CE, S * ncdf(d1) - disc * ncdf(d2), disc * ncdf(-d2) - S * ncdf(-d1))
            vega = S * np.exp(-0.5 * d1 * d1) * P.INV_SQRT_2PI * sq
            active &= vega >= 1e-8
            sig = np.where(active, np.clip(sig - (price - p) / vega, 0.01, 3.0), sig)
        d1 = (lnsk + (P.R + 0.5 * sig * sig) * T) / (sig * sq)
        nd1 = ncdf(d1)
        delta = np.where(CE, nd1, nd1 - 1.0)
    st.iv_sum += float(sig[valid].sum()); st.delta_sum += float(delta[valid].sum())
    short = valid & (p >= 2.0) & np.where(CE, (delta >= 0.25) & (delta <= 0.65), (delta >= -0.65) & (delta <= -0.25))
    # per-index aggregates
    po = P30[6:]
    up = (p > po).reshape(3, 164).sum(1)
    breadth = up / 164
    oi4 = s['OI'][6:].reshape(3, 2, 41, 2).sum(2)          # [ix, e, t]
    pcr = oi4[:, :, 1] / (oi4[:, :, 0] + 1)
    spot_mom = (s['EMA9'][0, :3] - s['EMA21'][0, :3]) / L[:3]
    with np.errstate(all='ignore'):
        ch30 = np.where(po > 0, (p - po) / po, 0.0).reshape(3, 2, 41, 2)
    pad = np.zeros((3, 2, 45, 2)); pad[:, :, 2:43] = ch30
    nb = (pad[:, :, 0:41] + pad[:, :, 1:42] + pad[:, :, 3:44] + pad[:, :, 4:45]) / CNT[None, None, :, None]
    f2_all = (ch30 - nb).reshape(-1)
    sel = np.flatnonzero(short); o = sel + 6
    m = len(sel)
    st.n_short += m
    if m:
        pp = p[sel]
        F = np.empty((m, 16))
        F[:, 0] = (np.abs(pp - P30[o]) / 30) / (np.abs(pp - P300[o]) / 300 + 0.01)
        F[:, 1] = ((V[o] - V30[o]) / 30) / ((V[o] - V300[o]) / 300 + 1)
        F[:, 2] = f2_all[sel]
        F[:, 3] = (s['OI'][o] - s['OI0'][o]) / (s['OI0'][o] + 1)
        F[:, 4] = pcr[IDX_O[sel], E_O[sel]]
        F[:, 5] = breadth[IDX_O[sel]]
        for tf in range(3):
            F[:, 6 + tf] = (s['EMA9'][tf, o] - s['EMA21'][tf, o]) / pp
        F[:, 9] = s['RSI'][0, o]; F[:, 10] = s['RSI'][1, o]
        F[:, 11] = s['ATR0'][o] / pp
        F[:, 12] = (pp - s['VWAP'][o]) / s['VWAP'][o]
        F[:, 13] = (s['ASK'][o] - s['BID'][o]) / pp
        F[:, 14] = (s['BQ'][o] - s['AQ'][o]) / (s['BQ'][o] + s['AQ'][o] + 1)
        F[:, 15] = np.where(CE[sel], spot_mom[IDX_O[sel]], -spot_mom[IDX_O[sel]])
        st.feat_sum += float(F.sum())
        X = F[:, FI]
        G = np.where(DIRS, X > TH, X < TH)                    # m x 50 green matrix
        score = G.astype(np.int64) @ W
        gate_ok = G[:, GATES].all(1)
        st.n_green += int(G.sum())
        st.n_gate += int(gate_ok.sum())
        st.score_sum += int(score[gate_ok].sum())
        st.n_signal += int((gate_ok & (score >= P.MIN_SCORE)).sum())
    st.n_evals += 1


# ---------------- Numba engine: wahi loop logic, compiled ----------------
def make_numba_eval():
    from numba import njit

    @njit(cache=True, fastmath=False)
    def nb_ncdf(x):
        z = abs(x)
        k = 1.0 / (1.0 + 0.2316419 * z)
        poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))))
        nn = 1.0 - math.exp(-0.5 * z * z) * 0.3989422804014327 * poly
        return nn if x >= 0 else 1.0 - nn

    @njit(cache=True, fastmath=False)
    def kernel(n, t_ns, L, V, OI, OI0, VWAP, BID, ASK, BQ, AQ, EMA9, EMA21, RSI, ATR0, ring_p, ring_v,
               K, EXP, FI, TH, DIRS, W, GATES, out_i, out_f):
        RING = ring_p.shape[0]
        ring_p[n % RING, :] = L; ring_v[n % RING, :] = V
        b30 = max(n - 30, 0) % RING; b300 = max(n - 300, 0) % RING
        R = 0.065; YEAR_NS = 365.0 * 86400e9; INV = 0.3989422804014327
        ch30 = np.zeros(164); f = np.zeros(16); pcr = np.zeros(2)
        for ix in range(3):
            S = L[ix]
            if S <= 0.0:
                continue
            base = 6 + ix * 164
            up = 0; oc0 = 0; oc1 = 0; op0 = 0; op1 = 0
            for o in range(base, base + 164):
                if L[o] > ring_p[b30, o]:
                    up += 1
                e = (o - base) // 82
                if (o - base) % 2 == 0:
                    if e == 0: oc0 += OI[o]
                    else: oc1 += OI[o]
                else:
                    if e == 0: op0 += OI[o]
                    else: op1 += OI[o]
                q = ring_p[b30, o]
                ch30[o - base] = (L[o] - q) / q if q > 0.0 else 0.0
            breadth = up / 164
            pcr[0] = op0 / (oc0 + 1); pcr[1] = op1 / (oc1 + 1)
            spot_mom = (EMA9[0, ix] - EMA21[0, ix]) / S
            for e in range(2):
                for k in range(41):
                    for t in range(2):
                        o = base + e * 82 + k * 2 + t
                        p = L[o]
                        if p <= 0.0:
                            continue
                        Kk = K[o - 6]
                        T = (EXP[o - 6] - t_ns) / YEAR_NS
                        sq = math.sqrt(T); disc = Kk * math.exp(-R * T); lnsk = math.log(S / Kk)
                        sig = 0.20
                        for _ in range(3):
                            d1 = (lnsk + (R + 0.5 * sig * sig) * T) / (sig * sq)
                            d2 = d1 - sig * sq
                            if t == 0:
                                price = S * nb_ncdf(d1) - disc * nb_ncdf(d2)
                            else:
                                price = disc * nb_ncdf(-d2) - S * nb_ncdf(-d1)
                            vega = S * math.exp(-0.5 * d1 * d1) * INV * sq
                            if vega < 1e-8:
                                break
                            sig = sig - (price - p) / vega
                            if sig < 0.01: sig = 0.01
                            if sig > 3.0: sig = 3.0
                        d1 = (lnsk + (R + 0.5 * sig * sig) * T) / (sig * sq)
                        delta = nb_ncdf(d1) if t == 0 else nb_ncdf(d1) - 1.0
                        out_f[0] += sig; out_f[1] += delta
                        if t == 0:
                            ok = delta >= 0.25 and delta <= 0.65
                        else:
                            ok = delta >= -0.65 and delta <= -0.25
                        if (not ok) or p < 2.0:
                            continue
                        out_i[0] += 1
                        f[0] = (abs(p - ring_p[b30, o]) / 30) / (abs(p - ring_p[b300, o]) / 300 + 0.01)
                        f[1] = ((V[o] - ring_v[b30, o]) / 30) / ((V[o] - ring_v[b300, o]) / 300 + 1)
                        s = 0.0; cnt = 0
                        for d in (-2, -1, 1, 2):
                            kk = k + d
                            if kk >= 0 and kk <= 40:
                                s += ch30[e * 82 + kk * 2 + t]; cnt += 1
                        f[2] = ch30[e * 82 + k * 2 + t] - s / cnt
                        f[3] = (OI[o] - OI0[o]) / (OI0[o] + 1)
                        f[4] = pcr[e]; f[5] = breadth
                        f[6] = (EMA9[0, o] - EMA21[0, o]) / p
                        f[7] = (EMA9[1, o] - EMA21[1, o]) / p
                        f[8] = (EMA9[2, o] - EMA21[2, o]) / p
                        f[9] = RSI[0, o]; f[10] = RSI[1, o]
                        f[11] = ATR0[o] / p
                        f[12] = (p - VWAP[o]) / VWAP[o]
                        f[13] = (ASK[o] - BID[o]) / p
                        f[14] = (BQ[o] - AQ[o]) / (BQ[o] + AQ[o] + 1)
                        f[15] = spot_mom if t == 0 else -spot_mom
                        fs = 0.0
                        for x in range(16):
                            fs += f[x]
                        out_f[2] += fs
                        score = 0; greens = 0; gate_ok = True
                        for j in range(50):
                            v = f[FI[j]]
                            green = (v > TH[j]) if DIRS[j] else (v < TH[j])
                            if green:
                                score += W[j]; greens += 1
                            elif GATES[j]:
                                gate_ok = False
                        out_i[1] += greens
                        if gate_ok:
                            out_i[2] += 1; out_i[3] += score
                            if score >= 70:
                                out_i[4] += 1

    def eval_numba(st, ctx, t_ns):
        s = snapshot(st)
        out_i = np.zeros(5, np.int64); out_f = np.zeros(3)
        kernel(st.n_evals, t_ns, s['L'], s['V'], s['OI'], s['OI0'], s['VWAP'], s['BID'], s['ASK'], s['BQ'],
               s['AQ'], s['EMA9'], s['EMA21'], s['RSI'], s['ATR0'], ctx.ring_p, ctx.ring_v, ctx.K, ctx.EXP,
               FI, TH, DIRS, W, GATES, out_i, out_f)
        st.n_short += int(out_i[0]); st.n_green += int(out_i[1]); st.n_gate += int(out_i[2])
        st.score_sum += int(out_i[3]); st.n_signal += int(out_i[4])
        st.iv_sum += float(out_f[0]); st.delta_sum += float(out_f[1]); st.feat_sum += float(out_f[2])
        st.n_evals += 1
    return eval_numba


def main():
    args = P.parse_args()
    meta = P.load_meta(f'{args.data}/meta.bin')
    ctx = Ctx(meta)
    if args.engine == 'numba':
        fn = make_numba_eval()
        # warm-up (JIT compile) ek dummy state par, timing se bahar
        dummy = P.State(); dummy.ltp[0] = 1.0
        fn(dummy, Ctx(meta), 0)
        label = 'py_numba'
    else:
        fn = eval_numpy
        label = 'py_numpy'
    P.run(args, evaluate_fn=lambda st, meta_, t_ns: fn(st, ctx, t_ns), label=label)


if __name__ == '__main__':
    main()
