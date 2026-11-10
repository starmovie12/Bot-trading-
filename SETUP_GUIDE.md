# Bot Setup Guide (malik ke liye, step by step)

**Tarikh:** 10 Nov 2026 · **Kisne:** Claude Code · **Website:** https://bot-trading-pi.vercel.app

Is guide ko upar se neeche, ek-ek step karke padho. Har step ke ant mein likha hai ki **kaise pata chalega ki step ho gaya**.
Kuch bhi samajh na aaye toh wahi step Claude ko bata do.

## Shuru karne se pehle 5 pakke niyam

1. **Koi chaabi kabhi chat, GitHub, WhatsApp ya email mein nahi.** API key, API secret, TOTP secret, PIN, Telegram token: sirf aapke password manager mein aur server ke encrypted store mein.
2. **Profit ki koi guarantee nahi.** SEBI ki study ke hisaab se option khareedne wale ~90% log nuksan mein the. Bot pehle Paper Mode mein sabit karega; sabit na ho toh asli paisa nahi.
3. **Upstox mein sirf EK API app.** Upstox ab ek user ko ek hi chalu API app deta hai; naya app banaoge toh purana delete ho jaata hai.
4. **Static IP market ke beech kabhi mat badlo.** Badalte hi saare token band ho jaate hain, aur IP hafte mein sirf ek baar badal sakta hai.
5. **Mahine ka server kharcha ₹1,500 ke andar** (aapka niyam). Is guide ka plan ~₹1,330 ka hai.

## Kya khareedna hai (seedha jawab)

| Hissa | Kya lena hai | Mahina kharcha (andaza, GST ke saath) |
|---|---|---|
| **Bot ka server** | **AWS Lightsail, Mumbai, Linux $12 plan** (2 vCPU, 2 GB RAM, 60 GB SSD, static IP shaamil) | ~₹1,330 |
| **Pehredaar ka server** | **Oracle Cloud Always Free** ki chhoti machine (`VM.Standard.E2.1.Micro`) | ₹0 |
| **Website (Dashboard)** | **Vercel Hobby** (`bot-trading-pi.vercel.app`) | ₹0 |
| **Kul** | | **~₹1,330** |

- Lightsail kyun: Upstox ke order aur live-data server AWS Mumbai mein hain, isliye network sabse chhota rehta hai.
- **Asli paise se pehle (Stage2) Plan B:** Bot Lightsail $7 (~₹776) + Pehredaar Vultr Mumbai $5 (~₹554). Kul wahi ~₹1,330. Oracle Free machine idle rehne par delete ho sakti hai, isliye asli paise ke liye paid Pehredaar.
- Rate ka andaza: $1 = ₹93.94 (9 Nov 2026). AWS India 18% GST lagata hai.

---

## 🟡 Step 1: Website theek karo (Vercel)

