// C++ port of py_plain.py (same logic, same checksum). Throw-away benchmark, production code nahi.
// Build: g++ -O2 -march=native -ffp-contract=off -o build/tickbench main.cpp
// Usage: tickbench <data_dir> <out_dir>   (sirf binary format)
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <sys/stat.h>
#include <vector>

static const int N = 498, RING = 301;
static const int64_t TF_NS[3] = {60000000000LL, 180000000000LL, 900000000000LL};
static const double R = 0.065, YEAR_NS = 365.0 * 86400e9, INV = 0.3989422804014327;
static const double BASE[16] = {1.0, 1.5, 0.0, 0.0, 0.8, 0.5, 0.0, 0.0, 0.0, 50.0, 50.0, 0.002, 0.0, 0.05, 0.0, 0.0};
static const double STEPS[16] = {0.25, 0.25, 0.002, 0.01, 0.1, 0.05, 0.0005, 0.0005, 0.0005, 5.0, 5.0, 0.001, 0.001, 0.02, 0.1, 0.0002};
static const bool DIR[16] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1};

struct Tick { int id; int64_t ts; double ltp; uint32_t ltq; double bid, ask; int64_t bq, aq, oi, vol; };
struct Candle { int64_t bucket = -1; double o = 0, h = 0, l = 0, c = 0; int64_t v = 0, ncl = 0;
                double pclose = 0, ema9 = 0, ema21 = 0, atr = 0, ag = 0, al = 0, rsi = 50.0; };
struct Check { int fi; double th; bool dir; int64_t w; bool gate; };

struct State {
  std::vector<double> ltp = std::vector<double>(N), cum_pv = std::vector<double>(N), vwap = std::vector<double>(N),
                      bid = std::vector<double>(N), ask = std::vector<double>(N);
  std::vector<int64_t> last_vol = std::vector<int64_t>(N), cum_v = std::vector<int64_t>(N),
                       bq = std::vector<int64_t>(N), aq = std::vector<int64_t>(N), oi = std::vector<int64_t>(N),
                       oi_open = std::vector<int64_t>(N, -1);
  std::vector<Candle> cdl = std::vector<Candle>(N * 3);   // [inst*3 + tf]
  std::vector<double> ring_p = std::vector<double>(RING * N);
  std::vector<int64_t> ring_v = std::vector<int64_t>(RING * N);
  int64_t n_evals = 0, n_short = 0, n_green = 0, n_gate = 0, n_signal = 0, score_sum = 0;
  double iv_sum = 0, delta_sum = 0, feat_sum = 0;
};

static inline double ncdf(double x) {
  double z = std::fabs(x);
  double k = 1.0 / (1.0 + 0.2316419 * z);
  double poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))));
  double n = 1.0 - std::exp(-0.5 * z * z) * INV * poly;
  return x >= 0 ? n : 1.0 - n;
}

static void close_candle(Candle &c) {
  double cl = c.c, h = c.h, l = c.l;
  if (c.ncl == 0) { c.ema9 = cl; c.ema21 = cl; c.atr = h - l; c.ag = 0; c.al = 0; }
  else {
    c.ema9 = c.ema9 + (2.0 / 10.0) * (cl - c.ema9);
    c.ema21 = c.ema21 + (2.0 / 22.0) * (cl - c.ema21);
    double pc = c.pclose;
    double tr = std::max(std::max(h - l, std::fabs(h - pc)), std::fabs(l - pc));
    c.atr = (c.atr * 13.0 + tr) / 14.0;
    double chg = cl - pc, g = chg > 0 ? chg : 0.0, ls = chg < 0 ? -chg : 0.0;
    c.ag = (c.ag * 13.0 + g) / 14.0;
    c.al = (c.al * 13.0 + ls) / 14.0;
  }
  c.rsi = c.al == 0.0 ? (c.ag > 0.0 ? 100.0 : 50.0) : 100.0 - 100.0 / (1.0 + c.ag / c.al);
  c.pclose = cl; c.ncl += 1;
}

static void update(State &st, const Tick &t) {
  int i = t.id; double p = t.ltp;
  int64_t dv = t.vol - st.last_vol[i];
  st.last_vol[i] = t.vol; st.ltp[i] = p;
  st.cum_pv[i] += p * (double)dv; st.cum_v[i] += dv;
  st.vwap[i] = st.cum_v[i] > 0 ? st.cum_pv[i] / (double)st.cum_v[i] : p;
  st.bid[i] = t.bid; st.ask[i] = t.ask; st.bq[i] = t.bq; st.aq[i] = t.aq; st.oi[i] = t.oi;
  if (st.oi_open[i] < 0) st.oi_open[i] = t.oi;
  for (int tf = 0; tf < 3; tf++) {
    int64_t b = t.ts / TF_NS[tf];
    Candle &c = st.cdl[i * 3 + tf];
    if (b != c.bucket) {
      if (c.bucket >= 0) close_candle(c);
      c.bucket = b; c.o = c.h = c.l = c.c = p; c.v = dv;
    } else {
      if (p > c.h) c.h = p;
      if (p < c.l) c.l = p;
      c.c = p; c.v += dv;
    }
  }
}

