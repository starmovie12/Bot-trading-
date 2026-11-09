// Rust port of py_plain.py (same logic, same checksum). Throw-away benchmark, production code nahi.
// Usage: tickbench <data_dir> <out_dir> [bin|json]
use std::fs;
use std::io::Write;
use std::time::Instant;

const N: usize = 498;
const TF_NS: [i64; 3] = [60_000_000_000, 180_000_000_000, 900_000_000_000];
const RING: usize = 301;
const R: f64 = 0.065;
const YEAR_NS: f64 = 365.0 * 86400e9;
const INV: f64 = 0.3989422804014327;
const MIN_SCORE: i64 = 70;
const BASE: [f64; 16] = [1.0, 1.5, 0.0, 0.0, 0.8, 0.5, 0.0, 0.0, 0.0, 50.0, 50.0, 0.002, 0.0, 0.05, 0.0, 0.0];
const STEPS: [f64; 16] = [0.25, 0.25, 0.002, 0.01, 0.1, 0.05, 0.0005, 0.0005, 0.0005, 5.0, 5.0, 0.001, 0.001, 0.02, 0.1, 0.0002];
const DIR: [bool; 16] = [true, true, true, true, true, true, true, true, true, true, true, true, true, false, true, true];

#[derive(Clone, Copy, Default)]
struct Tick { id: usize, ts: i64, ltp: f64, _ltq: u32, bid: f64, ask: f64, bq: i64, aq: i64, oi: i64, vol: i64 }

#[derive(serde::Deserialize)]
struct JTick { i: u16, t: u64, ltp: f64, ltq: u32, b: f64, a: f64, bq: u32, aq: u32, oi: u64, v: u64 }

struct Meta { strike: f64, exp_ns: i64 }

#[derive(Clone, Copy, Default)]
struct Candle { bucket: i64, o: f64, h: f64, l: f64, c: f64, v: i64, ncl: i64, pclose: f64,
                ema9: f64, ema21: f64, atr: f64, ag: f64, al: f64, rsi: f64 }

struct State {
    ltp: Vec<f64>, last_vol: Vec<i64>, cum_pv: Vec<f64>, cum_v: Vec<i64>, vwap: Vec<f64>,
    bid: Vec<f64>, ask: Vec<f64>, bq: Vec<i64>, aq: Vec<i64>, oi: Vec<i64>, oi_open: Vec<i64>,
    cdl: Vec<[Candle; 3]>,
    ring_p: Vec<f64>, ring_v: Vec<i64>,     // RING x N flat
    n_evals: i64, n_short: i64, n_green: i64, n_gate: i64, n_signal: i64, score_sum: i64,
    iv_sum: f64, delta_sum: f64, feat_sum: f64,
}

#[inline]
fn ncdf(x: f64) -> f64 {
    let z = x.abs();
    let k = 1.0 / (1.0 + 0.2316419 * z);
    let poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))));
    let n = 1.0 - (-0.5 * z * z).exp() * INV * poly;
    if x >= 0.0 { n } else { 1.0 - n }
}

fn close_candle(c: &mut Candle) {
    let (cl, h, l) = (c.c, c.h, c.l);
    if c.ncl == 0 {
        c.ema9 = cl; c.ema21 = cl; c.atr = h - l; c.ag = 0.0; c.al = 0.0;
    } else {
        c.ema9 = c.ema9 + (2.0 / 10.0) * (cl - c.ema9);
        c.ema21 = c.ema21 + (2.0 / 22.0) * (cl - c.ema21);
        let pc = c.pclose;
        let tr = (h - l).max((h - pc).abs()).max((l - pc).abs());
        c.atr = (c.atr * 13.0 + tr) / 14.0;
        let chg = cl - pc;
        let g = if chg > 0.0 { chg } else { 0.0 };
        let ls = if chg < 0.0 { -chg } else { 0.0 };
        c.ag = (c.ag * 13.0 + g) / 14.0;
        c.al = (c.al * 13.0 + ls) / 14.0;
    }
    c.rsi = if c.al == 0.0 { if c.ag > 0.0 { 100.0 } else { 50.0 } } else { 100.0 - 100.0 / (1.0 + c.ag / c.al) };
    c.pclose = cl;
    c.ncl += 1;
}

