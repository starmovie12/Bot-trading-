# Older history: what exists, and exact steps (owner order 2, section E)

Checked on 2026-11-18 on the Upstox developer pages (SOURCE):
- Expired option / future candles: endpoint `/v2/expired-instruments/historical-candle/...` needs **Upstox Plus**, and
  "Get Expiries" covers "up to six months of historical expiries". So **2022-24 expired BANKNIFTY option candles are
  NOT available from Upstox** (only about the last 6 months of expiries). Another vendor: not checked (verify nahi hua).
- Index and VIX candles: endpoint `/v3/historical-candle/{key}/minutes/1/{to_date}/{from_date}`; minutes data from
  January 2022; at most 1 month per request for 1-15 minute candles; India VIX key `NSE_INDEX|India VIX`. The page names
  no plan. The BANKNIFTY key `NSE_INDEX|Nifty Bank` is the one the data repo already uses.
- So the obtainable "older history" = BANKNIFTY index + India VIX, 1 minute, 2022-01 .. 2024-09 (direction stage S2 only;
  option P&L stays on the current regime, LAB ST6).

## Steps (on YOUR computer, with YOUR token; never paste the token into a chat)
1. Log in to Upstox the usual way and copy today's access token.
2. In a terminal: `export UPSTOX_TOKEN='<paste here>'` (it lives only in that terminal).
3. Save the script below as `fetch_history.py` and run `python3 fetch_history.py` (Python 3 + `requests`).
4. It writes `history_1m/<key>_<YYYY-MM>.csv`: about 66 files, about 520,000 rows, roughly 40 MB as CSV
   (ESTIMATE: 690 days x 375 minutes x 2 series; verify nahi hua). Put the folder into the data repo as a new folder
   `external/history_1m/` and tell me "item 6 daala". I then SEAL it (load, hash, no number read) before any search.

```python
import csv, os, time, datetime as dt, pathlib, requests
token = os.environ["UPSTOX_TOKEN"]
out = pathlib.Path("history_1m"); out.mkdir(exist_ok=True)
for key in ("NSE_INDEX|Nifty Bank", "NSE_INDEX|India VIX"):
    m = dt.date(2022, 1, 1)
    while m <= dt.date(2024, 9, 1):
        nxt = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        to = nxt - dt.timedelta(days=1)
        url = f"https://api.upstox.com/v3/historical-candle/{requests.utils.quote(key, safe='')}/minutes/1/{to}/{m}"
        r = requests.get(url, headers={"Accept": "application/json", "Authorization": f"Bearer {token}"}, timeout=30)
        r.raise_for_status()
        rows = r.json()["data"]["candles"]
        name = key.split("|")[1].replace(" ", "_")
        with open(out / f"{name}_{m:%Y-%m}.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["ts", "open", "high", "low", "close", "volume", "oi"]); w.writerows(rows)
        print(name, m, len(rows)); m = nxt; time.sleep(1)
```