static Check CHECKS[50];

static void evaluate(State &st, const std::vector<double> &strike, const std::vector<int64_t> &expns, int64_t t_ns) {
  int64_t n = st.n_evals; int slot = n % RING;
  std::memcpy(&st.ring_p[slot * N], st.ltp.data(), N * sizeof(double));
  std::memcpy(&st.ring_v[slot * N], st.last_vol.data(), N * sizeof(int64_t));
  int b30 = std::max<int64_t>(n - 30, 0) % RING, b300 = std::max<int64_t>(n - 300, 0) % RING;
  double ch30[164];
  for (int ix = 0; ix < 3; ix++) {
    double S = st.ltp[ix];
    if (S <= 0.0) continue;
    int base = 6 + ix * 164;
    int64_t up = 0, oce[2] = {0, 0}, ope[2] = {0, 0};
    for (int o = base; o < base + 164; o++) {
      double p30 = st.ring_p[b30 * N + o];
      if (st.ltp[o] > p30) up++;
      int e = (o - base) / 82;
      if ((o - base) % 2 == 0) oce[e] += st.oi[o]; else ope[e] += st.oi[o];
      ch30[o - base] = p30 > 0.0 ? (st.ltp[o] - p30) / p30 : 0.0;
    }
    double breadth = (double)up / 164.0;
    double pcr[2] = {(double)ope[0] / (double)(oce[0] + 1), (double)ope[1] / (double)(oce[1] + 1)};
    double spot_mom = (st.cdl[ix * 3].ema9 - st.cdl[ix * 3].ema21) / S;
    for (int e = 0; e < 2; e++) for (int k = 0; k < 41; k++) for (int t = 0; t < 2; t++) {
      int o = base + e * 82 + k * 2 + t;
      double p = st.ltp[o];
      if (p <= 0.0) continue;
      double K = strike[o];
      double T = (double)(expns[o] - t_ns) / YEAR_NS;
      double sq = std::sqrt(T), disc = K * std::exp(-R * T), lnsk = std::log(S / K);
      double sig = 0.20;
      for (int it = 0; it < 3; it++) {
        double d1 = (lnsk + (R + 0.5 * sig * sig) * T) / (sig * sq);
        double d2 = d1 - sig * sq;
        double price = t == 0 ? S * ncdf(d1) - disc * ncdf(d2) : disc * ncdf(-d2) - S * ncdf(-d1);
        double vega = S * std::exp(-0.5 * d1 * d1) * INV * sq;
        if (vega < 1e-8) break;
        sig = sig - (price - p) / vega;
        if (sig < 0.01) sig = 0.01;
        if (sig > 3.0) sig = 3.0;
      }
      double d1 = (lnsk + (R + 0.5 * sig * sig) * T) / (sig * sq);
      double delta = t == 0 ? ncdf(d1) : ncdf(d1) - 1.0;
      st.iv_sum += sig; st.delta_sum += delta;
      bool ok = t == 0 ? (delta >= 0.25 && delta <= 0.65) : (delta >= -0.65 && delta <= -0.25);
      if (!ok || p < 2.0) continue;
      st.n_short++;
      double f[16];
      double p30 = st.ring_p[b30 * N + o], p300 = st.ring_p[b300 * N + o];
      f[0] = (std::fabs(p - p30) / 30.0) / (std::fabs(p - p300) / 300.0 + 0.01);
      int64_t v = st.last_vol[o];
      f[1] = ((double)(v - st.ring_v[b30 * N + o]) / 30.0) / ((double)(v - st.ring_v[b300 * N + o]) / 300.0 + 1.0);
      double sm = 0.0; int cnt = 0;
      for (int d : {-2, -1, 1, 2}) { int kk = k + d; if (kk >= 0 && kk <= 40) { sm += ch30[e * 82 + kk * 2 + t]; cnt++; } }
      f[2] = ch30[e * 82 + k * 2 + t] - sm / (double)cnt;
      f[3] = (double)(st.oi[o] - st.oi_open[o]) / (double)(st.oi_open[o] + 1);
      f[4] = pcr[e]; f[5] = breadth;
      for (int tf = 0; tf < 3; tf++) f[6 + tf] = (st.cdl[o * 3 + tf].ema9 - st.cdl[o * 3 + tf].ema21) / p;
      f[9] = st.cdl[o * 3].rsi; f[10] = st.cdl[o * 3 + 1].rsi;
      f[11] = st.cdl[o * 3].atr / p;
      f[12] = (p - st.vwap[o]) / st.vwap[o];
      f[13] = (st.ask[o] - st.bid[o]) / p;
      f[14] = (double)(st.bq[o] - st.aq[o]) / (double)(st.bq[o] + st.aq[o] + 1);
      f[15] = t == 0 ? spot_mom : -spot_mom;
      double fs = 0.0; for (int x = 0; x < 16; x++) fs += f[x];
      st.feat_sum += fs;
      int64_t score = 0, greens = 0; bool gate_ok = true;
      for (const Check &c : CHECKS) {
        bool green = c.dir ? f[c.fi] > c.th : f[c.fi] < c.th;
        if (green) { score += c.w; greens++; } else if (c.gate) gate_ok = false;
      }
      st.n_green += greens;
      if (gate_ok) { st.n_gate++; st.score_sum += score; if (score >= 70) st.n_signal++; }
    }
  }
  st.n_evals++;
}

