# Bot Dashboard (branch `website`)

Yeh branch **sirf website** hai. Vercel isi branch se `bot-trading-pi.vercel.app` banata hai.
Bot ka code branch **`bot`** mein hai, aur idea/docs branch **`idea`** mein.

| Branch | Kya hai |
|---|---|
| `website` | Yeh website (Vercel) |
| `bot` | Bot ka code (Python, Pehredaar, tests, SETUP_GUIDE) |
| `idea` | Idea v4, audit, tech faisle, strategy, roadmap, research |

## Vercel settings (ek baar)
1. **Settings → Build and Deployment → Root Directory:** khaali chhodo (agar `pehredaar` likha hai toh hatao) → **Save**.
2. **Settings → Environments → Production → Branch Tracking:** `website` likho → **Save**.
3. **Deployments** mein jaakar sabse naye deployment par **⋯ → Redeploy** (ya is branch par koi naya commit).
4. **Settings → Deployment Protection → Vercel Authentication** production par bhi chalu karo; Vercel account par 2FA.

Website ko build ki zaroorat nahi: `vercel.json` mein framework "Other", install skip, output `public/`.

## Folder
| Folder | Kya |
|---|---|
| `public/` | Page (`index.html`, `app.js`, `style.css`) |
| `api/` | `/api/state`, `/api/health` (Vercel functions) |
| `lib/state.mjs` | Haalat ka dhaancha + signed push ki jaanch (bot ka `dashboard_push.py` yahi signature banata hai) |
| `test/` | Tests: `node --test` |

## Free plan (dekha 10 Nov 2026, https://vercel.com/docs/plans/hobby)
Sirf personal, non-commercial use. Mahine mein 1,000,000 function calls; isliye page har 5 second refresh hota hai.

## Suraksha
Koi npm dependency nahi, koi inline script nahi, sakht CSP aur headers, saara text `textContent` se.
Bot ki haalat sirf signed (HMAC) POST se aayegi; 5 second se purana signature reject. Website ke paas broker ya Telegram ki chaabi kabhi nahi.

## Tests
```bash
node --test
```
