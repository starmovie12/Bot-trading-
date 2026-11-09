@@REPLACE_LINE **Idea ka Version:** 3.1
**Idea ka Version:** 4.0 `[PRASTAAVIT-CC]` (purana: 3.1)
@@REPLACE_LINE **Tarikh:** 9 Nov 2026
**Tarikh:** 10 Nov 2026 (purana: 9 Nov 2026)
@@AFTER_LINE **Ek line ka saar:**

**[PRASTAAVIT-CC] Version 4.0 ka saar:** Is version mein malik ka likha ek bhi shabd nahi badla. Claude Code ne har section ka gehra audit kiya aur har nayi baat `[PRASTAAVIT-CC]` tag ke saath sahi ghar mein jodi. Har audit bindu ka ID `[F-xx | Gambhirta]` hai; poori suchi alag file `01b_Audit_Findings.md` mein hai. Strategy ke sudhaar Hypothesis (`H-xx`) ki tarah likhe hain, jinhe `03_Strategy_Edge_Plan.md` ke tareeke se test karna hai. Naye sawal "Abhi tay nahi hua" ke sabse upar hain. Pakka sirf malik karega.
@@AFTER_BLOCK ## 1. Daayra
`[PRASTAAVIT-CC]` Bot ka pehla lakshya profit ka vaada nahi hai. Lakshya yeh sabit karna hai ki kharche aur Slippage ke baad bot ki Net Expectancy (dekho: Naam-Suchi) positive hai. Agar Backtest, Paper Stage aur Stage2 mein yeh sabit na ho, toh bot Real Money Mode mein poore Lot par nahi jaata. Wajah: option khareedne wale zyada tar retail trader kharche, theta aur IV Crush se haarte hain (dekho: Tarikh wali baatein). Koi niyam profit ki guarantee nahi de sakta.

