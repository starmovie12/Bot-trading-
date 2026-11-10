"""Ek trade (khareed + bech) ka kharcha. Option KHAREEDNE wale ke hisaab se.

Pakke (dekha 11 Nov 2026): Upstox brokerage ₹20/order; STT bechne par premium ka 0.15% (1 Apr 2026 se).
Andaze (VERIFY NAHI HUA): exchange transaction charge, SEBI fee, stamp duty, GST ka aadhar.
Andaza wale fields `unverified()` mein aate hain; Real Money se pehle inhe broker contract note se pakka karna hai.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CostModel:
    brokerage_per_order: float = 20.0
    stt_sell_pct: float = 0.15
    gst_pct: float = 18.0
    stamp_buy_pct: float = 0.003  # andaza
    exchange_txn_pct: float = 0.05  # andaza (jaan-boojh kar thoda zyada)
    sebi_per_crore: float = 10.0  # andaza
    unverified_fields: tuple[str, ...] = field(default=("stamp_buy_pct", "exchange_txn_pct", "sebi_per_crore"))

    def unverified(self) -> tuple[str, ...]:
        return self.unverified_fields


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    brokerage: float
    stt: float
    exchange: float
    sebi: float
    stamp: float
    gst: float

    @property
    def total(self) -> float:
        return round(self.brokerage + self.stt + self.exchange + self.sebi + self.stamp + self.gst, 2)


def round_trip(buy_premium: float, sell_premium: float, qty: int, m: CostModel | None = None) -> CostBreakdown:
    if buy_premium < 0 or sell_premium < 0 or qty <= 0:
        raise ValueError("premium >= 0 aur qty > 0 chahiye")
    m = m or CostModel()
    buy_val = buy_premium * qty
    sell_val = sell_premium * qty
    turnover = buy_val + sell_val
    brokerage = 2 * m.brokerage_per_order
    exchange = turnover * m.exchange_txn_pct / 100
    sebi = turnover * m.sebi_per_crore / 1e7
    gst = (brokerage + exchange + sebi) * m.gst_pct / 100
    return CostBreakdown(
        brokerage=round(brokerage, 2),
        stt=round(sell_val * m.stt_sell_pct / 100, 2),
        exchange=round(exchange, 2),
        sebi=round(sebi, 2),
        stamp=round(buy_val * m.stamp_buy_pct / 100, 2),
        gst=round(gst, 2),
    )


def breakeven_points(premium: float, qty: int, m: CostModel | None = None) -> float:
    """Kitne point (premium mein) badhe toh kharcha nikle (lagbhag)."""
    return round(round_trip(premium, premium, qty, m).total / qty, 2)
