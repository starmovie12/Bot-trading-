@@AFTER_LINE | Ruka_Stock_Hadd |
| Ghadi_Skew_Sakht_Hadd `[PRASTAAVIT-CC]` | 50 milliseconds (hamesha `Data_Purana_Hadd` ke paanchve hisse se kam) `[TAKRAAV #27]` | Prastaavit | 3. Bot ka ek poora din, 7. Check Suchi | Ghadi ki galti data ki taazgi ke naap se bahut chhoti ho `[F-07]` |
| Bot_Lease_Samay `[PRASTAAVIT-CC]` | 4 second (hamesha Pehredaar ke control lene ke samay, yaani `Pehredaar_Dhadkan_Samay` guna `Pehredaar_Dhadkan_Chhoot_Ginti`, se kam) | Prastaavit | 5. Pehredaar aur Suraksha | Pehredaar ke control lene se pehle bot khud ruk jaaye `[F-05]` |
| Pehredaar_Swatantra_Milaan_Samay `[PRASTAAVIT-CC]` | 10 second | Prastaavit | 5. Pehredaar aur Suraksha | Pehredaar khud broker se bina Stop ke trade pakde `[F-16]` |
| Pehredaar_Token_Jaanch_Samay `[PRASTAAVIT-CC]` | 60 second | Prastaavit | 5. Pehredaar aur Suraksha | Pehredaar ka token kharab ho toh jaldi pata chale `[F-35]` |
| Broker_Stop_Min_Khiskaav `[PRASTAAVIT-CC]` | Premium ATR ka 0.5 guna, par kam se kam 2 Tick Size | Prastaavit | 5. Pehredaar aur Suraksha, 11. Exit | Har chhote khiskaav par Broker Stop badal kar broker ki modify seema na khatam ho `[F-08]` |
| Broker_Stop_Modify_Bajat `[PRASTAAVIT-CC]` | Broker ki ek order ki din ki modify seema ka 80 percent (seema: Tarikh wali baatein) | Prastaavit | 5. Pehredaar aur Suraksha | Seema se pehle cancel aur naya Broker Stop `[F-08]` |
| Feed_Stale_REST_Gati `[PRASTAAVIT-CC]` | Har 1 second, broker ki request seema ke andar | Prastaavit | 5. Pehredaar aur Suraksha | Feed atakne par broker se bhav maangne ki raftaar (H-15) `[F-33]` |
| Command_Max_Umar `[PRASTAAVIT-CC]` | 5 second | Prastaavit | 13. Dashboard | Purana ya dohraya Dashboard hukm na maana jaaye `[F-17]` |
| Dashboard_Band_Hadd `[PRASTAAVIT-CC]` | 60 second | Prastaavit | 13. Dashboard | Dashboard se judaav toote toh naye entry band `[F-47]` |
| Liquidity_Exit_Tikav_Samay `[PRASTAAVIT-CC]` | 10 second | Prastaavit | 3. Bot ka ek poora din | Pal bhar ke chaude spread par exit na ho `[F-29]` |
| Opening_Range_Samay `[PRASTAAVIT-CC]` | 9:15 se 9:30 (`Shuruaati_Dekhne_Ka_Samay` ke barabar) | Prastaavit | 2. Naam-Suchi, 3. Bot ka ek poora din, 7. Check Suchi | Opening Range ki ek hi lambai `[F-42]` |
| Gap_Ke_Baad_Range_Samay `[PRASTAAVIT-CC]` | 30 minute (9:15 se 9:45) | Prastaavit | 3. Bot ka ek poora din, 7. Check Suchi | Bade gap ke baad nayi range ki paribhasha `[F-25]` |
| Breakout_Candle_Timeframe `[PRASTAAVIT-CC]` | `Chart_Chhota_Timeframe` (3 minute) | Prastaavit | 2. Naam-Suchi, 7. Check Suchi | Saare breakout checks ek hi candle dekhein `[F-42]` |
| Realized_Volatility_Avadhi `[PRASTAAVIT-CC]` | Pichle 20 trading din (Backtest se pakka karna) | Prastaavit | 7. Check Suchi | IV ki tulna wali Realized Volatility ki avadhi `[F-42]` |
| Mazboot_Breakout_Paribhasha `[PRASTAAVIT-CC]` | Breakout Candle par Futures volume `Volume_Uchhal_Guna` ya zyada, aur agli OI Deewar `OI_Deewar_Stop_Guna` se door; baaki Kamzor Breakout | Prastaavit | 2. Naam-Suchi, 4. Expiry ke din ke niyam, 7. Check Suchi | Mazboot aur Kamzor Breakout ka saaf farak `[F-30]` `[F-42]` |
| Pullback_Paimana `[PRASTAAVIT-CC]` | Premium breakout ke baad ke sabse oonche bhav se kam se kam 0.5 premium-ATR neeche aaye, phir breakout disha mein ek band candle bane | Prastaavit | 2. Naam-Suchi, 7. Check Suchi | Chase_Guard ke pullback ka paimana `[F-42]` |
| Swing_Pushti_Candle_Ginti `[PRASTAAVIT-CC]` | Dono taraf 2 band candle | Prastaavit | 2. Naam-Suchi, 11. Exit | Swing Low aur Swing High ki pushti `[F-22]` |
| EMA_Slope_Hadd `[PRASTAAVIT-CC]` | Tay nahi (Backtest se tay ho; tab tak check Shadow Mode mein) | Tay nahi | 7. Check Suchi | "Sharp" slope ka number `[F-42]` |
| Futures_Discount_Hadd `[PRASTAAVIT-CC]` | Tay nahi | Tay nahi | 7. Check Suchi | "Futures discount mein phisalna" ka number `[F-39]` |
| Manipulation_Ajeeb_OI_Paimana `[PRASTAAVIT-CC]` | Tay nahi | Tay nahi | 7. Check Suchi | "Ajeeb OI" ka number |
| Settlement_Bhaari_Saude_Paimana `[PRASTAAVIT-CC]` | Tay nahi | Tay nahi | 7. Check Suchi | "Shant bazaar" aur "bhaari saude" ka number |
| OI_Bhaari_Badlaav_Paimana `[PRASTAAVIT-CC]` | Tay nahi | Tay nahi | 7. Check Suchi | "Bhaari matra mein naya OI" ka number `[F-44]` |
| VIX_Tezi_Paimana `[PRASTAAVIT-CC]` | Tay nahi | Tay nahi | 7. Check Suchi | VIX "tezi se badhe" aur Term-Structure ki shart ka number |
| SUSPICIOUS_Flag_Avadhi `[PRASTAAVIT-CC]` | Us index mein us trading din ke ant tak | Prastaavit | 4. Expiry ke din ke niyam, 7. Check Suchi | SUSPICIOUS flag ka ant tay ho `[F-32]` |
| Trailing_Kasi_Doori `[PRASTAAVIT-CC]` | Premium ke sabse oonche bhav se 0.5 ATR neeche | Prastaavit | 11. Exit | 1 Lot par "Trailing Stop-Loss kasna" ki doori `[F-46]` |
| Stop_Pushti_Ginti `[PRASTAAVIT-CC]` | Lagatar 2 depth updates | Prastaavit | 11. Exit | Ek galat bhav par Stop-Loss na chale `[F-21]` |
| Worst_Case_Nuksan_Guna `[PRASTAAVIT-CC]` | Entry premium ka 40 percent (Andaza; Stage2 ke asli gap-fill se sudhaar) | Prastaavit | 9. Risk aur Lot ginti | Risk ke hisaab mein ek trade ka sabse bura nuksan `[F-15]` |
| Fractional_Stake_Hissa `[PRASTAAVIT-CC]` | Vikalp A: Deposit-Adjusted Equity ka 25 percent, aur Backtest ke Kelly Hissa ke aadhe se zyada nahi | Prastaavit | 9. Risk aur Lot ginti | Poore balance ki jagah hisse wala vikalp (H-09) `[F-03]` |
| Stop_Unit_Din_Seema `[PRASTAAVIT-CC]` | Vikalp B: 1 Stop-Unit | Prastaavit | 9. Risk aur Lot ginti | Din ki seema ek Stop-Loss ke size se mel khaye (H-10) `[F-03]` |
| Stop_Unit_Hafta_Seema `[PRASTAAVIT-CC]` | Vikalp B: 2 Stop-Unit | Prastaavit | 9. Risk aur Lot ginti | Hafte ki seema Stop-Unit mein `[F-03]` |
| Stop_Unit_Mahina_Seema `[PRASTAAVIT-CC]` | Vikalp B: 4 Stop-Unit | Prastaavit | 9. Risk aur Lot ginti | Mahine ki seema Stop-Unit mein `[F-03]` |
| Prati_Trade_Max_Nuksan_Rupaye `[PRASTAAVIT-CC]` | Vikalp C: Tay nahi (malik rupaye mein tay kare) | Tay nahi | 9. Risk aur Lot ginti | Ek trade ka zyada se zyada Worst-Case Nuksan `[F-03]` |
| Data_Family_Max_Score_Hissa `[PRASTAAVIT-CC]` | Us waqt ke zaroori score ka 40 percent (sirf Ablation ke baad lagu) | Prastaavit | 8. Score, Gate aur Confidence ka hisaab | Ek hi data ke checks nakli bharosa na dein (H-11) `[F-43]` |
| Shadow_Se_Active_Min_Signal `[PRASTAAVIT-CC]` | 100 signal | Prastaavit | 15. Report, Record aur Niyam badalna | Shadow Mode se Active hone se pehle kam se kam data |
| Entry_Fill_Dar_Min `[PRASTAAVIT-CC]` | 80 percent | Prastaavit | 10. Entry | Spread-aware entry ka fill kitna ho toh theek (H-02) |
| Backtest_Min_Avadhi `[PRASTAAVIT-CC]` | 18 mahine Walk-Forward; aakhri 6 mahine Out-of-Sample (expiry weekday badalne wale dino ka alag nateeja) | Prastaavit | 16. Test aur Live par jaane ka plan | Backtest kitne lambe data par ho `[F-19]` |
| Backtest_Min_Trade_Ginti `[PRASTAAVIT-CC]` | Kul 300 trade, jismein Out-of-Sample mein kam se kam 100 | Prastaavit | 16. Test aur Live par jaane ka plan | Kam trade par kismat aur hunar alag nahi dikhte `[F-19]` |
| Expectancy_CI_Star `[PRASTAAVIT-CC]` | Out-of-Sample Net Expectancy ka ek-taraf 95 percent nichla Confidence Interval 0 se upar | Prastaavit | 16. Test aur Live par jaane ka plan | Ausat nahi, bharose ka daayra positive ho `[F-19]` |
| Profit_Factor_Min `[PRASTAAVIT-CC]` | Kharche ke baad 1.3 | Prastaavit | 16. Test aur Live par jaane ka plan | Munafa nuksan se saaf bada ho |
| Parameter_Stability_Paimana `[PRASTAAVIT-CC]` | Har mukhya number ko 20 percent upar-neeche karne par bhi Out-of-Sample Net Expectancy 0 se upar | Prastaavit | 16. Test aur Live par jaane ka plan | Ek hi number par tika nateeja kismat ho sakta hai |
| Paper_Gate_CC `[PRASTAAVIT-CC]` | Kam se kam 40 trading din aur 60 trade; Net Expectancy Backtest ke 90 percent daayre ke andar; koi Critical niyam nahi toota `[TAKRAAV #35]` | Prastaavit | 16. Test aur Live par jaane ka plan | Paper Stage ka data-based paimana `[F-19]` |
| Stage2_Gate_CC `[PRASTAAVIT-CC]` | Kam se kam 60 asli trade; asli Net Expectancy ka ek-taraf 90 percent nichla Confidence Interval 0 se upar; 120 trade tak sabit na ho toh ruk kar dobara design `[TAKRAAV #35]` | Prastaavit | 16. Test aur Live par jaane ka plan | Stage2 ka data-based paimana `[F-19]` |
| Stage_Override_Max_Lot `[PRASTAAVIT-CC]` | `Test_Stage2_Live_Lot` | Prastaavit | 16. Test aur Live par jaane ka plan | Override mein bhi chhota hi jokhim `[F-18]` |
| Live_Kill_Paimana `[PRASTAAVIT-CC]` | Koi ek: Deposit-Adjusted girawat Backtest ki 95 percent wali sabse buri girawat ke 1.5 guna se zyada; pichle 30 trade ki Net Expectancy Backtest ke 5 percent wale nichle daayre se neeche; pichle 20 trade ka median Slippage model ke 2 guna se zyada; koi bhi Critical niyam toota | Prastaavit | 16. Test aur Live par jaane ka plan | Live band karne ki saaf kasauti |
| Paper_Deri_Model `[PRASTAAVIT-CC]` | Stage2 mein naapi order-se-fill deri ka median; tab tak 300 milliseconds (Andaza) | Prastaavit | 16. Test aur Live par jaane ka plan | Paper fill asli se achha na dikhe `[F-52]` |
@@AFTER_LINE | Breadth_Kul_Stocks_Ginti |
| Breadth_Top_Stocks_Ginti `[PRASTAAVIT-CC]` | Index ki official suchi ke saare banks | Vazan mein top 10 stocks (har mahine official index page se) | Vazan mein top 10 stocks (har mahine official index page se) | Prastaavit | Nifty50 aur Sensex ka Index_Breadth_Check Gate bina suchi ke hamesha RED na ho `[F-02]` |
@@BEFORE_LINE ### Malik ki pushti ki suchi (prastaavit jawab, haan ya nahi)
### [PRASTAAVIT-CC] Naye sawal (10 Nov 2026), sabse zaroori upar