`[PRASTAAVIT-CC]` Bot kya nahi karega, us suchi mein yeh teen baatein bhi jode jaane ka prastaav hai. Bot Kill Latch lage hone par koi naya entry nahi leta. Bot Foreign Position wale instrument mein trade nahi leta. Bot jawab na aane par entry order bina broker ki pushti ke dobara nahi bhejta. Wajah: in teeno mein ek hi galti se dohra ya ulta jokhim ban sakta hai.
@@AFTER_BLOCK ## 2. Naam-Suchi
- **[PRASTAAVIT-CC]:** Claude Code ka 10 Nov 2026 ko sujhaya naya niyam, number, audit bindu ya sawal. Status "Prastaavit" hai. Malik ki pushti tak yeh pakka nahi. Malik ka purana likha isse nahi badalta.
- **Audit bindu (F-xx):** 10 Nov 2026 ke audit mein mili ek kami. Gambhirta chaar mein se ek: Critical, High, Med, Low. Poori suchi `01b_Audit_Findings.md` mein.
- **Hypothesis (H-xx):** Ek sudhaar ka andaza jo data se test hona baaki hai. Test ka tareeka `03_Strategy_Edge_Plan.md` mein.
- **ATM (At-The-Money):** Woh strike jo Spot Price ke sabse paas ho.
- **Moneyness Khaana:** Strike ko uske naam se nahi, ATM se doori se pehchanna (jaise ATM, ATM se ek strike upar).
- **Opening Range:** Din ke shuru ke tay samay (`Opening_Range_Samay`) ka sabse ooncha aur sabse neecha bhav.
- **Swing Low aur Swing High:** Chart par woh candle jiske dono taraf ki `Swing_Pushti_Candle_Ginti` band candles usse oonchi (Swing Low ke liye) ya neechi (Swing High ke liye) hon.
- **Pullback:** Breakout ke baad bhav ka thoda wapas aana aur phir breakout ki disha mein chalna (`Pullback_Paimana`).
- **Mazboot Breakout aur Kamzor Breakout:** Jo breakout `Mazboot_Breakout_Paribhasha` poori kare woh Mazboot Breakout hai. Baaki Kamzor Breakout hai.
- **Breakout Candle:** `Breakout_Candle_Timeframe` ki woh band candle jis par `Range_Breakout_Check` pehli baar GREEN hua.
- **NA-Data:** NA ka woh roop jab check aaj lagu hai par data nahi mila ya bharose ka nahi. Gate ke liye yeh RED hai.
- **NA-Lagu-Nahi:** NA ka woh roop jab check aaj ya is samay lagu hi nahi (jaise sirf expiry din wala check aam din). Yeh Gate ko na rokta hai na pass karta hai.
- **Lease (Control-Patta):** Bot ka broker ko hukm bhejne ka chhota samay wala haq. Har Pehredaar pushti par yeh naya hota hai. Lease khatam toh bot broker ko koi hukm nahi bhejta.
- **Kill Latch:** Kill-Switch dabne par laga pakka taala. Jab tak malik agle din Start Control se na khole, bot koi naya entry nahi leta.
- **Khula Trade:** Ek index mein bot ki khuli position, pending entry order ya chal raha exit. Teeno ko khula trade gina jaata hai.
- **Stop-Unit:** Ek trade mein entry se Stop-Loss tak ka rupaye mein sambhavit nuksan. Risk ko isi ikai mein ginne ka prastaav hai.
- **Worst-Case Nuksan:** Gap, Broker Stop ki doori aur MPP Order ka Slippage jod kar ek trade ka sabse bura sambhavit nuksan (`Worst_Case_Nuksan_Guna`).
- **Net Expectancy:** Kharche aur Slippage ke baad ek trade ka ausat fayda ya nuksan.
- **Confidence Interval:** Net Expectancy ka woh daayra jismein asli kimat hone ka tay bharosa ho. Kam trade par daayra chauda hota hai.
- **Profit Factor:** Kul munafe aur kul nuksan ka anupaat.
- **Risk of Ruin:** Itna paisa doobne ki sambhavna ki bot 1 Lot bhi na le sake.
- **Kelly Hissa:** Ganit ka woh hissa jo jeet-haar ke anupaat se batata hai ki har trade mein balance ka kitna hissa lagana lambe samay mein sabse tez badhta hai. Isse zyada lagane par nuksan ka khatra tez badhta hai.
- **Walk-Forward aur Out-of-Sample:** Purane data ke ek hisse par niyam tay karna aur agle anchhue hisse par parakhna. Anchhua hissa Out-of-Sample hai.
- **Ablation:** Ek-ek check hata kar dekhna ki nateeja kitna badla, taaki pata chale kaun sa check sach mein faayda deta hai.
- **Data Family:** Ek hi tarah ke data se bane checks ka group (jaise Disha wale ya volume wale checks).
- **Shadow Trade:** Reject hue signal par kaagaz par wahi entry, wahi Stop-Loss aur wahi exit niyam chala kar nikla nateeja.
- **Replay Record:** Bot ko mila har data aur liya har faisla, is tarah record ki din dobara chalane par wahi faisle nikle.
- **Monte Carlo:** Trades ke nateejon ko hazaaron baar alag kram mein chala kar dekhna ki balance ka kya-kya ho sakta hai.
@@AFTER_BLOCK ## 3. Bot ka ek poora din
`[PRASTAAVIT-CC]` `[F-07 | High]` `[TAKRAAV #27]` Dikkat: `Ghadi_Skew_Hadd` ki kimat `Data_Purana_Hadd` ke barabar ya usse badi hai. Itni ghadi ki galti mein purana data taaza dikh sakta hai, ya taaza data purana. Agar bot ki ghadi aur exchange ki ghadi ka farak `Ghadi_Skew_Sakht_Hadd` se zyada ho, toh subah Taiyari Fail ho aur din mein aisa ho toh naye entry band hon. Wajah: data ki taazgi ka har faisla sahi ghadi par tika hai. Asar: purane bhav par galat entry ka khatra ghatta hai; ghadi kharab din trade chhoot sakte hain.

