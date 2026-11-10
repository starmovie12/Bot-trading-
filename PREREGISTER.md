# PREREGISTER: pass/fail aur STOP ki shartein (result se PEHLE commit)

**Tarikh:** 11 Nov 2026 · **Strategy:** v3 (`STRATEGY_v3.md`) · Yeh file kisi bhi truth-test result se pehle commit hui.
Result dekhne ke baad koi shart badli = 1 STRIKE. Badlaav sirf naye, tarikh wale "Amendment" section se, aur sirf naya data aane se PEHLE.

## H0 (null): Strategy v3 mein kharche ke baad koi edge nahi
Edge sabit karna strategy ka kaam hai. Saboot na mile toh H0 maana jaata hai.

## Data ke do darje
| Darja | Kya | Kya sabit kar sakta hai |
|---|---|---|
| SYNTHETIC | `tests/` ka nakli data | Sirf yeh ki machinery (engine, tests) sahi chalti hai. **Kabhi Gate pass nahi kar sakta.** |
| REAL | Recorder (asli feed) ya kharida/broker ka historical option data | Sirf isi par verdict |

## Truth tests (REAL data, out-of-sample par)
| ID | Test | PASS sirf tab |
|---|---|---|
| T1 | RANDOM_ENTRY: ≥1,000 random-entry runs. Wahi exits, kharcha, sizing aur entry ki khidkiyan. Do null: (a) side + samay random, (b) regime wali side, samay random | Strategy ka OOS net P&L dono null ke **95th percentile se upar** |
| T2 | COST_STRESS: kharcha ×2 aur slippage ×2 | OOS net expectancy **> 0** |
| T3 | DELAY: entry 1, 2, 3 candle (5-min) der se | Delay 1 par expectancy, delay 0 ka ≥ 50% aur > 0. Delay 2 par > 0 |
| T4 | PARAM_SHAKE: har live parameter (max 12) ±20%, ek-ek karke | **Ek bhi** shake par verdict (PF ≥ 1.3 aur expectancy > 0) na palte |
| T5 | TOP3_REMOVED: sabse achhe 3 trade hatao | Net P&L **> 0** |
| T6 | WALK_FORWARD / OOS: parameter in-sample par jame. OOS = samay ke hisaab se aakhri 30%. Walk-forward (6 mahine seekho, 1 mahina jaancho) tab, jab ≥ 18 mahine ka data ho | OOS PF ≥ 1.3; OOS expectancy ka ek-taraf 95% nichla CI > 0; OOS ≥ 100 trade; kul ≥ 300 trade (niyam `Backtest_Min_Trade_Ginti`) |
| T6b | LOOK-AHEAD audit: har feature (EMA, VWAP, regime, setups, engine) par prefix test. Future data badalne se pichhla nateeja nahi badalna chahiye | Saare pass. **Ek bhi fail = poora result radd** |
| T7 | CASH_BASELINE: usi avadhi mein ₹15,000 FD par, server band | Strategy ka net (server kharcha ghata kar) **FD baseline se zyada** |
| T8 | RISK: OOS max drawdown; OOS trades se bootstrap Monte Carlo (10,000) | Max DD ≤ ₹3,000 (capital ka 20%); 95th percentile DD ≤ ₹4,000 (kul jeb) |

## Faisla (decision rule)
- **GO_PAPER:** sirf jab T1–T8 sab REAL data par PASS hon.
- **NOT_YET:** REAL trade < 300 ya OOS < 100 (saboot kam). Tab Shadow Mode: bot signal aur hypothetical trade likhta hai, broker ko kuch nahi bhejta.
- **STOP:** REAL OOS ≥ 100 trade hone ke baad bhi T1 fail ho, ya OOS expectancy (kharche ke baad) ≤ 0 ho.

## STOP shartein (₹ aur trade ginti mein)
| Kahan | STOP jab |
|---|---|
| Saboot jama karna | 6 mahine recording ke baad bhi < 150 qualifying signal (strategy itni kam chalti hai ki jaanchi hi nahi ja sakti) |
| Paper | 60 paper trade ke baad net (₹111/trade server hissa samet) < 0, ya expectancy ka 90% nichla CI < 0. Ya paper drawdown > ₹3,000 |
| Live (sirf GO ke baad) | Kul jeb ₹4,000 → hamesha ke liye band. Din ₹900, hafta ₹1,800. 30 live trade par net < −₹1,500 → STOP |

## Pehle se tay assumptions (SIM; LEDGER mein tag)
Server ₹1,330/mahina [SIM, verify], 12 trade/mahina [SIM], slippage 1 tick (₹0.05) har taraf [SIM].
Kharcha `CostModel` (STT 0.15% SOURCE; exchange/stamp/SEBI andaza).
