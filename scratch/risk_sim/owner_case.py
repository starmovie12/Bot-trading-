#!/usr/bin/env python3
"""Throw-away: malik ke asli case ka hisaab (production code nahi).

Malik (10 Nov 2026): balance Rs 10,000-15,000; achha (ITM/ATM) premium Rs 400-500;
niyam: achhe premium ka 1 Lot poore balance se bhi le lo, sasta/OTM kabhi nahi, paisa kam ho toh skip.
Lot (NSE/Upstox file, 10 Nov 2026): Nifty50 65, BankNifty 30, Sensex 20 (Jan 2027 contracts se 25: verify nahi hua).
Outcome model wahi andaza jo ruin_mc.py mein hai.
"""
import numpy as np

LOTS = {"Nifty50": 65, "BankNifty": 30, "Sensex (20)": 20, "Sensex (25, Jan 2027)": 25}
BUFFERS = {"10% Lot (9 Nov Prastaavit)": lambda lot_cost: 0.10 * lot_cost, "Rs 250 (CC Prastaav)": lambda lot_cost: 250.0}


def afford_table():
    print("## 1 Lot khareedne ke liye kitna paisa (premium x Lot + buffer)\n")
    print("| Index | Lot | Premium 400 | Premium 450 | Premium 500 |")
    print("|---|---|---|---|---|")
    for name, lot in LOTS.items():
        cells = []
        for prem in (400, 450, 500):
            c = prem * lot
            cells.append(f"Rs {c:,.0f} (+10%: {c*1.1:,.0f}; +250: {c+250:,.0f})")
        print(f"| {name} | {lot} | " + " | ".join(cells) + " |")
    print("\n## Kis balance par sabse mehenga kaunsa premium chal sakta hai (1 Lot)\n")
    print("| Index | Balance 10,000 (10% buffer / Rs 250 buffer) | Balance 15,000 (10% / Rs 250) |")
    print("|---|---|---|")
    for name, lot in LOTS.items():
        row = []
        for bal in (10_000, 15_000):
            row.append(f"Rs {bal/(lot*1.1):,.0f} / Rs {(bal-250)/lot:,.0f}")
        print(f"| {name} | {row[0]} | {row[1]} |")


def refill_sim(lot, prem, p, W=0.45, L=0.28, eq0=15_000, buf=250.0, n_trades=250, n_paths=20_000, seed=11):
    """Malik ka niyam + Fund Request: paisa 1 Lot se kam ho toh malik wapas Rs 15,000 tak bharta hai.
    Malik ka balance max Rs 15,000 rehta hai: upar ka munafa har trade ke baad nikaal liya jaata hai."""
    rng = np.random.default_rng(seed)
    lot_cost = prem * lot
    cost = 93.5 * lot / 65 + 15  # kharcha+slippage ka mota andaza (Nifty Rs 93.5 se scale) + STT farak
    eq = np.full(n_paths, float(eq0))
    deposits = np.full(n_paths, float(eq0))
    refills = np.zeros(n_paths)
    withdrawn = np.zeros(n_paths)
    worst = np.zeros(n_paths)  # running net (equity + nikala - daala) ka sabse neeche ka bindu
    for t in range(n_trades):
        need = lot_cost + buf
        low = eq < need
        add = np.where(low, eq0 - eq, 0.0)
        deposits += add
        refills += low
        eq = eq + add
        lots = np.floor((eq - buf) / lot_cost)  # malik: jitne poore Lot ka paisa
        win = rng.random(n_paths) < p
        r = np.where(win, W * rng.uniform(0.5, 1.5, n_paths),
                     -(L * rng.uniform(0.8, 1.2, n_paths) + np.where(rng.random(n_paths) < 0.05, 0.20, 0.0)))
        eq = eq + lots * (lot_cost * r - cost)
        extra = np.maximum(eq - eq0, 0.0)
        withdrawn += extra
        eq = eq - extra
        worst = np.minimum(worst, eq + withdrawn - deposits)
    net = eq + withdrawn - deposits
    return {
        "median refills": float(np.median(refills)),
        "median kul daala": float(np.median(deposits)),
        "median net (ant equity - kul daala)": float(np.median(net)),
        "P(net nuksan)": float((net < 0).mean()),
        "p10 net": float(np.quantile(net, 0.10)),
        "p90 net": float(np.quantile(net, 0.90)),
        "1 SL ka nuksan (% of 15k)": L * lot_cost / eq0,
        "median sabse neeche": float(np.median(worst)),
        "p95 sabse neeche": float(np.quantile(worst, 0.05)),
    }


if __name__ == "__main__":
    afford_table()
    print("\n## Malik ka niyam + Fund Request (kam hone par wapas Rs 15,000; upar ka munafa nikaala), 250 trade, 20,000 path\n")
    print("| Index @ premium | Jeet-dar (edge) | 1 SL = balance ka | Median refill | Median net (250 trade) | P(net nuksan) | p10 net | p90 net | Sabse neeche (median) | Sabse neeche (bura 5%) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for name, lot, prem in (("Sensex (20) @ 450", 20, 450), ("BankNifty @ 400", 30, 400)):
        for lbl, p in (("40% (barabar)", 0.40), ("45% (thoda edge)", 0.45), ("50% (achha edge)", 0.50)):
            m = refill_sim(lot, prem, p)
            print(f"| {name} | {lbl} | {m['1 SL ka nuksan (% of 15k)']:.0%} | {m['median refills']:.0f} | Rs {m['median net (ant equity - kul daala)']:,.0f} | {m['P(net nuksan)']:.0%} | Rs {m['p10 net']:,.0f} | Rs {m['p90 net']:,.0f} | Rs {m['median sabse neeche']:,.0f} | Rs {m['p95 sabse neeche']:,.0f} |")