`[PRASTAAVIT-CC]` `[F-23 | Med]` Dikkat: "kisi bhi index ke 1 Lot ke liye paisa kam" ka matlab saaf nahi. Is padhai se sasta index bhi band ho sakta hai. Agar free paisa kam se kam ek index ke 1 Lot aur `Balance_Extra_Buffer` ke liye kaafi ho, toh Start Control chale aur baaki index par alag "Paisa Kam" dikhe. Wajah: jo index khareeda ja sakta hai, use bina wajah na roka jaaye. Asar: zyada mauke, har trade ka risk wahi.

`[PRASTAAVIT-CC]` `[F-25 | Med]` Dikkat: bade gap ke baad "nayi range" kab bani, yeh tay nahi. Agar market `Bada_Gap_Hadd` se khule, toh bot `Gap_Ke_Baad_Range_Samay` tak ke sabse oonche aur sabse neeche bhav ko nayi range maane. Wajah: PRD wala AI apni taraf se range na gadhe. Asar: gap wale din ka vyavhaar test-yogya banta hai.

`[PRASTAAVIT-CC]` `[F-26 | Med]` Dikkat: khule trade ke dauran Din ka Mausam badal jaaye toh trade ka kya ho, yeh likha nahi. Agar khule trade ke dauran mausam Sideways ya Ulta-Palat ho jaaye, toh trade apne Exit niyam se hi chale. Lot ka cut sirf naye entry par lage. Wajah: mausam dheema sanket hai, aur Stop-Loss va Time-Stop pehle se trade ko sambhalte hain. Asar: bina wajah ke jaldi exit ka kharcha bachta hai.

`[PRASTAAVIT-CC]` `[F-27 | Med]` Hypothesis H-12: subah ka mausam pichle din ki candles ke saath bane ADX se aata hai, isliye woh kal dopahar ka haal zyada dikha sakta hai. Test: Backtest mein dekho ki "Trending" tag ke baad agle ghante mein index ki ek-disha chaal sach mein zyada aati hai ya nahi. Agar tag ka asar na mile, toh malik ke saath Din_Ka_Mausam_Gate dobara socha jaaye. Wajah: galat Sideways tag din ke saare mauke le jaata hai.

`[PRASTAAVIT-CC]` `[F-28 | Med]` Hypothesis H-08: Shock Mode mein saare khule trade turant band hote hain, chahe trade jhatke ki disha mein munafe mein ho. Us waqt bid-ask sabse chauda hota hai, isliye exit mehenga padta hai. Test: Backtest mein "turant exit" banam "munafe wale trade par Trailing Stop-Loss kasna" ki Net Expectancy milao. Malik ka `[TAKRAAV #9]` wala niyam tab tak waisa hi rahega. Asar: shock din ka Slippage ghat sakta hai.

`[PRASTAAVIT-CC]` `[F-29 | Med]` Dikkat: din ke ant mein ek pal ke liye Liquidity_Filter RED hone par bhi trade nikal jaata hai. Agar Liquidity_Filter `Liquidity_Exit_Tikav_Samay` tak lagatar RED rahe, tabhi yeh jaldi exit chale. Wajah: pal bhar ke chaude spread par exit sabse mehenga hota hai. Asar: bekaar exit kam.

`[PRASTAAVIT-CC]` `[F-35 | Med]` Dikkat: din ke beech token band ho jaaye (jaise usi app ka naya login), toh kya ho, yeh saaf nahi. Agar bot ya Pehredaar ko broker se "token band" ka jawab mile, toh naye entry turant band hon, Critical Alert jaaye aur Broker Stop broker par bana rahe. Malik ke naye login ke baad bot pehle record milaan kare, phir hi entry le. Wajah: bina chalte token ke bot apna trade na badal sakta hai na nikaal sakta hai.

