# R-b: Third-party Repos, Licence aur Security padhai

> Phase 1 research doc (sirf docs, koi production code nahi). Jaanch ki tarikh: **10 Nov 2026**.
> Main vakil nahi hoon. Licence wali har baat **vakil se confirm karna**.
> Koi bhi repo "surakshit" nahi likha gaya. Sirf yeh likha hai ki kya dekha.

## Saar (10 line)

1. **Upstox official SDK (`upstox/upstox-python`, MIT)**: REST ke liye pinned + hash-locked dependency ke roop mein use karo. Lekin iske **WebSocket feeder TLS certificate check band karte hain** (`ssl.CERT_NONE`, `check_hostname: False`) aur usi connection par access token bhejte hain. Isliye feeder khud likho, TLS verification ON rakho.
2. **openalgo (AGPL-3.0)**: use mat karo, vendor bhi mat karo. Licence ka sabse bada khatra yahi hai, aur iska Upstox streaming code bhi `CERT_NONE` use karta hai. Iska ek GitHub advisory bhi hai (SMTP TLS off).
3. **ta (MIT)**: khud likho (EMA/RSI/ATR/ADX/VWAP). Repo ki `test/data/*.csv` files test vector ke roop mein kaam aayengi. Dhyaan do: `ta` ka VWAP *rolling 14-bar* hai, session-reset wala nahi.
4. **smart-money-concepts (MIT)**: khud likho. Iska `swing_highs_lows` **future candles dekhta hai** (`shift(-n)`), isliye backtest mein lookahead bias aayega.
5. **vollib (MIT)**: Black-Scholes/Black-76 + IV khud likho, aur `tests/test_data.json` se answers milao. Dhyaan do: PyPI par 1.0.11/1.0.12 hain, lekin GitHub par sabse naya tag v1.0.10 hai.
6. **NseIndiaApi (GPL-3.0)**: use mat karo. Yeh NSE website ki unofficial API hai jo browser User-Agent ka naqli roop leti hai. Holidays aur option chain Upstox ki official API mein bhi hain.
7. **yfinance (Apache-2.0)**: bot mein nahi. Sirf alag research venv mein chalao. README khud kehta hai ki Yahoo API "personal use only" hai.
8. **supervisor (BSD-derived)**: zaroorat nahi. systemd ka `Restart=` + `WatchdogSec=` kaafi hai aur extra dependency bhi nahi lagti.
9. **python-telegram-bot (GPL-3 ya LGPL-3)**: khud likho. Seedha Bot API par HTTPS call (`sendMessage`) karo, 1-2 functions kaafi hain.
10. **Supply chain**: hash-locked lockfile + pip-audit/OSV zaroori hai. Misaal: LiteLLM (jo openalgo use karta hai) ke kuch PyPI versions mein OSV ne malicious code record kiya hai (MAL-2026-2144).

---

## Tareeqa (kaise jaancha)

- Har repo ko scratchpad ke andar **apne alag khaali folder** mein `git clone --depth 50` kiya: `/tmp/claude-0/-home-user-Bot-trading-/77174dff-d2c1-5e9c-9609-264ce8112447/scratchpad/repos/<naam>/src`. Project repo ke andar kuch clone nahi kiya. **Kisi repo ka code chalaya nahi.** Sirf `grep`/`sed`/`git log` se padha.
- Security grep ek alag folder ki script se kiya (`.../scratchpad/tools/secgrep.sh`). Isne yeh dhoondha: `http/https/ws/wss` hosts, `subprocess`, `os.system`, `eval(`, `exec(`, `pickle`, `marshal`, `importlib`, file-write patterns, aur telemetry words.
- Metadata ke sources: GitHub repo page (WebFetch), deps.dev API (stars/forks/OpenSSF Scorecard), PyPI JSON API (release/upload date), `git ls-remote --tags`, OSV.dev API (advisories), aur har repo ka GitHub Security → Advisories page.
- GitHub REST API (`api.github.com/repos/...`) is session mein band tha (proxy ne mana kiya). Isliye "owner type", "archived flag" jaisi API fields seedhe nahi mili.
- Stars GitHub page par rounded dikhte hain (jaise "5.3k"). deps.dev ka exact number uske snapshot ka hai, aaj ka nahi.

---

## (1) Har repo ka block

### 1. bukosabino/ta

| Field | Value |
|---|---|
| Repo | `bukosabino/ta`: https://github.com/bukosabino/ta |
| Kaam | pandas/numpy par bani technical indicators library (EMA, RSI, ATR, ADX, VWAP, MACD, Bollinger, etc.) |
| Zaroori file (asli path) | Sab maujood hain: `ta/trend.py` (`EMAIndicator` line 158, `ADXIndicator` line 678), `ta/momentum.py` (`RSIIndicator` line 14), `ta/volatility.py` (`AverageTrueRange` line 14), `ta/volume.py` (`VolumeWeightedAveragePrice` line 424), `ta/utils.py` (`_ema`) |
| License | **MIT**. `LICENSE` file mein likha hai: "Copyright 2020 Darío López Padial (Bukosabino)" |
| Maalik | `bukosabino` (GitHub user/org type: verify nahi hua, API band tha) |
| Aakhri commit | `a890410` · 2026-03-18 · "Update README.md" |
| Aakhri release | PyPI `ta` **0.11.0**, upload 2023-11-02. Git tag bhi 0.11.0 hai (kul 65 tags). Matlab 2023 ke baad koi PyPI release nahi aayi |
| Stars/forks | GitHub page: **5.3k / 1.2k**. deps.dev: 5245 / 1162, 160 open issues. OpenSSF Scorecard 2.9/10 (snapshot 2026-08-24) |
| Advisories | OSV (PyPI `ta`): koi nahi. GitHub Security tab: "There aren't any published security advisories." |
| Dependencies | `setup.py`: `numpy`, `pandas` (version pin nahi). `requirements-core.txt`: `numpy==1.21.5`, `pandas==1.3.5` (purane pins) |
| Kya dekha (security) | Imports sirf `numpy`, `pandas`, `math`, `typing` ke hain. `subprocess`/`eval`/`exec`/`pickle`/`importlib` ek bhi nahi. File write: 0. URLs sirf docstrings mein hain (stockcharts.com, investopedia, wikipedia), koi network code nahi |
| Formula ke baare mein dekha | EMA = `ewm(span=n, adjust=False)`. RSI = `ewm(alpha=1/n, adjust=False)` (Wilder style). **VWAP = rolling window (default `window=14`)**, jabki docstring "current day" kehta hai. Intraday session-reset VWAP ke liye yeh sahi nahi baithta. `test/data/` mein 32 CSV hain (`cs-rsi.csv`, `cs-atr.csv`, `cs-adx.csv`, `cs-vwap.csv`, ...) |
| Faisla | **Khud likho + `test/data/*.csv` se test vector milao.** Wajah: formula chhote hain, aur library numpy/pandas pin aur VWAP definition hamare kaam se mel nahi khaate. Test CSV copy karni ho toh MIT notice saath rakho |
| Jaanch ki tarikh | 10 Nov 2026 |

