MEMO CP1 · session 2
G0 NATIJA:
- U1 se U6: sab CONDITIONAL (adhoora). Wajah: koi kharcha ya lot size official page se pakka nahi (web band), aur F-MAXLOSS ka jawab baaki. FAIL bhi sabit nahi hua
- Sabse sasta static-IP server (API order ke liye): ₹554.25/mahina [ginti (purani baat par)] = 3.7% [ginti (purani baat par)] capital har mahine; purana plan ₹1,330.19/mahina [ginti (purani baat par)] = 8.87% [ginti (purani baat par)]
- MANUAL (signal bot de, order tum lagao): server ka kharcha nahi; baaki chhote kharche abhi sirf maanyata
- Default seema par ek lot ka premium: Nifty ₹16.50 [ginti (maanyata par)], Sensex ₹53.75 [ginti (maanyata par)] tak; Nifty par har round trip ka kharcha ₹49.74 [ginti (purani baat par)]
- Saboot: mahine mein baarah trade par sau pachaas trade tak 12.5 months [ginti (andaza par)]; do saal baad bhi pakadne laayak sabse chhota fayda ₹243.49 [ginti (andaza par)] har trade, jabki sambhav fayda sirf ₹25 [ginti (andaza par)] (VALIDATION_INFEASIBLE)

SAWAL F-INC-1 (code be92): INCIDENT #1 (sandbox_breach: is environment mein `CLOUDSDK_AUTH_ACCESS_TOKEN` naam ka variable hai) band karein? Pehle INCIDENT.md #1 ka 'MALIK KO KYA KARNA HAI' padho.
  DEFAULT JO MAINE LIYA: khula: is session mein web fetch aur push band; offline kaam chalu [tumhara niyam, MISSION §1 item 8-9]
  ₹ ASAR: ₹0 [ginti] seedha; par jab tak khula hai, official page se koi tathya (kharcha, niyam) pakka nahi hota, isliye G0 ka jawab adhoora (CONDITIONAL) rahega
  WAJAH: MISSION ka niyam: ACCESS_TOKEN wala koi bhi naam allowlist mein nahi aa sakta. Saboot ke hisaab se ye Google Cloud tool ka platform wala variable lagta hai (tumhari environment settings ke variables mein nahi hai), broker ka nahi; par niyam saaf hai
  ULTA KAISE KAREIN: pehle INCIDENT.md #1 ke do raaston mein se ek karo, phir `haan F-INC-1 be92`
  JAWAB: `haan F-INC-1 be92` / `na F-INC-1 be92`

SAWAL F-DATARIGHTS (code 3fa1): Kya Upstox ne likhit mein confirm kiya hai ki API ka market data apne personal backtest ke liye apni machine par store karna allowed hai?
  DEFAULT JO MAINE LIYA: na: Recorder sirf LIGHT (derived data, personal use, kabhi share nahi) [maanyata]
  ₹ ASAR: seedha ₹ nahi; par bina ijazat poora data rakhna Upstox ke niyam todna (Class C) ho sakta hai
  WAJAH: DATA_RIGHTS = UNVERIFIED (docs/REGULATORY.md): repo mein Upstox ke terms ka text nahi, aur web band tha
  ULTA KAISE KAREIN: Upstox ka likhit jawab milne par `haan F-DATARIGHTS 3fa1`
  JAWAB: `haan F-DATARIGHTS 3fa1` / `na F-DATARIGHTS 3fa1`

SAWAL F-MAXLOSS (code bca1): Poore experiment mein kul kitna paisa kho sakte ho, jiske baad bot hamesha ke liye ruk jaaye (MAX_TOTAL_LOSS_RS)?
  DEFAULT JO MAINE LIYA: ₹4,500 (capital ka 30%) [maanyata]
  ₹ ASAR: G0 ke hisaab se is default par ek lot ka premium sirf itna: Nifty ₹16.50 [ginti (maanyata par)], Sensex ₹53.75 [ginti (maanyata par)]; Nifty ₹100 premium ke liye F-MAXLOSS ₹26,250.44 [ginti (purani baat par)] chahiye, jo H1 mein sirf sabse dheeli seema par mumkin hai (EVIDENCE/T04/g0.json)
  WAJAH: tight aur palatne laayak default; G0 (T04) dikhayega kaunsi value kaunsa raasta kholti hai
  ULTA KAISE KAREIN: `set F-MAXLOSS <₹> bca1`
  JAWAB: `haan F-MAXLOSS bca1` / `na F-MAXLOSS bca1` / `set F-MAXLOSS <value> bca1`