`[PRASTAAVIT-CC]` Hypothesis H-03 aur H-13: trading zones aur event lock ke samay "Andaza" hain. Test: Backtest mein har aadhe ghante ke khaane ki alag Net Expectancy, aur event ke aas-paas ka nateeja dekho. Jo khaana kharche ke baad lagatar nuksan de, use malik ki manzoori se zone se hataya ja sakta hai. Wajah: samay ka asar data se sabit ho, yaad se nahi.
@@AFTER_BLOCK ## 4. Expiry ke din ke niyam
`[PRASTAAVIT-CC]` `[F-12 | High]` Dikkat: shift ke second par exit aur naya entry lagbhag ek saath bheje ja sakte hain. Exit pura fill hone se pehle entry chali, toh do trade ek saath khule reh sakte hain ya paisa kam pad sakta hai. Agar shift par purana trade band karna ho, toh naya entry tabhi bheja jaaye jab broker net quantity zero dikhaye aur free paisa dobara padh liya jaaye. Wajah: Order Baari sirf kram tay karti hai, fill ka intezaar nahi karti. Asar: dohre jokhim ka rasta band; shift ke baad entry thodi der se hogi.

`[PRASTAAVIT-CC]` `[F-30 | Med]` Dikkat: expiry ki subah "mazboot tezi" ki paribhasha nahi hai, aur tezi na ho toh kya, yeh bhi nahi. Agar expiry ki subah breakout `Mazboot_Breakout_Paribhasha` poori kare, toh current expiry chuni jaaye. Agar breakout Kamzor Breakout ho, toh us index mein subah koi trade na ho (Sawal 131). Wajah: expiry ki subah kamzor chaal par gamma ka jokhim fayde se bada hai.

`[PRASTAAVIT-CC]` `[F-31 | Med]` Dikkat: "ek hi bade daon ki tarah ginta hai" ka asli kaam saaf nahi. Agar ek hi disha ke do trade ek saath khulne wale hon (aakhri Mangalwar ya teeno index ek disha mein), toh doosra trade tabhi ho jab dono ka Worst-Case Nuksan milakar din ke bache Risk Limit ke andar ho. Wajah: saath chalne wale index ek saath girte hain, isliye do trade asal mein ek bada trade hain.

`[PRASTAAVIT-CC]` Hypothesis H-04: expiry ki subah current expiry ka ITM trade gamma ki wajah se bahut tez hilta hai. Test: Backtest mein expiry subah ke trades ki Net Expectancy, Slippage aur Broker Stop ka gap-fill alag dekho. Agar kharche ke baad nateeja kamzor ho, toh malik ki manzoori se expiry subah Lot cut ya trade band karne ka vikalp socha jaaye. Wajah: expiry din ka jokhim aam din se alag hai.
@@AFTER_BLOCK ## 5. Pehredaar aur Suraksha
`[PRASTAAVIT-CC]` `[F-06 | Critical]` Dikkat: poora Pehredaar is maanyata par tika hai ki uska alag app bot ke app se lage order dekh aur cancel kar sakta hai, aur khuli position band kar sakta hai. Yeh abhi verify nahi hua. Agar Real Money Mode se pehle yeh test asli account par pass na ho, toh Real Money Mode band rahe. Wajah: Broker Stop cancel kiye bina Pehredaar ka exit net short bana sakta hai. Asar: jab tak sabit na ho, Pehredaar par bharosa nahi.

`[PRASTAAVIT-CC]` `[F-05 | Critical]` Dikkat: bot zinda par dheema ho, ya bot aur Pehredaar ke beech network toote, toh dono ek hi trade par ek saath kaam kar sakte hain. Isse do exit order ya Broker Stop ki gadbad se account net short ho sakta hai. Agar bot ko `Bot_Lease_Samay` tak Pehredaar ki pushti na mile, toh bot broker ko koi bhi hukm (entry, exit, modify, cancel) nahi bhejta. `Bot_Lease_Samay` hamesha Pehredaar ke trade sambhalne ke samay (dhadkan ka samay aur chhoot ginti milakar) se chhota rahega. Wajah: ek waqt par sirf ek hissa broker ko hukm de.

