// Go port of py_plain.py (same logic, same checksum). Throw-away benchmark, production code nahi.
// Usage: tickbench <data_dir> <out_dir> [bin|json]
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"time"
)

const (
	N      = 498
	RING   = 301
	R      = 0.065
	YEARNS = 365.0 * 86400e9
	INV    = 0.3989422804014327
)

var TFNS = [3]int64{60000000000, 180000000000, 900000000000}
var BASE = [16]float64{1.0, 1.5, 0.0, 0.0, 0.8, 0.5, 0.0, 0.0, 0.0, 50.0, 50.0, 0.002, 0.0, 0.05, 0.0, 0.0}
var STEPS = [16]float64{0.25, 0.25, 0.002, 0.01, 0.1, 0.05, 0.0005, 0.0005, 0.0005, 5.0, 5.0, 0.001, 0.001, 0.02, 0.1, 0.0002}
var DIR = [16]bool{true, true, true, true, true, true, true, true, true, true, true, true, true, false, true, true}

type Tick struct {
	ID              int
	TS              int64
	LTP, Bid, Ask   float64
	BQ, AQ, OI, Vol int64
}
type JTick struct {
	I   uint16  `json:"i"`
	T   uint64  `json:"t"`
	LTP float64 `json:"ltp"`
	LTQ uint32  `json:"ltq"`
	B   float64 `json:"b"`
	A   float64 `json:"a"`
	BQ  uint32  `json:"bq"`
	AQ  uint32  `json:"aq"`
	OI  uint64  `json:"oi"`
	V   uint64  `json:"v"`
}
type Candle struct {
	bucket                                int64
	o, h, l, c                            float64
	v, ncl                                int64
	pclose, ema9, ema21, atr, ag, al, rsi float64
}
type Check struct {
	fi   int
	th   float64
	dir  bool
	w    int64
	gate bool
}
type State struct {
	ltp, cumPV, vwap, bid, ask                       [N]float64
	lastVol, cumV, bq, aq, oi, oiOpen                [N]int64
	cdl                                              [N][3]Candle
	ringP                                            [RING * N]float64
	ringV                                            [RING * N]int64
	nEvals, nShort, nGreen, nGate, nSignal, scoreSum int64
	ivSum, deltaSum, featSum                         float64
}

var CHECKS [50]Check

func ncdf(x float64) float64 {
	z := math.Abs(x)
	k := 1.0 / (1.0 + 0.2316419*z)
	poly := k * (0.319381530 + k*(-0.356563782+k*(1.781477937+k*(-1.821255978+k*1.330274429))))
	n := 1.0 - math.Exp(-0.5*z*z)*INV*poly
	if x >= 0 {
		return n
	}
	return 1.0 - n
}

func closeCandle(c *Candle) {
	cl, h, l := c.c, c.h, c.l
	if c.ncl == 0 {
		c.ema9, c.ema21, c.atr, c.ag, c.al = cl, cl, h-l, 0, 0
	} else {
		c.ema9 = c.ema9 + (2.0/10.0)*(cl-c.ema9)
		c.ema21 = c.ema21 + (2.0/22.0)*(cl-c.ema21)
		pc := c.pclose
		tr := math.Max(math.Max(h-l, math.Abs(h-pc)), math.Abs(l-pc))
		c.atr = (c.atr*13.0 + tr) / 14.0
		chg := cl - pc
		g, ls := 0.0, 0.0
		if chg > 0 {
			g = chg
		}
		if chg < 0 {
			ls = -chg
		}
		c.ag = (c.ag*13.0 + g) / 14.0
		c.al = (c.al*13.0 + ls) / 14.0
	}
	if c.al == 0 {
		if c.ag > 0 {
			c.rsi = 100
		} else {
			c.rsi = 50
		}
	} else {
		c.rsi = 100.0 - 100.0/(1.0+c.ag/c.al)
	}
	c.pclose = cl
	c.ncl++
}

func update(st *State, t *Tick) {
	i := t.ID
	p := t.LTP
	dv := t.Vol - st.lastVol[i]
	st.lastVol[i] = t.Vol
	st.ltp[i] = p
	st.cumPV[i] += p * float64(dv)
	st.cumV[i] += dv
	if st.cumV[i] > 0 {
		st.vwap[i] = st.cumPV[i] / float64(st.cumV[i])
	} else {
		st.vwap[i] = p
	}
	st.bid[i], st.ask[i], st.bq[i], st.aq[i], st.oi[i] = t.Bid, t.Ask, t.BQ, t.AQ, t.OI
	if st.oiOpen[i] < 0 {
		st.oiOpen[i] = t.OI
	}
	for tf := 0; tf < 3; tf++ {
		b := t.TS / TFNS[tf]
		c := &st.cdl[i][tf]
		if b != c.bucket {
			if c.bucket >= 0 {
				closeCandle(c)
			}
			c.bucket, c.o, c.h, c.l, c.c, c.v = b, p, p, p, p, dv
		} else {
			if p > c.h {
				c.h = p
			}
			if p < c.l {
				c.l = p
			}
			c.c = p
			c.v += dv
		}
	}
}