SAWAL F-H2PCT (code be04): H2 (bot ka naya kharcha har mahine) capital ke kitne % par rokein? Abhi ₹1,500 = 10% [tumhara niyam]; mera prastaav 4% (₹600) [maanyata].
  DEFAULT JO MAINE LIYA: ₹1,500 = 10% [tumhara niyam] har mahine, jab tak tum jawab na do
  ₹ ASAR: sabse sasta static-IP server ₹554.25 [ginti (purani baat par)] = 3.70% [ginti (purani baat par)] capital har mahine; ₹1,330 wala plan 8.87% [ginti (purani baat par)] (EVIDENCE/T04/g0.json). 4% [maanyata] par sirf sabse sasta raasta bachta hai
  WAJAH: server ka kharcha har mahine capital ko pehle hi kha jaata hai, saboot aane se pehle bhi; tight seema = kam nuksaan
  ULTA KAISE KAREIN: `set F-H2PCT <%> be04`
  JAWAB: `haan F-H2PCT be04` / `na F-H2PCT be04` / `set F-H2PCT <%> be04`

SAWAL F-S118 (code b07e): Tumhara Sawal 118: din / hafte / mahine ke nuksan-taale kis roop mein hon: rupaye ya capital ka % (`rs`), stop-loss ki ginti (`sl`), ya dono (`both`, jo pehle lage)?
  DEFAULT JO MAINE LIYA: `both`, jo taala pehle lage [maanyata]; SL-ginti ka purana sujhav: din 1, hafta 2, mahina 4 SL [purani baat]
  ₹ ASAR: rupaye wale taale T06 mein niyam.toml se aayenge (jo kam ₹ risk de wahi jeetega)
  WAJAH: dono taale saath = zyada tight, aur palatna aasaan
  ULTA KAISE KAREIN: `set F-S118 rs b07e` ya `set F-S118 sl b07e`
  JAWAB: `haan F-S118 b07e` / `na F-S118 b07e` / `set F-S118 <value> b07e`

SAWAL F-I7STOP (code 7aa8): Kya ek trade ka max nuksaan stop-loss ke hisaab se gina ja sakta hai (I7 stop-based), jabki stop na lage to poora premium ja sakta hai?
  DEFAULT JO MAINE LIYA: na: sirf 'by construction' (long option mein jo premium diya wahi max nuksaan) [maanyata]
  ₹ ASAR: by construction mein ek lot ka poora premium ek trade ki seema mein aana chahiye, isliye bahut kam strike fit hote hain (EVIDENCE/T04/g0.json)
  WAJAH: stop gap ya kam liquidity mein nahi lagta; by construction wala hisaab kabhi jhooth nahi bolta
  ULTA KAISE KAREIN: `haan F-I7STOP 7aa8` (tab REPORT stop na lagne wala sabse bura ₹ case bhi dikhayegi)
  JAWAB: `haan F-I7STOP 7aa8` / `na F-I7STOP 7aa8`

SAWAL F-DATAAGE (code 732c): Purana (historical) market data kitne mahine purana tak istemaal ho?
  DEFAULT JO MAINE LIYA: us index ke aakhri expiry-din ya lot-size badlav ki tareekh se pehle ka nahi (T03 tareekh dhoondhega), aur zyada se zyada 36 mahine [maanyata]
  ₹ ASAR: zyada purana data = purane niyam wale din; kam data = saboot kam
  WAJAH: purane niyam (lot size, expiry din) wala data aaj ke kharche aur risk ko galat dikhata hai
  ULTA KAISE KAREIN: `set F-DATAAGE <mahine> 732c`
  JAWAB: `haan F-DATAAGE 732c` / `na F-DATAAGE 732c` / `set F-DATAAGE <value> 732c`

