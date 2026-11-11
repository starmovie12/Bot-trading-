# RECORDER_SPEC (MISSION V11 §10, T05)

The Recorder writes read-only market data: no order, no broker write, ever. Code:
`src/bot/recorder/snapshot.py` (built on the M0 journal `src/bot/recorder/journal.py`), synthetic feed
`src/bot/recorder/synthetic_feed.py`, settings `recorder.toml`.

## Status (session 3)

- Built and tested on a **synthetic** feed only (tag SIM). Nothing here is evidence about the market.
- The adapter for the live Upstox feed is **not built**: the Market Data Feed V3 (WebSocket + protobuf,
  modes ltpc / option_greeks / full / full_d30) is known only from the owner's research [HISTORY]; its
  official schema was not fetched (web off: INCIDENT #1). The adapter must turn feed messages into the
  normalised message below; contract tests on redacted copies of real responses come with it (I13).
- **DATA_RIGHTS = UNVERIFIED** (docs/REGULATORY.md). So: LIGHT scope, derived data only, personal use only,
  never shared. FULL scope stays off (needs DATA_RIGHTS = OK, a PC and `haan F-RECFULL <code>`).
- Market-data calls need no static IP [HISTORY: the static-IP rule covers order APIs only].

## Normalised message (schema, I13)

| field | type | required | meaning |
|---|---|---|---|
| key | text | yes | instrument key (the adapter maps it from the instrument master) |
| exch_ts_ns | integer | yes | exchange timestamp, UTC epoch nanoseconds |
| ltp_paise | integer | yes | last traded price in paise (I12: no float money) |
| vol | integer | yes | traded volume |
| bid_paise, ask_paise | integer | no | best bid / ask in paise |
| oi | integer | no | open interest |
| iv_bp | integer | no | implied volatility in basis points |
| iv_src | `feed` or `computed` | no | where the IV came from |

An unknown field is logged (`schema_warning`) and dropped. A missing required field, a wrong type, a boolean
where a number is expected, or an unknown `iv_src` is a `schema` alert: the message is not recorded and
`entries_allowed()` turns False until the feed is fixed. The recorder adds `local_ts_ns` (local clock).

## Scope

- **LIGHT (default, phone-safe):** NIFTY, BANKNIFTY and SENSEX spot + near future + option chain ATM ± 5
  strikes, CE and PE, nearest expiry (BankNifty: current monthly) = 72 instruments; one snapshot per
  instrument per minute, 09:15-15:30 IST (375 minutes) = 27,000 [CODE(SIM)] rows a day. Measured on the
  synthetic feed: 7.5 MB raw, 1.35 MB gzipped per day [SIM], so about 340 MB a year [CODE(SIM)] — inside the
  2 GB cap of `recorder.toml` for more than a year.
- **FULL (PC only, gated):** ATM ± 10 strikes, current + next expiry (252 option contracts), tick stream and
  ≥ 5 depth levels if available. 1-4 GB a day before compression [ESTIMATE]. Not built until its gates open.

## Storage

- One append-only journal per IST day (`data/recorder/YYYY-MM-DD.jsonl`, gitignored, never committed),
  hash-chained line by line; a crash leaves at most a partial last line, which the next open cuts.
- At the day's end: gzip plus a `.sha256` sidecar (`seal_day`); `verify_day` checks the sidecar and reads
  the whole chain.
- Size cap per machine (`recorder.toml`): an alert at `alert_pct` (80%); at the cap recording stops with
  an alert. Nothing is ever deleted silently.
- Full disk: the recorder stops with a `disk_full` alert; the plain journal stays readable (no gzip
  attempt without space).
- Late messages for a minute already written are counted (`late`) and never rewrite history.

## Backup (T09)

At least two copies, one off the machine, daily; the restore is tested locally (T09 drill). The
off-machine copy is UNVERIFIED until the owner sets one up (the agent cannot create accounts or spend).

## Clock (I11)

Both timestamps are kept. The owner's machine keeps NTP on (operating-system setting). If exchange and
local time differ by more than `max_drift_s` (2 s) the recorder raises `clock_drift` and entries are not
allowed. The NSE / BSE holiday calendar from an official page is UNVERIFIED; the Upstox holiday API
(`/v2/market/holidays`) [HISTORY] is the candidate source.

## Quality

Gap detection (whole minutes missing → `gap` alert, entries blocked until data is contiguous), duplicate
and stale detection, and a one-line daily health result (`health`): OK when at least 99% of the expected
one-minute snapshots exist and none repeats; otherwise NOT OK, and that day does not count for G1.

## Token

The daily login is the owner's ritual. The read-only Analytics Token (one year, GET only) [HISTORY] may
suit the Recorder (verify with Upstox). The token lives only on the owner's machine, outside the bundle
folder, file mode 600, and never goes into a data pack.

## Machine (F-MACHINE)

PC: sleep off 08:45-16:00 IST. Android / Termux: `termux-wake-lock`, battery optimisation OFF for Termux,
charger connected, Termux notification kept; LIGHT scope only. On power or internet loss the journal
survives (the kill -9 test); the missing minutes show up in the health line.

## Day 1

Dry-run only: connect and log, nothing saved (`SnapshotRecorder(dry_run=True)`); described in
OWNER_START.md (T09).

## Tests

- `tests/test_recorder_mvp.py`: one synthetic day journals and replays identically; 5 simulated days with
  no gaps; `kill -9` mid-write recovery; full-disk behaviour; size-cap alert; a corrupted day file is
  detected; dry-run saves nothing; late messages never rewrite a minute.
- Feed-side invariants: `tests/invariants/test_i04_feed_stale_gap.py`, `test_i11_time.py`,
  `test_i13_feed_schema.py`.
