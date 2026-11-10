# Deploy: EK HI SERVER (malik ka niyam, 11 Nov 2026: ₹1,500/mahina budget)

| Kya | Kahan | Kharcha |
|---|---|---|
| Bot (Python) | AWS Lightsail Mumbai, Linux $12 plan (2 vCPU, 2 GB) + static IP | ~₹1,330/mahina (dekha 9 Nov 2026) |
| Pehredaar (Go) | **Usi server par alag systemd service** (`pehredaar.service`) | ₹0 |
| Website | Vercel Hobby (repo Bot-trading-website-) | ₹0 |

## Ek server ka khatra (saaf baat)
Server hi band ho gaya (AWS outage, disk full) toh bot aur Pehredaar **dono** ruk jaate hain.
Isliye bachav broker par hai, server par nahi:
1. **Broker Stop:** har entry ke turant baad SL-M order broker par (server mare toh bhi SL broker par zinda).
2. Bot apni "heartbeat" website ko bhejta hai; 30 s tak na aaye toh website laal (aur M7 mein Telegram alert).
3. Doosra server tabhi, jab bot munafa dene lage aur malik paise se kharidna chahe. Tab tak sab isi ek server par.

## Memory
2 GB RAM: bot `MemoryMax=1200M`, Pehredaar `MemoryMax=200M` + `OOMScoreAdjust=-500` (kernel pehle bot ko rokega).
Swap band (latency). Chrony se ghadi sahi.
