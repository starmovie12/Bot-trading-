# AUTOPSY (T07, session 3, 2026-11-11)

Scope (MISSION §12 T07): the Recorder and the shared modules; order-path bugs are written down as inputs
for T13a / T13b, not fixed here (FULL-B is CLOSED). Evidence: `EVIDENCE/T07/`.

## (a) Inventory

Full module → definitions → imports list: `EVIDENCE/T07/inventory.txt`. Who calls whom, in short:

| area | modules | job | called by |
|---|---|---|---|
| entry points | `bot.__main__` (`python -m bot --check`), `bot.recorder.__main__`, `bot.niyam` | dry-run checks; Recorder CLI; niyam-file check | deploy/bot.service (oneshot check), the owner, CI |
| limits | `bot.limits` | the one source of risk limits (`limits.toml`) | `bot.__main__`, `bot.strategy.rules` |
| Recorder | `bot.recorder.snapshot`, `journal`, `clock`, `notify`, `synthetic_feed`, `ticks` | read-only market data → hash-chained day journals; backtest views | Recorder CLI, backtest (`ticks`), tests |
| strategy (v3, HISTORY) | `bot.strategy.*`, `bot.dimaag.*` | strike selection, rules, costs, regime, setups | backtest engine, `bot.haath.orders` (costs) |
| backtest | `bot.backtest.engine`, `metrics` | simulated trades on journals or synthetic days | tests, tools |
| paper orders | `bot.haath.orders` | PAPER-only order manager (`LiveTradingForbidden`) | `bot.__main__` (guard check only), tests |
| login | `bot.login.*`, `bot.dashboard_push` | TOTP login helper, secret store, signed dashboard push | tests only (no runtime caller) |
| watchdog | `pehredaar/` (Go) | lease timing check (M0) | deploy/pehredaar.service |

No `legacy/` folder exists (no zip was provided).

## (b) Ranked list of capital-killing bugs

| rank | area | finding | where | status |
|---|---|---|---|---|
| 1 | SL miss | the exchange rejects SL-M for options [HISTORY]; a broker-side SL (limit) can stay unfilled in a gap, so the stop is not a guarantee | order path | T13b: I7 by construction + I9b `reduce_only` band ladder |
| 2 | position state after restart | the paper manager keeps the day lock, the total-loss lock and the open SL in memory only; a restart could re-enable trading after a lock or duplicate the SL | `bot.haath.orders`, `bot.strategy.rules` | T13a / T13b (I3 reconcile, persisted state) |
| 3 | duplicate order | idempotency keys exist in the paper manager only; the real path needs an intent log (I2) | order path | T13b |
| 4 | token expiry / IP change | token valid until 03:30 next day, IP change once a week [HISTORY]: no defined behaviour in code yet (I6) | order path | T13b |
| 5 | VPS / internet drop | the watchdog has no broker access (good) but there is no kill path yet (I5) | `pehredaar/` | T13b |
| 6 | time / calendar (Recorder) | **bug A**: one message with a wrong exchange date split the day; the second seal overwrote the first `.jsonl.gz` (data loss) | `bot.recorder.snapshot` | **fixed here** (fail → pass: `EVIDENCE/T07/bugA_before_fix.txt`, `bugA_after_fix.txt`) |
| 7 | market hours | F&O hours moved (15:40 from 2026-08-03, index F&O 15:45 from 2026-12-07, expiring contracts 15:30 [HISTORY]); the paper manager squares off at 15:15 | order path | T13a: read the session calendar |
| 8 | time / calendar (expiry) | expiry on a holiday is not shifted in `instruments.py` (noted there) | strategy | T13a: instrument master |
| 9 | money maths | `bot.strategy.costs` uses float and `round()` (binary rounding can move a paisa) | shared | T13a: Decimal (I12); G0 already uses Decimal |
| 10 | partial fill | handled in the paper manager (SL quantity = filled quantity) | order path | T13b re-checks against real fills |
| 11 | rate limit | paper manager 8 / 400 / 1,800 below the broker's 10 / 500 / 2,000 [HISTORY] | order path | keep; T13b gateway |
| 12 | journal reopen | the writer reads only the last 64 KB to find the chain head; one line longer than that would break a reopen (snapshot lines are about 280 bytes) | `bot.recorder.journal` | low; noted |

## (c) Fixed here (failing test first)

- Bug A: `tests/test_recorder_autopsy.py` failed before the fix (2 tests) and passes after it. Fix: a message
  whose exchange and local clocks differ by more than `max_drift_s` is alerted and never recorded; rows for a
  day that is already sealed are not written (`day_already_sealed` alert); `seal_day` refuses to overwrite an
  existing `.jsonl.gz`.
- I8 on every track: `tests/invariants/test_i08_live_flag_off.py` and `tests/invariants/test_order_path_disabled.py`
  (paper only; `BOT_MODE` other than paper refused; the owner's `LIVE_TRADING_ENABLED` has no effect; the Recorder
  refuses `--live`; no module names a broker order API; the paper manager has no network import; the Recorder
  and niyam entry points cannot import any order module). The live flag stays OFF in code.
