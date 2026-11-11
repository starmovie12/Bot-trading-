"""I12 money (MISSION V11 §7): Decimal / paise only, never float; tick rounding; charges rounded by rule.

The G0 economics (tools/economics.py) is the money path that exists on every track.
"""

from __future__ import annotations

import ast
import inspect
import re
import textwrap
from decimal import Decimal
from typing import Any

from tools import economics as eco

TEST_INPUTS: dict[str, Any] = {
    "facts": {
        "brokerage_fo_per_order": {"value": "20", "tag": "SOURCE"},
        "stt_option_sell": {"value": "0.15", "tag": "SOURCE"},
        "nse_txn_charge_composite": {"value": "0.03553", "tag": "SOURCE"},
        "bse_txn_charge": {"value": "0.0325", "tag": "SOURCE"},
        "sebi_fee": {"value": "10", "tag": "SOURCE"},
        "stamp_duty_buy": {"value": "0.003", "tag": "SOURCE"},
        "gst": {"value": "18", "tag": "SOURCE"},
    },
    "limits": {},
    "params": {},
}


def test_money_rounds_half_up_to_paise() -> None:
    assert eco.money(Decimal("1.005")) == Decimal("1.01")
    assert eco.money(Decimal("1.004")) == Decimal("1.00")
    assert eco.money(Decimal("-1.005")) == Decimal("-1.01")
    assert eco.money(Decimal("1072.5")) == Decimal("1072.50")


def test_round_trip_charges_match_a_hand_computation() -> None:
    m = eco.Model(TEST_INPUTS)
    # buy 1000, sell 1000, 2 orders, NSE: brokerage 40.00; STT 1.50; exchange 0.71; SEBI 0.00;
    # stamp 0.03; GST 18% of (40.00 + 0.71 + 0.00) = 7.33 → total 49.57
    total = m.charges(Decimal("1000"), Decimal("1000"), 2, "NSE")
    assert isinstance(total, Decimal)
    assert total == Decimal("49.57")
    assert total == total.quantize(Decimal("0.01"))


def test_bse_uses_its_own_exchange_rate() -> None:
    m = eco.Model(TEST_INPUTS)
    nse = m.charges(Decimal("1000"), Decimal("1000"), 2, "NSE")
    bse = m.charges(Decimal("1000"), Decimal("1000"), 2, "BSE")
    assert bse < nse


def test_max_fit_premium_is_a_tick_multiple_and_tight() -> None:
    m = eco.Model(TEST_INPUTS)
    lot, limit = Decimal(65), Decimal(1125)
    p = m.max_fit_premium(lot, "NSE", 1, limit)
    assert p % eco.TICK == 0
    assert p * lot + m.charges(p * lot, p * lot, 2, "NSE") <= limit
    q = p + eco.TICK
    assert q * lot + m.charges(q * lot, q * lot, 2, "NSE") > limit


def test_money_paths_contain_no_float() -> None:
    for fn in (eco.money, eco.Model.charges, eco.Model.max_fit_premium, eco.Model.server, eco.Model.baseline):
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        for node in ast.walk(tree):
            assert not (isinstance(node, ast.Constant) and isinstance(node.value, float)), fn.__name__
            assert not (isinstance(node, ast.Name) and node.id == "float"), fn.__name__


def test_every_output_amount_is_a_paise_string_with_a_tag() -> None:
    result = eco.compute(eco.build_inputs())
    seen = 0

    def walk(node: Any) -> None:
        nonlocal seen
        if isinstance(node, dict):
            if set(node) == {"value", "tag"}:
                seen += 1
                assert isinstance(node["value"], str)
                assert re.fullmatch(r"-?\d+(\.\d{1,2})?", node["value"]), node
                assert re.fullmatch(r"CODE\([A-Z]+(·stressed)?\)", node["tag"]), node
                return
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(result)
    assert seen > 50
