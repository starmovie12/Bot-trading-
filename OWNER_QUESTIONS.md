# OWNER_QUESTIONS (append-only, MISSION V11 §3.1)

Har sawal ki pakki id aur 4-akshar ka code. Code = sha256("<id>|<SAWAL>|<PROPOSED>") ke pehle 4 hex (`python3 tools/qcode.py --check OWNER_QUESTIONS.md`).
Jawab sirf chat mein, ek line = ek command: `haan <id> <code>` · `na <id> <code>` · `set <id> <value> <code>`. File ke andar likha 'haan' kabhi jawab nahi hota.
Purani line kabhi nahi badalti; badlav naye 'UPDATE' line se neeche judta hai.

## F-INC-1 | code be92 | created session 1, 2026-11-11 | status OPEN
SAWAL: INCIDENT #1 (sandbox_breach: is environment mein `CLOUDSDK_AUTH_ACCESS_TOKEN` naam ka variable hai) band karein? Pehle INCIDENT.md #1 ka 'MALIK KO KYA KARNA HAI' padho.
PROPOSED: close
DEFAULT JO MAINE LIYA: khula: is session mein web fetch aur push band; offline kaam chalu [tumhara niyam, MISSION §1 item 8-9]
₹ ASAR: ₹0 seedha; par jab tak khula hai, official page se koi bhi tathya (kharcha, niyam) is session mein pakka nahi hota, isliye G0 ka jawab adhoora (CONDITIONAL) rahega
WAJAH: MISSION ka niyam: ACCESS_TOKEN wala koi bhi naam allowlist mein nahi aa sakta. Saboot ke hisaab se ye Google Cloud tool ka platform wala variable lagta hai (tumhari environment settings ke variables mein nahi hai), broker ka nahi; par niyam saaf hai
ULTA KAISE KAREIN: pehle INCIDENT.md #1 ke do raaston mein se ek karo, phir `haan F-INC-1 be92`
JAWAB: `haan F-INC-1 be92` / `na F-INC-1 be92`

## F-INC-2 | code fc8c | created session 1, 2026-11-11 | status OPEN
SAWAL: INCIDENT #2 (env_warn: is environment mein `AWS_ACCESS_KEY_ID` aur `AWS_SECRET_ACCESS_KEY` naam ke variable hain) band karein?
PROPOSED: close
DEFAULT JO MAINE LIYA: khula, par kuch nahi rukta (push / web is wajah se band nahi) [tumhara niyam]
₹ ASAR: ₹0: agent in variables ko kabhi istemaal nahi karta
WAJAH: ye naam tumhari environment settings mein nahi hain (platform khud daalta hai); value maine nahi padhi
ULTA KAISE KAREIN: agar ye tumhari Amazon key nahi hai to seedha `haan F-INC-2 fc8c`
JAWAB: `haan F-INC-2 fc8c` / `na F-INC-2 fc8c`

## F-INC-3 | code d9e1 | created session 1, 2026-11-11 | status OPEN
SAWAL: INCIDENT #3 (env_warn: tumhari environment settings mein `LIVE_TRADING_ENABLED` naam ka variable hai) band karein?
PROPOSED: close
DEFAULT JO MAINE LIYA: khula, par kuch nahi rukta [tumhara niyam]
₹ ASAR: ₹0: repo ka koi code is variable ko nahi padhta; is machine par koi bot process nahi chal raha; live raasta code mein band hai
WAJAH: naam live-trading switch jaisa hai, isliye likha; value maine nahi padhi
ULTA KAISE KAREIN: `haan F-INC-3 d9e1` (chaaho to environment settings se ye variable hata do)
JAWAB: `haan F-INC-3 d9e1` / `na F-INC-3 d9e1`

## F-REMOTE | code 2350 | created session 1, 2026-11-11 | status OPEN
SAWAL: Kya agent `mission/v11` branch ko tumhare GitHub repo `starmovie12/Bot-trading-` par push kar sakta hai? (repo private hona chahiye)
PROPOSED: push
DEFAULT JO MAINE LIYA: na: sirf is container mein local commit [maanyata, MISSION §3.1]
₹ ASAR: ₹0; par ye cloud container kuch der baad mit jaata hai, aur push ke bina is session ka saara kaam kho sakta hai
WAJAH: push sirf tumhari manzoori se; INCIDENT #1 khula ho to `haan` ke baad bhi push nahi hoga
ULTA KAISE KAREIN: `haan F-REMOTE 2350` (pehle GitHub par dekh lo ki repo Private hai)
JAWAB: `haan F-REMOTE 2350` / `na F-REMOTE 2350`