template <class T> static T rd(const char *p) { T v; std::memcpy(&v, p, sizeof(T)); return v; }

static std::string slurp(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  return std::string((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
}

static void write_u64(const std::string &path, const std::vector<uint64_t> &v) {
  FILE *f = std::fopen(path.c_str(), "wb"); std::fwrite(v.data(), 8, v.size(), f); std::fclose(f);
}

int main(int argc, char **argv) {
  std::string data = argv[1], out = argv[2];
  for (int j = 0; j < 50; j++) { int fi = j % 16; CHECKS[j] = {fi, BASE[fi] + STEPS[fi] * (double)(j / 16), DIR[fi], 1 + j % 4, fi == 13}; }
  std::string mb = slurp(data + "/meta.bin");
  std::vector<double> strike(N); std::vector<int64_t> expns(N);
  for (int o = 0; o < N; o++) { strike[o] = rd<double>(&mb[o * 24 + 8]); expns[o] = (int64_t)rd<uint64_t>(&mb[o * 24 + 16]); }
  std::string raw = slurp(data + "/ticks.bin");
  size_t n_ticks = raw.size() / 62;
  State st;
  std::vector<uint64_t> tick_ns(n_ticks), eval_ns, eval_at;
  int64_t cur_sec = -1;
  auto origin = std::chrono::steady_clock::now();
  auto now = [&]() { return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now() - origin).count(); };
  uint64_t wall0 = now();
  for (size_t n = 0; n < n_ticks; n++) {
    uint64_t t0 = now();
    const char *b = raw.data() + n * 62;
    Tick t{rd<uint16_t>(b), (int64_t)rd<uint64_t>(b + 2), rd<double>(b + 10), rd<uint32_t>(b + 18), rd<double>(b + 22),
           rd<double>(b + 30), rd<uint32_t>(b + 38), rd<uint32_t>(b + 42), (int64_t)rd<uint64_t>(b + 46), (int64_t)rd<uint64_t>(b + 54)};
    int64_t sec = t.ts / 1000000000LL;
    if (sec != cur_sec) {
      if (cur_sec >= 0) {
        uint64_t e0 = now();
        evaluate(st, strike, expns, (cur_sec + 1) * 1000000000LL);
        uint64_t e1 = now();
        eval_ns.push_back(e1 - e0); eval_at.push_back(n); t0 += e1 - e0;
      }
      cur_sec = sec;
    }
    update(st, t);
    tick_ns[n] = now() - t0;
  }
  double wall = (now() - wall0) / 1e9;
  double fsum = 0.0;
  for (int tf = 0; tf < 3; tf++) for (int i = 0; i < N; i++) { Candle &c = st.cdl[i * 3 + tf]; fsum += c.ema9 + c.ema21 + c.rsi + c.atr; }
  for (int i = 0; i < N; i++) fsum += st.vwap[i];
  mkdir(out.c_str(), 0755);
  write_u64(out + "/tick_ns.u64", tick_ns); write_u64(out + "/eval_ns.u64", eval_ns); write_u64(out + "/eval_at.u64", eval_at);
  char buf[1024];
  std::snprintf(buf, sizeof buf, "{\"impl\": \"cpp\", \"format\": \"bin\", \"n_ticks\": %zu, \"wall_s\": %.6f, \"checksum\": {\"n_evals\": %lld, \"n_short\": %lld, \"n_green\": %lld, \"n_gate\": %lld, \"n_signal\": %lld, \"score_sum\": %lld, \"iv_sum\": %.17g, \"delta_sum\": %.17g, \"feat_sum\": %.17g, \"final_sum\": %.17g}}",
                n_ticks, wall, (long long)st.n_evals, (long long)st.n_short, (long long)st.n_green, (long long)st.n_gate, (long long)st.n_signal, (long long)st.score_sum, st.iv_sum, st.delta_sum, st.feat_sum, fsum);
  FILE *f = std::fopen((out + "/result.json").c_str(), "w"); std::fputs(buf, f); std::fclose(f);
  std::puts(buf);
  return 0;
}