fn update(st: &mut State, t: &Tick) {
    let i = t.id;
    let dv = t.vol - st.last_vol[i];
    st.last_vol[i] = t.vol;
    let p = t.ltp;
    st.ltp[i] = p;
    st.cum_pv[i] += p * dv as f64;
    st.cum_v[i] += dv;
    st.vwap[i] = if st.cum_v[i] > 0 { st.cum_pv[i] / st.cum_v[i] as f64 } else { p };
    st.bid[i] = t.bid; st.ask[i] = t.ask; st.bq[i] = t.bq; st.aq[i] = t.aq; st.oi[i] = t.oi;
    if st.oi_open[i] < 0 { st.oi_open[i] = t.oi; }
    for tf in 0..3 {
        let b = t.ts / TF_NS[tf];
        let c = &mut st.cdl[i][tf];
        if b != c.bucket {
            if c.bucket >= 0 { close_candle(c); }
            c.bucket = b; c.o = p; c.h = p; c.l = p; c.c = p; c.v = dv;
        } else {
            if p > c.h { c.h = p; }
            if p < c.l { c.l = p; }
            c.c = p; c.v += dv;
        }
    }
}

fn evaluate(st: &mut State, meta: &[Meta], t_ns: i64) {
    let n = st.n_evals as usize;
    let slot = n % RING;
    st.ring_p[slot * N..(slot + 1) * N].copy_from_slice(&st.ltp);
    st.ring_v[slot * N..(slot + 1) * N].copy_from_slice(&st.last_vol);
    let b30 = (if n >= 30 { n - 30 } else { 0 }) % RING;
    let b300 = (if n >= 300 { n - 300 } else { 0 }) % RING;
    let mut checks = [(0usize, 0.0f64, true, 0i64, false); 50];
    for j in 0..50 {
        let fi = j % 16;
        checks[j] = (fi, BASE[fi] + STEPS[fi] * (j / 16) as f64, DIR[fi], 1 + (j % 4) as i64, fi == 13);
    }
    let mut ch30 = [0.0f64; 164];
    for ix in 0..3 {
        let s = st.ltp[ix];
        if s <= 0.0 { continue; }
        let base = 6 + ix * 164;
        let mut up = 0i64; let mut oce = [0i64; 2]; let mut ope = [0i64; 2];
        for o in base..base + 164 {
            let p30 = st.ring_p[b30 * N + o];
            if st.ltp[o] > p30 { up += 1; }
            let e = (o - base) / 82;
            if (o - base) % 2 == 0 { oce[e] += st.oi[o]; } else { ope[e] += st.oi[o]; }
            ch30[o - base] = if p30 > 0.0 { (st.ltp[o] - p30) / p30 } else { 0.0 };
        }
        let breadth = up as f64 / 164.0;
        let pcr = [ope[0] as f64 / (oce[0] + 1) as f64, ope[1] as f64 / (oce[1] + 1) as f64];
        let spot_mom = (st.cdl[ix][0].ema9 - st.cdl[ix][0].ema21) / s;
        for e in 0..2 { for k in 0..41usize { for t in 0..2 {
            let o = base + e * 82 + k * 2 + t;
            let p = st.ltp[o];
            if p <= 0.0 { continue; }
            let kk_ = meta[o].strike;
            let tt = (meta[o].exp_ns - t_ns) as f64 / YEAR_NS;
            let sq = tt.sqrt();
            let disc = kk_ * (-R * tt).exp();
            let lnsk = (s / kk_).ln();
            let mut sig = 0.20;
            for _ in 0..3 {
                let d1 = (lnsk + (R + 0.5 * sig * sig) * tt) / (sig * sq);
                let d2 = d1 - sig * sq;
                let price = if t == 0 { s * ncdf(d1) - disc * ncdf(d2) } else { disc * ncdf(-d2) - s * ncdf(-d1) };
                let vega = s * (-0.5 * d1 * d1).exp() * INV * sq;
                if vega < 1e-8 { break; }
                sig = sig - (price - p) / vega;
                if sig < 0.01 { sig = 0.01; }
                if sig > 3.0 { sig = 3.0; }
            }
            let d1 = (lnsk + (R + 0.5 * sig * sig) * tt) / (sig * sq);
            let delta = if t == 0 { ncdf(d1) } else { ncdf(d1) - 1.0 };
            st.iv_sum += sig; st.delta_sum += delta;
            let ok = if t == 0 { delta >= 0.25 && delta <= 0.65 } else { delta >= -0.65 && delta <= -0.25 };
            if !ok || p < 2.0 { continue; }
            st.n_short += 1;
            let mut f = [0.0f64; 16];
            let p30 = st.ring_p[b30 * N + o]; let p300 = st.ring_p[b300 * N + o];
            f[0] = ((p - p30).abs() / 30.0) / ((p - p300).abs() / 300.0 + 0.01);
            let v = st.last_vol[o];
            f[1] = ((v - st.ring_v[b30 * N + o]) as f64 / 30.0) / ((v - st.ring_v[b300 * N + o]) as f64 / 300.0 + 1.0);
            let mut sm = 0.0; let mut cnt = 0i64;
            for d in [-2i64, -1, 1, 2] {
                let kk = k as i64 + d;
                if kk >= 0 && kk <= 40 { sm += ch30[e * 82 + kk as usize * 2 + t]; cnt += 1; }
            }
            f[2] = ch30[e * 82 + k * 2 + t] - sm / cnt as f64;
            f[3] = (st.oi[o] - st.oi_open[o]) as f64 / (st.oi_open[o] + 1) as f64;
            f[4] = pcr[e]; f[5] = breadth;
            for tf in 0..3 { f[6 + tf] = (st.cdl[o][tf].ema9 - st.cdl[o][tf].ema21) / p; }
            f[9] = st.cdl[o][0].rsi; f[10] = st.cdl[o][1].rsi;
            f[11] = st.cdl[o][0].atr / p;
            f[12] = (p - st.vwap[o]) / st.vwap[o];
            f[13] = (st.ask[o] - st.bid[o]) / p;
            f[14] = (st.bq[o] - st.aq[o]) as f64 / (st.bq[o] + st.aq[o] + 1) as f64;
            f[15] = if t == 0 { spot_mom } else { -spot_mom };
            let mut fs = 0.0; for x in f.iter() { fs += *x; }
            st.feat_sum += fs;
            let (mut score, mut greens, mut gate_ok) = (0i64, 0i64, true);
            for &(fi, th, dr, w, gate) in checks.iter() {
                let green = if dr { f[fi] > th } else { f[fi] < th };
                if green { score += w; greens += 1; } else if gate { gate_ok = false; }
            }
            st.n_green += greens;
            if gate_ok { st.n_gate += 1; st.score_sum += score; if score >= MIN_SCORE { st.n_signal += 1; } }
        }}}
    }
    st.n_evals += 1;
}