### 2. joshyattridge/smart-money-concepts

| Field | Value |
|---|---|
| Repo | `joshyattridge/smart-money-concepts`: https://github.com/joshyattridge/smart-money-concepts |
| Kaam | SMC/ICT indicators: FVG, swing highs/lows, BOS/CHoCH, order blocks, liquidity, previous high/low, sessions, retracements |
| Zaroori file | `smartmoneyconcepts/smc.py` maujood hai (987 lines) |
| License | **MIT**. `LICENSE` mein copyright "Copyright (c) 2020 NeuralNine" likha hai, yaani repo owner ka naam nahi (sirf jo dekha woh likha hai) |
| Maalik | `joshyattridge` |
| Aakhri commit | `1b62fd6` · 2026-04-03 · "Update version to 0.0.27 in setup.py and smc.py" |
| Aakhri release | PyPI `smartmoneyconcepts` **0.0.27**, upload 2026-04-03. Lekin sabse naya git tag **0.0.26** hai, yaani 0.0.27 ka tag repo mein nahi dikha. Kul 16 tags |
| Stars/forks | GitHub page: **2.2k / 907**. deps.dev par project "not found", isliye Scorecard nahi mila |
| Advisories | OSV: koi nahi. GitHub tab: koi nahi |
| Dependencies | `pandas>=2.0.2`, `numpy>=1.24.3`, `numba>=0.58.1`. Dhyaan do: `smc.py` `numba` import nahi karta, phir bhi woh install hota hai |
| Kya dekha (security) | Network/subprocess/eval/pickle/file-write ek bhi nahi. `__init__.py` import hote hi rangeen "give a star" banner print karta hai, jab tak env `SMC_CREDIT` `'1'` se alag na ho |
| Logic ke baare mein dekha | `swing_highs_lows()` mein `ohlc["high"].shift(-(swing_length // 2)).rolling(...)` hai, yaani yeh **aage ki candles dekhta hai**. BOS/CHoCH/OB/liquidity sab swings par tike hain. Backtest mein isse lookahead bias aayega, aur live mein swing `swing_length` bars ki deri se confirm hoga |
| Faisla | **Khud likho** (concept samajhne ke liye padho). Wajah: lookahead, extra numba dependency, aur import par print side-effect |
| Jaanch ki tarikh | 10 Nov 2026 |

### 3. vollib/py_vollib

| Field | Value |
|---|---|
| Repo | `vollib/py_vollib`: https://github.com/vollib/py_vollib |
| Kaam | Black, Black-Scholes, Black-Scholes-Merton price, implied volatility (Jäckel "Let's Be Rational"), greeks (analytical/numerical) |
| Zaroori file | Maujood hain: `vollib/black_scholes/implied_volatility.py` (105 lines), `vollib/black_scholes/greeks/analytical.py` (280), `vollib/black/` (`implied_volatility.py`, `greeks/`). Package ka naam ab `vollib` hai (commit 2026-01-13 "Rename package py_vollib → vollib"). `py_vollib/__init__.py` ab sirf compat shim hai jo `DeprecationWarning` deta hai. `vollib/lets_be_rational/__init__.py` asal kaam bahari package `py_lets_be_rational` se import karta hai |
| License | **MIT**, "Copyright (c) 2015, Gammon Capital LLC" |
| Maalik | `vollib` org |
| Aakhri commit | `master`: `11f2058` · 2026-04-30 · "Release vollib 1.0.7". Branch `refactor/extract-packages`: 2026-05-29 · "Release vollib 1.0.10" (tag v1.0.10 isi branch par hai) |
| Aakhri release | PyPI `vollib` **1.0.11** (upload 2026-06-01), PyPI `py_vollib` **1.0.12** (upload 2026-06-01). GitHub tags sirf **v1.0.10 tak** hain. Matlab PyPI 1.0.11/1.0.12 ka matching tag repo mein nahi dikha |
| Stars/forks | GitHub page: **446 / 97** (deps.dev 444/97) |
| Advisories | OSV (`vollib`, `py_vollib`, `py-lets-be-rational`): koi nahi. GitHub tab: koi nahi |
| Dependencies | `master` pyproject mein 7 direct hain: `cody-special`, `piecewise-rational`, `py_lets_be_rational`, `simplejson`, `numpy`, `pandas`, `scipy`. `cody-special` aur `piecewise-rational` dono PyPI 1.0.0 par hain, upload 2026-01-13, author "vollib team" |
| Kya dekha (security) | Network/subprocess/eval/pickle/file-write ek bhi nahi. `importlib` sirf `py_vollib` shim mein hai (module alias ke liye) |
| Test data | `tests/test_data.json` mein columns S, K, R, t, v, bs_call, bs_put, aur greeks (CD, CG, CT, CV, CR, PD, ...) hain. Achha test vector source hai |
| Faisla | **Khud likho** (Black-Scholes/Black-76 price, IV ke liye Newton + Brent/bisection fallback, analytical greeks) **+ `tests/test_data.json` se milao.** Wajah: formula chhota hai, aur repo/PyPI version gap ke saath 7 dependencies hain |
| Jaanch ki tarikh | 10 Nov 2026 |

### 4. marketcalls/openalgo