func evaluate(st *State, strike []float64, expns []int64, tns int64) {
	n := st.nEvals
	slot := int(n % RING)
	copy(st.ringP[slot*N:(slot+1)*N], st.ltp[:])
	copy(st.ringV[slot*N:(slot+1)*N], st.lastVol[:])
	b30 := int(max(n-30, 0) % RING)
	b300 := int(max(n-300, 0) % RING)
	var ch30 [164]float64
	for ix := 0; ix < 3; ix++ {
		S := st.ltp[ix]
		if S <= 0 {
			continue
		}
		base := 6 + ix*164
		var up int64
		var oce, ope [2]int64
		for o := base; o < base+164; o++ {
			p30 := st.ringP[b30*N+o]
			if st.ltp[o] > p30 {
				up++
			}
			e := (o - base) / 82
			if (o-base)%2 == 0 {
				oce[e] += st.oi[o]
			} else {
				ope[e] += st.oi[o]
			}
			if p30 > 0 {
				ch30[o-base] = (st.ltp[o] - p30) / p30
			} else {
				ch30[o-base] = 0
			}
		}
		breadth := float64(up) / 164.0
		pcr := [2]float64{float64(ope[0]) / float64(oce[0]+1), float64(ope[1]) / float64(oce[1]+1)}
		spotMom := (st.cdl[ix][0].ema9 - st.cdl[ix][0].ema21) / S
		for e := 0; e < 2; e++ {
			for k := 0; k < 41; k++ {
				for t := 0; t < 2; t++ {
					o := base + e*82 + k*2 + t
					p := st.ltp[o]
					if p <= 0 {
						continue
					}
					K := strike[o]
					T := float64(expns[o]-tns) / YEARNS
					sq := math.Sqrt(T)
					disc := K * math.Exp(-R*T)
					lnsk := math.Log(S / K)
					sig := 0.20
					for it := 0; it < 3; it++ {
						d1 := (lnsk + (R+0.5*sig*sig)*T) / (sig * sq)
						d2 := d1 - sig*sq
						var price float64
						if t == 0 {
							price = S*ncdf(d1) - disc*ncdf(d2)
						} else {
							price = disc*ncdf(-d2) - S*ncdf(-d1)
						}
						vega := S * math.Exp(-0.5*d1*d1) * INV * sq
						if vega < 1e-8 {
							break
						}
						sig = sig - (price-p)/vega
						if sig < 0.01 {
							sig = 0.01
						}
						if sig > 3.0 {
							sig = 3.0
						}
					}
					d1 := (lnsk + (R+0.5*sig*sig)*T) / (sig * sq)
					var delta float64
					if t == 0 {
						delta = ncdf(d1)
					} else {
						delta = ncdf(d1) - 1.0
					}
					st.ivSum += sig
					st.deltaSum += delta
					var ok bool
					if t == 0 {
						ok = delta >= 0.25 && delta <= 0.65
					} else {
						ok = delta >= -0.65 && delta <= -0.25
					}
					if !ok || p < 2.0 {
						continue
					}
					st.nShort++
					var f [16]float64
					p30, p300 := st.ringP[b30*N+o], st.ringP[b300*N+o]
					f[0] = (math.Abs(p-p30) / 30.0) / (math.Abs(p-p300)/300.0 + 0.01)
					v := st.lastVol[o]
					f[1] = (float64(v-st.ringV[b30*N+o]) / 30.0) / (float64(v-st.ringV[b300*N+o])/300.0 + 1.0)
					sm, cnt := 0.0, 0
					for _, d := range [4]int{-2, -1, 1, 2} {
						kk := k + d
						if kk >= 0 && kk <= 40 {
							sm += ch30[e*82+kk*2+t]
							cnt++
						}
					}
					f[2] = ch30[e*82+k*2+t] - sm/float64(cnt)
					f[3] = float64(st.oi[o]-st.oiOpen[o]) / float64(st.oiOpen[o]+1)
					f[4], f[5] = pcr[e], breadth
					for tf := 0; tf < 3; tf++ {
						f[6+tf] = (st.cdl[o][tf].ema9 - st.cdl[o][tf].ema21) / p
					}
					f[9], f[10] = st.cdl[o][0].rsi, st.cdl[o][1].rsi
					f[11] = st.cdl[o][0].atr / p
					f[12] = (p - st.vwap[o]) / st.vwap[o]
					f[13] = (st.ask[o] - st.bid[o]) / p
					f[14] = float64(st.bq[o]-st.aq[o]) / float64(st.bq[o]+st.aq[o]+1)
					if t == 0 {
						f[15] = spotMom
					} else {
						f[15] = -spotMom
					}
					fs := 0.0
					for x := 0; x < 16; x++ {
						fs += f[x]
					}
					st.featSum += fs
					var score, greens int64
					gateOK := true
					for _, c := range &CHECKS {
						var green bool
						if c.dir {
							green = f[c.fi] > c.th
						} else {
							green = f[c.fi] < c.th
						}
						if green {
							score += c.w
							greens++
						} else if c.gate {
							gateOK = false
						}
					}
					st.nGreen += greens
					if gateOK {
						st.nGate++
						st.scoreSum += score
						if score >= 70 {
							st.nSignal++
						}
					}
				}
			}
		}
	}
	st.nEvals++
}

