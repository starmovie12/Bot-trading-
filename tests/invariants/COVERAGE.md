# Invariant coverage (MISSION V11 §7; mission_check #14 enforces it once T07 is terminal)

| invariant | coverage |
|---|---|
| I4 | tests/invariants/test_i04_feed_stale_gap.py (feed side); order side N/A(order path not built) |
| I8 | T07 creates tests/invariants/test_order_path_disabled.py |
| I11 | tests/invariants/test_i11_time.py (holiday calendar: UNVERIFIED, official page not fetched) |
| I12 | tests/invariants/test_i12_money.py |
| I13 | tests/invariants/test_i13_feed_schema.py (feed side); order side N/A(order path not built) |
| I1 | N/A(order path not built) |
| I2 | N/A(order path not built) |
| I3 | N/A(order path not built) |
| I5 | N/A(order path not built) |
| I6 | N/A(order path not built) |
| I7 | N/A(order path not built) |
| I9 | N/A(order path not built) |
| I10 | N/A(order path not built); the static call-site scan runs as mission_check #8 |
