# Audit report (11 Nov 2026): website + bot + plan

Tareeka: pehle kamiyan dhoondhi, phir theek ki, phir dobara jaancha. Har line par haalat likhi hai: **Theek** / **Baaki** (wajah ke saath).

## A. Website (repo `Bot-trading-website-`, PR #1)
Jaanch ke tareeke:
- **dataviz skill:** palette validator se rang jaanche.
- **code-review skill (high):** bug dhoondhe.
- **Playwright:** phone par 51 aur desktop par 49 button-checks.
- **Tests:** 16 node tests.
- **Build:** local Vercel build.

| # | Kami | Haalat |
|---|---|---|
| W1 | Controls ke buttons band (disabled) the; "har button kaam kare" nahi tha | Theek: ON/OFF, Paper/Real ("REAL"), Pause, Square-off, Kill ("KILL"), Reset ("RESET"), log. Abhi practice mode, kyunki bot juda nahi |
| W2 | Phone par card header ke buttons upar-neeche ho jaate the | Theek: header wrap niyam, sab control ek height (40/44px) |
| W3 | Phone par page 8-14px side mein scroll hota tha | Theek: header chhota (Khula/Band, chhupe label) |
| W4 | Neeche ka menu form fields ko dhak leta tha | Theek: `scroll-padding-bottom` |
| W5 | Chart tooltip har 5 s refresh mein gayab ho jaata tha | Theek: refresh ke baad wapas usi candle par |
| W6 | Dark mode mein EMA ke rang validator mein FAIL the | Theek: `#3987e5` / `#c98500` (PASS) |
| W7 | Chart ki table view nahi thi (accessibility) | Theek: Chart aur P&L dono mein "Table dikhao" |
| W8 | CSV ke naam mein UTC tareekh (raat 12 se 5:30 ke beech galat din) | Theek: IST tareekh |
| W9 | Header mode chip "Paper" dikhata tha, jabki Real chuna gaya tha | Theek: "Real (practice)" |
| W10 | Segment buttons arrow key se nahi badalte the | Theek: ← → aur roving tabindex |
| W11 | CSV mein formula-injection ka khatra | Theek: `=`, `+`, `-` aur `@` se shuru hone wale text ke aage `'` |
| W12 | Toast (khabar) bade the aur 3 jama hokar page dhak dete the | Theek: chhote, max 2 |
| W13 | Real Money website se: website hack hui toh paisa khatre mein | **Baaki (M7):** hukm signed (HMAC) + 2FA; bot khud Gates jaanch kar hi Real chalu kare. Abhi sirf practice |
| W14 | Vercel par Deployment Protection | **Baaki (malik):** Setup Step 2 |

## B. Bot (repo `Bot-trading-`)
| # | Kami | Haalat |
|---|---|---|
| B1 | Lot size, expiry ke din, Bank Nifty weekly: sab purane niyam par | Theek: `strategy/instruments.py` (65/20/30; Tue/Thu; Bank Nifty sirf monthly) |
| B2 | Kharche ka model nahi tha (STT 0.15% naya) | Theek: `costs.py`. Andaza wale fields alag (`unverified()`), Real se pehle contract note se pakka karne hain |
| B3 | "1 lot, premium quality, paisa kam ho toh skip" code mein nahi tha | Theek: `selection.py` (ITM, phir ATM; OTM kabhi nahi; spread, OI, capital aur risk jaanch; warna SKIP) |
| B4 | ₹15k mein 1 lot ka risk bahut zyada (25% SL par ~15% capital) | Theek: `risk_per_trade` = min(din ki seema ka 60%, capital ka 6%); upar ho toh SKIP |
| B5 | Entry/exit ke niyam (time-stop, trailing, hard exit, halt) code mein nahi the | Theek: `rules.py` + 8 tests |
| B6 | Plan mein 2 server (Oracle) the | Theek: **sirf ek Amazon Lightsail**. `deploy/bot.service` + `deploy/pehredaar.service` (alag service, memory seema, OOM niyam) |
| B7 | Ek server mare toh SL? | Theek (niyam): har entry ke baad broker par SL (limit) order (options par SL-M exchange reject karta hai: docs/REGULATORY.md). Code M5 (order manager) mein |
| B8 | Bot ka chalu hone ka entrypoint (`python -m bot`) abhi nahi hai | **Baaki (M1):** server setup ke saath |
| B9 | Regime, gap-day niyam, setups S1/S2/S3 | Theek: `bot/dimaag/` + tests. Event calendar ka source **baaki** |
| B11 | Risk sirf 25% premium SL se: ₹15k par bot kabhi trade nahi leta | Theek: chart SL × delta (Round 4) |
| B12 | Backtest Gate jaanchne ka tool nahi | Theek: `bot/backtest/` (engine, metrics, gate). Asli data recorder (M1) se aayega |
| B13 | Recorder nahi tha: asli data ke bina Gate bekaar | Theek: `bot/recorder/` (journal hash-chain, crash par adhuri line chhodo, beech ki gadbad pakdo, gzip; ticks se candles + option book, lookahead nahi). Live feed (M2) server ke baad |
| B14 | Reader poori file memory mein padhta (1 din ~150MB) | Theek: line-by-line; reopen par sirf file ka aakhri hissa |
| B10 | Chhutti par expiry shift | **Baaki:** broker instrument list se (verify nahi hua) |

## C. Strategy
3 round ki poori report `strategy/AUDIT_ROUNDS.md` mein hai. Final `strategy/STRATEGY_v2.md` (v2.3). Sabse badi 3 baatein:
1. Bank Nifty ₹15k mein trade nahi hoga, sirf signal ke liye.
2. Option khareedne wala aam taur par zyada daam deta hai (VRP). Isliye sirf trend din, kam samay hold, aur bahut SKIP.
3. Har setup ek parikalpana hai. Backtest (≥200 trade), Paper (≥60 trade, ≥3 mahine) aur Stage2 pass hone tak Real Money nahi.

## D. Malik ke faisle (website: Settings → Risk niyam form)
1. Kul_Jeb_Nuksan_Seema (₹).
2. Din ki nuksan seema (₹). Iske bina bot entry nahi lega.
3. Risk Limit ki ikai.
4. Data_Purana_Hadd.
5. Breadth stocks.
6. Vakil se: TOTP auto-login SEBI 2FA niyam ke andar hai ya nahi.
