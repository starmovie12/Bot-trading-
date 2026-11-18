# LOTS MATH (owner order 4, D-47 B; arithmetic, not a trial)

Brokerage is FLAT per order: ₹20 an order whatever the quantity (constants.toml SOURCE), so 1 round
trip pays ₹40 + GST for 1, 2 or 3 lots. Spread, slippage, STT, exchange, SEBI, IPFT and stamp grow with the
quantity. Stressed: charges x 1.5, spread / slippage x 2 (ST7). Premium and delta: F6 medians (30-min hold).

| strike | lots | qty | stressed cost ₹ | cost ₹ per lot | cost pts per unit | break-even index pts | premium x qty ₹ (max loss by construction) |
|---|---|---|---|---|---|---|---|
| ITM2 | 1 | 30 | 231 | 231 | 7.69 | 14.0 | 21,330 |
| ITM2 | 2 | 60 | 391 | 195 | 6.51 | 11.8 | 42,660 |
| ITM2 | 3 | 90 | 550 | 183 | 6.12 | 11.1 | 63,990 |
| ITM1 | 1 | 30 | 224 | 224 | 7.48 | 14.4 | 19,560 |
| ITM1 | 2 | 60 | 378 | 189 | 6.30 | 12.1 | 39,120 |
| ITM1 | 3 | 90 | 531 | 177 | 5.91 | 11.4 | 58,680 |
| ATM | 1 | 30 | 219 | 219 | 7.29 | 14.9 | 18,000 |
| ATM | 2 | 60 | 367 | 183 | 6.11 | 12.5 | 36,000 |
| ATM | 3 | 90 | 515 | 172 | 5.72 | 11.7 | 54,000 |
| CAP15 | 1 | 30 | 199 | 199 | 6.64 | 17.0 | 12,510 |
| CAP15 | 2 | 60 | 328 | 164 | 5.46 | 14.0 | 25,020 |
| CAP15 | 3 | 90 | 456 | 152 | 5.07 | 13.0 | 37,530 |

Reading:
- The flat brokerage (₹20 an order, ~₹71 a round trip after GST and the x1.5 stress) is shared by more
  lots: ATM costs ₹219 a lot at 1 lot, ₹183 at 2, ₹172 at 3, so the break-even falls from 14.9 to 12.5
  to 11.7 index points (CAP15 17.0 -> 13.0): a real but modest cut, about 3 points at 3 lots.
- It does not create an edge: a trade still needs its average index move to beat ~12-14 points, and
  profit AND loss both scale with the lots (3 lots = 3 x the swing).
- Loss-first cap (pinned MAX_TRADE_LOSS_RS ₹35,700 per trade, D-47): the by-construction max loss is
  premium x qty, so 2 ATM lots (₹36,000), 2 ITM2 lots (₹42,660) and every 3-lot size are above it;
  only CAP15 fits 2 lots (₹25,020), and 1 lot fits for every strike. Larger sizes are skipped.
- Size only helps a strategy that ALREADY has a positive stressed net per trade; on a negative one
  it multiplies the loss.
