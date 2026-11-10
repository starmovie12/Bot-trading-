"""Order manager (PAPER ONLY). Broker ko hukm dene wala akela hissa; abhi sirf nakli (paper) broker.

Iron laws jo yahan code mein lagte hain:
1. Live broker ka koi class NAHI. `OrderManager(mode=...)` sirf "paper" maanta hai.
2. Har entry se pehle max nuksan (₹, kharche samet) jaancha jaata hai; zyada ho toh entry mana.
3. Entry fill (poora ya adha) hote hi usi qty ka SL broker par. SL lagana fail -> position turant band + halt.
4. SL trigger hua par fill nahi (gap) -> 2 second baad aggressive exit (3 baar reprice, phir protected market).
5. Ek waqt par sirf 1 position; ek idempotency key se sirf ek entry (duplicate order nahi).
6. 15:15 par sab square-off. Daily loss / kul jeb / reject-ginti / SL-fail par kill-switch (latch).
7. Har badlaav journal mein; restart par `restore` + `reconcile` se haalat wapas, bina SL ki position nahi bachti.
8. Order rate: 8/second se zyada nahi (Upstox 10/s, SEBI ≤10 OPS bina registration).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from bot.recorder.journal import JournalWriter, Record
from bot.strategy.costs import CostModel, round_trip

TICK = 0.05


class LiveTradingForbidden(RuntimeError):
    """Iron law: is code mein live order ka raasta hai hi nahi."""


class Status(Enum):
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    TRIGGERED = "triggered"  # SL trigger hua, fill ka intezaar
    CANCELLED = "cancelled"
    REJECTED = "rejected"


Kind = Literal["LIMIT", "SL", "MKT_PROTECTED"]


@dataclass(slots=True)
class Order:
    oid: str
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: int
    kind: Kind
    price: float
    trigger: float = 0.0
    filled: int = 0
    avg: float = 0.0
    status: Status = Status.OPEN
    t_submit: float = 0.0
    t_trigger: float | None = None


class PaperBroker:
    """Nakli broker: quote ke hisaab se fill. Tests ke liye reject/adha-fill/gap daal sakte hain."""

    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}
        self.quotes: dict[str, tuple[float, float]] = {}
        self.max_fill_per_step: int | None = None  # None = poora; warna adha fill
        self.reject_next: set[str] = set()  # "BUY"/"SELL"/"SL" agle order ko reject
        self.position: dict[str, int] = {}

    def set_quote(self, symbol: str, bid: float, ask: float) -> None:
        self.quotes[symbol] = (bid, ask)

    def submit(self, o: Order, now: float) -> Order:
        tag = "SL" if o.kind == "SL" else o.side
        if tag in self.reject_next:
            self.reject_next.discard(tag)
            o.status = Status.REJECTED
        o.t_submit = now
        self.orders[o.oid] = o
        return o

    def cancel(self, oid: str) -> None:
        o = self.orders.get(oid)
        if o and o.status in (Status.OPEN, Status.PARTIAL, Status.TRIGGERED):
            o.status = Status.CANCELLED

    def _fill(self, o: Order, px: float) -> None:
        room = o.qty - o.filled
        n = room if self.max_fill_per_step is None else min(room, self.max_fill_per_step)
        o.avg = (o.avg * o.filled + px * n) / (o.filled + n)
        o.filled += n
        o.status = Status.FILLED if o.filled == o.qty else Status.PARTIAL
        self.position[o.symbol] = self.position.get(o.symbol, 0) + (n if o.side == "BUY" else -n)

    def step(self, now: float) -> None:
        for o in self.orders.values():
            q = self.quotes.get(o.symbol)
            if q is None or o.status not in (Status.OPEN, Status.PARTIAL, Status.TRIGGERED):
                continue
            bid, ask = q
            if o.kind == "SL" and o.status == Status.OPEN:
                if bid <= o.trigger:
                    o.status = Status.TRIGGERED
                    o.t_trigger = now
                else:
                    continue
            if o.side == "BUY" and ask <= o.price:
                self._fill(o, ask)
            elif o.side == "SELL" and (o.kind == "MKT_PROTECTED" or bid >= o.price):
                self._fill(o, bid)


@dataclass(slots=True)
class Limits:
    max_loss_per_trade: float
    daily_loss_limit: float
    kul_jeb_limit: float
    start_capital: float
    square_off_minute: int = 15 * 60 + 15
    sl_place_timeout_s: float = 2.0
    sl_fill_timeout_s: float = 2.0
    entry_cancel_s: float = 3.0
    max_rejects: int = 3
    reject_window_s: float = 300.0
    max_orders_per_s: int = 8


@dataclass(slots=True)
class Position:
    key: str
    symbol: str
    qty: int
    entry: float
    sl: float
    entry_oid: str
    sl_oid: str | None = None
    exit_oid: str | None = None
    exit_tries: int = 0
    opened_at: float = 0.0
    sell_oids: list[str] = field(default_factory=list)  # SL + har exit order (adhe fill bhi gine jaate hain)


@dataclass(slots=True)
class Ledger:
    realised: float = 0.0
    lifetime_pnl: float = 0.0
    halted: str | None = None  # kill-switch ki wajah (latch); "kul jeb" wala hamesha ke liye
    used_keys: set[str] = field(default_factory=set)
    rejects: deque[float] = field(default_factory=deque)


class OrderManager:
    def __init__(
        self,
        broker: PaperBroker,
        limits: Limits,
        *,
        mode: str = "paper",
        journal: JournalWriter | None = None,
        clock: Callable[[], float],
        costs: CostModel | None = None,
    ) -> None:
        if mode != "paper" or not isinstance(broker, PaperBroker):
            raise LiveTradingForbidden("sirf paper mode; live order ka raasta is code mein nahi hai")
        self.b = broker
        self.lim = limits
        self.journal = journal
        self.clock = clock
        self.costs = costs or CostModel()
        self.pos: Position | None = None
        self.led = Ledger()
        self._sent: deque[float] = deque()
        self._seq = 0

    # ---------- chhote helpers ----------
    def _log(self, ev: str, **data: object) -> None:
        if self.journal is not None:
            self.journal.write(ev, int(self.clock() * 1e9), dict(data))

    def _oid(self, tag: str) -> str:
        self._seq += 1
        return f"{tag}-{self._seq}"

    def _rate_ok(self) -> bool:
        now = self.clock()
        while self._sent and now - self._sent[0] >= 1.0:
            self._sent.popleft()
        if len(self._sent) >= self.lim.max_orders_per_s:
            return False
        self._sent.append(now)
        return True

    def _halt(self, why: str) -> None:
        if self.led.halted is None:
            self.led.halted = why
            self._log("halt", why=why)

    def _submit(self, o: Order) -> Order | None:
        if not self._rate_ok():
            self._log("rate_limited", oid=o.oid)
            return None
        got = self.b.submit(o, self.clock())
        self._log(
            "submit",
            oid=o.oid,
            side=o.side,
            kind=o.kind,
            qty=o.qty,
            price=o.price,
            trigger=o.trigger,
            status=got.status.value,
        )
        if got.status == Status.REJECTED:
            now = self.clock()
            self.led.rejects.append(now)
            while self.led.rejects and now - self.led.rejects[0] > self.lim.reject_window_s:
                self.led.rejects.popleft()
            if len(self.led.rejects) >= self.lim.max_rejects:
                self._halt(f"{self.lim.max_rejects} reject {int(self.lim.reject_window_s)}s mein")
        return got

    def kill_reasons(self, minute: int) -> str | None:
        if self.led.halted:
            return self.led.halted
        if -self.led.realised >= self.lim.daily_loss_limit:
            return "din ki nuksan seema"
        if -self.led.lifetime_pnl >= self.lim.kul_jeb_limit:
            return "kul jeb seema (hamesha ke liye)"
        if minute >= self.lim.square_off_minute:
            return "square-off ka samay"
        return None

    # ---------- entry ----------
    def open(self, key: str, symbol: str, qty: int, limit_price: float, sl_price: float, minute: int) -> str:
        """Entry ki koshish. Lautata hai: 'submitted' ya mana karne ki wajah."""
        if key in self.led.used_keys:
            return "duplicate: yeh signal pehle hi use ho chuka"
        why = self.kill_reasons(minute)
        if why:
            return f"kill-switch: {why}"
        if self.pos is not None:
            return "pehle se ek position (sirf 1)"
        if not (0 < sl_price < limit_price) or qty <= 0:
            return "galat SL/qty"
        fees = round_trip(limit_price, sl_price, qty, self.costs).total
        risk = (limit_price - sl_price) * qty + fees
        if risk > self.lim.max_loss_per_trade:
            return f"max nuksan ₹{risk:,.0f} > seema ₹{self.lim.max_loss_per_trade:,.0f}"
        room = self.lim.daily_loss_limit + self.led.realised
        if risk > room:
            return f"aaj ki bachi seema ₹{room:,.0f} se zyada risk"
        o = Order(self._oid("E"), symbol, "BUY", qty, "LIMIT", limit_price)
        got = self._submit(o)
        if got is None:
            return "rate limit: abhi nahi"
        self.led.used_keys.add(key)
        if got.status == Status.REJECTED:
            return "entry reject"
        self.pos = Position(key, symbol, 0, 0.0, sl_price, o.oid, opened_at=self.clock())
        self._log("open", key=key, symbol=symbol, qty=qty, limit=limit_price, sl=sl_price)
        return "submitted"

    # ---------- har tick par ----------
    def on_tick(self, minute: int) -> None:
        self.b.step(self.clock())
        p = self.pos
        if p is None:
            return
        now = self.clock()
        entry = self.b.orders.get(p.entry_oid)  # restart ke baad "?" ho sakta hai
        if entry is not None:
            if entry.filled > p.qty:  # naya fill (poora/adha)
                p.qty, p.entry = entry.filled, entry.avg
                self._ensure_sl()
            if entry.status in (Status.OPEN, Status.PARTIAL) and now - entry.t_submit >= self.lim.entry_cancel_s:
                self.b.cancel(entry.oid)  # bacha hua hissa radd; jo bhara uska SL
                self._log("entry_cancel_rest", filled=entry.filled)
                if entry.filled == 0:
                    self.pos = None
                    return
        if self._sold() >= p.qty > 0:
            self._settle()
            return
        if p.qty > 0 and p.sl_oid is None and now - p.opened_at >= self.lim.sl_place_timeout_s:
            self._halt("bina SL ki position (blind)")
            self._exit("blind position")
        if p.sl_oid and p.exit_oid is None:
            sl = self.b.orders[p.sl_oid]
            stuck = sl.status in (Status.TRIGGERED, Status.PARTIAL) and sl.t_trigger is not None
            if stuck and sl.t_trigger is not None and now - sl.t_trigger >= self.lim.sl_fill_timeout_s:
                self.b.cancel(sl.oid)
                self._log("sl_gap", trigger=sl.trigger, filled=sl.filled)
                self._exit("SL trigger par poora fill nahi (gap)")
        if self.pos is not None and self.pos.exit_oid:
            self._watch_exit()
        if self.pos is not None and self.pos.qty > 0 and minute >= self.lim.square_off_minute:
            self._exit("15:15 square-off")

    def _ensure_sl(self) -> None:
        p = self.pos
        assert p is not None  # noqa: S101
        if p.sl_oid:
            old = self.b.orders[p.sl_oid]
            if old.qty == p.qty:
                return
            self.b.cancel(old.oid)  # adha fill badha: SL ki qty badlo
        limit = max(TICK, round(p.sl - 2 * TICK, 2))
        o = Order(self._oid("SL"), p.symbol, "SELL", p.qty, "SL", limit, trigger=p.sl)
        got = self._submit(o)
        if got is None or got.status == Status.REJECTED:
            self._halt("SL lagana fail")
            self._exit("SL lagana fail")
            return
        p.sl_oid = o.oid
        p.sell_oids.append(o.oid)
        self._log("sl_live", oid=o.oid, qty=p.qty, trigger=p.sl)

    def _exit(self, why: str) -> None:
        p = self.pos
        if p is None or p.qty <= 0 or p.exit_oid:
            return
        if p.sl_oid:
            self.b.cancel(p.sl_oid)
        left = p.qty - self._sold()
        if left <= 0:
            return
        q = self.b.quotes.get(p.symbol)
        bid = q[0] if q else p.sl
        o = Order(self._oid("X"), p.symbol, "SELL", left, "LIMIT", max(TICK, round(bid - 2 * TICK, 2)))
        p.exit_tries = 1
        self._log("exit", why=why)
        got = self._submit(o)
        p.exit_oid = o.oid if got else None
        if got:
            p.sell_oids.append(o.oid)

    def _watch_exit(self) -> None:
        p = self.pos
        assert p is not None and p.exit_oid  # noqa: S101
        x = self.b.orders[p.exit_oid]
        if self._sold() >= p.qty:
            self._settle()
            return
        if x.status not in (Status.CANCELLED, Status.REJECTED) and self.clock() - x.t_submit < 1.0:
            return
        self.b.cancel(x.oid)  # reprice: 3 baar, phir protected market
        q = self.b.quotes.get(p.symbol)
        bid = q[0] if q else x.price
        p.exit_tries += 1
        kind: Kind = "MKT_PROTECTED" if p.exit_tries > 3 else "LIMIT"
        o = Order(self._oid("X"), p.symbol, "SELL", p.qty - self._sold(), kind, max(TICK, round(bid - 2 * TICK, 2)))
        got = self._submit(o)
        p.exit_oid = o.oid if got else None
        if got:
            p.sell_oids.append(o.oid)

    def _sold(self) -> int:
        p = self.pos
        return 0 if p is None else sum(self.b.orders[o].filled for o in p.sell_oids if o in self.b.orders)

    def _settle(self) -> None:
        p = self.pos
        assert p is not None  # noqa: S101
        fills = [self.b.orders[o] for o in p.sell_oids if o in self.b.orders and self.b.orders[o].filled]
        sold = sum(x.filled for x in fills)
        if sold < p.qty:
            return  # adha exit: baaki ka intezaar
        avg_exit = sum(x.avg * x.filled for x in fills) / sold
        for o in (p.sl_oid, p.exit_oid):
            if o:
                self.b.cancel(o)  # bacha hua koi order na latke
        fees = round_trip(p.entry, avg_exit, p.qty, self.costs).total
        pnl = round((avg_exit - p.entry) * p.qty - fees, 2)
        self.led.realised += pnl
        self.led.lifetime_pnl += pnl
        self._log("closed", key=p.key, pnl=pnl, exit=round(avg_exit, 2))
        self.pos = None
        if -self.led.realised >= self.lim.daily_loss_limit:
            self._halt("din ki nuksan seema")
        if -self.led.lifetime_pnl >= self.lim.kul_jeb_limit:
            self._halt("kul jeb seema (hamesha ke liye)")

    # ---------- restart ----------
    def new_day(self) -> None:
        """Naya din: din ka P&L/reject saaf; kul jeb wala halt hamesha ke liye rehta hai."""
        self.led.realised = 0.0
        self.led.rejects.clear()
        if self.led.halted and not self.led.halted.startswith("kul jeb"):
            self.led.halted = None

    def restore(self, records: list[Record], *, lifetime_before_today: float = 0.0) -> None:
        """Aaj ke journal se haalat wapas: kaun se signal use hue, P&L, halt, khuli position."""
        self.led.lifetime_pnl = lifetime_before_today
        if -lifetime_before_today >= self.lim.kul_jeb_limit:
            self.led.halted = "kul jeb seema (hamesha ke liye)"
        for r in records:
            d = r.data
            if r.kind == "open":
                self.led.used_keys.add(str(d["key"]))
                self.pos = Position(str(d["key"]), str(d["symbol"]), 0, 0.0, float(str(d["sl"])), "?")
            elif r.kind == "closed":
                pnl = float(str(d["pnl"]))
                self.led.realised += pnl
                self.led.lifetime_pnl += pnl
                self.pos = None
            elif r.kind == "halt":
                self.led.halted = str(d["why"])

    def reconcile(self, broker_qty: int, symbol: str, avg: float) -> str:
        """Restart ke baad broker ki asli position se milaan. Bina SL ki position kabhi nahi chhodte."""
        if broker_qty == 0:
            self.pos = None
            return "koi position nahi"
        if self.pos is None or self.pos.symbol != symbol:
            self._halt("anjaan position broker par")
            self.pos = Position(
                "reconcile", symbol, broker_qty, avg, max(TICK, round(avg * 0.75, 2)), "?", opened_at=self.clock()
            )
            self._exit("anjaan position")
            return "anjaan position: exit + halt"
        self.pos.qty, self.pos.entry, self.pos.opened_at = broker_qty, avg, self.clock()
        self.pos.sl_oid = None
        self._ensure_sl()
        return "position mili: SL dobara lagaya"
