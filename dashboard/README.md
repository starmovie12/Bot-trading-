# Dashboard (Vercel par, `.vercel.app`)

Malik ka niyam (10 Nov 2026): website Vercel par. Abhi yeh **dhaancha** hai: page "NAKLI DATA" dikhata hai,
kyunki bot abhi broker se juda nahi. Controls (Start/Stop/Kill-Switch) M7 mein aayenge.

## Vercel par lagane ke steps (malik khud karega; koi chaabi chat mein nahi)
1. vercel.com par GitHub se login karo, aur Vercel account par **2FA chalu** karo.
2. **Add New → Project →** `starmovie12/Bot-trading-` import karo.
3. **Root Directory:** khaali (repo root) ya `dashboard`: **dono chalenge** (root `vercel.json` aur `dashboard/vercel.json` dono framework "Other", koi build nahi, sahi output folder batate hain).
4. **Deploy** dabao. URL milega: `<naam>.vercel.app`.
5. **Settings → Deployment Protection → Vercel Authentication** production par bhi chalu karo, taaki website sirf aapke Vercel login se khule.
6. `DASHBOARD_PUSH_KEY` abhi **mat** daalo. Yeh M7 mein lagega, aur iski kimat kabhi chat ya repo mein nahi jaayegi.

Vercel production `main` branch se banata hai. Isliye yeh PR merge hone ke baad hi website par dikhega.

## Free plan ki shartein (dekha 10 Nov 2026, https://vercel.com/docs/plans/hobby)
- Hobby plan free hai, par **sirf personal, non-commercial use** ke liye.
- Mahine mein 1,000,000 function calls aur 4 Active CPU-ghante tak free; seema tootne par ~30 din ruk sakta hai.
- Isliye page har **5 second** refresh hota hai (`Dashboard_Push_Samay`), 1 second nahi.

## 500 FUNCTION_INVOCATION_FAILED wali galti (10 Nov 2026)
Website par har page function se ja raha tha. Sabse sambhav wajah: project repo root se bana aur Vercel ne Python project dekh kar galat tareeke se chalaya. Fix: root `vercel.json` (`framework: null`, `installCommand: ""`, `outputDirectory: "dashboard/public"`), root `api/` jo `dashboard/api` ko hi chalata hai, aur `.vercelignore`.

## STATIC_BUILD_NO_OUT_DIR wali galti (10 Nov 2026, dusra fix)
Vercel build ne "No Output Directory named public" diya. Vercel CLI 65.11.0 se yahi build local par har layout mein chalaya; builder output ka rasta `workPath + entrypoint ka folder + outputDirectory` se banata hai, aur cloud par entrypoint alag ho sakta hai. Fix: `build.mjs` website ki files `dashboard/public` ke saath repo root `public/` mein bhi rakhta hai, aur dono `vercel.json` mein `outputDirectory: "public"`. Build log mein `[bot-dashboard]` wali lines cwd aur settings dikhati hain (koi secret nahi).

## Suraksha
- Koi npm dependency nahi. Koi inline script nahi; sakht CSP aur security headers (`vercel.json`).
- Saara text `textContent` se lagta hai (XSS se bachav).
- Bot ki haalat sirf signed (HMAC) POST se aayegi (`lib/state.mjs`); `Command_Max_Umar` (5 s) se purana signature reject.
- Dashboard ke paas broker ya Telegram ki chaabi kabhi nahi hogi.

## Tests
```bash
cd dashboard && node --test
```