| Field | Value |
|---|---|
| Repo | `marketcalls/openalgo`: https://github.com/marketcalls/openalgo |
| Kaam | Self-hosted Flask platform: 30+ Indian brokers ka API bridge, websocket proxy, sandbox (paper trading), strategy/script runner, AI agent (LiteLLM), Telegram/WhatsApp bot, MCP server |
| Zaroori file | Sab maujood hain. `broker/upstox/` (6,329 py lines) mein `api/auth_api.py`, `api/order_api.py`, `api/data.py`, `api/funds.py`, `api/gtt_api.py`, `api/margin_api.py`, `api/rate_limiter.py`, `database/master_contract_db.py`, `mapping/*`, `streaming/MarketDataFeedV3.proto`, `streaming/upstox_client.py`, `streaming/upstox_adapter.py` hain. `services/` (104,819 py lines), `sandbox/` (10,413), `websocket_proxy/` (6,185) |
| License | **AGPL-3.0**. `License.md` mein GNU AGPL v3 ka poora text hai. README kehta hai: "OpenAlgo is released under the **AGPL V3.0 License**" |
| Maalik | `marketcalls` |
| Aakhri commit | `a1b9e32` · 2026-11-06 · "Fix : resolved issues present in the PR 2396 (#2397)" |
| Aakhri release | GitHub page par Releases section khaali hai. 74 git tags hain, lekin koi semver nahi (jaise `openalgov2-cicd`). `pyproject.toml` mein `version = "2.0.3.3"`. Dhyaan do: PyPI `openalgo` 2.0.5 (MIT) **alag repo** (`openalgo-python-library`, client) hai, yeh server nahi |
| Stars/forks | GitHub page: **3.0k / 1.4k**, watchers 66. deps.dev: 414 open issues |
| Advisories | GitHub Security tab par **GHSA-4vvw-xw2w-38g8**: "TLS certificate verification disabled in SMTP connections exposes mail credentials and password reset links" (Moderate, published Nov 1, 2026). OSV: server PyPI par nahi hai, isliye package query lagu nahi |
| Dependencies | `requirements.txt` mein 149 pinned (`==`) lines, `pyproject.toml` mein ~151 dependency lines, `uv.lock` bhi hai. Inmein `litellm==1.106.6` hai. OSV ke MAL-2026-2144 record ke mutabik LiteLLM ke versions 1.82.7, 1.82.8, 1.107.0 malicious the. 1.106.6 us list mein nahi hai |
| Kya dekha (security) | (a) **`broker/upstox/streaming/upstox_client.py:226` mein `sslopt={"cert_reqs": ssl.CERT_NONE}` hai.** Aur bhi kai brokers mein yahi pattern hai, `broker/paytm/.../paytm_websocket.py:253` ka comment kehta hai: "The rest of the codebase still uses CERT_NONE on most brokers". (b) Upstox hosts: `api.upstox.com`, `api-hft.upstox.com` (orders), `assets.upstox.com` (instrument master `.json.gz` download hota hai, temp file likh kar baad mein delete). (c) Poore repo mein 30+ broker hosts, `api.telegram.org`, aur AI ke liye `api.openai.com` (voice), `api.tavily.com`, `api.perplexity.ai` (websearch tool). Provider list mein openai/anthropic/ollama waghera hain (LiteLLM ke through). `services/agent/builder.py:1070` par `telemetry=False` set hai. (d) `services/openscript_runner_service.py` user scripts ko `subprocess.Popen` se chalata hai (design se). `websocket_proxy/app_integration.py` proxy ko subprocess mein chala sakta hai. (e) `frontend/dist/` mein prebuilt JS committed hai (370 files, ~13 MB), jise review karna mushkil hai. (f) PostHog/Sentry jaisi telemetry grep mein nahi mili (jo mila woh "plausible" jaise aam English words the) |
| Faisla | **Use nahi, vendor nahi. Khud likho** (Upstox official docs/SDK se). Wajah: AGPL copyleft, bahut bada attack surface (AI agent, script runner, 150 dependencies), aur Upstox WebSocket mein TLS check band. Sirf padhne ke liye reference theek hai, code copy mat karna |
| Jaanch ki tarikh | 10 Nov 2026 |

### 5. BennyThadikaran/NseIndiaApi

| Field | Value |
|---|---|
| Repo | `BennyThadikaran/NseIndiaApi`: https://github.com/BennyThadikaran/NseIndiaApi |
| Kaam | NSE website ki **unofficial** JSON endpoints (`https://www.nseindia.com/api`) aur archives (`nsearchives.nseindia.com`) ka wrapper: option chain, holidays, status, corporate filings, bhavcopy |
| Zaroori file | Asli path repo root se `src/nse/NSE.py` hai (2,307 lines). Saath mein `cookie_store.py`, `transport.py`, `retry.py`, `_utils.py`. `holidays()` line 1771 par hai aur `{base_url}/holiday-master` call karta hai |
| License | **GPL-3.0** (`LICENSE` = GNU GPL v3 text) |
| Maalik | `BennyThadikaran` |
| Aakhri commit | `b7fd7eb` · 2026-10-30 · "bump to version 5.1.1" |
| Aakhri release | Tag `v5.1.1`. PyPI `nse` **5.1.1**, upload 2026-10-30. Kul 60 tags |
| Stars/forks | GitHub page: **162 / 46** |
| Advisories | OSV: koi nahi. GitHub tab: koi nahi |
| Dependencies | `httpx~=0.28.1`, `pyrate-limiter` (`==3.9` ya `~=4.5.0`). Optional: `httpx[http2]` |
| Kya dekha (security) | Hosts: `www.nseindia.com`, `nsearchives.nseindia.com`, `archives.nseindia.com`. **Browser User-Agent ka naqli roop leta hai** (`"Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/118.0"`) aur Referer set karta hai. Cookies file par save karta hai (Mozilla cookie jar, default `cookies.txt`) aur cache dir banata hai. Subprocess/eval/pickle nahi hai |
| Faisla | **Use nahi. Upstox official API se khud likho** (`/v2/market/holidays`, `/v2/option/chain`, upstox-python SDK ke `market_holidays_and_timings_api.py` aur `options_api.py` mein dekha). Wajah: unofficial endpoint kabhi bhi badal ya block ho sakta hai, aur GPL bhi hai. NSE ki terms of use: verify nahi hua |
| Jaanch ki tarikh | 10 Nov 2026 |

### 6. ranaroussi/yfinance

