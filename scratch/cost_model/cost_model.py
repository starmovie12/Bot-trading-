#!/usr/bin/env python3
"""
Throw-away cost calculator (Phase 1 scratch). Sirf ganit. Production code NAHI.
Koi broker, network, key ya account se connection nahi.

Har rate ke saath source aur "dekha" tarikh likhi hai. Rate badle toh sirf RATES dict badlo.
Chalane ka tareeka:  python3 scratch/cost_model/cost_model.py
"""

# ---------------------------------------------------------------------------
# RATES (dekha: 10 Nov 2026). Percent values ko fraction mein rakha hai.
# ---------------------------------------------------------------------------
RATES = {
    # STT: sale of option = 0.15% of premium, seller pays. Lagu: 1 Apr 2026.
    # Source: NSE circular NSE/FATAX/73524 (31 Mar 2026), Finance Act 2026 (assent 30 Mar 2026).
    "stt_sell": 0.0015,
    # Exchange transaction charge, equity options, on premium, each side.
    # NSE: Rs 3,552.99 txn + Rs 0.01 IPFT = Rs 3,553 per crore = 0.03553%. Lagu: 1 Mar 2026.
    # Source: NSE circular NSE/FA/73061 (27 Feb 2026).
    "txn_nse": 3553 / 1e7,
    # BSE Sensex options: Rs 3,250 per crore premium = 0.0325%. Lagu: 1 Oct 2024.
    # Source: Upstox + Zerodha charges pages (dekha 10 Nov 2026); BSE notice khud nahi khula (403).
    "txn_bse": 3250 / 1e7,
    # SEBI turnover fee: 0.0001% (Rs 10 per crore), dono side.
    # Source: NSE investor page "SEBI Turnover Fees, STT and Other levies" (updated 17/04/2026).
    "sebi": 10 / 1e7,
    # Stamp duty: equity options 0.003% of premium, sirf buyer. Lagu: 1 Jul 2020.
    # Source: same NSE investor page.
    "stamp_buy": 0.00003,
    # GST 18% on brokerage + exchange txn charge (+IPFT) + SEBI fee (conservative; Zerodha
    # SEBI fee ko GST base mein ginta hai, Upstox page nahi likhta. Farak paise mein hai).
    "gst": 0.18,
}

# Brokerage per executed order (Upstox), teen scenario:
BROKERAGE = {
    "api_promo_10": 10.0,   # upstox.com/trading-api: Rs 10/order via API, "Valid till 31st Dec 2026"
    "standard_20": 20.0,    # upstox.com/brokerage-charges: options "Flat Rs 20 per executed order"
    "plus_30": 30.0,        # Upstox Plus T&C: equity options Rs 30 (manual orders)
}

# Lot size (dekha 10 Nov 2026):
# NIFTY 65, BANKNIFTY 30 -> NSE fo_mktlots.csv (NOV-26 .. ) ; NSE circular NSE/FAOP/70616.
# SENSEX 20 (Nov/Dec 2026 contracts), 25 (Jan 2027 se) -> Upstox public instrument master
# (BSE.json.gz, 8 Nov 2026). BSE ka notice verify nahi hua.
LOT = {"NIFTY": 65, "BANKNIFTY": 30, "SENSEX": 20, "SENSEX_JAN27": 25}
EXCH = {"NIFTY": "nse", "BANKNIFTY": "nse", "SENSEX": "bse", "SENSEX_JAN27": "bse"}
TICK = 0.05  # Rs, Upstox instrument master tick_size 5.0 paise for all three


def round_trip(index, buy, sell, lots=1, brokerage=20.0, orders_per_side=1):
    """Ek buy + ek sell (same din). Rupaye mein har charge lautata hai."""
    q = LOT[index] * lots
    b_val = buy * q
    s_val = sell * q
    txn_rate = RATES["txn_" + EXCH[index]]
    brk = brokerage * orders_per_side * 2
    stt = RATES["stt_sell"] * s_val
    txn = txn_rate * (b_val + s_val)
    sebi = RATES["sebi"] * (b_val + s_val)
    stamp = RATES["stamp_buy"] * b_val
    gst = RATES["gst"] * (brk + txn + sebi)
    total = brk + stt + txn + sebi + stamp + gst
    gross = s_val - b_val
    return {
        "qty": q, "buy_value": b_val, "sell_value": s_val, "gross_pnl": gross,
        "brokerage": brk, "stt": stt, "txn": txn, "sebi": sebi, "stamp": stamp, "gst": gst,
        "total": total, "net_pnl": gross - total,
        "pct_of_buy_premium": 100 * total / b_val,
    }


def breakeven(index, buy, lots=1, brokerage=20.0, orders_per_side=1):
    """Sell price jahan net P&L = 0 (slippage ke bina). Closed form:
    P_be = (P_buy*(1+v_b) + F/Q) / (1 - v_s)"""
    q = LOT[index] * lots
    t = RATES["txn_" + EXCH[index]]
    g = RATES["gst"]
    F = brokerage * orders_per_side * 2 * (1 + g)
    v_b = RATES["stamp_buy"] + (t + RATES["sebi"]) * (1 + g)
    v_s = RATES["stt_sell"] + (t + RATES["sebi"]) * (1 + g)
    p_be = (buy * (1 + v_b) + F / q) / (1 - v_s)
    return p_be, p_be - buy


def fmt(x):
    return f"{x:,.2f}"


def main():
    examples = [
        ("NIFTY", 200.0, 220.0),
        ("BANKNIFTY", 300.0, 280.0),
        ("SENSEX", 200.0, 240.0),
        ("SENSEX_JAN27", 200.0, 240.0),
    ]
    for name, br in BROKERAGE.items():
        print(f"\n=== Brokerage scenario: {name} (Rs {br}/executed order) ===")
        for idx, b, s in examples:
            r = round_trip(idx, b, s, brokerage=br)
            p_be, pts = breakeven(idx, b, brokerage=br)
            print(f"{idx:13s} lot={r['qty']:3d} buy {b:.2f} -> sell {s:.2f} | "
                  f"gross {fmt(r['gross_pnl'])} | charges {fmt(r['total'])} "
                  f"({r['pct_of_buy_premium']:.2f}% of buy premium) | net {fmt(r['net_pnl'])} | "
                  f"breakeven sell {p_be:.2f} (+{pts:.2f} pts, ~{pts / TICK:.0f} ticks)")
            if name == "standard_20":
                print("              breakup: brokerage {brokerage:.2f}, STT {stt:.2f}, txn {txn:.2f}, "
                      "SEBI {sebi:.4f}, stamp {stamp:.2f}, GST {gst:.2f}".format(**r))

    print("\n=== Slippage sensitivity (standard_20): har side N tick (Rs 0.05) bura fill ===")
    for idx, b, s in examples[:3]:
        q = LOT[idx]
        for n in (0, 1, 2, 4):
            slip = n * TICK
            r = round_trip(idx, b + slip, s - slip, brokerage=20.0)
            print(f"{idx:10s} {n} tick/side: buy {b + slip:.2f} sell {s - slip:.2f} | "
                  f"slippage cost Rs {2 * slip * q:.2f} | charges {fmt(r['total'])} | net {fmt(r['net_pnl'])}")

    print("\n=== Index points andaza (ATM delta ~0.5 maana; sirf andaza) ===")
    for idx, b, _ in examples[:3]:
        _, pts = breakeven(idx, b, brokerage=20.0)
        print(f"{idx:10s} premium breakeven +{pts:.2f} pts  => index ~{pts / 0.5:.1f} pts (delta 0.5)")


if __name__ == "__main__":
    main()
