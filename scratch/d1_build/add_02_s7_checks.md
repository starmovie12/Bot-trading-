@@BEFORE_LINE ### Din_Ka_Mausam_Gate
`[PRASTAAVIT-CC]` `[F-43 | Med]` Neeche ki table batati hai ki kaun se checks ek hi Data Family ke hain. Ek family ke checks aksar ek saath GREEN ya RED hote hain, isliye unke points alag saboot nahi hain. Yeh table Check Suchi ki upar wali table ko nahi badalti; sirf Ablation aur `Data_Family_Max_Score_Hissa` ke liye hai (dekho: Score, Gate aur Confidence ka hisaab).

| Data Family `[PRASTAAVIT-CC]` | Checks |
| :--- | :--- |
| Disha (VWAP aur EMA) | EMA_Slope_Check, Timeframe_Match_Check, Teeno_Index_Disha_Check, Heavyweight_Stocks_Check, Volume_Uchhal_Check (VWAP wala hissa) |
| Breakout Candle | Range_Breakout_Check, Trap_Detection_Check, Lambi_Wick_Check, Chase_Guard, Volatility_Squeeze_Check, Order_Block_BOS_CHoCH_FVG_Check |
| Volume aur raftaar | Premium_Tezi_Check, Volume_Uchhal_Check, Strike_Volume_Filter, Rate_Update_Gati_Check, Iceberg_Order_Check, Pre_Breakout_Alert_Check |
| OI | OI_Deewar_Doori_Gate, OI_Deewar_Short_Covering_Check, PCR_Trend_Check, Max_Pain_Shift_Check, GEX_Positioning_Check, Gamma_Flip_Check, Kharcha_Filter (deewar ki doori) |
| IV | IV_Overpriced_Filter, IVP_Filter, VIX_Gati_Term_Structure_Check, IV_Skew_Check, Bade_Event_Lock (IV thanda) |
| Index ke stocks | Index_Breadth_Check, Heavyweight_Stocks_Check, Manipulation_Cash_Volume_Check |
| Liquidity aur kharcha | Liquidity_Filter, Kharcha_Filter, Fake_Spike_Filter |
@@AFTER_BLOCK ### Din_Ka_Mausam_Gate
`[PRASTAAVIT-CC]` `[F-42 | Med]` "Opening range" ki lambai `Opening_Range_Samay` hai. Bade gap ke baad nayi range `Gap_Ke_Baad_Range_Samay` se banti hai (dekho: Bot ka ek poora din). Wajah: range ki lambai tay na ho toh har baar alag nateeja aayega.
@@AFTER_BLOCK ### Bade_Event_Lock
`[PRASTAAVIT-CC]` `[F-37 | Med]` `[TAKRAAV #34]` Dikkat: `IV_Thanda_Paimana` kehta hai ki IV khabar se pehle ke level ke paas aaye. Par khabar ke baad IV aksar pehle se bhi neeche gir jaata hai (IV Crush). Tab yeh shart kabhi poori nahi hogi aur lock din bhar rahega. Agar khabar ke baad IV khabar se pehle ke level ke `IV_Thanda_Paimana` wale daayre ke andar ho ya usse neeche ho, toh IV thanda maana jaaye. Wajah: IV ka girna khareedne wale ke liye theek hai; khatra uska upar rehna hai.
@@AFTER_BLOCK ### Delta_Filter
`[PRASTAAVIT-CC]` `[F-41 | Med]` Dikkat: Delta aur IV nikalne ki baatein tay nahi: expiry tak ka samay kis ikai mein (din ya trading minute), byaaj dar kitni, aur underlying Spot hai ya Futures. Expiry din par samay ki ikai se Delta bahut badal jaata hai. Agar broker ka greeks data Paper Stage mein apne hisaab se mel khaye, toh wahi liya jaaye; warna ek hi tareeka Delta_Filter aur teeno IV checks mein lage (Sawal 115). Wajah: ek hi strike ka Delta do jagah alag na nikle.
@@AFTER_BLOCK ### Premium_Range_Gate
`[PRASTAAVIT-CC]` `[F-24 | Med]` `[TAKRAAV #33]` Dikkat: `Target_Premium_Range` Delta band ke strikes aur free paise se banta hai. Isliye yeh Gate zyada tar Delta_Filter aur Balance_Ek_Lot_Gate ko hi dohrata hai. Range sirf `Mausam_Dobara_Jaanch_Samay` par banti hai, isliye beech mein bhav khiskne par purani range sahi strike ko rok sakti hai. Agar range ka kaam sirf paise ki seema hai, toh range har evaluation par taaze bhav se bane, aur Range Alert ka matlab ho "signal pass hua par paisa kam" (Sawal 130). Wajah: ek hi data se do Gate bina naye fayde ke trade na rokein.
@@AFTER_BLOCK ### Balance_Ek_Lot_Gate
`[PRASTAAVIT-CC]` `[F-45 | Low]` Dikkat: kai Lot lene par `Balance_Extra_Buffer` har Lot par lagega ya ek baar, yeh saaf nahi. Agar bot kai Lot le, toh un sab Lot ka kharcha aur har Lot ka `Balance_Extra_Buffer` dono free paise ke andar hon; warna Lot ek-ek karke ghatein. Wajah: kharche ke baad order reject na ho.
@@AFTER_BLOCK ### IV_Overpriced_Filter
`[PRASTAAVIT-CC]` `[F-42 | Med]` Realized Volatility `Realized_Volatility_Avadhi` ki avadhi se nikalti hai. "Khabar se pehle IV phool gaya" ka matlab hai: Bade_Event_Lock ki khabar se pehle ke din IV `IV_Overpriced_Hadd` se upar ho. Wajah: avadhi tay na ho toh yeh check har baar alag nateeja dega.