`[PRASTAAVIT-CC]` `[F-05 | Critical]` Agar Pehredaar trade sambhale, toh woh pehle "Pehredaar ne control liya" nishan likhta hai. Is nishan ke baad bot us din broker ko koi hukm nahi bhejta, jab tak malik naya Start Control na de. Wajah: control ka lena-dena saaf ho, dono ek saath na chalein. Asar: net short aur dohre exit ka sabse bada rasta band.

`[PRASTAAVIT-CC]` `[F-16 | High]` Pehredaar ki dhadkan sirf "zinda" ka sanket na ho, bot ki haalat bhi le jaaye: aakhri tick ki umar, aakhri record milaan ki umar, khule trade aur unke Broker Stop. Pehredaar apne token se khud bhi har `Pehredaar_Swatantra_Milaan_Samay` par broker ki positions aur pending orders padhta hai. Agar bot ki koi position `Entry_Ke_Baad_Broker_Stop_Samay` se zyada der sahi quantity ke Broker Stop ke bina mile, toh Pehredaar control lekar use band kare. Wajah: zinda par andha bot bhi khatarnak hai. Asar: bina Stop ke trade ka samay chhota.

`[PRASTAAVIT-CC]` `[F-35 | Med]` Agar Pehredaar ka token `Pehredaar_Token_Jaanch_Samay` ki jaanch mein kaam na kare, toh naye entry band hon aur Critical Alert jaaye. Yeh jaanch bina order lagaye hoti hai. Wajah: kharab token wala Pehredaar sirf bharosa deta hai, suraksha nahi.

`[PRASTAAVIT-CC]` `[F-04 | Critical]` `[TAKRAAV #29]` Dikkat: Kill-Switch ka hukm sirf Pehredaar ko jaata hai. Agar bot zinda hai, toh woh band trade ko "haath se band" maan kar `Record_Farak_Pause_Samay` ke baad phir entry le sakta hai. Agar Kill-Switch dabe, toh Kill Latch lage jise bot aur Pehredaar dono padhte hain. Kill Latch ke saath bot koi naya entry nahi leta, aur Pehredaar bot ke Order Tag wala har naya order cancel karke trade band karta hai. Wajah: Kill-Switch ka matlab "sab kuch rokna" hai, sirf aaj ke trade kaatna nahi.

`[PRASTAAVIT-CC]` `[F-04 | Critical]` Kill Latch sirf malik agle trading din Start Control se kholta hai. Asar: Kill-Switch ke baad dobara nuksan ka rasta band; us din ke baaki mauke jaate hain.

`[PRASTAAVIT-CC]` `[F-08 | High]` `[TAKRAAV #31]` Dikkat: Trailing Stop-Loss har khiskaav par Broker Stop badalta hai, par broker ek order ko din mein seemit baar hi badalne deta hai (dekho: Tarikh wali baatein). Seema poori hone par badlaav reject hoga, aur "do baar reject" wale niyam se trade jabardasti band hoga. Agar naya Stop-Loss purane se `Broker_Stop_Min_Khiskaav` se kam khiske, toh Broker Stop na badla jaaye. Agar ek Broker Stop ke badlaav `Broker_Stop_Modify_Bajat` tak pahunchein, toh bot purana Broker Stop cancel karke, confirm lekar naya Broker Stop lagaye. Wajah: broker ki seema se trade ka galat exit na ho.

`[PRASTAAVIT-CC]` `[F-08 | High]` Asar: jabardasti exit ghatte hain. Broker Stop thoda peeche reh sakta hai, par bot ka apna Stop-Loss poora chalta hai.

`[PRASTAAVIT-CC]` `[F-09 | High]` Dikkat: exit ke waqt Broker Stop aadha fill ho sakta hai, aur cancel sirf baaki hisse ka hota hai. Agar Broker Stop ka cancel confirm ho, toh exit order ki quantity hamesha broker ki us waqt ki net quantity hogi, bot ki yaad wali quantity nahi. Wajah: aadhe fill ke baad puri quantity bechne se account net short hota hai. Asar: net short ka ek aur rasta band.

