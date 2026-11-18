"""S3 day loader: one DESIGN day -> arrays on the 375-minute grid (m = minutes after 09:15), cached as parquet.

Every 1-minute table row at minute m is known at ts_open + 1 min, i.e. usable by the decision of bar t iff m <= t.
Holdout days (data/lab/split.json) are guarded: any read raises HoldoutLocked and is appended to the access log,
unless one HOLDOUT_REUSED session was opened for a committed candidate (max 1 per program, §14.2).
"""

from __future__ import annotations

import datetime as dt
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from lab.data import BANK_STOCKS, VIX, read_day
from lab.s3.registry import FIX, STATS

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "data/banknifty/repo"
SPLIT = ROOT / "data/lab/split.json"
PROFILE = ROOT / "data/lab/data_profile.json"
CACHE = ROOT / "wip/cache"
ACCESS_LOG = ROOT / "wip/holdout_access.log"
HOLDOUT_USES = ROOT / "wip/holdout_uses.json"
N = 375  # 09:15 .. 15:29
NAN = float("nan")
type F64 = np.ndarray[Any, np.dtype[np.float64]]
CACHE_VERSION = 1


class HoldoutLocked(RuntimeError):
    """A holdout day was read outside the one allowed HOLDOUT_REUSED session."""


@cache
def split() -> dict[str, tuple[dt.date, ...]]:
    raw = json.loads(SPLIT.read_text())
    return {k: tuple(dt.date.fromisoformat(x) for x in raw[k]) for k in ("design", "holdout")}


_OPEN: dict[str, str] = {}


def guard(day: dt.date, log: Path = ACCESS_LOG) -> None:
    """Raise (and log) on any read of a holdout day outside an opened holdout session."""
    if day in split()["holdout"] and not _OPEN:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as fh:
            fh.write(f"{dt.datetime.now(dt.UTC).isoformat()} BLOCKED {day.isoformat()}\n")
        raise HoldoutLocked(f"holdout day {day} is locked (§14.2)")


def access_count(log: Path = ACCESS_LOG) -> int:
    return len(log.read_text().splitlines()) if log.exists() else 0


@contextmanager
def holdout_session(candidate_hash: str, uses: Path = HOLDOUT_USES) -> Iterator[None]:
    """The single HOLDOUT_REUSED run of this program; a second call aborts."""
    done = json.loads(uses.read_text()) if uses.exists() else []
    if len(done) >= int(STATS["HOLDOUT_MAX_USES"]):
        raise HoldoutLocked("holdout already used once in program S3 (§14.2)")
    uses.parent.mkdir(parents=True, exist_ok=True)
    uses.write_text(json.dumps([*done, {"candidate": candidate_hash, "at": dt.datetime.now(dt.UTC).isoformat()}]))
    _OPEN["candidate"] = candidate_hash
    try:
        yield
    finally:
        _OPEN.clear()


@cache
def profile() -> dict[str, Any]:
    out: dict[str, Any] = json.loads(PROFILE.read_text())
    return out


def lot_size(expiry: dt.date) -> int:
    """Lot of the contract (§5.2) from the data repo's instrument records (data_profile lots_by_expiry)."""
    return int(profile()["lots_by_expiry"][expiry.isoformat()])


def prev_day(day: dt.date) -> dt.date:
    ready = sorted(
        dt.date.fromisoformat(d)
        for d, v in profile()["days"].items()
        if v.get("price_ready") == "READY" and v.get("health", {}).get("session_type") == "NORMAL"
    )
    before = [d for d in ready if d < day]
    if not before:
        raise LookupError(f"no trading day before {day}")
    return before[-1]