`[PRASTAAVIT-CC]` Hypothesis H-01: jab IV aur Realized Volatility ka anupaat kam ho aur IVP neeche ho, tab entry ki Net Expectancy zyada hoti hai. Test: Backtest mein trades ko IV-RV anupaat ke khaanon mein baant kar Net Expectancy milao. Wajah: sasta premium khareedna theta aur IV Crush ka nuksan ghatata hai.
@@AFTER_BLOCK ### IVP_Filter
`[PRASTAAVIT-CC]` `[F-51 | Med]` Dikkat: "Shock Mode ke baad bade clean breakout" wali chhoot ka koi paimana nahi hai. Agar malik yeh paimana tay na kare, toh pehle version mein yeh chhoot band rahe aur IVP `IVP_Mehenga_Hadd` se upar hone par Gate RED hi rahe. Wajah: vague chhoot se mehenge IV mein trade ho sakta hai. Asar: kuch bade din chhoot sakte hain, par IV Crush ka nuksan bachta hai.
@@AFTER_BLOCK ### Liquidity_Filter
`[PRASTAAVIT-CC]` `[F-60 | Med]` Dikkat: "rate ka farak" kaise naapa jaaye, yeh saaf nahi: sirf bid-ask farak se ya poore order ki quantity ko depth mein chala kar. Agar order ki quantity top level ki quantity se zyada ho, toh Slippage depth ke levels mein chal kar naapa jaaye: khareedte waqt ask taraf, bechte waqt bid taraf. Wajah: bade order mein top level ka bhav dhokha deta hai.
@@AFTER_BLOCK ### Strike_Volume_Filter
`[PRASTAAVIT-CC]` `[F-38 | Med]` Dikkat: kisi strike ka pichle dinon ka volume uske aaj ke haal se mel nahi khaata. Har din strike ki ATM se doori aur expiry tak ke bache din badal jaate hain. Agar volume ka average banana ho, toh woh usi Moneyness Khaane aur usi tarah ke bache dinon wale strike ke volume se bane, strike ke naam se nahi. Wajah: galat average se asli volume wala strike bhi RED ho sakta hai.
@@AFTER_BLOCK ### Chase_Guard
`[PRASTAAVIT-CC]` `[F-42 | Med]` "Pullback dekar chale" ka paimana `Pullback_Paimana` hai (dekho: Naam-Suchi, Pullback). Wajah: bina paimane ke yeh shart har baar alag padhi jaayegi.
@@AFTER_BLOCK ### Manipulation_Cash_Volume_Check
`[PRASTAAVIT-CC]` `[F-01 | Critical]` Yeh check sirf expiry din aur `Manipulation_Check1_Samay` mein lagu hai; baaki samay yeh NA-Lagu-Nahi hai (dekho: Faisle ka raasta). `[F-02 | Critical]` Nifty50 aur Sensex ke stocks ki suchi tay hone tak un index ke expiry din yeh check NA-Data hoga aur Gate RED karega (Sawal 16). "Ajeeb OI" ka paimana tay nahi hai (`Manipulation_Ajeeb_OI_Paimana`). Wajah: vague shart par Gate ka faisla har baar alag hoga.
@@AFTER_BLOCK ### Manipulation_Settlement_Check
`[PRASTAAVIT-CC]` `[F-01 | Critical]` Yeh check sirf expiry din `Settlement_Manipulation_Check_Samay` ke baad lagu hai; usse pehle yeh NA-Lagu-Nahi hai. "Shant bazaar" aur "bhaari saude" ka paimana tay nahi (`Settlement_Bhaari_Saude_Paimana`). `[F-32 | Med]` SUSPICIOUS flag us index mein `SUSPICIOUS_Flag_Avadhi` tak rehta hai. Wajah: flag ka ant tay na ho toh agle din ka trade bhi bina wajah ruk sakta hai.
@@AFTER_BLOCK ### Lambi_Wick_Check
`[PRASTAAVIT-CC]` `[F-42 | Med]` Breakout Candle `Breakout_Candle_Timeframe` ki hoti hai. Yahi candle Range_Breakout_Check, Chase_Guard aur Trap_Detection_Check mein bhi maani jaati hai. Wajah: chaaron check ek hi candle dekhein, warna aapas mein takraayenge.
@@AFTER_BLOCK ### Tick_Heartbeat_Check
`[PRASTAAVIT-CC]` `[F-07 | High]` Data ki umar do tarah se naapi jaaye: exchange ki chhap se, aur bot ke apne data paane ke samay se. Agar dono mein se koi bhi `Data_Purana_Hadd` se purana ho, toh RED. Ghadi ki jaanch `Ghadi_Skew_Sakht_Hadd` se ho (dekho: Bot ka ek poora din). Wajah: ghadi ki galti data ki taazgi ka naap bigaad deti hai.
@@AFTER_BLOCK ### Volume_Uchhal_Check
`[PRASTAAVIT-CC]` `[F-39 | Med]` Dikkat: GREEN aur RED ki shart sirf Call ke hisaab se likhi hai. Agar trade Put ka ho, toh shartein ulti padhi jaayein: bhav VWAP se neeche ho aur Futures premium mein na uchhle. Yahi ulta niyam Iceberg_Order_Check par bhi lage. "Futures discount mein phisalna" ka paimana `Futures_Discount_Hadd` hai. Wajah: Put ke liye PRD wala AI ulta niyam na bana de.
@@AFTER_BLOCK ### Trap_Detection_Check
`[PRASTAAVIT-CC]` `[F-42 | Med]` Mazboot Breakout aur Kamzor Breakout ka farak `Mazboot_Breakout_Paribhasha` se hai. `[F-57 | Low]` Band candle ke intezaar mein tikav ka samay aksar apne aap poora ho jaata hai. Isliye yeh check Range_Breakout_Check ki hi Data Family mein hai. Wajah: ek hi baat do baar points na de.
@@AFTER_BLOCK ### Range_Breakout_Check
`[PRASTAAVIT-CC]` `[F-42 | Med]` Breakout `Breakout_Candle_Timeframe` ki band candle par dekha jaata hai, aur "opening range" `Opening_Range_Samay` ki hai. `[F-55 | Low]` `Chart_Range_Breakout_Samay` ek range hai; bot ek hi kimat chune (Sawal 133). Wajah: do kimat par do alag breakout banenge.