`[PRASTAAVIT-CC]` `[F-10 | High]` Dikkat: jawab na aane par entry dobara bhejna dohra trade bana sakta hai, aur broker ki order suchi der se update ho sakti hai. Agar entry order ka jawab na aaye, toh bot use bina pushti kabhi dobara nahi bhejta; woh Order Tag se broker ko `Signal_Dobara_Order_Roak_Samay` tak poochta rehta hai. Har irade ka Order Tag alag hota hai aur kabhi dohraya nahi jaata. Exit order sirf tab dobara jaata hai jab broker position khuli dikhaye. Wajah: ek trade chhootna, do trade lagne se sasta hai.

`[PRASTAAVIT-CC]` `[F-11 | High]` Dikkat: agar malik ka Foreign Position usi instrument mein ho jismein bot ka trade hai, toh broker ki net quantity mein dono mil jaate hain. Tab bot ka exit ya Net Quantity Guard malik ke Lot bhi bech sakta hai. Agar kisi instrument mein kisi bhi product ka Foreign Position ho, toh bot us instrument mein naya trade nahi leta. Bot apni quantity sirf apne Order Tag wale fill se ginta hai. Wajah: bot malik ke trade ko kabhi na chhooye.

`[PRASTAAVIT-CC]` `[F-33 | Med]` Hypothesis H-15 (vikalp): `Blind_Position_Hadd` par turant MPP exit ke bajay, bot pehle broker se har `Feed_Stale_REST_Gati` par bhav maange. Agar bhav mile, toh apna Stop-Loss aur exit niyam usi bhav par chalaye. Agar broker se bhi bhav na mile, tabhi trade MPP Order se band ho. Malik ka niyam test hone tak waisa hi rahega. Wajah: thodi der ka feed atakna har khule trade ko mehenge exit mein na dhakele.

`[PRASTAAVIT-CC]` `[F-34 | Med]` Reject ki suchi mein do aur jode jaayein. Agar broker "bahut zyada request" bole, toh Order Baari dheemi ho, naye entry rukein, aur exit va Broker Stop pehle jaayein. Agar exchange ki order-per-second seema ka reject aaye, toh us din naye entry band hon aur Zaroori Alert jaaye. Wajah: seema todne par broker ya exchange account par rok laga sakte hain.

`[PRASTAAVIT-CC]` `[F-36 | Med]` Agar bot dobara chalu ho, toh woh Intent Log ka har adhoora irada broker se milata hai. Irada broker par fill mile toh trade apna maana jaaye; na mile toh irada band. Jab tak yeh milaan poora na ho, bot naya entry nahi leta. Wajah: crash ke beech bheja order bina khabar ke khula na rahe.
@@AFTER_BLOCK ## 6. Faisle ka raasta
`[PRASTAAVIT-CC]` `[F-01 | Critical]` `[TAKRAAV #26]` Dikkat: niyam kehta hai ki "us din lagu na hone" wala check NA hai, aur Gate ka NA RED hai. Manipulation_Cash_Volume_Check aur Manipulation_Settlement_Check Gate hain, par sirf expiry din aur tay samay par lagu hote hain. Is niyam se aam din par yeh RED hokar har trade rok denge. Asar: is sudhaar ke bina bot ya toh kabhi trade nahi lega, ya PRD wala AI apni taraf se niyam gadhega.

`[PRASTAAVIT-CC]` `[F-01 | Critical]` Agar check lagu hai par data nahi mila, toh woh NA-Data hai aur Gate ke liye RED. Agar check aaj ya is samay lagu hi nahi, toh woh NA-Lagu-Nahi hai; woh Gate ko na rokta hai na pass karta hai. Dashboard par NA-Lagu-Nahi alag rang mein dikhe. Score ke liye dono NA par 0 point. Wajah: suraksha bani rahe par bot bina wajah poore din na ruke.
