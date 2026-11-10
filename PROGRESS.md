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

## Agla kadam
1. Malik: Vercel par website lagao (`dashboard/README.md` ke steps), aur Deployment Protection chalu karo.
2. M1 baaki: Upstox feed client (TLS ON, official .proto pin), Recorder, probe. Asli Upstox connection ke liye trial server (Lightsail Mumbai) aur malik ka "go" chahiye.
3. Malik ke faisle baaki: `Data_Purana_Hadd` ki ek kimat, `Kul_Jeb_Nuksan_Seema`, Risk Limit ki ikai (Sawal 118).