fn rd<const K: usize>(b: &[u8], o: usize) -> [u8; K] { b[o..o + K].try_into().unwrap() }

fn decode_bin(b: &[u8], o: usize) -> Tick {
    Tick { id: u16::from_le_bytes(rd(b, o)) as usize, ts: u64::from_le_bytes(rd(b, o + 2)) as i64,
           ltp: f64::from_le_bytes(rd(b, o + 10)), _ltq: u32::from_le_bytes(rd(b, o + 18)),
           bid: f64::from_le_bytes(rd(b, o + 22)), ask: f64::from_le_bytes(rd(b, o + 30)),
           bq: u32::from_le_bytes(rd(b, o + 38)) as i64, aq: u32::from_le_bytes(rd(b, o + 42)) as i64,
           oi: u64::from_le_bytes(rd(b, o + 46)) as i64, vol: u64::from_le_bytes(rd(b, o + 54)) as i64 }
}

fn decode_json(line: &[u8]) -> Tick {
    let j: JTick = serde_json::from_slice(line).unwrap();
    Tick { id: j.i as usize, ts: j.t as i64, ltp: j.ltp, _ltq: j.ltq, bid: j.b, ask: j.a, bq: j.bq as i64,
           aq: j.aq as i64, oi: j.oi as i64, vol: j.v as i64 }
}