func writeU64(path string, v []uint64) {
	b := make([]byte, 8*len(v))
	for i, x := range v {
		binary.LittleEndian.PutUint64(b[i*8:], x)
	}
	os.WriteFile(path, b, 0644)
}

func main() {
	data, out := os.Args[1], os.Args[2]
	fmtArg := "bin"
	if len(os.Args) > 3 {
		fmtArg = os.Args[3]
	}
	for j := 0; j < 50; j++ {
		fi := j % 16
		CHECKS[j] = Check{fi, BASE[fi] + STEPS[fi]*float64(j/16), DIR[fi], int64(1 + j%4), fi == 13}
	}
	mb, _ := os.ReadFile(data + "/meta.bin")
	strike := make([]float64, N)
	expns := make([]int64, N)
	le := binary.LittleEndian
	for o := 0; o < N; o++ {
		strike[o] = math.Float64frombits(le.Uint64(mb[o*24+8:]))
		expns[o] = int64(le.Uint64(mb[o*24+16:]))
	}
	var raw []byte
	var lines [][]byte
	var nTicks int
	if fmtArg == "bin" {
		raw, _ = os.ReadFile(data + "/ticks.bin")
		nTicks = len(raw) / 62
	} else {
		rj, _ := os.ReadFile(data + "/ticks.ndjson")
		lines = bytes.Split(bytes.TrimRight(rj, "\n"), []byte("\n"))
		nTicks = len(lines)
	}
	st := &State{}
	for i := 0; i < N; i++ {
		st.oiOpen[i] = -1
		for tf := 0; tf < 3; tf++ {
			st.cdl[i][tf] = Candle{bucket: -1, rsi: 50}
		}
	}
	tickNs := make([]uint64, nTicks)
	var evalNs, evalAt []uint64
	curSec := int64(-1)
	origin := time.Now()
	now := func() uint64 { return uint64(time.Since(origin).Nanoseconds()) }
	wall0 := now()
	var t Tick
	var jt JTick
	for n := 0; n < nTicks; n++ {
		t0 := now()
		if fmtArg == "bin" {
			b := raw[n*62:]
			t = Tick{int(le.Uint16(b)), int64(le.Uint64(b[2:])), math.Float64frombits(le.Uint64(b[10:])),
				math.Float64frombits(le.Uint64(b[22:])), math.Float64frombits(le.Uint64(b[30:])),
				int64(le.Uint32(b[38:])), int64(le.Uint32(b[42:])), int64(le.Uint64(b[46:])), int64(le.Uint64(b[54:]))}
		} else {
			if err := json.Unmarshal(lines[n], &jt); err != nil {
				panic(err)
			}
			t = Tick{int(jt.I), int64(jt.T), jt.LTP, jt.B, jt.A, int64(jt.BQ), int64(jt.AQ), int64(jt.OI), int64(jt.V)}
		}
		sec := t.TS / 1000000000
		if sec != curSec {
			if curSec >= 0 {
				e0 := now()
				evaluate(st, strike, expns, (curSec+1)*1000000000)
				e1 := now()
				evalNs = append(evalNs, e1-e0)
				evalAt = append(evalAt, uint64(n))
				t0 += e1 - e0
			}
			curSec = sec
		}
		update(st, &t)
		tickNs[n] = now() - t0
	}
	wall := float64(now()-wall0) / 1e9
	fsum := 0.0
	for tf := 0; tf < 3; tf++ {
		for i := 0; i < N; i++ {
			c := &st.cdl[i][tf]
			fsum += c.ema9 + c.ema21 + c.rsi + c.atr
		}
	}
	for i := 0; i < N; i++ {
		fsum += st.vwap[i]
	}
	os.MkdirAll(out, 0755)
	writeU64(out+"/tick_ns.u64", tickNs)
	writeU64(out+"/eval_ns.u64", evalNs)
	writeU64(out+"/eval_at.u64", evalAt)
	res := fmt.Sprintf(`{"impl": "go", "format": "%s", "n_ticks": %d, "wall_s": %f, "checksum": {"n_evals": %d, "n_short": %d, "n_green": %d, "n_gate": %d, "n_signal": %d, "score_sum": %d, "iv_sum": %.17g, "delta_sum": %.17g, "feat_sum": %.17g, "final_sum": %.17g}}`,
		fmtArg, nTicks, wall, st.nEvals, st.nShort, st.nGreen, st.nGate, st.nSignal, st.scoreSum, st.ivSum, st.deltaSum, st.featSum, fsum)
	os.WriteFile(out+"/result.json", []byte(res), 0644)
	fmt.Println(res)
}
