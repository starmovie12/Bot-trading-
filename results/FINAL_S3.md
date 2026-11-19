# FINAL_S3 · Program S3 / S3.1 band (owner order 7, D1 STOP)

[BACKTEST·OOS] PRE-TAX · DESIGN 362 din, nested OOS = blocks 2–5 (290 din) · series BASE · holdout **ek baar bhi nahi padha** (access log 0, holdout_uses 0)

## Seedha sach (6 line)
1. **Strategy jaisi likhi thi (T1-P), ghaate mein hai:** 555 trade, −₹99,562 (−₹179/trade). §14.1 ke 9 mein se 1 gate pass hua. NULL-RANDOM p 0.41, yaani entry random entry jaisi.
2. **R1–R4 (nested sudhaar) bhi FAIL:** sabse achha R4 raha, −₹62,727 (469 trade), 0/4 windows positive. Kul 160 fits aur 62 distinct configs.
3. **Asli galti exit mein thi (D-58):** kharche se pehle gear engine sirf +₹19,239 kamata hai. Unhi entries par seedha 10-bar exit +₹87,865 kamata, yaani exit ne ~₹68,600 gawaaye.
4. **D1 signal test (exit theek karke) bhi saabit nahi hua.**
   - X-T0 ke saath kharche se pehle (mid) +₹131/trade hai, aur random se behtar dikhta hai: p(mid) 0.035.
   - Par asli net mein p(net) 0.097 hai, aur sirf 2/4 windows mein mid positive hai.
   - Kharcha ₹214/trade hai, yaani mid edge kharche se kam hai. Net −₹43,619 (525 trade).
5. **Edge kam samay ka hai aur jaldi khatam hota hai:** H = 3/10 bar par mid +₹119/+₹131, lekin H = 20/30 par negative (−₹81/−₹69). Spread ₹0.50 tak ghatane par bhi R0 zero se neeche raha.
6. **Faisla:** S3 STOP. Holdout nahi khola gaya, koi STRATEGY PASS nahi, koi naya family nahi, aur Phase 4 band hai.

## Ek dhyaan dene wali baat (sirf observation, strategy nahi)
- Entry ke waqt option ki chaal (OptATR5) ke top tercile mein 145 trade the: mid +₹340/trade, net +₹121/trade [BACKTEST·OOS].
- Neeche wale tercile mein mid −₹8/trade raha.
- Yeh tercile split order 7 §3 mein pehle se registered diagnosis tha, aur chaal gate (R14) D1 se pehle registered tha, isliye yeh post-hoc nahi hai (sudhaar, D-61). Holdout S3 mein abhi bhi ek baar use ho sakta hai (§14.2, HOLDOUT_REUSED, uses 0); asli seema yeh hai ki 90 din chhota hai, power kam hai.
- Iska matlab sirf itna hai: option buyer ko tabhi mauka hai jab chaal kharche ka kai guna ho. Yeh profit ka daava nahi hai.

## Kya madad karega (malik ka faisla)
1. **Asli bid-ask spread ka naap** (§18 #1): ATM aur ₹350 strike, 09:20 / 11:00 / 13:00 / 15:00 par, 3–5 din. Kharcha ₹214/trade sabse bada dushman hai.
2. **Naya, anchhua data:** paper/shadow logging (paisa nahi), jismein pehle se likha niyam ho ("T1-P signal + OptATR5 high tercile + X-T0/X-T exit"). Isse upar wala observation aage ke data par jaanch sakte hain. Yeh Phase 4 ka hissa hai, isliye sirf malik ke "build bot" hukm par.
3. Tab tak koi live ya paper paisa nahi.

Files:
- results/s3_rounds.md (R0–R4 cards + chart table)
- results/s3_s31.md (D1 card, edge curve, tercile)
- results/s3_d1_summary.json
- results/s3_trades.csv, s3_signals_*.csv, s3_r1…r4_trades.csv
- DECISIONS D-54…D-60

## Sudhaar (owner order 8, D-61)
- Holdout: S3 mein ek baar use ho sakta hai (§14.2, HOLDOUT_REUSED, uses 0). 90 din chhota hai, isliye power kam hai.
- OptATR5 tercile split order 7 §3 mein registered diagnosis tha, aur chaal gate (R14) D1 se pehle registered tha, isliye yeh post-hoc nahi hai.
- NULL p ab per-trade mean par gina jaata hai (FIX-13). D1 ka recount `results/s3_s31.md` mein hai.