`[PRASTAAVIT-CC]` Hypothesis H-14: Spot index mein asli saude nahi hote, isliye breakout Futures ke bhav par jaldi aur saaf dikh sakta hai. Test: Backtest mein Spot wale aur Futures wale breakout ki Net Expectancy aur deri milao. Wajah: jaldi aur saaf signal Slippage aur Chase ka nuksan ghatata hai.
@@AFTER_BLOCK ### EMA_Slope_Check
`[PRASTAAVIT-CC]` `[F-42 | Med]` "Sharp" slope ka paimana `EMA_Slope_Hadd` hai, jo abhi Tay nahi. Agar yeh Backtest se tay na ho, toh yeh check score mein na gine aur Shadow Mode mein chale. Wajah: bina paimane ka GREEN bharose ka nahi.
@@AFTER_BLOCK ### OI_Deewar_Short_Covering_Check
`[PRASTAAVIT-CC]` `[F-44 | Med]` Dikkat: OI exchange se der-der mein badalta hai, isliye yeh sabse dheema sanket hai, par iska vazan sabse bade mein se hai. "Bhaari matra mein naya OI" ka paimana bhi tay nahi (`OI_Bhaari_Badlaav_Paimana`). Hypothesis H-11: Ablation mein dekho ki is check ka vazan sach mein utna faayda deta hai ya nahi. Wajah: purane data par bada vazan galat breakout ko pass kar sakta hai.
@@AFTER_BLOCK ### Teeno_Index_Disha_Check
`[PRASTAAVIT-CC]` `[F-40 | Med]` Dikkat: "teeno alag Disha" ka matlab saaf nahi, jaise jab do ek Disha mein hon aur ek FLAT. Agar teeno trade ki Disha mein hon toh GREEN, aur koi ek bhi ulti Disha mein ho toh RED. Baaki haal mein 0 point aur confidence par asar nahi. Wajah: beech ki haalat ka faisla PRD wala AI na kare. "Ek bada daon" ka matlab Expiry ke din ke niyam ke `[F-31]` wale niyam jaisa hai.
@@AFTER_BLOCK ### Index_Breadth_Check
`[PRASTAAVIT-CC]` `[F-02 | Critical]` `[TAKRAAV #32]` Dikkat: yeh check Gate bhi hai, aur Nifty50 va Sensex ke stocks ki suchi Tay nahi hai. Data na hone se yeh NA-Data hoga aur Gate RED karega, yaani Nifty50 aur Sensex mein kabhi trade nahi hoga. Agar malik suchi tay na kare, toh suchi index ke official vazan wale page se har mahine bane, aur sabse bade vazan ke `Breadth_Top_Stocks_Ginti` stocks liye jaayein. Jab tak suchi pakki na ho, Nifty50 aur Sensex sirf Paper Mode mein chalein. Wajah: Gate ka data hi na ho toh Gate poore index ko band kar deta hai.

`[PRASTAAVIT-CC]` `[F-58 | Low]` BankNifty ke banks ki ginti exchange badal sakta hai. Agar index ki official suchi mein ginti badle, toh check usi suchi se chale, aur `BankNifty_Kul_Banks_Ginti` ka farak malik ko dikhaya jaaye (dekho: Tarikh wali baatein). Wajah: purani suchi par Breadth galat niklega.
@@AFTER_BLOCK ### VIX_Gati_Term_Structure_Check
`[PRASTAAVIT-CC]` `[F-42 | Med]` "Tezi se badhe" aur Term-Structure ki shart ka paimana tay nahi (`VIX_Tezi_Paimana`). Wajah: pehle version ke check ki shart number ke bina test nahi ho sakti.
