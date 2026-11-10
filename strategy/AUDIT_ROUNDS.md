# Strategy: 3 audit round (malik ka niyam: "banao → kamiyan dhoondho → theek karo", teen baar)

Har round mein pichhle version ki kamiyan dhoondhi, theek ki, aur nayi version banai. Final: `STRATEGY_v2.md` (v2.3).

## Round 1: v2 (pehla draft) → v2.1
| # | Kami | Kitni gambhir | Sudhaar |
|---|---|---|---|
| R1-1 | Purane niyam par plan tha: Bank Nifty weekly maana, lot 75/35, expiry Thursday | Critical | 2026 ke niyam: Nifty Tue, Sensex Thu, Bank Nifty sirf monthly; lot 65/30/20 (`instruments.py`) |
| R1-2 | Bank Nifty ka monthly ATM ₹15k mein aata hi nahi, phir bhi trade list mein | High | Bank Nifty = sirf signal (`tradable=False`) |
| R1-3 | Kharcha purane STT (0.10%) par | High | 0.15% (1 Apr 2026 se); andaze wale fields `unverified()` |
| R1-4 | ORB "seedha" maana, jabki khule backtest mein lookahead bug mila tha | High | Entry hamesha signal candle ke **baad**; ORB sirf retest + VWAP + regime ke saath |
| R1-5 | Theta ka dhyan nahi: bina chaal ke position ghanto pakde rakhna | High | 15 min time-stop (+5% na ho toh exit) |
| R1-6 | Nifty aur Sensex dono mein ek saath entry ho sakti thi (dono ek taraf chalte hain) | High | Ek samay par sirf 1 open position (`can_enter`) |
| R1-7 | VIX uchhalne par bhi entry | Med | VIX din mein ≥ 8% upar toh entry band |

## Round 2: v2.1 → v2.2
| # | Kami | Kitni gambhir | Sudhaar |
|---|---|---|---|
| R2-1 | **₹15k capital, 1 full lot, 25% SL = ek trade mein ~15% capital ka risk.** Do haar = ~30% ek din mein | Critical | Risk per trade seema = min(din ki seema ka 60%, capital ka 6%) ≈ ₹900. Isse zyada risk ho toh **SKIP** (`selection.py` 4th check) |
| R2-2 | Premium SL aur underlying SL mein kaunsa pehle, tay nahi | High | Jo pehle lage (`on_tick`: hard SL + `structure_broken`) |
| R2-3 | Ek hi server: server mare toh SL kaun lagayega? | High | **Broker Stop:** entry ke turant baad broker par SL-M (deploy/README) |
| R2-4 | Expiry din dopahar ka "jua" (theta + gamma) | High | Expiry din 13:30 ke baad entry nahi; S4 sirf paper |
| R2-5 | Din ki nuksan seema 0 (tay nahi) hone par bhi bot chal sakta tha | High | Seema tay nahi = entry band (`can_enter`) |
| R2-6 | Bahut saare parameter = overfitting | Med | Har setup ≤ 6 parameter; walk-forward; out-of-sample girawat ≤ 30% |
| R2-7 | Gap din par pehle 30 min ka josh | Med | Gap > 1%: pehle 30 min koi entry nahi (code M3 mein, abhi doc mein) |

## Round 3: v2.2 → v2.3 (final)
| # | Kami | Kitni gambhir | Sudhaar |
|---|---|---|---|
| R3-1 | Expiry din ITM option band hone tak rakha toh exercise par STT 0.15% intrinsic par | High | 15:15 hard exit (har din) |
| R3-2 | Breakeven jeet-dar ka hisaab hi nahi tha | Med | Ganit section: R = ₹900, +2R par ~36% jeet chahiye (kharcha samet) |
| R3-3 | Gates mein trade ki ginti kam (30) | Med | Backtest ≥ 200, Paper ≥ 60 trade aur ≥ 3 mahine |
| R3-4 | Chhutti par expiry shift ka niyam nahi | Med | Bot roz broker ki instrument list se expiry lega; `is_expiry_day` sirf backup (verify nahi hua) |
| R3-5 | Event calendar (RBI/Budget/Fed/results) ka source tay nahi | Med | Malik + Claude M3 mein tay karenge; tab tak un dino paper |
| R3-6 | Historical intraday option data muft nahi | Med | Pehle apna recorder (M1) data jama kare; Upstox expired-instrument history verify karna |
| R3-7 | "Sabse badhiya strategy" ka dava | Low | Hata diya. Saare setup hypothesis hain; data hi faisla karega |

## Abhi bhi khuli baatein (code ya malik ka faisla chahiye)
- Kul_Jeb_Nuksan_Seema, din ki nuksan seema, Risk Limit ki ikai (website **Settings** form se JSON).
- Event calendar ka source; exchange charge / stamp ka pakka rate (contract note).
- Gap-day niyam aur regime (Parat 1) ka code: M3.
