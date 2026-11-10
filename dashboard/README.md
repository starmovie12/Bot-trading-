# Dashboard (Vercel par, `.vercel.app`)

Malik ka niyam (10 Nov 2026): website Vercel par. Abhi yeh **dhaancha** hai: page "NAKLI DATA" dikhata hai,
kyunki bot abhi broker se juda nahi. Controls (Start/Stop/Kill-Switch) M7 mein aayenge.

## Vercel par lagane ke steps (malik khud karega; koi chaabi chat mein nahi)
1. vercel.com par GitHub se login karo, aur Vercel account par **2FA chalu** karo.
2. **Add New → Project →** `starmovie12/Bot-trading-` import karo.
3. **Root Directory:** `dashboard`. **Framework Preset:** Other. Build command khaali chhodo.
4. **Deploy** dabao. URL milega: `<naam>.vercel.app`.
5. **Settings → Deployment Protection → Vercel Authentication** production par bhi chalu karo, taaki website sirf aapke Vercel login se khule.
6. `DASHBOARD_PUSH_KEY` abhi **mat** daalo. Yeh M7 mein lagega, aur iski kimat kabhi chat ya repo mein nahi jaayegi.

Vercel production `main` branch se banata hai. Isliye yeh PR merge hone ke baad hi website par dikhega.

## Free plan ki shartein (dekha 10 Nov 2026, https://vercel.com/docs/plans/hobby)
- Hobby plan free hai, par **sirf personal, non-commercial use** ke liye.
- Mahine mein 1,000,000 function calls aur 4 Active CPU-ghante tak free; seema tootne par ~30 din ruk sakta hai.
- Isliye page har **5 second** refresh hota hai (`Dashboard_Push_Samay`), 1 second nahi.

## Suraksha
- Koi npm dependency nahi. Koi inline script nahi; sakht CSP aur security headers (`vercel.json`).
- Saara text `textContent` se lagta hai (XSS se bachav).
- Bot ki haalat sirf signed (HMAC) POST se aayegi (`lib/state.mjs`); `Command_Max_Umar` (5 s) se purana signature reject.
- Dashboard ke paas broker ya Telegram ki chaabi kabhi nahi hogi.

## Tests
```bash
cd dashboard && node --test
```