Yeh sawal 10 Nov 2026 ke audit se aaye hain (dekho: `01b_Audit_Findings.md`). Purane sawal dobara nahi likhe; jahan purana sawal ab zyada zaroori hai, wahan sirf uska number likha hai.

- Sawal 117 (Pehredaar ka haq): kya Pehredaar ka alag Upstox app bot ke app ke order cancel aur position band kar sakta hai? Kyun zaroori: poora Pehredaar isi par tika hai; Real Money Mode se pehle asli test chahiye `[F-06]`.
- Sawal 118 (Lot ka niyam): poora balance wala niyam rakhna hai ya Vikalp A, B ya C? Kyun zaroori: abhi ek Stop-Loss se din, hafte aur mahine ki teeno seemayein toot-ti hain `[F-03]`.
- Sawal 119 (NA ke do roop): NA-Data aur NA-Lagu-Nahi manzoor? Kyun zaroori: iske bina aam din par manipulation Gates har trade rokte hain `[F-01]`.
- Sawal 16 ab Critical hai: Nifty50 aur Sensex ki stocks suchi ke bina Index_Breadth_Check Gate un index ko band rakhta hai. Jawab tak `Breadth_Top_Stocks_Ginti` wala prastaav aur sirf Paper Mode `[F-02]`.
- Sawal 120 (Kill Latch): Kill-Switch ke baad us din bot band, aur agle din Start Control se hi khule? Kyun zaroori: abhi Kill-Switch ke baad bot phir entry le sakta hai `[F-04]`.
- Sawal 121 (Lease): Pehredaar ke control lene par us din bot broker ko koi hukm na bheje? Kyun zaroori: dono ek saath chale toh net short ho sakta hai `[F-05]`.
- Sawal 122 (Real Money ka taala): Backtest Gate pass hone tak Real Money Mode band, aur Stage Override sirf `Stage_Override_Max_Lot`? Kyun zaroori: abhi parakh ek click se chhoot sakti hai `[F-18]`.
- Sawal 123 (Stage ke paimane): `Backtest_Min_Avadhi`, `Paper_Gate_CC`, `Stage2_Gate_CC` aur `Live_Kill_Paimana` manzoor? Kyun zaroori: abhi ke paimane kismat aur hunar ko alag nahi karte `[F-19]`.
- Sawal 124 (stop ka chunav): ATR aur swing low mein se door wala stop, aur cap se door ho toh trade skip (H-06) ya cap par stop? Kyun zaroori: yeh har trade ka nuksan tay karta hai `[F-22]`.
- Sawal 125 (stop ka bhav): bot ka Stop-Loss best bid par `Stop_Pushti_Ginti` ke saath chale? Kyun zaroori: galat bhav par stop chalna seedha nuksan hai `[F-21]`.
- Sawal 126 (haath ka trade): Foreign Position wale instrument mein bot trade na kare? Kyun zaroori: warna bot malik ke Lot bech sakta hai `[F-11]`.
- Sawal 127 (din ki seema): naye entry se pehle khule trade ka Worst-Case Nuksan bhi din ki seema mein gina jaaye? Kyun zaroori: warna do trade milkar seema tod dete hain `[F-14]`.
- Sawal 128 (feed atakna): `Blind_Position_Hadd` par pehle broker se bhav maang kar chalna (H-15), ya turant MPP exit? Kyun zaroori: chhote atkaav par mehenga exit bachta hai `[F-33]`.
- Sawal 129 (aapat rasta): Dashboard band ho toh Kill-Switch ka doosra rasta kya ho? Kyun zaroori: abhi sirf Upstox app bachta hai `[F-47]`.
- Sawal 130 (range ka kaam): `Target_Premium_Range` sirf paise ki seema hai ya malik ki premium pasand bhi? Kyun zaroori: isi se Premium_Range_Gate aur Range Alert ka matlab tay hota hai `[F-24]`.
- Sawal 131 (expiry subah): expiry ki subah Kamzor Breakout par koi trade nahi, ya agli expiry? Kyun zaroori: abhi niyam chup hai `[F-30]`.
- Sawal 132 (Profit Lock): dopahar ki kamai par bhi Daily Profit Lock lage? Kyun zaroori: niyam mein sirf "subah ke trades" likha hai `[F-50]`.
- Sawal 133 (range wale Pakka numbers): `Aas_Paas_Strikes_Ginti`, `Chart_Range_Breakout_Samay`, `Mazboot_Breakout_Tikav_Samay`, `Kamzor_Breakout_Tikav_Samay`, `Daily_Max_Auto_Entries` aur `Premium_Max_Stop_Loss_Percent` mein se har ek ki ek hi kimat kya ho? Kyun zaroori: code ek hi number par chalta hai `[F-55]`.
- Sawal 134 (BankNifty ki suchi): BankNifty ke banks ki ginti index ki official suchi se roz li jaaye? Kyun zaroori: exchange ginti badal sakta hai `[F-58]`.
- Sawal 135 (data kharid): Backtest ke liye kaunsa purana data aur kitne budget mein kharidna hai (dekho: `03_Strategy_Edge_Plan.md`)? Kyun zaroori: data ki quality niyam se zyada nateeja badalti hai.
@@AFTER_LINE - **[TAKRAAV #25]
- **[TAKRAAV #26] `[PRASTAAVIT-CC]` Gate ka NA RED banam sirf expiry din wale manipulation Gates:** Aam din par Manipulation_Cash_Volume_Check aur Manipulation_Settlement_Check lagu nahi, isliye NA aur RED hokar har trade rokte hain. `[PRASTAAVIT-CC HAL]` NA ke do roop: NA-Data (Gate RED) aur NA-Lagu-Nahi (Gate par asar nahi) `[F-01]`.
- **[TAKRAAV #27] `[PRASTAAVIT-CC]` `Ghadi_Skew_Hadd` banam `Data_Purana_Hadd`:** Ghadi ki chhoot data ki taazgi ki seema jitni badi hai. `[PRASTAAVIT-CC HAL]` `Ghadi_Skew_Sakht_Hadd` aur data ki umar apne paane ke samay se bhi `[F-07]`.
- **[TAKRAAV #28] `[PRASTAAVIT-CC]` Poore balance ka Lot banam hafte aur mahine ki Risk Limit:** Ek Stop-Loss `Monthly_Loss_Risk_Limit` se bhi bada ho sakta hai, isliye pehle nuksan par bot mahine bhar rukta hai. `[PRASTAAVIT-CC HAL]` malik Vikalp A, B ya C chune; tab tak Monte Carlo ka nateeja malik ko dikhe `[F-03]`.
- **[TAKRAAV #29] `[PRASTAAVIT-CC]` Kill-Switch "sab kuch rokta hai" banam hukm sirf Pehredaar ko:** Bot ko Kill-Switch ka pata nahi chalta. `[PRASTAAVIT-CC HAL]` Kill Latch jise bot aur Pehredaar dono padhte hain `[F-04]`.
- **[TAKRAAV #30] `[PRASTAAVIT-CC]` `Trailing_Stop_Doori` banam `ATR_Stop_Guna`:** Trailing ki doori pehle stop se chhoti hai aur shuru hone ka samay likha nahi. `[PRASTAAVIT-CC HAL]` trailing breakeven ke baad shuru `[F-20]`.
- **[TAKRAAV #31] `[PRASTAAVIT-CC]` Har khiskaav par Broker Stop badalna banam broker ki din ki modify seema:** `[PRASTAAVIT-CC HAL]` `Broker_Stop_Min_Khiskaav` aur `Broker_Stop_Modify_Bajat` `[F-08]`.
- **[TAKRAAV #32] `[PRASTAAVIT-CC]` Index_Breadth_Check ka Gate banam Nifty50 aur Sensex ki suchi Tay nahi:** `[PRASTAAVIT-CC HAL]` `Breadth_Top_Stocks_Ginti`; tab tak Nifty50 aur Sensex sirf Paper Mode `[F-02]`.
- **[TAKRAAV #33] `[PRASTAAVIT-CC]` Premium_Range_Gate banam Delta_Filter aur Balance_Ek_Lot_Gate:** Range unhi do se banti hai, isliye Gate dohraav hai aur purani range sahi strike rok sakti hai. `[PRASTAAVIT-CC HAL]` range har evaluation par bane; Range Alert ka matlab "paisa kam" `[F-24]`.
- **[TAKRAAV #34] `[PRASTAAVIT-CC]` `IV_Thanda_Paimana` banam IV Crush:** IV gir kar pehle se neeche aaye toh shart kabhi poori nahi hoti. `[PRASTAAVIT-CC HAL]` shart ek-taraf: IV daayre ke andar ya neeche `[F-37]`.
- **[TAKRAAV #35] `[PRASTAAVIT-CC]` 9 Nov ke Stage numbers aur Stage Override banam CC ke data-based Stage Gates:** `Paper_Mode_Avadhi`, `Paper_Mode_Trade_Ginti` aur `Stage2_Avadhi` chhote hain, aur Override se parakh chhoot sakti hai `[TAKRAAV #12]`. `[PRASTAAVIT-CC HAL]` `Paper_Gate_CC`, `Stage2_Gate_CC` aur Backtest Gate se pehle Real Money band `[F-18]` `[F-19]`.
@@AFTER_LINE ## 21. Badlaav-suchi

- **10 Nov 2026 (Version 3.1 → 4.0) `[PRASTAAVIT-CC]`:** Claude Code ne poori file ka section-wise audit kiya. Malik ka ek bhi purana shabd nahi badla ya hataya; har nayi baat `[PRASTAAVIT-CC]` tag ke saath, status Prastaavit. Original file ka sha256 `c8770e6791923dcb9f03786371a3dbe9ae91a92f00164f90fc982239df0dabb1` hai. Neeche har badlaav ki ek line hai.
- 4.0: Header mein Version 3.1 → 4.0, Tarikh 9 Nov → 10 Nov 2026, aur "Version 4.0 ka saar" joda.
- 4.0: Daayra mein Net Expectancy wala lakshya aur "kya nahi karega" ke 3 naye bindu jode.
- 4.0: Naam-Suchi mein 29 naye naam jode (`[PRASTAAVIT-CC]`, Audit bindu, Hypothesis, ATM, Moneyness Khaana, Opening Range, Swing Low/High, Pullback, Mazboot/Kamzor Breakout, Breakout Candle, NA-Data, NA-Lagu-Nahi, Lease, Kill Latch, Khula Trade, Stop-Unit, Worst-Case Nuksan, Net Expectancy, Confidence Interval, Profit Factor, Risk of Ruin, Kelly Hissa, Walk-Forward/Out-of-Sample, Ablation, Data Family, Shadow Trade, Replay Record, Monte Carlo).
- 4.0: F-01 (Critical) NA ke do roop, Section 6 aur dono manipulation checks mein; `[TAKRAAV #26]`.
- 4.0: F-02 (Critical) Nifty50/Sensex ki suchi ke bina Breadth Gate; `Breadth_Top_Stocks_Ginti`; `[TAKRAAV #32]`; Sawal 16 Critical.
- 4.0: F-03 (Critical) poore balance ka Lot banam Risk Limit; Vikalp A/B/C, H-09, H-10; `[TAKRAAV #28]`; Sawal 118.
- 4.0: F-04 (Critical) Kill Latch; `[TAKRAAV #29]`; Sawal 120.
- 4.0: F-05 (Critical) Lease aur "Pehredaar ne control liya" nishan; `Bot_Lease_Samay`; Sawal 121.
- 4.0: F-06 (Critical) Pehredaar ke app ka haq verify karna; Sawal 117.
- 4.0: F-07 (High) ghadi banam data ki taazgi; `Ghadi_Skew_Sakht_Hadd`; `[TAKRAAV #27]`.
- 4.0: F-08 (High) Broker Stop ki modify seema; `Broker_Stop_Min_Khiskaav`, `Broker_Stop_Modify_Bajat`; `[TAKRAAV #31]`.
- 4.0: F-09 (High) Broker Stop aadha fill par exit ki quantity broker se.
- 4.0: F-10 (High) entry kabhi bina pushti dobara nahi; Order Tag kabhi dohraya nahi.
- 4.0: F-11 (High) Foreign Position wale instrument mein bot trade nahi; Sawal 126.
- 4.0: F-12 (High) expiry shift par exit fill ke baad hi entry.
- 4.0: F-13 (High) Khula Trade ki paribhasha mein pending order.
- 4.0: F-14 (High) din ki seema mein khule trade ka Worst-Case Nuksan; Sawal 127.
- 4.0: F-15 (High) Worst-Case Nuksan aur `Worst_Case_Nuksan_Guna`.
- 4.0: F-16 (High) Pehredaar ki haalat wali dhadkan, apna milaan, apna alert rasta.
- 4.0: F-17 (High) Dashboard hukm ki suraksha; `Command_Max_Umar`.
- 4.0: F-18 (High) Backtest Gate se pehle Real Money band; `Stage_Override_Max_Lot`; `[TAKRAAV #35]`; Sawal 122.
- 4.0: F-19 (High) Confidence Interval wale Stage Gates aur `Live_Kill_Paimana`; Sawal 123.
- 4.0: F-20 (High) trailing breakeven ke baad; `[TAKRAAV #30]`.
- 4.0: F-21 (High) Stop-Loss best bid par; `Stop_Pushti_Ginti`; Sawal 125.
- 4.0: F-22 (High) do stop mein se chunav; H-06; Sawal 124.
- 4.0: F-23 se F-61 (Med/Low) apne sections mein jode: Start ke paise, gap ki range, mausam ka badlaav, ADX ki deri (H-12), Shock exit (H-08), liquidity exit, token band, expiry subah, bada daon, SUSPICIOUS ki avadhi, feed atakna (H-15), reject suchi, restart milaan, IV thanda, strike volume baseline, Put ke ulte niyam, Teeno Disha, greeks ke tareeke, vague paimane, Data Family (H-11), OI ki deri, Lot ka buffer, trailing kasna, Dashboard band, Shadow Trade, Replay Record, Profit Lock, IVP chhoot, Paper fill, BankNifty suchi, liquidity naap, exit aadha fill.
- 4.0: Section 7 mein Data Family table joda (Check Suchi ki table nahi badli).
- 4.0: Section 12 mein doosra nakli udaharan (galti wala din) joda; pehla udaharan waisa hi hai.
- 4.0: Section 18 mein 44 naye number rows aur Teeno Index table mein 1 row; sab `[PRASTAAVIT-CC]`, status Prastaavit ya Tay nahi.
- 4.0: Section 19 mein Sawal 117 se 135 aur `[TAKRAAV #26]` se `[TAKRAAV #35]` jode.
- 4.0: Strategy Hypothesis H-01 se H-15 apne ghar mein jode; test `03_Strategy_Edge_Plan.md` mein.