fn write_u64(path: String, v: &[u64]) {
    let mut f = fs::File::create(path).unwrap();
    let bytes: Vec<u8> = v.iter().flat_map(|x| x.to_le_bytes()).collect();
    f.write_all(&bytes).unwrap();
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let (data, out) = (&a[1], &a[2]);
    let fmt = if a.len() > 3 { a[3].as_str() } else { "bin" };
    let mb = fs::read(format!("{data}/meta.bin")).unwrap();
    let meta: Vec<Meta> = (0..N).map(|o| Meta { strike: f64::from_le_bytes(rd(&mb, o * 24 + 8)),
        exp_ns: u64::from_le_bytes(rd(&mb, o * 24 + 16)) as i64 }).collect();
    let raw_bin; let raw_json; let lines: Vec<&[u8]>;
    let n_ticks;
    if fmt == "bin" {
        raw_bin = fs::read(format!("{data}/ticks.bin")).unwrap(); n_ticks = raw_bin.len() / 62; lines = vec![];
    } else {
        raw_bin = vec![];
        raw_json = fs::read(format!("{data}/ticks.ndjson")).unwrap();
        lines = raw_json.split(|c| *c == b'\n').filter(|l| !l.is_empty()).collect();
        n_ticks = lines.len();
    }
    let mut st = State {
        ltp: vec![0.0; N], last_vol: vec![0; N], cum_pv: vec![0.0; N], cum_v: vec![0; N], vwap: vec![0.0; N],
        bid: vec![0.0; N], ask: vec![0.0; N], bq: vec![0; N], aq: vec![0; N], oi: vec![0; N], oi_open: vec![-1; N],
        cdl: vec![[Candle { bucket: -1, rsi: 50.0, ..Default::default() }; 3]; N],
        ring_p: vec![0.0; RING * N], ring_v: vec![0; RING * N],
        n_evals: 0, n_short: 0, n_green: 0, n_gate: 0, n_signal: 0, score_sum: 0,
        iv_sum: 0.0, delta_sum: 0.0, feat_sum: 0.0,
    };
    let mut tick_ns = vec![0u64; n_ticks];
    let mut eval_ns: Vec<u64> = Vec::new(); let mut eval_at: Vec<u64> = Vec::new();
    let mut cur_sec: i64 = -1;
    let origin = Instant::now();
    let now = || origin.elapsed().as_nanos() as u64;
    let wall0 = now();
    for n in 0..n_ticks {
        let mut t0 = now();
        let t = if fmt == "bin" { decode_bin(&raw_bin, n * 62) } else { decode_json(lines[n]) };
        let sec = t.ts / 1_000_000_000;
        if sec != cur_sec {
            if cur_sec >= 0 {
                let e0 = now();
                evaluate(&mut st, &meta, (cur_sec + 1) * 1_000_000_000);
                let e1 = now();
                eval_ns.push(e1 - e0); eval_at.push(n as u64);
                t0 += e1 - e0;
            }
            cur_sec = sec;
        }
        update(&mut st, &t);
        tick_ns[n] = now() - t0;
    }
    let wall = (now() - wall0) as f64 / 1e9;
    let mut fsum = 0.0;
    for tf in 0..3 { for i in 0..N { let c = &st.cdl[i][tf]; fsum += c.ema9 + c.ema21 + c.rsi + c.atr; } }
    for i in 0..N { fsum += st.vwap[i]; }
    fs::create_dir_all(out).unwrap();
    write_u64(format!("{out}/tick_ns.u64"), &tick_ns);
    write_u64(format!("{out}/eval_ns.u64"), &eval_ns);
    write_u64(format!("{out}/eval_at.u64"), &eval_at);
    let res = format!("{{\"impl\": \"rust\", \"format\": \"{fmt}\", \"n_ticks\": {n_ticks}, \"wall_s\": {wall}, \"checksum\": {{\"n_evals\": {}, \"n_short\": {}, \"n_green\": {}, \"n_gate\": {}, \"n_signal\": {}, \"score_sum\": {}, \"iv_sum\": {:?}, \"delta_sum\": {:?}, \"feat_sum\": {:?}, \"final_sum\": {:?}}}}}",
        st.n_evals, st.n_short, st.n_green, st.n_gate, st.n_signal, st.score_sum, st.iv_sum, st.delta_sum, st.feat_sum, fsum);
    fs::write(format!("{out}/result.json"), &res).unwrap();
    println!("{res}");
}
