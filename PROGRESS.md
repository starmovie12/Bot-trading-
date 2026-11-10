# PROGRESS (code, branch `main`)

Docs ka progress: branch `idea`, `docs/PROGRESS.md`.

## Milestones (docs/04_Build_Roadmap.md)
| M | Naam | Status |
|---|---|---|
| M0 | Neev: dhaancha, CI, hash-lock, niyam-file + loader | **ho gaya (10 Nov 2026)** |
| M1 | Apna feed client + Recorder + probe | baaki (malik ka roz login aur trial server chahiye) |
| M2 | Candles, indicators, IV/greeks, replay | baaki |
| M3 | Check engine + scoring | baaki |
| M4 | Backtester + Backtest Gate | baaki (data kharid aur NSE licence jawab chahiye) |
| M5-M10 | Haath, Pehredaar, Dashboard, Paper, Stage2, Poora Lot | baaki |

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

## Agla kadam
M1 ke liye malik se: Upstox ka roz login kaun aur kaise karega (Sawal 139), aur trial server (Lightsail Mumbai) kab lena hai. Bina malik ke "go" ke koi kharcha ya broker connection nahi.