| Field | Value |
|---|---|
| Repo | `ranaroussi/yfinance`: https://github.com/ranaroussi/yfinance |
| Kaam | Yahoo Finance se historical data, quote aur live (websocket) data |
| Zaroori file | Maujood hain: `yfinance/base.py` (992), `yfinance/scrapers/quote.py` (947), `yfinance/live.py` (351) |
| License | **Apache-2.0** (`LICENSE.txt`). Root mein `NOTICE` file nahi mili |
| Maalik | `ranaroussi` |
| Aakhri commit | `2492a85` · 2026-11-07 · "Merge pull request #3037 ..." |
| Aakhri release | Tag `1.8.0`. PyPI **1.8.0**, upload 2026-11-03. Kul 131 tags |
| Stars/forks | GitHub page: **25.9k / 3.5k**. Scorecard 5.5 |
| Advisories | OSV: koi nahi. GitHub tab: koi nahi |
| Dependencies | 11 direct: `beautifulsoup4`, `curl_cffi>=0.17`, `lxml`, `numpy`, `pandas`, `peewee`, `platformdirs`, `protobuf`, `pytz`, `requests`, `websockets` |
| Kya dekha (security) | Hosts: `query1/query2.finance.yahoo.com`, `finance.yahoo.com`, `wss://streamer.finance.yahoo.com`, `fc.yahoo.com`, `guce/consent.yahoo.com`. `curl_cffi` (browser impersonation) use karta hai. User cache dir (`py-yfinance`) mein SQLite cache likhta hai. **`cache.py:378` mein `pickle.loads(data.cookie_bytes)` hai.** Local cache file par jiska control ho, woh code chala sakta hai (local trust boundary). README kehta hai: "the Yahoo! finance API is intended for personal use only" |
| Faisla | **Bot mein use nahi.** Research ke liye alag venv mein pinned dependency ke roop mein chalega. Wajah: unofficial data source, broker key wale process mein extra network/pickle surface, aur Upstox ke paas official data pehle se hai |
| Jaanch ki tarikh | 10 Nov 2026 |

### 7. Supervisor/supervisor

| Field | Value |
|---|---|
| Repo | `Supervisor/supervisor`: https://github.com/Supervisor/supervisor |
| Kaam | Process control system: crash hone par auto-restart, logs, XML-RPC control |
| Zaroori file | `supervisor/` package, `LICENSES.txt`, `COPYRIGHT.txt` maujood hain |
| License | **BSD-derived (Repoze-style)**. `LICENSES.txt` ki 4 shartein: notice rakhna, binary mein notice dena, naam se endorse na karna, aur "If any files are modified, you must cause the modified files to carry prominent notices stating that you changed the files". PyPI metadata: "BSD-derived (http://www.repoze.org/LICENSE.txt)". `http_client.py` (RDFLib) aur medusa ke alag notices hain |
| Maalik | `Supervisor` org. `COPYRIGHT.txt` ke mutabik "Agendaless Consulting and Contributors" |
| Aakhri commit | `abc6046` · 2025-12-21 · "Fix typo" |
| Aakhri release | **4.3.0** (`CHANGES.rst`: 2025-08-23, PyPI upload 2025-08-23). Changelog mein "4.4.0.dev0 (Next Release)" likha hai |
| Stars/forks | GitHub page: **9.2k / 1.3k**. Scorecard 3.2 |
| Advisories | OSV mein purane issues hain: **GHSA-x7c8-4x3h-874w / CVE-2017-11610** (fixed 3.0.1/3.1.4/3.2.4/3.3.3) aur **PYSEC-2019-126 / CVE-2019-12105** (fixed 4.0.3). 4.3.0 par OSV query: koi nahi. GitHub tab: koi nahi |
| Dependencies | `install_requires=[]` (setuptools sirf Python < 3.8 par) |
| Kya dekha (security) | `subprocess` core kaam ke liye hai (process chalana). `eval` sirf ek commented line mein hai (`templating.py:1274`). `skel/sample.conf` kehta hai: `[inet_http_server]` default mein band hai, "intended for use within a trusted environment only", aur username/password default mein khaali hain ("open server") |
| Faisla | **Zaroorat nahi, systemd use karo.** Wajah: Linux par systemd pehle se hai, `Restart=on-failure` + `WatchdogSec=` se hang bhi pakda jaata hai, aur koi extra dependency nahi lagti. Agar supervisor lena hi pade toh 4.3.0 pin karo, sirf unix socket rakho, `inet_http_server` band rakho |
| Jaanch ki tarikh | 10 Nov 2026 |

### 8. upstox/upstox-python (official SDK)

| Field | Value |
|---|---|
| Repo | `upstox/upstox-python`: https://github.com/upstox/upstox-python |
| Kaam | Upstox ka official Python SDK (swagger-codegen se bana): REST APIs (orders, market quote, option chain, holidays) + WebSocket feeders (market data v3 protobuf, portfolio stream) |
| Zaroori file | `upstox_client/` maujood hai (59,447 py lines). Mukhya files: `configuration.py`, `api_client.py`, `api/options_api.py` (`/v2/option/chain`, `/v2/option/contract`), `api/market_holidays_and_timings_api.py` (`/v2/market/holidays`, `/v2/market/status/{exchange}`, `/v2/market/timings/{date}`), `feeder/market_data_feeder_v3.py`, `feeder/portfolio_data_feeder.py`, `feeder/proto/MarketDataFeedV3.proto` |
| License | **MIT** (`LICENSE.txt`: "Copyright 2023 Upstox") |
| Maalik | `upstox` org |
| Aakhri commit | `2865547` · 2026-11-09 · "ci: pin Semgrep, runner and rules in Security Check Scan (#170)" |
| Aakhri release | Tag `v2.30.0`. PyPI `upstox-python-sdk` **2.30.0**, upload 2026-09-07. `setup.py` mein `VERSION = "2.30.0"`. README ab bhi "Package version: 2.23.0" dikhata hai (purana). Kul 35 tags |
| Stars/forks | GitHub page: **193 / 128**. Scorecard 5.9 |
| Advisories | OSV: koi nahi. GitHub tab: "There aren't any published security advisories." |
| Dependencies | `setup.py` REQUIRES (7): `urllib3>=1.15`, `six>=1.10`, `certifi`, `python-dateutil`, `websocket-client`, **`uuid`**, `protobuf`. PyPI par `uuid` package ka version **1.30** hai, aakhri upload **2007-05-26**, summary "(Python 2.3 or higher)". Python stdlib mein `uuid` pehle se hai, isliye yeh bekaar ki purani dependency hai |
| Kya dekha (security) | REST mein `verify_ssl = True` default hai (theek). **Lekin `feeder/market_data_feeder_v3.py` (line ~39-54) aur `feeder/portfolio_data_feeder.py` (line ~28-44) mein `sslopt = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}` hai, aur saath mein header `Authorization` (access token) bhi bhejte hain.** Yeh code commit `dd596cd` (2024-11-27, "init commit for v3 websocket") se hai. GitHub issues mein "ssl/CERT_NONE/certificate" search kiya, is par koi issue nahi mila. Hosts: `api.upstox.com`, `api-hft.upstox.com` (order host), `api-sandbox.upstox.com`, `wss://api.upstox.com/v3/feed/market-data-feed`, `wss://api.upstox.com/v2/feed/portfolio-stream-feed`. `github.com` ke 400+ hits sirf swagger-codegen comments mein hain. Subprocess/eval/pickle nahi. File write sirf file-download response ke liye (`tempfile`) |
| Proto | SDK ki `MarketDataFeedV3.proto` aur openalgo ki copy, dono comments/whitespace hata kar **official** https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto se match karti hain. Official file ka sha256: `3e1c939dce2c83a3fef91405c5ca268dfa089aae973319f56685f12a5afcf612` (10 Nov 2026 ko download kiya) |
| Faisla | **Use (pinned + hash-locked dependency), sirf REST ke liye. WebSocket feeder khud likho.** Feeder mein TLS verification ON rakho aur official `.proto` ko pin karo. Wajah: official SDK hai aur MIT hai, lekin feeder ka TLS-off hamare access token ke liye khatra hai. `uuid` package ko lockfile mein note karke review karo |
| Jaanch ki tarikh | 10 Nov 2026 |