def _minute(ts: pa.ChunkedArray, day: dt.date) -> np.ndarray[Any, np.dtype[np.int64]]:
    """Minutes from `day` 09:15 IST (negative for an earlier day)."""
    base = dt.datetime.combine(day, dt.time(9, 15), tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30)))
    us = pc.subtract(ts, pa.scalar(base, ts.type)).cast(pa.int64()).to_numpy()
    return np.asarray(us // 60_000_000, dtype=np.int64)


def _grid(tb: pa.Table, day: dt.date, cols: dict[str, str]) -> dict[str, F64]:
    out = {k: np.full(N, NAN) for k in cols}
    if tb.num_rows == 0:
        return out
    m = _minute(tb["ts_open"], day)
    ok = (m >= 0) & (m < N)
    for k, c in cols.items():
        v = tb[c].cast(pa.float64()).to_numpy(zero_copy_only=False)
        out[k][m[ok]] = v[ok]
    return out


def _stale(tb: pa.Table, day: dt.date) -> np.ndarray[Any, np.dtype[np.bool_]]:
    s = np.ones(N, dtype=bool)
    if tb.num_rows:
        m = _minute(tb["ts_open"], day)
        ok = (m >= 0) & (m < N)
        s[m[ok]] = tb["is_stale"].to_numpy(zero_copy_only=False)[ok]
    return s


OHLC = {"o": "o", "h": "h", "l": "l", "c": "c"}


def _base(day: dt.date) -> tuple[pa.Table, dict[str, Any]]:
    cols: dict[str, Any] = {}
    spot = read_day(REPO, "spot_1m", day)
    for k, v in _grid(spot, day, OHLC).items():
        cols[f"spot_{k}"] = v
    fut = read_day(REPO, "fut_1m", day)
    exps = sorted(set(fut["expiry_date"].to_pylist()))
    early = int(FIX["FUT_PICK_BARS"])
    vol = {
        e: float(np.nansum(_grid(fut.filter(pc.equal(fut["expiry_date"], e)), day, {"v": "v"})["v"][:early]))
        for e in exps
    }
    fexp = max(exps, key=lambda e: (vol[e], -e.toordinal()))  # §4.3: most 09:15-09:19 volume; tie -> nearer
    f1 = fut.filter(pc.equal(fut["expiry_date"], fexp))
    for k, v in _grid(f1, day, {**OHLC, "v": "v"}).items():
        cols[f"fut_{k}"] = v
    for k, v in _grid(read_day(REPO, "vix_1m", day, underlying=VIX), day, OHLC).items():
        cols[f"vix_{k}"] = v
    for s in BANK_STOCKS:
        cols[f"stk_{s}"] = _grid(read_day(REPO, "stock_1m", day, underlying=s), day, {"c": "c"})["c"]
    cm = read_day(REPO, "chain_metrics_1m", day)
    cmc = {
        "call_wall": "call_oi_wall_DERIVED",
        "put_wall": "put_oi_wall_DERIVED",
        "pcr": "pcr_DERIVED",
        "max_pain": "max_pain_DERIVED",
        "gex": "gex_proxy_PROXY",
        "gamma_flip": "gamma_flip_PROXY",
        "atm_iv": "atm_iv_DERIVED",
    }
    cols |= {f"cm_{k}": v for k, v in _grid(_avail_ok(cm, day), day, cmc).items()}
    meta = {"fut_expiry": fexp.isoformat()}
    return pa.table(cols), meta


def _avail_ok(tb: pa.Table, day: dt.date) -> pa.Table:
    """Derived 1-minute rows must be known one minute after their start (asserted, never assumed)."""
    if tb.num_rows:
        lag = _minute(tb["available_from_ts"], day) - _minute(tb["ts_open"], day)
        if not np.all(lag == 1):
            raise ValueError("derived 1-minute row with available_from_ts != ts_open + 1 min")
    return tb


def _options(day: dt.date) -> tuple[pa.Table, pa.Table, dt.date]:
    opt = read_day(REPO, "options", day)
    expiry = min(e for e in set(opt["expiry_date"].to_pylist()) if e >= day)
    opt = opt.filter(pc.equal(opt["expiry_date"], expiry))
    g = _avail_ok(read_day(REPO, "iv_greeks_1m", day), day)
    g = g.filter(pc.equal(g["expiry_date"], expiry))
    o = pa.table(
        {
            "m": _minute(opt["ts_open"], day),
            "strike": opt["strike"].cast(pa.float64()),
            "cp": opt["option_type"],
            **{k: opt[k].cast(pa.float64()) for k in ("o", "h", "l", "c", "v", "oi")},
            "stale": opt["is_stale"],
        }
    )
    gk = pa.table(
        {
            "m": _minute(g["ts_open"], day),
            "strike": g["strike"].cast(pa.float64()),
            "cp": g["option_type"],
            "delta": g["delta_DERIVED"].cast(pa.float64()),
            "iv": g["iv_DERIVED"].cast(pa.float64()),
            "hs_proxy": g["half_spread_PROXY"].cast(pa.float64()),
            "vbase": g["volume_baseline_same_dte_DERIVED"].cast(pa.float64()),
            "vbase_ok": pc.equal(g["baseline_same_dte_status"], "OK"),
        }
    )
    o = o.join(gk, ["m", "strike", "cp"], join_type="left outer").sort_by([("strike", "ascending"), ("m", "ascending")])
    ch = _avail_ok(read_day(REPO, "chain_1m", day), day)
    ch = ch.filter(pc.equal(ch["expiry_date"], expiry))
    c = pa.table(
        {
            "m": _minute(ch["ts_open"], day),
            "strike": ch["strike"].cast(pa.float64()),
            **{f"{s}_{k}": ch[f"{s}_{k}_DERIVED"].cast(pa.float64()) for s in ("ce", "pe") for k in ("close", "oi")},
        }
    )
    return o, c, expiry


def _bars(table: str, day: dt.date, prev: dt.date) -> pa.Table:
    parts = []
    for d in (prev, day):
        tb = read_day(REPO, table, d)
        parts.append(
            pa.table(
                {
                    "avail_m": _minute(tb["available_from_ts"], day),
                    **{k: tb[f"{k}_DERIVED"].cast(pa.float64()) for k in ("o", "h", "l", "c")},
                    "is_partial": tb["is_partial"],
                }
            )
        )
    return pa.concat_tables(parts).sort_by("avail_m")


def _daily(day: dt.date) -> dict[str, Any]:
    return daily_from(read_day(REPO, "daily_metrics_DERIVED", day), day)


def daily_from(tb: pa.Table, day: dt.date) -> dict[str, Any]:
    """The day's INTRADAY_PREV_CLOSE row (known 09:15); EOD_INCLUSIVE is never used (§4.2)."""
    tb = tb.filter(pc.equal(tb["version"], "INTRADAY_PREV_CLOSE"))  # §4.2: never EOD_INCLUSIVE
    if tb.num_rows != 1:
        return {"ivp": NAN, "ivp_ok": False, "rv20": NAN}
    r = tb.to_pylist()[0]
    if _minute(tb["available_from_ts"], day)[0] > 0:
        raise ValueError("INTRADAY_PREV_CLOSE row not known at 09:15")
    ivp = r["ivp_vix_PROXY"]
    return {
        "ivp": NAN if ivp is None else float(ivp),
        "ivp_ok": r["ivp_status"] == "OK",
        "rv20": NAN if r["rv20_DERIVED"] is None else float(r["rv20_DERIVED"]),
    }


def build_day(day: dt.date, cache_dir: Path = CACHE) -> Path:
    """Extract one day once into cache_dir/<day>/ (parquet + meta.json); returns the folder."""
    guard(day)
    prev = prev_day(day)
    guard(prev)
    out = cache_dir / day.isoformat()
    if (out / "meta.json").exists() and json.loads((out / "meta.json").read_text()).get("v") == CACHE_VERSION:
        return out
    out.mkdir(parents=True, exist_ok=True)
    base, meta = _base(day)
    pspot = read_day(REPO, "spot_1m", prev)
    pg = _grid(pspot, prev, OHLC)
    pq.write_table(base, out / "base.parquet")
    pq.write_table(pa.table({f"spot_{k}": v for k, v in pg.items()}), out / "prev.parquet")
    o, c, expiry = _options(day)
    pq.write_table(o, out / "opt.parquet")
    pq.write_table(c, out / "chain.parquet")
    pq.write_table(_bars("bars_3m", day, prev), out / "b3.parquet")
    pq.write_table(_bars("bars_15m", day, prev), out / "b15.parquet")
    stale = _stale(read_day(REPO, "spot_1m", day), day)
    meta |= {
        "v": CACHE_VERSION,
        "day": day.isoformat(),
        "prev": prev.isoformat(),
        "expiry": expiry.isoformat(),
        "dte": (expiry - day).days,
        "lot": lot_size(expiry),
        "spot_stale_bars": int(stale.sum()),
        **_daily(day),
    }
    (out / "meta.json").write_text(json.dumps(meta, sort_keys=True))
    return out


@dataclass
class Day:
    """One day's arrays (minute grid). Options: dense [K, N] per (strike, CE/PE) of the nearest expiry."""

    day: dt.date
    meta: dict[str, Any]
    base: dict[str, F64]
    prev: dict[str, F64]
    strikes: F64
    cp: np.ndarray[Any, np.dtype[np.str_]]
    opt: dict[str, F64]
    stale: np.ndarray[Any, np.dtype[np.bool_]]
    vbase_ok: np.ndarray[Any, np.dtype[np.bool_]]
    chain: pa.Table
    b3: pa.Table
    b15: pa.Table
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def lot(self) -> int:
        return int(self.meta["lot"])

    @property
    def dte(self) -> int:
        return int(self.meta["dte"])

    def k(self, strike: float, cp: str) -> int:
        idx = np.flatnonzero((self.strikes == strike) & (self.cp == cp))
        return int(idx[0]) if idx.size else -1


def _dense(o: pa.Table) -> tuple[F64, Any, dict[str, F64], Any, Any]:
    keys = sorted(set(zip(o["strike"].to_pylist(), o["cp"].to_pylist(), strict=True)))
    kidx = {key: i for i, key in enumerate(keys)}
    rows = np.array([kidx[x] for x in zip(o["strike"].to_pylist(), o["cp"].to_pylist(), strict=True)], dtype=np.int64)
    m = o["m"].to_numpy()
    ok = (m >= 0) & (m < N)
    arr: dict[str, F64] = {}
    for c in ("o", "h", "l", "c", "v", "oi", "delta", "iv", "hs_proxy", "vbase"):
        a = np.full((len(keys), N), NAN)
        a[rows[ok], m[ok]] = o[c].to_numpy(zero_copy_only=False).astype(np.float64)[ok]
        arr[c] = a
    stale = np.ones((len(keys), N), dtype=bool)
    stale[rows[ok], m[ok]] = o["stale"].to_numpy(zero_copy_only=False)[ok]
    vok = np.zeros((len(keys), N), dtype=bool)
    vok[rows[ok], m[ok]] = o["vbase_ok"].fill_null(False).to_numpy(zero_copy_only=False)[ok]
    strikes = np.array([s for s, _ in keys], dtype=np.float64)
    cps = np.array([c for _, c in keys])
    return strikes, cps, arr, stale, vok


def load(day: dt.date, cache_dir: Path = CACHE) -> Day:
    guard(day)
    f = cache_dir / day.isoformat()
    if not (f / "meta.json").exists():
        build_day(day, cache_dir)
    meta = json.loads((f / "meta.json").read_text())

    def cols(name: str) -> dict[str, F64]:
        tb = pq.read_table(f / name)
        return {c: tb[c].to_numpy().astype(np.float64) for c in tb.column_names}

    strikes, cps, arr, stale, vok = _dense(pq.read_table(f / "opt.parquet"))
    return Day(
        day=day,
        meta=meta,
        base=cols("base.parquet"),
        prev=cols("prev.parquet"),
        strikes=strikes,
        cp=cps,
        opt=arr,
        stale=stale,
        vbase_ok=vok,
        chain=pq.read_table(f / "chain.parquet"),
        b3=pq.read_table(f / "b3.parquet"),
        b15=pq.read_table(f / "b15.parquet"),
    )


def design_days() -> tuple[dt.date, ...]:
    return split()["design"]


def build_all(days: tuple[dt.date, ...], workers: int = 4) -> None:
    from concurrent.futures import ProcessPoolExecutor  # noqa: PLC0415

    with ProcessPoolExecutor(workers) as ex:
        list(ex.map(build_day, days))


if __name__ == "__main__":
    os.environ.pop("UPSTOX_RO_TOKEN", None)
    build_all(design_days())
    print(len(list(CACHE.glob("*/meta.json"))), "days cached")
