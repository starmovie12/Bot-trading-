# PROGRESS (code, branch `main`)

Docs ka progress: branch `idea`, `docs/PROGRESS.md`.

## Milestones (docs/04_Build_Roadmap.md)
| M | Naam | Status |
|---|---|---|
| M0 | Neev: dhaancha, CI, hash-lock, niyam-file + loader | **ho gaya (10 Nov 2026)** |
| M1 | Apna feed client + Recorder + probe | **chal raha:** auto-login (TOTP) module + tests ho gaye; feed client, Recorder, probe baaki |
| M2 | Candles, indicators, IV/greeks, replay | baaki |
| M3 | Check engine + scoring | baaki |
| M4 | Backtester + Backtest Gate | baaki (data kharid aur NSE licence jawab chahiye) |
| M7 | Dashboard | **dhaancha shuru:** Vercel page (NAKLI data), signed push jaanch, security headers; login (Vercel Authentication), store, controls baaki |
| M5, M6, M8-M10 | Haath, Pehredaar, Paper, Stage2, Poora Lot | baaki |

## M0 acceptance (docs/04 M0)
| Test | Nateeja |
|---|---|
| Lint (ruff) aur format | PASS |
| Type check (mypy strict) | PASS |
| Tests (pytest, network band) | PASS: 18 tests |
| Dev deps sirf hash-match se install (`--require-hashes`) | PASS (40 packages, 739 hashes) |
| Dependency audit (pip-audit) | PASS: koi known vulnerability nahi |
| Niyam-file: 202 numbers, galat status/unit/range par fail | PASS |
| TLS-off aur chaabi jaisa text code mein nahi | PASS |
| Go: gofmt, vet, test, govulncheck | PASS |
| Koi network call / order code nahi | PASS (test se) |

## Log
- 10 Nov 2026: Malik ke kehne par docs branch `idea` mein gaye, `main` par code shuru (M0).
- 10 Nov 2026: Niyam-file idea v4 (sha256 `0bb3218f…d9d7`) se bani. 81 numbers ki saaf typed kimat; 121 malik/backtest ke faisle ka intezaar karte hain (code guess nahi karta).
- Lease ka niyam (Bot_Lease_Samay 4 s < Pehredaar ke control ka samay 6 s) Python aur Go dono mein test hai.

## Log (M1 shuru, 10 Nov 2026)
- Malik ke faisle: roz haath se login nahi (Bot TOTP raste se khud), website Vercel par. Idea v4 (branch `idea`) mein likhe: F-80, F-81, TAKRAAV #42-#43.
- `src/bot/login/`: RFC 6238 ke saare test vectors pass; Upstox TOTP request docs (10 Nov 2026) jaisa; Pehredaar ko login mana; token print par `****`; nakli server par tests. **Asli login nahi kiya.**
- `dashboard/`: 8 Node tests; browser mein light/dark/mobile jaancha, koi console error nahi.
- `config/niyam.toml` idea v4 ke naye version se dobara bani (203 numbers; naya `Dashboard_Push_Samay`).
- Tests: Python 38, Node 8, Go 2.

## Log (10 Nov 2026, website fix + setup guide)
- Vercel par `bot-trading-pi.vercel.app` har path par 500 FUNCTION_INVOCATION_FAILED de raha tha. Fix: root `vercel.json` + root `api/` + `.vercelignore`; dono layout (root aur `dashboard`) local Vercel-jaise server par jaanche (har path 200), phone dark mode screenshot theek.
- `SETUP_GUIDE.md` + `SETUP_GUIDE.pdf`: 9 step, peeli Step headings (PDF), kya khareedna (ek hi Lightsail $12 server + Vercel = ~₹1,330), chaabiyan systemd-creds se.

- 10 Nov 2026: PR #3 ke baad Vercel build "STATIC_BUILD_NO_OUT_DIR". Vercel CLI 65.11.0 aur @vercel/static-build 26.0.1 ka code padh kar wajah samjhi (output rasta = workPath + entrypoint ka folder + outputDirectory). Fix: `dashboard/build.mjs` + dono `vercel.json` mein `outputDirectory: public`; 5 layout local par pass (static 3 files + 2 functions).

- 10 Nov 2026 (malik): website aur bot alag branch mein. `website` = sirf Vercel website (repo root par, koi build nahi); `bot` = bot code (is branch par Vercel build band). Vercel ki asli galti mili: project ka **Root Directory `pehredaar`** set tha (build log: `/vercel/path0/pehredaar/build.mjs`). Malik ko 2 settings badalni hain (SETUP_GUIDE Step 1).

## Agla kadam
1. Malik: Vercel par naya project repo `Bot-trading-website-` se banao (SETUP_GUIDE Step 1), aur Deployment Protection chalu karo.
2. M1 baaki: Upstox feed client (TLS ON, official .proto pin), Recorder, probe. Asli Upstox connection ke liye trial server (Lightsail Mumbai) aur malik ka "go" chahiye.
3. Malik ke faisle baaki: `Data_Purana_Hadd` ki ek kimat, `Kul_Jeb_Nuksan_Seema`, Risk Limit ki ikai (Sawal 118).

## Log (11 Nov 2026)
- Malik ke kehne par website aur bot alag branch mein: `website` (sirf Vercel website), `bot` (sirf bot code). `idea` aur `bot` par Vercel build band.
- `main` ab `bot` jaisa hi code (PR se). Purana `dashboard/` folder `main` se hata; website ka code branch `website` mein hai.
- Tests: Python 38 (`bot`), Node 10 (`website`), Go pass.
- Malik ke kehne par website alag **repo** mein: https://github.com/starmovie12/Bot-trading-website- (branch `main`). Is repo se branch `website` delete. Bot ka code is repo ki `main` mein.
- SETUP_GUIDE Step 1 badla: Vercel par naya project naye repo se (Root Directory khaali, production branch `main`); purana project delete.

## Log (11 Nov 2026, strategy v2 + ek server)
- Malik ka niyam: **sirf EK Amazon Lightsail Mumbai server** (~₹1,330/mahina, ₹1,500 ke andar). Koi free/doosra server nahi. Pehredaar usi par alag systemd service (`deploy/`).
- Internet research (expiry Tue/Thu, Bank Nifty weekly band, lot 65/30/20, STT 0.15%, SEBI FY25 ~91% nuksan, VRP) se `strategy/STRATEGY_v2.md` (v2.3) aur 3 audit round `strategy/AUDIT_ROUNDS.md`.
- Naya code `src/bot/strategy/`: instruments (expiry calendar), costs (kharcha, andaza fields alag), selection (ITM→ATM, OTM kabhi nahi, affordability + risk seema par SKIP), rules (entry/exit, time-stop, trailing, halt, risk per trade). Tests: `tests/test_strategy.py`.
- Poori audit report: `AUDIT_REPORT.md`.
- Malik: ₹15,000 = ek mahine ki salary, "aakhri mauka". Isliye **kul jeb ka taala** (`account_allows_trading`): seema par bot hamesha ke liye band. Prastaav ₹4,000; faisla malik ka.
- `bot/dimaag/` (regime, setups) aur `bot/backtest/` (engine + gate) bane. Round 4: risk sirf 25% SL se ginne par bot kabhi trade nahi leta tha; ab chart SL × delta.
- NAKLI data par backtest: Gate FAIL (sirf 9 trade < 200). Yeh number asli market ke nahi.