### 9. python-telegram-bot/python-telegram-bot

| Field | Value |
|---|---|
| Repo | `python-telegram-bot/python-telegram-bot`: https://github.com/python-telegram-bot/python-telegram-bot |
| Kaam | Telegram Bot API ka async Python wrapper + `ext` framework (handlers, job queue, persistence) |
| Zaroori file | `src/telegram/` (`_bot.py`, `request/`, `ext/`) |
| License | **Dual**: `LICENSE` (GPLv3), `LICENSE.lesser` (LGPLv3), `LICENSE.dual` ("You may choose either license."). `pyproject.toml` mein `license = "LGPL-3.0-only"`. README: "You may copy, distribute and modify the software provided that modifications are described and licensed for free under LGPL-3" |
| Maalik | `python-telegram-bot` org |
| Aakhri commit | `bf2c8f3` · 2026-11-09 · "Use inspect.iscoroutinefunction instead of the deprecated asyncio.iscoroutinefunction (#5389)" |
| Aakhri release | Tag `v22.8`. PyPI **22.8**, upload 2026-06-12. `_version.py` mein 22.8.0 final hai |
| Stars/forks | GitHub page: **29.6k / 6.2k**. Scorecard 5.5 |
| Advisories | OSV: koi nahi. GitHub tab: koi nahi |
| Dependencies | Core: `httpx >=0.27,<0.29` (+ Python 3.14 par `httpcore`). Extras alag hain (`ext`, `http2`, `passport`, `socks`, ...) |
| Kya dekha (security) | Host `api.telegram.org`. `_utils/de_json.py:56` mein `eval(` hai, lekin sirf type-annotation strings par (internal). `subprocess` sirf `__main__.py` mein hai (`git describe` se version print). `pickle` sirf `ext/_picklepersistence.py` aur callback-data cache mein hai |
| Faisla | **Khud likho.** Seedha Bot API par HTTPS `POST https://api.telegram.org/bot<token>/sendMessage` karo, 1-2 functions kaafi hain. Wajah: hume sirf alert bhejna hai, aur library ke bina GPL/LGPL ka sawaal aur dependency dono khatam ho jaate hain |
| Jaanch ki tarikh | 10 Nov 2026 |

---

## (2) Licence ka asar

> Main vakil nahi hoon, vakil se confirm karna. Yeh table official licence text aur GNU FAQ padh kar likha gaya hai.

