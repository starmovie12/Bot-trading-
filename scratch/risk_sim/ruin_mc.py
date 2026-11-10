#!/usr/bin/env python3
"""Throw-away Monte Carlo: sizing niyam ka Risk of Ruin (production code nahi).

Maanyatayein (sab ANDAZA, asli data nahi):
- Nifty50 option premium Rs 200, Lot 65 -> 1 Lot = Rs 13,000 (Lot: NSE, 10 Nov 2026).
- Round-trip kharcha ~Rs 80.5/lot (R_d) + Slippage 2 tick/side = 4 tick * 0.05 * 65 = Rs 13 -> Rs 93.5/lot.
- Jeet: premium par +W * U(0.5,1.5). Haar: -L * U(0.8,1.2); haar mein 5% "gap" case -(L+0.20).
- Ek path = 250 trade (~1 saal, ~1 trade/din). 20,000 paths. Koi naya paisa nahi daala jaata.
- "Ruin" = equity itni kam ki 1 Lot + 10% buffer na kharida ja sake.
"""
import numpy as np

LOT_COST = 200 * 65
COST_PER_LOT = 80.52 + 13.0
BUF = 0.10
N_TRADES, N_PATHS = 250, 20_000
GAP_P, GAP_EXTRA = 0.05, 0.20


def outcomes(rng, p, W, L, shape):
    win = rng.random(shape) < p
    u_w = rng.uniform(0.5, 1.5, shape)
    u_l = rng.uniform(0.8, 1.2, shape)
    gap = rng.random(shape) < GAP_P
    r = np.where(win, W * u_w, -(L * u_l + np.where(gap, GAP_EXTRA, 0.0)))
    return r


def lots_for(policy, eq):
    afford = np.floor(eq / (LOT_COST * (1 + BUF)))
    if policy == "malik_poora_balance":
        return afford
    if policy == "A_25pct_stake":
        return np.minimum(afford, np.floor(0.25 * eq / LOT_COST))
    if policy == "A_10pct_stake":
        return np.minimum(afford, np.floor(0.10 * eq / LOT_COST))
    if policy == "C_max_loss_5pct":  # Worst-case nuksan (40% premium) <= 5% equity
        return np.minimum(afford, np.floor(0.05 * eq / (0.40 * LOT_COST)))
    raise ValueError(policy)


def simulate(p, W, L, policy, eq0, seed=7):
    rng = np.random.default_rng(seed)
    r = outcomes(rng, p, W, L, (N_PATHS, N_TRADES))
    eq = np.full(N_PATHS, float(eq0))
    peak = eq.copy()
    maxdd = np.zeros(N_PATHS)
    ruined = np.zeros(N_PATHS, bool)
    traded = np.zeros(N_PATHS)
    first_sl_pct = None
    for t in range(N_TRADES):
        lots = lots_for(policy, eq)
        lots = np.where(ruined, 0, lots)
        if t == 0:
            first_sl_pct = float(np.median(lots * LOT_COST * L / eq0))
        pnl = lots * (LOT_COST * r[:, t] - COST_PER_LOT)
        eq = eq + pnl
        traded += lots > 0
        peak = np.maximum(peak, eq)
        maxdd = np.maximum(maxdd, 1 - eq / peak)
        ruined |= np.floor(eq / (LOT_COST * (1 + BUF))) < 1
    stopped = (~ruined) & (lots_for(policy, eq) < 1)
    return {
        "P(ruin)": ruined.mean(),
        "P(niyam se ruka)": stopped.mean(),
        "P(eq<50% start)": (eq < 0.5 * eq0).mean(),
        "median end/start": float(np.median(eq / eq0)),
        "P(end>start)": (eq > eq0).mean(),
        "median maxDD": float(np.median(maxdd)),
        "p95 maxDD": float(np.quantile(maxdd, 0.95)),
        "median trades": float(np.median(traded)),
        "1st SL % of eq": first_sl_pct,
    }


def edge(p, W, L):
    loss = L + GAP_P * GAP_EXTRA
    cost = COST_PER_LOT / LOT_COST
    mu = p * W - (1 - p) * loss - cost
    # Kelly (do-nateeje wala andaza): f* = (p*W - q*loss)/(W*loss), cost ko mu mein
    f = (p * W - (1 - p) * loss - cost) / (W * loss)
    # Ek trade ka sigma (stake ka hissa)
    var = p * (W**2 * (1 + 1 / 12)) + (1 - p) * (loss**2) - (p * W - (1 - p) * loss) ** 2
    return mu, f, var**0.5


if __name__ == "__main__":
    scen = {
        "Bura (p=0.35)": (0.35, 0.45, 0.28),
        "Barabar ke paas (p=0.40)": (0.40, 0.45, 0.28),
        "Thoda edge (p=0.45)": (0.45, 0.45, 0.28),
        "Achha edge (p=0.50)": (0.50, 0.45, 0.28),
    }
    print("## Scenario ki ganit (stake ke hisse mein)")
    print("| Scenario | Net Expectancy/trade | Kelly Hissa | Sigma/trade | 95% bharose ke liye trade (n=(1.645*sigma/mu)^2) |")
    print("|---|---|---|---|---|")
    for k, (p, W, L) in scen.items():
        mu, f, s = edge(p, W, L)
        n = (1.645 * s / mu) ** 2 if mu > 0 else float("inf")
        print(f"| {k} | {mu*100:+.2f}% | {max(f,0)*100:.1f}% | {s*100:.1f}% | {'kabhi nahi' if mu<=0 else int(round(n))} |")
    print("\nNote: Rs 14,000 se Nifty ka 1 Lot (13,000 + 10% buffer = 14,300) nahi khareeda ja sakta; isliye 15,000 se shuru.")
    for eq0 in (15_000, 52_000, 1_30_000):
        print(f"\n## Shuruaati equity Rs {eq0:,}")
        print("| Scenario | Niyam | P(ruin) | P(niyam se ruka) | P(eq<50%) | Median ant/shuru | P(munafa) | Median maxDD | p95 maxDD | Median trades | Pehla SL % equity |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for k, (p, W, L) in scen.items():
            for pol in ("malik_poora_balance", "A_25pct_stake", "A_10pct_stake", "C_max_loss_5pct"):
                m = simulate(p, W, L, pol, eq0)
                print(f"| {k} | {pol} | {m['P(ruin)']:.1%} | {m['P(niyam se ruka)']:.1%} | {m['P(eq<50% start)']:.1%} | {m['median end/start']:.2f} | {m['P(end>start)']:.1%} | {m['median maxDD']:.0%} | {m['p95 maxDD']:.0%} | {m['median trades']:.0f} | {m['1st SL % of eq']:.0%} |")
