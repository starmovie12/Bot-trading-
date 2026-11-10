# 01b: Audit Findings (Bot Idea v3.1 → v4.0)

**Tarikh:** 10 Nov 2026 · **Kisne:** Claude Code · **Input:** `docs/00_input/bot_idea_final.md` (sha256 `c8770e67…dabb1`) · **Output:** `docs/01_Bot_Idea_v4.md`

## Saar (10 line)
1. Idea ka gehra audit section-by-section hua. Kul **79 bindu** mile: **8 Critical, 19 High, 38 Med, 14 Low**.
2. Sabse bada khatra: kuch niyam bot ko **kabhi trade na karne** ya **galat trade** karne ki taraf le jaate hain (F-01, F-02).
3. Doosra bada khatra: **paisa doobne ke raaste**. Bot aur Pehredaar ek saath chal sakte hain aur account net short ho sakta hai (F-05). Kill-Switch ke baad bot phir entry le sakta hai (F-04). Upstox ab ek user ko sirf ek chalu API app deta hai, isliye Pehredaar ka alag app mumkin nahi; shared token ka design chahiye (F-76, F-06, F-62).
4. Teesra: **poore balance ka 1 Lot** wala niyam aur Risk Limit aapas mein mel nahi khaate (F-03). 10 Nov 2026 ko malik ne poora balance + "premium ki quality pehle" pakka kiya; ab sirf Risk Limit ki ikai aur `Kul_Jeb_Nuksan_Seema` ka sawal hai. Malik ke ₹10-15k balance mein Nifty50 ka achha strike lagbhag kabhi nahi aata (F-77).
5. Har fix `[PRASTAAVIT-CC]` tag ke saath v4 mein sahi ghar mein likha hai. Malik ka ek bhi shabd nahi badla (script se verify: 0 lines missing).
6. Strategy ke 15 sudhaar Hypothesis H-01 se H-15 hain. Inhe `03_Strategy_Edge_Plan.md` ke tareeke se test karna hai.
7. 25 sawal (Sawal 117-141; Sawal 118 malik ke jawab ke baad chhota hua) aur 16 nayi Takraav (#26-#41) "Abhi tay nahi hua" mein jode.
8. 49 naye number rows (malik ke 3 naye number: `Malik_Max_Balance`, `Achha_Premium_Udaharan`, `Server_Mahina_Budget`) (sab Prastaavit ya Tay nahi). Inme Stage Gates aur Live band karne ki kasauti bhi hain.
9. Research se 10 nayi baatein mili (bazaar ke naye samay, STT 0.15%, Upstox ke niyam, SDK mein TLS jaanch band). Yeh Section 20 aur 17 mein source ke saath hain.
10. Asar ke andaze qualitative hain. Asli rupaye ka asar Backtest aur Paper Stage hi batayenge.

**Prakar ki chaabi:** (a) aapas ki takraav · (b) aisa rule jisse paisa aasaani se doob sakta hai · (c) khaali jagah jahan PRD wala AI guess karega · (d) vague shabd bina number · (e) ek hi data ko dohrate checks · (r) research se mili nayi baat.

## Gambhirta ki ginti

| Gambhirta | Ginti | Matlab |
|---|---|---|
| Critical | 8 | Fix ke bina Real Money Mode nahi chalna chahiye |
| High | 19 | Asli paise se pehle fix zaroori |
| Med | 38 | Paper Stage se pehle fix ya test |
| Low | 14 | Saaf-safai; PRD ke saath theek ho sakta hai |

## Top 10 (sabse gambhir pehle)

| # | ID | Ek line |
|---|---|---|
| 1 | F-01 | Gate ka NA = RED, isliye sirf-expiry wale manipulation Gates aam din har trade rokte hain |
| 2 | F-05 | Bot aur Pehredaar ek saath broker ko hukm de sakte hain, isliye net short ho sakta hai |
| 3 | F-04 | Kill-Switch bot ko nahi rokta; thodi der baad bot phir entry le sakta hai |
| 4 | F-76 | Upstox ka "ek user, ek chalu API app" niyam: Pehredaar ka alag app/token mumkin nahi; shared token ka design aur test chahiye |
| 5 | F-06 | Pehredaar ka app bot ke order cancel kar sakta hai ya nahi, verify nahi hua |
| 6 | F-03 | Poore balance ka Lot (malik ka faisla): ek Stop-Loss se mahine ki seema toot-ti hai; asli khatra baar-baar paisa daalna |
| 7 | F-02 | Nifty50/Sensex ki stocks suchi nahi, isliye Breadth Gate un index ko hamesha band rakhta hai |
| 8 | F-09 | Broker Stop aadha fill ho chuka ho aur exit poori quantity ka jaaye, toh net short |
| 9 | F-10 | Jawab na aane par entry dobara bheji toh dohra trade |
| 10 | F-15 | "Nuksan Stop-Loss % se bandha hai" gap mein jhooth; risk ka hisaab galat |

## Saare bindu

Asar ka matlab profit/loss par andaza hai, number nahi. "v4 mein" column batata hai ki fix kis section mein hai.

| ID | § | Prakar | Gambhirta | Dikkat | Fix (Prastaavit-CC) | P&L par asar | v4 mein |
|---|---|---|---|---|---|---|---|
| F-01 | 6, 7 | a, c | Critical | "Lagu nahi" check NA hai, aur Gate ka NA RED hai. Manipulation_Cash_Volume_Check aur Manipulation_Settlement_Check aam din har trade rokte hain | NA ke do roop: NA-Data (Gate RED), NA-Lagu-Nahi (Gate par asar nahi) | Iske bina bot trade hi nahi karega, ya PRD wala AI apna niyam gadhega | §6, §7, TAKRAAV #26, Sawal 119 |
| F-02 | 7, 18 | c, a | Critical | Index_Breadth_Check Gate hai, par Nifty50/Sensex ki suchi Tay nahi. NA-Data → RED, yaani Nifty50 aur Sensex kabhi trade nahi | Official vazan se top-N suchi (`Breadth_Top_Stocks_Ginti`); tab tak sirf Paper | 2 index ke saare mauke khulenge | §7, §18, TAKRAAV #32, Sawal 16 |
| F-03 | 9 | a, b | Critical | Poore balance ka Lot + 25-30% Stop-Loss: ek nuksan Daily (3%), Weekly (6-8%) aur Monthly (15%) teeno se bada. Pehle nuksan par bot mahine bhar rukta hai. Poora balance lagane par positive ausat ke saath bhi balance ghat sakta hai | **Malik ka faisla (10 Nov 2026):** poora balance + premium ki quality pehle; Vikalp A aur C nahi. Bacha: Vikalp B (Stop-Unit seema) + `Kul_Jeb_Nuksan_Seema` (Sawal 118); Monte Carlo (D3 §5.4) | Risk of Ruin bahut ghat sakta hai; trade size chhota | §9, §18, TAKRAAV #28, Sawal 118 |
| F-04 | 5, 13 | a, b | Critical | Kill-Switch sirf Pehredaar ko jaata hai. Zinda bot `Record_Farak_Pause_Samay` ke baad phir entry le sakta hai | Kill Latch (bot + Pehredaar dono padhein), agle din Start se hi khule | Kill ke baad ka dobara nuksan band | §5, TAKRAAV #29, Sawal 120 |
| F-05 | 5 | b | Critical | Bot dheema ya network toota: bot aur Pehredaar dono exit/cancel bhejte hain, isliye net short ya Broker Stop ki gadbad | Lease: bot `Bot_Lease_Samay` ke baad hukm nahi bhejta; "Pehredaar ne control liya" nishan | Net short ka sabse bada rasta band | §5, §18, Sawal 121 |
| F-06 | 5 | c | Critical | Pehredaar ka alag app bot ke app ke order cancel kar sakta hai ya nahi, verify nahi hua | Real Money se pehle asli test; fail ho toh Real Money band | Pehredaar par jhootha bharosa khatam | §5, Sawal 117 |
| F-76 | 5, 20 | r, a | Critical | Upstox: 1 Apr 2026 se ek user ka sirf ek chalu API app; naya token purana band. "Pehredaar ka alag app/token" ab mumkin nahi | Ek app, roz ek token, login ek jagah se; token encrypted raste se Pehredaar tak; Pehredaar Secondary IP se. Shared token ka asli test zaroori | Pehredaar ka design bachta hai; NSE "ek API key" (F-62) bhi poora | §5, §20, TAKRAAV #38, Sawal 141 |
| F-62 | 5, 20 | r | Critical | NSE standard A.4: bina registration algo sirf ek pehle se tay API key se. Pehredaar ka alag app = alag key | Upstox + vakil ki likhit pushti tak Real Money band | Account par rok ka khatra | §5, §20, TAKRAAV #37, Sawal 136 |
| F-07 | 3, 7 | a, b | High | `Ghadi_Skew_Hadd` (1 s) ≥ `Data_Purana_Hadd` (0.5-1 s); taazgi ka naap bekaar | `Ghadi_Skew_Sakht_Hadd` (50 ms) + apne paane ke samay se umar | Purane bhav par entry kam | §3, §7, TAKRAAV #27 |
| F-08 | 5, 11 | a, b | High | Trailing har khiskaav par Broker Stop badalta hai; modify ki seema (agar ho) par reject se jabardasti exit | `Broker_Stop_Min_Khiskaav` + `Broker_Stop_Modify_Bajat` + cancel-aur-naya | Bekaar exit kam, order traffic kam | §5, §18, TAKRAAV #31 |
| F-09 | 5 | b | High | Exit ke waqt Broker Stop aadha fill; poori quantity bechi toh net short | Exit quantity = cancel confirm ke baad broker ki net quantity | Net short ka rasta band | §5 |
| F-10 | 5 | b | High | Jawab na aane par entry dobara bheji toh dohra trade | Entry kabhi bina pushti dobara nahi; Order Tag kabhi dohraya nahi | Dohra trade lagbhag khatam; kabhi entry chhootegi | §1, §5 |
| F-11 | 5 | b, c | High | Malik ka haath ka trade usi instrument mein ho toh net quantity mil jaati hai; bot malik ke Lot bech sakta hai | Foreign Position wale instrument mein bot trade nahi | Kuch strike chhootenge | §1, §5, Sawal 126 |
| F-12 | 4 | b | High | Expiry shift par exit fill se pehle naya entry | Net quantity zero aur paisa dobara padhne ke baad hi entry | Dohra jokhim band | §4 |
| F-13 | 10 | c, b | High | "Khula trade" mein pending order gine jaate hain ya nahi, tay nahi; limits toot sakti hain | Khula Trade = position + pending entry + chalta exit | Dohra jokhim band | §2, §10 |
| F-14 | 9 | b | High | Din ka nuksan sirf band trade se; khule trade ka nuksan nahi gina | Naye entry se pehle khule trade ka Worst-Case Nuksan bhi gino | Do trade milkar seema nahi todenge | §9, Sawal 127 |
| F-15 | 9 | b | High | "Nuksan Stop-Loss % se bandha" gap, Broker Stop ki doori aur MPP mein sach nahi | Worst-Case Nuksan (`Worst_Case_Nuksan_Guna`) se risk gino | Asli risk dikhega; Lot kam ho sakte hain | §9, §18 |
| F-16 | 5, 14 | b, c | High | Dhadkan sirf "zinda"; Pehredaar khud broker nahi padhta; bot mara toh alert kaun bheje | Haalat wali dhadkan, Pehredaar ka apna milaan aur apna alert rasta | Bina Stop ka trade jaldi pakda jaayega | §5, §14 |
| F-17 | 13 | b | High | Internet par khula Dashboard bot/Pehredaar ko hukm deta hai; nakli hukm ka khatra | Signed, ek-baar, `Command_Max_Umar`; bot/Pehredaar khud hukm lein; Pehredaar sirf Kill maane | Hack se paisa bachega | §13 |
| F-18 | 16 | b | High | Malik Paper se pehle Real Money chun sakta hai; parakh chhoot jaati hai | Backtest Gate se pehle Real Money band; Override sirf 1 Lot + likhit pushti | Shuruaati nuksan ka bada rasta band | §16, TAKRAAV #35, Sawal 122 |
| F-19 | 16 | c | High | Stage paimana "nuksan nahi" + 30 trade: kismat aur hunar alag nahi dikhte; kill criteria nahi | Confidence Interval wale Gates + `Live_Kill_Paimana` | Bina edge ke live jaane se bachav | §16, §18, Sawal 123 |
| F-20 | 11 | a | High | Trailing (1 ATR) pehle stop (1.5 ATR) se paas; kab shuru, likha nahi | Trailing breakeven ke baad | Jaldi kate trade kam | §11, TAKRAAV #30 |
| F-21 | 11 | c, b | High | Stop-Loss kis bhav par chale (LTP/bid/mid), tay nahi | Best bid + `Stop_Pushti_Ginti` | Galat bhav par stop kam | §11, Sawal 125 |
| F-22 | 11 | c | High | ATR stop aur swing low stop mein se kaunsa, tay nahi | Door wala; cap se door ho toh vikalp H-06 (skip) | Stop sahi jagah; kuch trade kam | §11, Sawal 124 |
| F-63 | 3, 4, 20 | r, a | High | F&O ab 3:40 PM tak; 7 Dec 2026 se 3:45 PM (expiry din 3:30 PM); settlement ka tareeka badla | Roz exchange/broker ki timing se milao; malik naye samay tay kare | Galat samay par trade nahi | §3, §4, §20, TAKRAAV #36, Sawal 137 |
| F-64 | 5, 17 | r, b | High | Upstox SDK ke live data hisse mein TLS certificate jaanch band; usi par token jaata hai | Feed khud likho, TLS jaanch ON, official .proto pin | Token chori ka rasta band | §5, §17 |
| F-77 | 9, 7 | r, c | High | Malik ka balance ₹10-15k aur achha premium ₹400-500: Nifty50 ka 1 Lot ₹26,000-32,500, yaani balance se bahar; 10% buffer BankNifty ka achha strike bhi rokta hai | Bot Nifty50 mein zyada tar skip karega (malik ka niyam sahi); `Balance_Extra_Buffer_CC` ₹250 (margin shart jaanch kar); report mein "Balance Kam" ginti | Kam index, par sasta premium kabhi nahi; buffer se BankNifty ke mauke wapas | §9, §18, TAKRAAV #39, #41 |
| F-79 | 5 | b | Med | Pehredaar/Dashboard free server par: provider idle machine delete kar sakta hai; IP badal sakta hai | Pehredaar ki dhadkan na ho toh naye entry band; IP badlaav sirf market ke baad; asli paise se pehle paid Pehredaar (D2 D8 Plan B) | Bachat ke saath suraksha bani rahe | §5 |
| F-23 | 3 | c | Med | "Kisi bhi index ka 1 Lot" ka matlab saaf nahi; sasta index bhi band ho sakta hai | Kam se kam ek index ka paisa ho toh Start; baaki par alag "Paisa Kam" | Zyada mauke | §3 |
| F-24 | 3, 7 | e, a | Med | Range Delta band aur free paise se banti hai; Premium_Range_Gate dohraav; purani range sahi strike rokti hai | Range har evaluation par; Range Alert = "paisa kam" | Kam bekaar reject | §7, TAKRAAV #33, Sawal 130 |
| F-25 | 3 | c | Med | Bade gap ke baad "nayi range" tay nahi | `Gap_Ke_Baad_Range_Samay` | Test-yogya | §3 |
| F-26 | 3 | c | Med | Khule trade ke beech mausam badle toh kya, tay nahi | Trade apne exit se; Lot cut sirf naye entry par | Bekaar exit kam | §3 |
| F-27 | 3 | b | Med | Subah ka ADX pichle din ki candles se bhara; kal ka haal dikhata hai | H-12: Mausam tag ka asar Backtest mein naapo | Galat Sideways din kam | §3 |
| F-28 | 3 | b | Med | Shock Mode mein munafe wale trade bhi sabse chaude spread par band | H-08: turant exit banam trailing | Shock din Slippage kam ho sakta hai | §3 |
| F-29 | 3 | b | Med | Pal bhar ke Liquidity RED par din ke ant mein exit | `Liquidity_Exit_Tikav_Samay` | Bekaar exit kam | §3 |
| F-30 | 4 | d, c | Med | Expiry subah "mazboot tezi" tay nahi; warna kya, tay nahi | `Mazboot_Breakout_Paribhasha`; kamzor par us index mein trade nahi | Gamma jokhim kam | §4, Sawal 131 |
| F-31 | 4, 7 | d, c | Med | "Ek hi bada daon" ka kaam saaf nahi | Ek-disha ke do trade ka Worst-Case Nuksan din ki bachi seema mein | Correlated nuksan kam | §4, §7 |
| F-32 | 4, 7 | c | Med | SUSPICIOUS flag ka ant tay nahi | `SUSPICIOUS_Flag_Avadhi` | Bekaar rok kam | §7 |
| F-33 | 5 | b | Med | 3 s ke feed atkaav par har trade turant MPP se band | H-15: pehle broker se bhav, tab bhi na mile toh MPP | Mehenge exit kam | §5, Sawal 128 |
| F-34 | 5 | c | Med | "Bahut zyada request" aur exchange OPS reject ka niyam nahi | Order Baari dheemi, entry band, exit pehle | Account rok ka khatra kam | §5 |
| F-35 | 3, 5 | c, b | Med | Din ke beech token band; Pehredaar ke token ki jaanch nahi | Entry band + alert; Pehredaar token jaanch | Andhe bot ka khatra kam | §3, §5 |
| F-36 | 5 | c | Med | Restart par adhoore Intent ka milaan aur entry rok saaf nahi | Intent Log ka har irada broker se milao; tab tak entry nahi | Bhoola order nahi | §5 |
| F-37 | 7 | a, d | Med | `IV_Thanda_Paimana` do-taraf; IV Crush ke baad shart kabhi poori nahi | Ek-taraf: daayre ke andar ya neeche | Event ke baad ke mauke wapas | §7, TAKRAAV #34 |
| F-38 | 7 | c | Med | Strike ka volume baseline strike ke naam se; moneyness/expiry badalti hai | Moneyness Khaana + bache din se baseline | Galat reject kam | §7 |
| F-39 | 7 | c | Med | Volume_Uchhal/Iceberg ki shart sirf Call ke liye likhi | Put ke liye ulti shart | Put par sahi signal | §7 |
| F-40 | 7 | c | Med | "Teeno alag Disha" ka matlab (FLAT ke saath) saaf nahi | Sab saath = GREEN, koi ulta = RED, baaki 0 | Test-yogya | §7 |
| F-41 | 7 | c | Med | Delta/IV ka tareeka (samay ki ikai, byaaj, Spot ya Futures) tay nahi | Broker greeks agar mel khaye; warna ek hi tareeka | Delta galat nahi | §7, Sawal 115 |
| F-42 | 7 | d, c | Med | Opening range, breakout candle, RV ki avadhi, pullback, "sharp" EMA, Mazboot/Kamzor breakout: number/paribhasha nahi | Naye number rows (§18) | Test-yogya | §7, §18 |
| F-43 | 8 | e | Med | Kai checks ek hi data (Disha, volume, OI) se; GREEN ginti nakli bharosa deti hai | Data Family table + `Data_Family_Max_Score_Hissa` (Ablation ke baad) | Nakli signal kam | §7, §8 |
| F-44 | 7 | b, e | Med | OI der se badalta hai par OI check ka vazan sabse bada (5) | H-11 Ablation; `OI_Bhaari_Badlaav_Paimana` | Purane data par entry kam | §7 |
| F-45 | 7, 9 | c | Low | Kai Lot par `Balance_Extra_Buffer` har Lot par ya ek baar, saaf nahi | Har Lot par | Order reject kam | §7 |
| F-46 | 11 | d | Med | "Trailing kas deta hai" ki doori nahi | `Trailing_Kasi_Doori` | Test-yogya | §11 |
| F-47 | 13 | c | Med | Dashboard band ho toh Start/Stop/Kill kaise, tay nahi | `Dashboard_Band_Hadd` ke baad naye entry band + alert | Bina control ke naya jokhim nahi | §13, Sawal 129 |
| F-48 | 15 | c | Med | Reject signal ka nateeja ek pal ke bhav se | Shadow Trade (wahi entry/exit/kharcha) | Gates ka sahi faisla | §15 |
| F-49 | 15 | c | Med | Replay ke liye raw data record ka niyam nahi | Replay Record; Backtest/Paper/Live ek hi niyam | Galti dobara dekh sakte hain | §15 |
| F-50 | 9 | d | Low | Profit Lock sirf "subah ke trades"; poore balance par lock = din band | Malik se pushti | Niyam ka asar saaf | §9, Sawal 132 |
| F-51 | 7 | d | Med | IVP ki chhoot "bade clean breakout" vague | Pehle version mein chhoot band | Mehenge IV ka nuksan kam | §7 |
| F-52 | 16 | c | Med | Paper Mode ka fill niyam tay nahi | Depth mein chal kar fill + `Paper_Deri_Model` | Paper nateeja sach ke paas | §16 |
| F-60 | 7 | c | Med | Liquidity ka "rate ka farak" kaise naapa jaaye, tay nahi | Order quantity ko depth mein chala kar | Bade order mein sahi Slippage | §7 |
| F-61 | 11 | b | Med | Exit order aadha fill ho toh kya, saaf nahi | Bacha hissa reprice; Broker Stop quantity bache Lot jitni | Aadha trade bina Stop nahi | §11 |
| F-65 | 5, 20 | r | Med | Static IP badalte hi saare token band; hafte mein ek baar | Kharab machine par wahi IP nayi machine par | DR mein token band nahi | §5, §20 |
| F-66 | 5, 20 | r | Med | Broker ka Kill Switch maujood hai (pehle position band karni padti hai) | Kill-Switch ke baad broker Kill Switch bhi | Doosri suraksha parat | §5, Sawal 138 |
| F-67 | 16, 20 | r | Med | Upstox sandbox sirf order ka dhaancha jaanchta hai, fill nahi | Bot ka apna Paper Mode | Paper nateeja bharose ka | §16, Sawal 116 |
| F-69 | 5, 20 | r | Med | Live data ke connection ek account par seemit; bot + Pehredaar milakar | Connection ki ginti pehle tay; Pehredaar zaroorat par seedha bhav maange | Data band hone ka khatra kam | §5 |
| F-70 | 3, 20 | r | Med | Upstox ka official TOTP login aa gaya; idea ka "automatic ki salah nahi" purana | Malik TOTP ya phone manzoori chune; vakil se poochna | Subah ka login bharose ka | §20, Sawal 139 |
| F-71 | 5, 20 | r | Med | "Ek order 25 baar modify" Upstox docs mein nahi mila | F-08 ka niyam ehtiyaat ke liye rakho; Upstox se poochho | — | §20 |
| F-72 | 3 (D3) | r | Med | NSE purane data ki licence mein "commercial use" ki line | Kharid se pehle NSE se likhit jawab | Galat licence se bachav | Sawal 140 |
| F-78 | 6 | a | Low | Barabari ki aakhri shart "kam Lot kharcha" malik ke "quality pehle" se takra sakti hai | Pehle zyada Delta (band ke andar), phir kam kharcha | Achha strike chuna jaaye | §6, TAKRAAV #40 |
| F-53 | 2 | c | Low | ATM, swing low, opening range, pullback jaise shabd Naam-Suchi mein nahi | 29 naye naam | Saaf PRD | §2 |
| F-54 | 2 | a | Low | Risk Limit ki paribhasha mein mahina nahi; Daily Profit Lock ke do naam; Limit Order ki paribhasha sirf entry ki | Sirf note; malik ka shabd nahi badla | — | yahi file |
| F-55 | 18 | d | Low | "Pakka" numbers range mein hain (4 se 5, 30 se 45, 15 se 30 s, 3 se 4, 25 se 30%) | Malik ek kimat chune | Ek hi niyam | Sawal 133 |
| F-56 | 18 | a | Low | `Max_Pain_Paas_Hadd` naam "hadd" ka par kimat samay ki | Sirf note | — | yahi file |
| F-57 | 7 | e | Low | Trap_Detection ka tikav band candle ke intezaar mein aksar apne aap poora | Breakout Candle family mein gino | Dohre points kam | §7 |
| F-58 | 7, 18 | r | Low | BankNifty ke banks ki ginti exchange badal sakta hai | Roz official suchi se | Breadth sahi | §7, Sawal 134 |
| F-59 | 5 | c | Low | "Fill 1 Lot se kam" F&O mein ho sakta hai ya nahi, verify nahi hua | Niyam bina nuksan ke rakho | — | yahi file |
| F-68 | 20 | r | Low | Algo Name header docs ke hisaab se sirf exchange-approved algo ke liye zaroori | Upstox se confirm | — | §20 |
| F-73 | 20 | r | Low | Sensex Lot Jan 2027 se 25 (verify nahi hua); Nifty freeze Upstox file mein 1,755 vs circular 1,800 | Roz Instrument Master se; hard-code nahi | Order reject nahi | §20 |
| F-74 | 9 | a | Low | Lot cut "aadhe" 1 Lot par nahi lagta, aur poore balance mein aksar 1 Lot hi hota hai; drawdown Lot cut asal mein kabhi nahi lagega | Vikalp A/B mein drawdown par hissa ghatana | Girawat mein risk kam | yahi file, Sawal 118 |
| F-75 | 14 | b | Low | Range Alert ke baad malik ka manual trade bot ke Foreign Position niyam se takra sakta hai (F-11) | Alert mein likho: "haath ka trade is instrument ko bot ke liye band karega" | Malik aur bot ka takraav kam | yahi file |

## (d) Vague shabd jinke number nahi (pehle version ke checks pehle)

| Shabd | Kahan | v4 mein |
|---|---|---|
| "mazboot tezi" | §4 expiry subah | `Mazboot_Breakout_Paribhasha` |
| "nayi range" | §3 bada gap | `Gap_Ke_Baad_Range_Samay` |
| "opening range" | §7 Range_Breakout, Ulta_Palat | `Opening_Range_Samay` |
| "sharp" slope | §7 EMA_Slope_Check | `EMA_Slope_Hadd` (Tay nahi) |
| "pullback" | §7 Chase_Guard | `Pullback_Paimana` |
| "ajeeb OI" | §7 Manipulation_Cash_Volume_Check | `Manipulation_Ajeeb_OI_Paimana` (Tay nahi) |
| "shant bazaar", "bhaari saude" | §7 Manipulation_Settlement_Check | `Settlement_Bhaari_Saude_Paimana` (Tay nahi) |
| "bhaari matra mein naya OI" | §7 OI_Deewar_Short_Covering_Check | `OI_Bhaari_Badlaav_Paimana` (Tay nahi) |
| "Futures discount mein phisle" | §7 Volume_Uchhal_Check | `Futures_Discount_Hadd` (Tay nahi) |
| "tezi se badhe", Term-Structure | §7 VIX_Gati_Term_Structure_Check | `VIX_Tezi_Paimana` (Tay nahi) |
| "bade clean breakout" | §7 IVP_Filter | chhoot band (F-51) |
| "kas deta hai" | §11 Exit | `Trailing_Kasi_Doori` |
| "khabar se pehle IV phool gaya" | §7 IV_Overpriced_Filter | paribhasha joda (F-42) |
| "saaf door", "tezi se" (Shadow checks) | §7 Gamma_Flip, IV_Skew, Pre_Breakout, Iceberg | Shadow Mode mein; number Ablation se pehle chahiye |

## (e) Ek hi data ko dohrate checks (Data Family)

| Data Family | Checks | Khatra |
|---|---|---|
| Disha (VWAP + EMA) | EMA_Slope, Timeframe_Match, Teeno_Index_Disha, Heavyweight, Volume_Uchhal (VWAP) | Ek trend ke 4-5 GREEN = ek saboot |
| Breakout Candle | Range_Breakout, Trap_Detection, Lambi_Wick, Chase_Guard, Squeeze, OB/BOS | Ek candle ke kai faisle |
| Volume aur raftaar | Premium_Tezi, Volume_Uchhal, Strike_Volume, Rate_Update_Gati, Iceberg, Pre_Breakout | Ek volume uchhal kai jagah ginta hai |
| OI | OI_Deewar_Doori, OI_Deewar_SC, PCR, Max_Pain, GEX, Gamma_Flip, Kharcha_Filter | OI der se aata hai; kai checks ek purane data par |
| IV | IV_Overpriced, IVP, VIX_Gati, IV_Skew, Bade_Event_Lock | IV ek hi baat kehta hai |
| Index ke stocks | Index_Breadth, Heavyweight, Manipulation_Cash_Volume | Ek suchi ki kami teeno ko maarti hai (F-02) |
| Liquidity aur kharcha | Liquidity, Kharcha, Fake_Spike | Slippage do jagah gina jaata hai |
| Dohra Gate | Premium_Range_Gate vs Delta_Filter + Balance_Ek_Lot_Gate | F-24 |

## Strategy Hypotheses (test: `03_Strategy_Edge_Plan.md`)

| ID | Ghar (v4) | Hypothesis |
|---|---|---|
| H-01 | §7 IV_Overpriced | IV/RV kam aur IVP neeche hone par Net Expectancy zyada |
| H-02 | §10 Entry | Bid-ask ke beech se shuru hone wala Limit Order Slippage ghatata hai, fill-dar `Entry_Fill_Dar_Min` se upar rehta hai |
| H-03 | §3 | Samay ke kuch khaane kharche ke baad lagatar nuksan dete hain |
| H-04 | §4 | Expiry subah current expiry ka trade kharche ke baad kamzor hai |
| H-05 | §11 | Stop-Unit ke guna par munafa lena % se behtar |
| H-06 | §11 | Cap se door stop ho toh trade skip karna behtar |
| H-07 | §11 | Theta aur bache din ke hisaab wala Time-Stop behtar |
| H-08 | §3 | Shock mein munafe wale trade ko trail karna turant exit se behtar |
| H-09 | §9 | ~~Hissa wala sizing (Vikalp A)~~ malik ne nahi maana (10 Nov 2026); test band |
| H-10 | §9 | Stop-Unit wali Risk Limit (Vikalp B) seemaon ko sach mein lagu karti hai |
| H-11 | §8 | Ablation se kuch checks bekaar niklenge; Data Family cap nakli signal ghatata hai |
| H-12 | §3 | "Trending" tag agle ghante ki ek-disha chaal ko sach mein pehchanta hai |
| H-13 | §3 | Event window se nuksan bachta hai, mauke kam nahi jaate |
| H-14 | §7 | Futures par breakout Spot se jaldi aur saaf |
| H-15 | §5 | Feed atakne par broker se bhav maangna turant MPP exit se sasta |

## Self-check (Deliverable 1)

| Check | Nateeja |
|---|---|
| Original ki har line v4 mein usi kram mein (script `scratch/d1_build/build_v4.py`) | PASS: 0 missing (sirf header ke 2 lines whitelisted: Version, Tarikh; purani kimat "purana:" ke saath maujood) |
| Instruction block bilkul same | PASS |
| Har nayi baat par `[PRASTAAVIT-CC]` tag | PASS (lint `scratch/d1_build/lint_cc.py`) |
| CC paragraph mein number sirf Numbers list, udaharan, repo, tarikh wali baatein mein | PASS (bache flag sirf naam hain: Nifty50, Stage2, "1 Lot", "0 point") |
| Koi vaakya bahut lamba nahi, koi paragraph 5 vaakya se zyada nahi | PASS (lint) |
| Idea mein tech ke naam nahi (repo section ke bahar) | PASS: TLS, SDK, API key jaise shabd technical concepts hain, kisi language/library ka naam nahi |
| Har naya naam Naam-Suchi mein | PASS (29 naye naam) |
| Takraav suljhaaye nahi, dikhaye (#26-#41 + `[PRASTAAVIT-CC HAL]`) | PASS |
| Naye sawal sabse upar, sabse zaroori pehle | PASS (Sawal 117-141) |
| Version 4.0, tarikh, Badlaav-suchi mein har badlaav ki line | PASS |
| Koi key, token, password nahi | PASS |
| "Profit pakka" / "100% safe" jaise shabd nahi | PASS |
| Cross-reference jaanch (`scratch/d1_build/xref_check.py`): har naam Numbers list ya Check Suchi mein, har F/TAKRAAV/Sawal/H ka asli entry | PASS (bache naam sirf Badlaav-suchi ke itihaas mein: purane hataye niyam, TAKRAAV #14, Sawal 24/47) |
| Numbers list: 202 rows, har row 5 column, status sirf Pakka/Andaza/Prastaavit/Tay nahi | PASS (Pakka 35, Andaza 36, Prastaavit 123, Tay nahi 8) |
| Kuch hataya? | Malik ka kuch nahi hataya. Malik ke 10 Nov 2026 ke jawab par mere 2 prastaav (Vikalp A, C) hataye, Badlaav-suchi mein likha |