| Licence (repo) | (i) Bot sirf malik ke apne account ke liye, private, kisi ko diya nahi | (ii) Bot doosron ko diya / becha / SaaS ki tarah chalaya | Source |
|---|---|---|---|
| **MIT** (ta, smart-money-concepts, vollib, upstox-python) | Kuch bhi kar sakte ho | Copy/modify/sell kar sakte ho, lekin "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software" ki shart maanni hogi | Har repo ki `LICENSE` file. https://opensource.org/license/mit |
| **Apache-2.0** (yfinance) | Kuch bhi kar sakte ho | Section 4 "Redistribution" lagu hoga: licence ki copy deni hogi, modified files par notice lagana hoga, aur NOTICE file ho toh uska text bhi dena hoga | `LICENSE.txt` line 90 se. https://www.apache.org/licenses/LICENSE-2.0 |
| **BSD-derived / Repoze** (supervisor) | Kuch bhi kar sakte ho | Notice rakhna hoga. Badli hui files par "prominent notices stating that you changed the files" lagane honge | `LICENSES.txt`. http://www.repoze.org/LICENSE.txt (PyPI metadata ke link se, page khud nahi khola) |
| **LGPL-3.0** (python-telegram-bot ka ek vikalp) | Private use mein source dene ki zimmedari nahi | Library ko alag aur badalne layak rakhna hoga. Library mein badlav kiye toh woh LGPL mein dene honge. GNU FAQ #LGPLStaticVsDynamic ke mutabik dynamic vs static linking ki shartein alag hain | https://www.gnu.org/licenses/lgpl-3.0.html · https://www.gnu.org/licenses/gpl-faq.html#LGPLStaticVsDynamic |
| **GPL-3.0** (NseIndiaApi, PTB ka doosra vikalp) | GNU FAQ: "You are free to make modifications and use them privately, without ever releasing them" (#GPLRequireSourcePostedPublic). Ek hi organization ke andar copy karna "distribution" nahi hai (#InternalDistribution). Web par modified GPL chalana bhi release nahi maana jaata (#UnreleasedMods) | GPL library ko link/import kiya toh "the terms of the GPL apply to the entire combination" (#IfLibraryIsGPL). Bechna allowed hai, lekin "only under the terms of the GNU GPL" (#GPLCommercially). Wrapper laga kar bachna nahi chalega (#GPLWrapper) | https://www.gnu.org/licenses/gpl-3.0.html · https://www.gnu.org/licenses/gpl-faq.html |
| **AGPL-3.0** (openalgo) | Agar sirf aap khud use karte ho (koi aur network se use nahi karta), toh practical mein source dene ka sawaal sirf aapke apne liye hai. **Lekin** agar web UI internet par khula hai aur koi doosra use karta hai, toh Section 13 lagu ho sakta hai. Vakil se confirm karna | **Section 13:** "if you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network ... an opportunity to receive the Corresponding Source". GNU FAQ #UnreleasedModsAGPL ke mutabik website par modified AGPL chalane wali company ko source release karna padega. Corresponding Source mein linked libraries bhi aati hain (#AGPLv3CorrespondingSource). Yaani openalgo ka code bot mein mila kar SaaS chalaya toh **poora bot ka source** dena pad sakta hai | `License.md` (openalgo) Section 13. https://www.gnu.org/licenses/agpl-3.0.html · https://www.gnu.org/licenses/gpl-faq.html#UnreleasedModsAGPL · #AGPLv3InteractingRemotely |

**Sabse bada licence khatra:** openalgo (AGPL-3.0). Iska ek bhi file copy kiya aur bot kabhi network service ki tarah doosron ko diya, toh poora bot AGPL ho sakta hai. Doosra khatra NseIndiaApi (GPL-3.0) hai: distribute karte hi poora bot GPL ho jaayega. Hamara plan (khud likho + MIT/official SDK) in dono se bachata hai.

---

## (3) Behtar vikalp

| Zaroorat | Vikalp | Kya dekha (10 Nov 2026) | Source |
|---|---|---|---|
| Upstox SDK doosri languages | **Official**: Python, Node.js (`upstox-js-sdk`), Java (`com.upstox.api:upstox-java-sdk`), PHP (`upstox/upstox-php-sdk`), .NET (`upstox-dotnet-sdk`) | Upstox "Installing the SDK" page par yahi 5 hain. GitHub org page: upstox-nodejs (39 stars), upstox-java (15, MIT), upstox-php (5, MIT), upstox-dotnet (3). Sabka aakhri commit Nov 2026 hai ("ci: pin Semgrep ..."). Node repo mein LICENSE file nahi hai, lekin `package.json` mein `"license": "MIT"`, version 2.31.0. .NET repo root mein LICENSE file nahi mili. Node SDK `src/` mein `rejectUnauthorized` grep se nahi mila (sirf grep kiya, poora review nahi) | https://upstox.com/developer/api-documentation/installing-sdk/ · https://github.com/orgs/upstox/repositories |
| Rust Upstox client | `upstox-rust-sdk` (**third-party**, official nahi) | crates.io: v1.0.1, MPL-2.0, ~7.3k downloads. Repo `Aviral-Omar/upstox-rust-sdk`: 1 star, aakhri commit 2025-09-14 | https://crates.io/crates/upstox-rust-sdk · https://github.com/Aviral-Omar/upstox-rust-sdk |
| Go Upstox client | Koi official nahi | pkg.go.dev par 4 third-party modules mile: `nsvirk/goupstoxsession` v0.1.0 (MIT, Apr 2026), `nsvirk/brokersession` v1.2.0 (MIT), `adeludedperson/go-upstox` (no license), `santoshanand/brokers` (no license). Sab "Imported by 0" hain | https://pkg.go.dev/search?q=upstox |
| C++ Upstox client | Koi official nahi mila | Upstox community thread mein C++ SDK maanga gaya hai. Koi official repo nahi dikha | https://community.upstox.com/t/will-there-be-a-c-sdk-for-the-upstox-apis/14386 |
| Market feed `.proto` (official) | `https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto` | Docs page is link ko "Market Data V3 Proto" kehta hai. Connection limit: Standard "2 connections per user", Upstox Plus "5". Proto ke `OptionGreeks` mein delta, theta, gamma, vega, rho hain, aur `oi`, `iv` fields bhi hain | https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ |
| Indicators (C) | **TA-Lib** (`TA-Lib/ta-lib`) | LICENSE: BSD style, "Copyright (c) 1999-2026, Mario Fortier". deps.dev: BSD-3-Clause, 1718 stars. Aakhri commit 2026-11-09 | https://github.com/TA-Lib/ta-lib |
| Indicators (Python wrapper) | `TA-Lib/ta-lib-python` | LICENSE: "BSD 2-Clause License". deps.dev: 12,391 stars. Aakhri commit 2026-11-05. PyPI `TA-Lib` 0.8.3, upload 2026-10-28. C library alag install karni padti hai | https://github.com/TA-Lib/ta-lib-python |
| pandas-ta ki sthiti | **Bharosa mat karo** | `github.com/twopirllc/pandas-ta` 10 Nov 2026 ko **HTTP 404** de raha tha, aur `git clone` bhi fail hua. PyPI par aakhri version `0.4.71b0` (2025-09-14) hai. Ek fork ke PyPI page par notice hai ki July 1, 2026 tak support na mila toh archive hoga. Asal mein kya hua: verify nahi hua | https://pypi.org/project/pandas-ta/ · https://pypi.org/project/pandas-ta-kozmoai/ |
| Indicators (Rust) | `ta` crate (`greyblake/ta-rs`) | MIT, 875 stars. **Aakhri commit 2022-10-21**, crate 0.5.0 aakhri update 2021-06-26, yaani purana hai | https://crates.io/crates/ta · https://github.com/greyblake/ta-rs |
| Indicators (Rust, aur) | `yata`, `kand`, `rust_ti` | yata: Apache-2.0, 403 stars, crate 0.7.0 (2024-03-07). kand: Apache-2.0 OR MIT, 555 stars, 0.2.2 (2025-03-05). rust_ti: MIT, 2.2.0 (2025-10-19) | crates.io API |
| **Indicators: sabse achha raasta** | **Khud likho** (EMA, RSI, ATR, ADX, VWAP, Black-Scholes IV) | Har formula ke test vector ke liye `ta/test/data/cs-*.csv` (MIT) aur `vollib/tests/test_data.json` (MIT) use karo | Upar repo blocks |
| Telegram | **Library ke bina seedha Bot API** | Official doc: "All queries to the Telegram Bot API must be served over HTTPS" aur form `https://api.telegram.org/bot<token>/METHOD_NAME` hona chahiye. GET aur POST dono chalte hain, aur JSON (`application/json`) bhi. Latest entry: Bot API 10.4 (November 9, 2026) | https://core.telegram.org/bots/api |
| Pehredaar (watchdog) | **systemd** | `WatchdogSec=`: "The service must call sd_notify(3) regularly with "WATCHDOG=1" ... If the time between two such calls is larger than the configured time, then the service is placed in a failed state and it will be terminated with SIGABRT". Saath mein `Restart=on-failure/on-watchdog`, `RestartSec=` (default 100ms), aur exponential backoff ke liye `RestartSteps=`/`RestartMaxDelaySec=` | https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html |
| Pehredaar (alternative) | Go/Rust static binary watchdog | Is par gehri research nahi ki: verify nahi hua. systemd pehle se OS mein hai, isliye alag binary ki zaroorat dikhi nahi | — |
| RBI MPC schedule | RBI press release | "Meeting Schedule of the Monetary Policy Committee for 2026-2027" (Mar 23, 2026): April 6-8, June 3-5, August 3-5, October 5-7, December 2-4 (2026), February 3-5 (2027) | https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=62422 |
| MoSPI release calendar | MoSPI "Advance Release Calendar (2026-27)" PDF | Sept 2026 wala PDF khola (8 pages: CPI, PLFS, IIP, GDP ki dates aur PIB links). Isse naya version ho sakta hai: verify nahi hua | https://www.mospi.gov.in/uploads/documents/releaseCalender/1791356248513-ARC_2026_27_Sept_2026.pdf |
| NSE holidays / special session | NSE official page + Upstox holidays API | NSE page ka title "Market Timings & Holidays - NSE India" hai. Note likha hai: "Muhurat Trading will be conducted on Sunday, November 08, 2026 on account of Diwali Laxmi Pujan". Holiday table JS se load hoti hai, mere fetch mein nahi aayi. Upstox SDK mein `/v2/market/holidays` aur `/v2/market/timings/{date}` hain | https://www.nseindia.com/resources/exchange-communication-holidays |
| Holiday calendar repo (maintained) | `pandas_market_calendars` (MIT, 1006 stars, aakhri commit 2026-10-31) mein `holidays/nse.py` ("1996 through 2026"). `exchange_calendars` (Apache-2.0, 686 stars, aakhri commit 2026-09-15) mein `XBOM` | Third-party hain, isliye har saal NSE circular se milana zaroori hai | https://github.com/rsheftel/pandas_market_calendars · https://github.com/gerrymanoim/exchange_calendars |
| Strike-wise GEX / dealer data (India) | **Koi official NSE GEX feed nahi mila** | Third-party sites (stockmojo, optionslens/StrikeVue, Tradejini NxtOption) NSE option chain se GEX khud nikaalti hain. Woh yeh maan kar chalti hain ki "dealers long calls / short puts", jo andaza hai, asli dealer data nahi. NSE "Participant wise Open Interest" (Client/DII/FII/Pro, EOD CSV) official hai, lekin woh page maine khud nahi khola: verify nahi hua. Hamara raasta: Upstox option chain/feed ke OI + gamma se khud compute karo, aur andaza hi maano | https://stockmojo.in/gamma-exposure/nifty · https://optionslens.pages.dev/in/NIFTY/gex · https://bseindia.com/markets/Derivatives/DeriReports/DeriMarketDisclosures.aspx |

---

## (4) Supply-chain niyam (bot ke liye)

1. **Hash-locked lockfile zaroori hai.** pip "hash-checking mode": "This mode uses local hashes, embedded in a requirements.txt file, to protect against remote tampering". `--require-hashes` se yeh zabardasti chalu ho jaata hai. Saath mein `--only-binary :all:` ka sujhav bhi hai. Source: https://pip.pypa.io/en/stable/topics/secure-installs/
2. Lockfile banane ke do tareeke:
   - `pip-compile --generate-hashes requirements.in` (pip-tools, BSD-3-Clause). Source: https://github.com/jazzband/pip-tools
   - `uv pip compile --generate-hashes` ("Include distribution hashes in the output file"). `uv export` mein `--no-hashes` flag hota hai. `uv sync --locked` ka matlab: "Assert that the uv.lock will remain unchanged ... If the lockfile is missing or needs to be updated, uv will exit with an error". Source: https://docs.astral.sh/uv/reference/cli/
3. **Har release se pehle audit chalao.** `pip-audit -r requirements.txt --require-hashes`. Iske paas PyPI aur OSV services hain (`-s osv`), aur `--strict` bhi. Licence Apache 2.0. Source: https://github.com/pypa/pip-audit. Doosra tool: OSV-Scanner (https://google.github.io/osv-scanner/)
4. **Rust ho toh:** `Cargo.lock` commit karo ("When in doubt, check Cargo.lock into the version control system"). Build `cargo build --locked` se karo ("Cargo will exit with an error when ... The lock file is missing") ya `--frozen` (= `--locked` + `--offline`). `cargo-audit` (RustSec DB, Apache-2.0/MIT) aur `cargo-deny` (advisories, bans, licenses, sources) bhi chalao. Sources: https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html · https://doc.rust-lang.org/cargo/commands/cargo-build.html · https://github.com/rustsec/rustsec/tree/main/cargo-audit · https://embarkstudios.github.io/cargo-deny/
5. **Exact version pin karo, `>=` mat likho.** Is research mein mile asli misaal:
   - LiteLLM: OSV **MAL-2026-2144** ke mutabik 1.82.7, 1.82.8, 1.107.0 malicious the. Record ke details ke mutabik `.pth` file har Python start par credential-stealer chalati thi. Record ke andar ek source (amazon-inspector) ka note ulta bhi kehta hai, yaani record mein conflict hai. Phir bhi seekh yahi hai ki version-range nahi, exact pin + hash rakho. Source: https://osv.dev/vulnerability/MAL-2026-2144
   - vollib: PyPI 1.0.11/1.0.12 ka GitHub tag nahi mila, yaani publish hua code repo se match karta hai ya nahi, pata nahi. Aisi dependency mat lo, ya wheel ka hash khud review karke lock karo.
   - upstox-python ki `uuid` dependency PyPI par 2007 ka Python-2 era package hai. Lockfile review mein aisi cheezein pakdo.
6. **Broker key wale process mein dependencies kam se kam rakho.** Research tools (yfinance, pandas notebooks) ko alag venv/user mein rakho, unhe key ka access na ho.
7. **TLS kabhi band mat karo.** Code review checklist mein `CERT_NONE`, `check_hostname=False`, `verify=False` ka grep zaroori rakho (upstox SDK feeder aur openalgo dono mein yeh mila).
8. Upstox `.proto` ko repo mein pin karo aur uska sha256 record karo (upar diya hai). Upstox ka naya proto aaye toh diff karke update karo.
9. Koi bhi third-party code **sirf padhna**: alag folder mein clone karo, chalao mat. Vendor karna ho toh sirf zaroori file + LICENSE copy karo + commit hash note karo.

---

## (5) Verify nahi hua

- GitHub REST API band tha, isliye owner type (user/org), `archived` flag aur exact `pushed_at` API se nahi mile. Commit tarikh `git log` se li, stars GitHub page (rounded) aur deps.dev se.
- GitHub "Releases" section page par khaali dikha (openalgo, upstox-python, smc). Isliye "aakhri release" ke liye git tag + PyPI upload date li. GitHub Release objects ki tarikh: verify nahi hua.
- smart-money-concepts deps.dev par nahi mila, isliye Scorecard/open-issues nahi mile.
- PyPI `vollib` 1.0.11 / `py_vollib` 1.0.12 ka code repo se match karta hai ya nahi: verify nahi hua (wheel nahi khola).
- `smartmoneyconcepts` 0.0.27 ka git tag repo mein nahi hai. PyPI wheel aur repo ka mel: verify nahi hua.
- `ta` ki `test/data/cs-*.csv` ka asli source (StockCharts spreadsheet?): verify nahi hua.
- Upstox index (Nifty/BankNifty/Sensex) feed mein volume aata hai ya nahi (VWAP ke liye zaroori): verify nahi hua.
- Upstox Java/.NET/PHP SDK ke WebSocket TLS settings: grep adhoora raha (timeout). Node SDK mein sirf grep se `rejectUnauthorized` nahi mila, poora review nahi kiya.
- NSE website terms of use (NseIndiaApi ke liye) aur Yahoo terms ka poora padhna: verify nahi hua.
- pandas-ta GitHub 404 kyun hai (delete, rename ya private): verify nahi hua.
- NSE holiday table ka content (JS se load hota hai) aur NSE participant-wise OI page: khud nahi khola.
- MoSPI ka Sept 2026 PDF sabse naya hai ya nahi: verify nahi hua.
- Go/Rust static-binary watchdog options: research nahi ki.
- cargo-deny ke har check ka detail aur OSV-Scanner ki lockfile support list: docs page par poori nahi dikhi.
- `uv export` default mein hashes deta hai ya nahi: sirf `--no-hashes` flag ka text dekha, default ki baat verify nahi hui.
- Saari licence vyakhya: **main vakil nahi hoon, vakil se confirm karna.**
- LiteLLM MAL-2026-2144 record ke andar sources mein matbhed hai (upar note kiya).

---

## (6) Sources (sab dekha: 10 Nov 2026)

**Repos (clone + page)**
- https://github.com/bukosabino/ta (clone `a890410`)
- https://github.com/joshyattridge/smart-money-concepts (clone `1b62fd6`)
- https://github.com/vollib/py_vollib (clone `11f2058`, branch `refactor/extract-packages`)
- https://github.com/marketcalls/openalgo (clone `a1b9e32`) · https://github.com/marketcalls/openalgo/security/advisories
- https://github.com/BennyThadikaran/NseIndiaApi (clone `b7fd7eb`)
- https://github.com/ranaroussi/yfinance (clone `2492a85`)
- https://github.com/Supervisor/supervisor (clone `abc6046`)
- https://github.com/upstox/upstox-python (clone `2865547`) · https://github.com/upstox/upstox-python/issues?q=is%3Aissue+ssl+OR+CERT_NONE+OR+certificate
- https://github.com/python-telegram-bot/python-telegram-bot (clone `bf2c8f3`)
- Har repo ka `/security/advisories` page (upar wale repo URLs + `/security/advisories`)

**Metadata / advisories**
- deps.dev: https://api.deps.dev/v3/projects/github.com%2F{owner}%2F{repo}
- PyPI JSON: https://pypi.org/pypi/{package}/json (ta, smartmoneyconcepts, vollib, py_vollib, py-lets-be-rational, cody-special, piecewise-rational, openalgo, nse, yfinance, supervisor, upstox-python-sdk, python-telegram-bot, uuid, pandas-ta, TA-Lib, uv)
- OSV: https://api.osv.dev/v1/query · https://osv.dev/vulnerability/MAL-2026-2144 · https://osv.dev/vulnerability/GHSA-x7c8-4x3h-874w · https://osv.dev/vulnerability/PYSEC-2019-126
- crates.io: https://crates.io/api/v1/crates?q=upstox · https://crates.io/crates/ta · https://crates.io/crates/yata · https://crates.io/crates/kand · https://crates.io/crates/rust_ti · https://crates.io/crates/upstox-rust-sdk
- pkg.go.dev: https://pkg.go.dev/search?q=upstox

**Upstox official**
- https://upstox.com/developer/api-documentation/installing-sdk/
- https://upstox.com/developer/api-documentation/sdk/
- https://upstox.com/developer/api-documentation/v3/get-market-data-feed/
- https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto
- https://github.com/orgs/upstox/repositories
- https://community.upstox.com/t/will-there-be-a-c-sdk-for-the-upstox-apis/14386

**Licence**
- https://www.gnu.org/licenses/gpl-faq.html (#GPLRequireSourcePostedPublic, #UnreleasedMods, #UnreleasedModsAGPL, #InternalDistribution, #GPLCommercially, #IfLibraryIsGPL, #GPLWrapper, #LGPLStaticVsDynamic, #AGPLv3InteractingRemotely, #AGPLv3CorrespondingSource)
- https://www.gnu.org/licenses/agpl-3.0.html · https://www.gnu.org/licenses/gpl-3.0.html · https://www.gnu.org/licenses/lgpl-3.0.html
- https://www.apache.org/licenses/LICENSE-2.0 · https://opensource.org/license/mit
- AGPL Section 13 ka text openalgo ki `License.md` se padha (sha256 `76a97c87...5182`)

**Vikalp / ops**
- https://github.com/TA-Lib/ta-lib · https://github.com/TA-Lib/ta-lib-python · https://github.com/greyblake/ta-rs
- https://pypi.org/project/pandas-ta/ · https://pypi.org/project/pandas-ta-kozmoai/ · https://github.com/twopirllc/pandas-ta (404)
- https://core.telegram.org/bots/api
- https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=62422
- https://www.mospi.gov.in/uploads/documents/releaseCalender/1791356248513-ARC_2026_27_Sept_2026.pdf
- https://www.nseindia.com/resources/exchange-communication-holidays
- https://github.com/rsheftel/pandas_market_calendars · https://github.com/gerrymanoim/exchange_calendars
- https://stockmojo.in/gamma-exposure/nifty · https://optionslens.pages.dev/in/NIFTY/gex · https://www.tradejini.com/blogs/how-traders-can-use-gamma-exposure-to-understand-market-direction-part-1 · https://bseindia.com/markets/Derivatives/DeriReports/DeriMarketDisclosures.aspx

**Supply chain**
- https://pip.pypa.io/en/stable/topics/secure-installs/
- https://github.com/jazzband/pip-tools
- https://docs.astral.sh/uv/reference/cli/
- https://github.com/pypa/pip-audit
- https://google.github.io/osv-scanner/
- https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html · https://doc.rust-lang.org/cargo/commands/cargo-build.html
- https://github.com/rustsec/rustsec/tree/main/cargo-audit · https://embarkstudios.github.io/cargo-deny/