**Kyun:** abhi website "500 FUNCTION_INVOCATION_FAILED" dikha rahi thi; har page, CSS file tak, function se ja raha tha. Sabse sambhav wajah: Vercel project repo ke root se bana, aur wahan Python ka project dekh kar Vercel ne site ko galat tareeke se chalaya (Vercel ke logs hum nahi dekh sakte, isliye yeh andaza hai). Fix: ab `vercel.json` Vercel ko saaf batati hai ki koi framework nahi, koi build nahi, aur website ki files kahan hain. Repo root aur `dashboard` dono se chalega (PR #3).

1. GitHub par **PR #3 kholo → "Merge pull request" → "Confirm merge"** dabao.
2. Vercel par apna project `bot-trading` kholo → **Deployments**. 1-2 minute mein naya deployment "Ready" ho jaayega. Na ho toh sabse upar wale deployment par **⋯ → Redeploy**.
3. **Settings → Build and Deployment** mein dekho:
    - Framework Preset: **Other** (hamari `vercel.json` khud yahi set karti hai).
    - Root Directory: **khaali (repo root)** ya **`dashboard`**. Dono chalenge.
    - Build Command aur Install Command mein kuch bhi likha ho, hamari `vercel.json` use badal deti hai.

**Ho gaya kaise pata chalega:**

- https://bot-trading-pi.vercel.app khole toh **"Bot Dashboard"** aur peela **"NAKLI DATA"** banner dikhe. Yeh sahi hai; bot abhi juda nahi hai.
- https://bot-trading-pi.vercel.app/api/health par `{"ok":true,...}` dikhe.

## 🟡 Step 2: Website ko sirf apne liye band karo (suraksha)

1. Vercel → apni photo → **Account Settings → Authentication**: **Two-Factor Authentication chalu karo**.
2. Project → **Settings → Deployment Protection → Vercel Authentication**: production (asli website) par bhi chalu karo.
3. Logout karke website kholo: Vercel login maangna chahiye.

**Ho gaya kaise pata chalega:** private/incognito window mein website kholne par login page aaye.

(Vercel aur AWS ke menu ke naam samay ke saath thode badal sakte hain; mile nahi toh Settings mein search karo.)

**Dhyan:** Vercel ka free plan sirf personal use ke liye hai. Bot doosron ke liye banaya toh paid plan chahiye.

## 🟡 Step 3: Upstox account taiyar karo

**A. TOTP chalu karo** (bot isi se roz khud login karega):

1. Upstox app ya website ki security settings mein **TOTP / Authenticator** chalu karo. Exact menu ka naam verify nahi hua; na mile toh Upstox support se poochho.
2. TOTP chalu karte waqt QR code ke saath ek **text key (secret)** milti hai. Use apne password manager mein save karo. **Yahi bot ka "TOTP secret" hai.**
3. Authenticator app (jaise Google Authenticator) mein bhi QR scan kar lo.
4. Apna **6 digit PIN** yaad rakho; bot ko yeh bhi chahiye.

**B. Ek API app banao:**

1. Kholo: https://account.upstox.com/developer/apps ("Manage API Apps").
2. **Algo Trading App** banao. **Sirf ek app.** Purana app ho toh naya mat banao, purana hi use karo.
3. App ki **API key** aur **API secret** password manager mein save karo. **Chat mein kabhi nahi.**
4. **Static IPs abhi khaali chhodo.** Yeh Step 6 mein bharenge.

**Ho gaya kaise pata chalega:** Upstox developer page par ek app dikhe, aur aapke password manager mein 4 cheezein hon: API key, API secret, TOTP secret, PIN.

## 🟡 Step 4: Bot ka server lo (AWS Lightsail Mumbai)

1. https://aws.amazon.com par account banao (card chahiye). Root account par **MFA (2FA) chalu** karo.
2. Lightsail kholo: https://lightsail.aws.amazon.com
3. **Create instance** dabao:
    - Region: **Mumbai (ap-south-1)**
    - Platform: **Linux/Unix** → Blueprint: **OS Only → Ubuntu 24.04 LTS**
    - Plan: **$12/month** (2 GB RAM, 2 vCPU, 60 GB SSD)
    - Naam: `bot-mumbai` → **Create instance**
4. Left menu mein **Networking → Create static IP** dabao. Region Mumbai, resource `bot-mumbai`, naam `bot-ip` → **Create**.
5. Yeh IP likh lo. **Yahi aapka Upstox "Primary IP" hai.**
6. Instance → **Networking** tab → IPv4 Firewall mein sirf **SSH (22)** rakho. HTTP (80) dikhe toh hata do; bot ko koi khula darwaza nahi chahiye.

**Ho gaya kaise pata chalega:** instance "Running" dikhe, aur public IP ke paas neeli pin (static) dikhe.

**Kharcha:** ~$12/mahina + GST. Static IP machine se jude rehne tak free hai; khaali pada rahe toh charge lagta hai.

## 🟡 Step 5: Pehredaar ka server lo (Oracle Cloud Free)

1. https://www.oracle.com/cloud/free/ par account banao. **Home Region: Mumbai** chuno. Yeh baad mein nahi badalta, aur free machine sirf home region mein banti hai.
2. **Compute → Instances → Create instance:**
    - Image: **Ubuntu 24.04**
    - Shape: **VM.Standard.E2.1.Micro** ("Always Free" likha ho)
    - Public IP: haan
3. Instance ka **public IP** likh lo. **Yahi Upstox "Secondary IP" hai.**
4. Agar "out of host capacity" aaye, toh kuch ghante baad dobara try karo.

**Ho gaya kaise pata chalega:** instance "Running" dikhe aur upar "Always Free" likha ho.

**Khatra:** Oracle 7 din tak lagbhag idle machine ko delete kar sakta hai, aur machine dobara banane par IP badal sakta hai. Isliye asli paise se pehle Plan B (Vultr Mumbai $5) par jaayenge.

## 🟡 Step 6: Dono IP Upstox mein daalo

1. **Kab:** market band hone ke baad (3:30 PM ke baad) ya weekend par. Kabhi market ke beech nahi.
2. https://account.upstox.com/developer/apps → apne app par **Static IPs** dabao.
3. **Primary IP** = Lightsail static IP (Step 4). **Secondary IP** = Oracle IP (Step 5). Save karo.

**Ho gaya kaise pata chalega:** Static IPs form mein dono IP dikhen.

**Niyam:** IP hafte mein sirf ek baar badal sakte hain, aur badalte hi purane token band ho jaate hain.

## 🟡 Step 7: Chaabiyan server par encrypted rakho

**Kab:** jab Claude M1 mein server set kare, ya usse pehle. Yeh kaam **aap khud karoge**, Claude ko chaabi kabhi mat dena.

1. Lightsail mein instance kholo aur browser SSH ka **Connect** button dabao. Browser mein server ka terminal khulega (button ka exact naam thoda alag ho sakta hai).
2. Yeh line chalao (folder banta hai):
```bash
sudo mkdir -p /etc/systemd/system/bot.service.d && echo "[Service]" | sudo tee /etc/systemd/system/bot.service.d/50-secrets.conf
```
3. Har chaabi ke liye ek line chalao. Yeh chaabi poochegi; type karke Enter dabao. Screen par chaabi nahi dikhegi, aur file mein encrypted jaayegi.
```bash
systemd-ask-password -n "Upstox PIN (6 digit):" | sudo systemd-creds encrypt --name=upstox_pin -p - - | sudo tee -a /etc/systemd/system/bot.service.d/50-secrets.conf > /dev/null
```
```bash
systemd-ask-password -n "Upstox TOTP secret:" | sudo systemd-creds encrypt --name=upstox_totp_secret -p - - | sudo tee -a /etc/systemd/system/bot.service.d/50-secrets.conf > /dev/null
```
```bash
systemd-ask-password -n "Upstox API key:" | sudo systemd-creds encrypt --name=upstox_api_key -p - - | sudo tee -a /etc/systemd/system/bot.service.d/50-secrets.conf > /dev/null
```
4. File ko sirf root ke padhne layak banao:
```bash
sudo chmod 600 /etc/systemd/system/bot.service.d/50-secrets.conf
```

**Ho gaya kaise pata chalega:** `sudo grep -c SetCredentialEncrypted /etc/systemd/system/bot.service.d/50-secrets.conf` chalao; jawab **3** aaye. File mein chaabiyan sirf encrypted (lambe ulte-seedhe akshar) dikhengi.

**Yeh kaise kaam karta hai:** systemd chaabi ko machine ki apni key se encrypt karta hai. Bot chalte waqt use sirf bot process ko deta hai (Ubuntu 24.04, systemd 255).

## 🟡 Step 8: Claude ko agla kaam do (M1: live data)

Naye Claude Code session mein yeh prompt paste karo:
```
# PHASE 2 / M1 (baaki): UPSTOX FEED CLIENT + RECORDER + PROBE + SERVER SETUP.
Repo: starmovie12/Bot-trading- (code: main, docs: branch idea). Pehle README.md, PROGRESS.md, SETUP_GUIDE.md padho.
Malik ne SETUP_GUIDE ke Step 1-7 kar liye hain (Lightsail Mumbai bot server, Oracle Pehredaar, Static IPs, chaabiyan systemd-creds mein).
Kaam: (1) Upstox market feed V3 client khud likho: TLS jaanch ON, official MarketDataFeed.proto pin (sha256), reconnect,
do timestamp. Order wala koi code nahi. (2) Recorder: har raw event append-only file mein. (3) bot.service (systemd) jo
src/bot/login se roz subah TOTP login kare (secrets sirf $CREDENTIALS_DIRECTORY se). (4) Probe script (docs/02 D6).
(5) Server hardening (SSH key, firewall, swap band, chrony) ke commands malik ko step-by-step do.
Niyam: koi chaabi na maango na likho; asli order nahi; har library internet se verify; pehle chhota plan; har kadam commit; PR banao.
```

## 🟡 Step 9: Roz kya karna hai (jab bot chalega)

- **Kuch nahi dabana.** Bot subah khud login karega (TOTP), aur har login ki khabar Telegram par aayegi.
- Dashboard dekho: https://bot-trading-pi.vercel.app
- Anjaan login ki khabar aaye toh **turant** Upstox mein TOTP aur PIN badlo, aur Claude ko batao.
- **Pehle Paper Mode.** Real Money tabhi, jab Backtest Gate, Paper Gate aur Stage2 Gate pass hon (docs/03).

---

## Kabhi mat karna

- Chaabi (API key/secret, TOTP secret, PIN, Telegram token) chat, GitHub, screenshot ya email mein.
- Market ke beech Static IP badalna, ya Upstox mein doosra API app banana.
- Pehredaar ke server se login karna (bot ka token band ho jaayega).
- Backtest aur Paper pass hue bina Real Money Mode chalu karna.
- Server par "dekh lete hain" wale commands chalana jo samajh na aayein. Pehle Claude se poochho.

## Aapke faisle jo abhi baaki hain (bot inke bina asli paise par nahi chalega)

1. **Jeb ke kul nuksan ki seema** (rupaye mein, `Kul_Jeb_Nuksan_Seema`): kitna nuksan hone par bot poori tarah ruke?
2. **Risk Limit ki ikai:** percent mein rahe, ya Stop-Loss ki ginti mein (din 1, hafta 2, mahina 4)?
3. **`Data_Purana_Hadd`:** 500 ms ya 1 second? Ek kimat chuno.
4. **Nifty50 aur Sensex ke stocks ki suchi** (Breadth check ke liye), ya Claude ka prastaav (vazan mein top 10) maan lo.
5. **Vakil se:** TOTP se roz automatic login SEBI ke 2FA niyam ke andar hai ya nahi.

## Kahan kya hai

- Code: GitHub `main` branch. Idea aur saari research: branch `idea` (`docs/01_Bot_Idea_v4.md` aur aage).
- Website ka code: `dashboard/` folder. Website ki setting: `vercel.json` (root aur `dashboard/` dono mein).
- Kaam ka haal: `PROGRESS.md`.

## Sources (sab dekhe 10 Nov 2026)

- Upstox My Apps aur Static IP: https://upstox.com/developer/api-documentation/appendix/my-apps-support-for-algo-trading-circular/
- Upstox TOTP login: https://upstox.com/developer/api-documentation/get-token/
- Upstox ek user ek app: https://community.upstox.com/t/important-new-sebi-exchange-mandates-for-api-trading-effective-1st-april-2026/14822
- Lightsail plans: https://aws.amazon.com/lightsail/pricing/ · static IP: https://docs.aws.amazon.com/lightsail/latest/userguide/lightsail-create-static-ip.html · https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-static-ip-addresses-in-amazon-lightsail.html
- Oracle Always Free: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Vercel Hobby: https://vercel.com/docs/plans/hobby · vercel.json: https://vercel.com/docs/project-configuration/vercel-json
- systemd-creds (Ubuntu 24.04): https://manpages.ubuntu.com/manpages/noble/man1/systemd-creds.1.html
- SEBI F&O study (Aug 2026): https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf
