# Bot-trading- (code)

BankNifty, Nifty50 aur Sensex options ka trading bot. **Yeh `main` branch sirf code ke liye hai.**
Poora idea (v4), audit, tech faisle, strategy plan aur roadmap **branch `idea`** par hain:
`docs/01_Bot_Idea_v4.md`, `docs/02_Tech_Decisions.md`, `docs/03_Strategy_Edge_Plan.md`, `docs/04_Build_Roadmap.md`.

## Abhi kahan hain
- M0 (Neev) ho gaya. **M1 shuru:** auto-login module (TOTP) aur Vercel website ka dhaancha. Status: `PROGRESS.md`.
- **Abhi kisi broker (Upstox) ya Telegram se koi asli connection nahi.** Login ka code hai, par asli login nahi kiya gaya. Koi order code nahi.
- Profit ki koi guarantee nahi. Goal: kharche ke baad positive expectancy **sabit** karna; sabit na ho toh live nahi.

## Dhaancha
| Folder | Kya hai |
|---|---|
| `src/bot/niyam.py` | Niyam-file ka loader aur validation. Code koi number guess nahi karta |
| `src/bot/login/` | Roz ka auto-login (malik ka niyam: haath se nahi). TOTP (RFC 6238), secrets sirf encrypted store se, token sirf memory mein |
| `src/bot/dashboard_push.py` | Bot se website ko signed haalat |
| `dashboard/` | Vercel website (static page + function). Lagane ke steps: `dashboard/README.md` |
| `vercel.json`, `api/`, `.vercelignore` | Vercel project repo root se bana ho tab bhi website chale |
| `SETUP_GUIDE.md` / `SETUP_GUIDE.pdf` | **Malik ke liye step-by-step setup** (kya khareedna, kya settings, kis kram mein) |
| `src/bot/dimaag/` | Feed, candles, checks, scoring (M2, M3) |
| `src/bot/haath/` | Order manager, broker ko hukm dene wala akela hissa (M5) |
| `src/bot/recorder/` | Har event ka record, replay ke liye (M1) |
| `pehredaar/` | Pehredaar (Go): Lease ka niyam; baaki M6 mein |
| `config/niyam.toml` | Idea ki Numbers list (202 numbers). **Haath se mat badlo**; idea file badlo aur generator chalao |
| `tools/niyam_from_idea.py` | Idea file se `config/niyam.toml` banane wala |
| `tests/` | Tests (network band) |

## Checks chalana (developer ke liye)
```bash
uv venv .venv && . .venv/bin/activate
```
```bash
uv pip install --require-hashes -r requirements-dev.lock
```
```bash
ruff check . && ruff format --check . && mypy && pytest
```
```bash
PYTHONPATH=src python -m bot.niyam config/niyam.toml
```
```bash
cd pehredaar && go vet ./... && go test ./...
```
```bash
cd dashboard && node --test
```

## Niyam (har session)
- Key, token, password kabhi code, config, log ya chat mein nahi.
- Har dependency exact version + hash ke saath (`requirements-dev.lock`). TLS jaanch kabhi band nahi.
- Numbers sirf `config/niyam.toml` se; "Tay nahi" ya range wale number par code `NeedsDecision` deta hai.