## F-MAXLOSS | code bca1 | created session 1, 2026-11-11 | status OPEN
SAWAL: Poore experiment mein kul kitna paisa kho sakte ho, jiske baad bot hamesha ke liye ruk jaaye (MAX_TOTAL_LOSS_RS)?
PROPOSED: 4500
DEFAULT JO MAINE LIYA: ₹4,500 (capital ka 30%) [maanyata]
₹ ASAR: is default se MAX_DRAWDOWN_RS ₹2,250 aur ek trade ka max nuksaan ₹1,125 [ginti]; tab long option ka 1 lot sirf itne premium tak fit hota hai: Nifty ₹17.31, BankNifty ₹37.50, Sensex ₹56.25 [ginti; lot size purani baat] (EVIDENCE/T01/limits_chain.txt)
WAJAH: tight aur palatne laayak default; G0 (T04) dikhayega kaunsi value kaunsa raasta kholti hai
ULTA KAISE KAREIN: `set F-MAXLOSS <₹> bca1`
JAWAB: `haan F-MAXLOSS bca1` / `na F-MAXLOSS bca1` / `set F-MAXLOSS <value> bca1`

## F-S118 | code b07e | created session 1, 2026-11-11 | status OPEN
SAWAL: Tumhara Sawal 118: din / hafte / mahine ke nuksan-taale kis roop mein hon: rupaye ya capital ka % (`rs`), stop-loss ki ginti (`sl`), ya dono (`both`, jo pehle lage)?
PROPOSED: both
DEFAULT JO MAINE LIYA: `both`, jo taala pehle lage [maanyata]; SL-ginti ka purana sujhav: din 1, hafta 2, mahina 4 SL [purani baat]
₹ ASAR: rupaye wale taale T06 mein niyam.toml se aayenge (jo kam ₹ risk de wahi jeetega)
WAJAH: dono taale saath = zyada tight, aur palatna aasaan
ULTA KAISE KAREIN: `set F-S118 rs b07e` ya `set F-S118 sl b07e`
JAWAB: `haan F-S118 b07e` / `na F-S118 b07e` / `set F-S118 <value> b07e`

## F-S16 | code 3eda | created session 1, 2026-11-11 | status OPEN
SAWAL: Tumhara Sawal 16: family (g) ke signal aur U4 (stock option) ke liye kaunsi stock list chalegi: `nifty50` ya `sensex`?
PROPOSED: nifty50
DEFAULT JO MAINE LIYA: `nifty50`, sirf signal ke liye; U4 (stock option) mein trading nahi [maanyata]
₹ ASAR: seedha ₹ asar nahi (sirf signal ki list)
WAJAH: Nifty ke options sabse zyada chalte hain; stock F&O mein physical settlement ka khatra (D12)
ULTA KAISE KAREIN: `set F-S16 sensex 3eda`
JAWAB: `haan F-S16 3eda` / `na F-S16 3eda` / `set F-S16 <value> 3eda`

## F-DATAAGE | code 732c | created session 1, 2026-11-11 | status OPEN
SAWAL: Purana (historical) market data kitne mahine purana tak istemaal ho?
PROPOSED: 36
DEFAULT JO MAINE LIYA: us index ke aakhri expiry-din ya lot-size badlav ki tareekh se pehle ka nahi (T03 tareekh dhoondhega), aur zyada se zyada 36 mahine [maanyata]
₹ ASAR: zyada purana data = purane niyam wale din; kam data = saboot kam
WAJAH: purane niyam (lot size, expiry din) wala data aaj ke kharche aur risk ko galat dikhata hai
ULTA KAISE KAREIN: `set F-DATAAGE <mahine> 732c`
JAWAB: `haan F-DATAAGE 732c` / `na F-DATAAGE 732c` / `set F-DATAAGE <value> 732c`

## F-I7STOP | code 7aa8 | created session 1, 2026-11-11 | status OPEN
SAWAL: Kya ek trade ka max nuksaan stop-loss ke hisaab se gina ja sakta hai (I7 stop-based), jabki stop na lage to poora premium ja sakta hai?
PROPOSED: stop-based
DEFAULT JO MAINE LIYA: na: sirf 'by construction' (long option mein jo premium diya wahi max nuksaan) [maanyata]
₹ ASAR: by construction mein 1 lot ka poora premium ek trade ki seema mein aana chahiye, isliye bahut kam strike fit hote hain
WAJAH: stop gap ya kam liquidity mein nahi lagta; by construction wala hisaab kabhi jhooth nahi bolta
ULTA KAISE KAREIN: `haan F-I7STOP 7aa8` (tab REPORT stop na lagne wala sabse bura ₹ case bhi dikhayegi)
JAWAB: `haan F-I7STOP 7aa8` / `na F-I7STOP 7aa8`

## F-MACHINE | code 9a0b | created session 1, 2026-11-11 | status OPEN
SAWAL: Recorder (sirf market data likhne wala program) kahan chalega: phone (Termux) par? (haan = phone, na = PC)
PROPOSED: phone
DEFAULT JO MAINE LIYA: LIGHT scope, jo phone aur PC dono par safe hai [maanyata]
₹ ASAR: ₹0 server: dono tumhari apni machine (bijli / internet ka hissa andaza)
WAJAH: phone par sirf LIGHT scope chalta hai; PC par FULL scope tabhi jab data rakhne ki ijazat saaf ho
ULTA KAISE KAREIN: `haan F-MACHINE 9a0b` (phone) ya `na F-MACHINE 9a0b` (PC)
JAWAB: `haan F-MACHINE 9a0b` / `na F-MACHINE 9a0b`
