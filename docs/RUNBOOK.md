# RUNBOOK (Recorder only; MISSION V11 T09). At most two pages.

Covers only what exists: the read-only Recorder. The kill switch and the static-IP change come only with
FULL-B. The live feed adapter is NOT built yet: today only `--dry-run` runs (synthetic feed).

## Commands (inside the bundle folder)

| task | command |
|---|---|
| machine check (nothing saved) | `python3 -m bot.recorder --dry-run` |
| health of one recorded day | `python3 -m bot.recorder --health data/recorder/<YYYY-MM-DD>.jsonl.gz` |
| alert / heartbeat check (nothing sent) | `python3 -m bot.recorder --alert-dry-run outbox` |
| make a data pack for the agent | `python3 tools/pack_data.py --data data/recorder --out .` |
| check a pack (agent side) | `python3 tools/pack_data.py --verify <pack.zip> --into data/recorder` |
| check a restored backup | `python3 tools/backup_verify.py <restored data folder>` |
| live recording | `python3 -m bot.recorder --live` → REFUSED until the adapter exists |

## Alerts and what to do

| alert | meaning | action |
|---|---|---|
| `stale` (entries blocked) | no fresh message for 120 s | check internet / app; nothing else |
| `gap` | whole minutes missing | the day's health shows it; that day may not count for G1 |
| `clock_drift` | exchange vs local time apart > 2 s | turn on automatic time (NTP) |
| `schema` | a feed message of unknown shape: not recorded | send the line to the agent |
| `schema_warning` | an unknown field was dropped | nothing; the agent reviews it |
| `size_cap_80` | 80% of the size cap used | make a data pack, back it up |
| `size_cap_full` | cap reached: recording stopped | free space or raise the cap in recorder.toml (owner) |
| `disk_full` | disk full: recording stopped | free space; the day's journal stays readable |

## Backup and restore (daily)

1. Copy `data/recorder/` to a second place (a second disk or a cloud folder the owner sets up; that
   off-machine copy is UNVERIFIED until it exists).
2. Restore drill: copy the backup into a new folder, run `python3 tools/backup_verify.py <folder>`;
   every day must say OK.

## Never

No order, no broker write, no token inside the bundle or a data pack, no deleting recorded days.