SAWAL F-MACHINE (code 9a0b): Recorder (sirf market data likhne wala program) kahan chalega: phone (Termux) par? (haan = phone, na = PC)
  DEFAULT JO MAINE LIYA: LIGHT scope, jo phone aur PC dono par safe hai [maanyata]
  ₹ ASAR: server ka ₹0 [ginti]: dono tumhari apni machine (bijli / internet ka hissa abhi maanyata)
  WAJAH: phone par sirf LIGHT scope chalta hai; PC par FULL scope tabhi jab data rakhne ki ijazat saaf ho
  ULTA KAISE KAREIN: `haan F-MACHINE 9a0b` (phone) ya `na F-MACHINE 9a0b` (PC)
  JAWAB: `haan F-MACHINE 9a0b` / `na F-MACHINE 9a0b`

SAWAL F-RECFULL (code 99ea): PC par Recorder ka FULL scope (tick + depth) chalayein? Ye sirf tab lagu hai jab DATA_RIGHTS = OK ho.
  DEFAULT JO MAINE LIYA: na: LIGHT scope [maanyata]
  ₹ ASAR: server ka kharcha nahi; FULL scope ka data din mein bahut bada (disk) [andaza]
  WAJAH: DATA_RIGHTS abhi UNVERIFIED hai, isliye ye sawal abhi lagu nahi hota
  ULTA KAISE KAREIN: DATA_RIGHTS OK hone ke baad `haan F-RECFULL 99ea`
  JAWAB: `haan F-RECFULL 99ea` / `na F-RECFULL 99ea`

SAWAL F-S16 (code 3eda): Tumhara Sawal 16: family (g) ke signal aur U4 (stock option) ke liye kaunsi stock list chalegi: `nifty50` ya `sensex`?
  DEFAULT JO MAINE LIYA: `nifty50`, sirf signal ke liye; U4 (stock option) mein trading nahi [maanyata]
  ₹ ASAR: seedha ₹ asar nahi (sirf signal ki list)
  WAJAH: Nifty ke options sabse zyada chalte hain; stock F&O mein physical settlement ka khatra (D12)
  ULTA KAISE KAREIN: `set F-S16 sensex 3eda`
  JAWAB: `haan F-S16 3eda` / `na F-S16 3eda` / `set F-S16 <value> 3eda`

SAWAL F-REMOTE (code 2350): Kya agent `mission/v11` branch ko tumhare GitHub repo `starmovie12/Bot-trading-` par push kar sakta hai? (repo private hona chahiye)
  DEFAULT JO MAINE LIYA: na: sirf is container mein local commit [maanyata, MISSION §3.1]
  ₹ ASAR: ₹0 [ginti]; par ye cloud container kuch der baad mit jaata hai, aur push ke bina saara kaam kho sakta hai
  WAJAH: push sirf tumhari manzoori se; INCIDENT #1 khula ho to `haan` ke baad bhi push nahi hoga
  ULTA KAISE KAREIN: `haan F-REMOTE 2350` (pehle GitHub par dekh lo ki repo Private hai)
  JAWAB: `haan F-REMOTE 2350` / `na F-REMOTE 2350`

SAWAL F-INC-3 (code d9e1): INCIDENT #3 (env_warn: tumhari environment settings mein `LIVE_TRADING_ENABLED` naam ka variable hai) band karein?
  DEFAULT JO MAINE LIYA: khula, par kuch nahi rukta [tumhara niyam]
  ₹ ASAR: ₹0 [ginti]: repo ka koi code is variable ko nahi padhta; koi bot process nahi chal raha; live raasta code mein band hai
  WAJAH: naam live-trading switch jaisa hai, isliye likha; value maine nahi padhi
  ULTA KAISE KAREIN: `haan F-INC-3 d9e1` (chaaho to environment settings se ye variable hata do)
  JAWAB: `haan F-INC-3 d9e1` / `na F-INC-3 d9e1`

SAWAL F-INC-2 (code fc8c): INCIDENT #2 (env_warn: is environment mein `AWS_ACCESS_KEY_ID` aur `AWS_SECRET_ACCESS_KEY` naam ke variable hain) band karein?
  DEFAULT JO MAINE LIYA: khula, par kuch nahi rukta (push / web is wajah se band nahi) [tumhara niyam]
  ₹ ASAR: ₹0 [ginti]: agent in variables ko kabhi istemaal nahi karta
  WAJAH: ye naam tumhari environment settings mein nahi hain (platform khud daalta hai); value maine nahi padhi
  ULTA KAISE KAREIN: agar ye tumhari Amazon key nahi hai to seedha `haan F-INC-2 fc8c`
  JAWAB: `haan F-INC-2 fc8c` / `na F-INC-2 fc8c`
