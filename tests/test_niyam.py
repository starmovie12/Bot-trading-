from __future__ import annotations

import copy
import tomllib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from bot.niyam import NeedsDecision, NiyamError, consistency_issues, load, parse

ROOT = Path(__file__).resolve().parents[1]
NIYAM = ROOT / "config" / "niyam.toml"


def _raw() -> dict[str, object]:
    with NIYAM.open("rb") as f:
        return tomllib.load(f)


def test_niyam_file_loads_with_all_rows() -> None:
    n = load(NIYAM)
    assert n.idea_version == "4.0"
    assert len(n.numbers) >= 203
    assert "Dashboard_Push_Samay" in n.numbers
    assert len(n.index_numbers) == 8
    assert {x.status for x in n.numbers.values()} <= {"Pakka", "Andaza", "Prastaavit", "Tay nahi"}


def test_tay_nahi_never_has_a_value() -> None:
    n = load(NIYAM)
    for x in n.numbers.values():
        if x.status == "Tay nahi":
            assert not x.is_typed, x.name


def test_known_values_from_idea() -> None:
    n = load(NIYAM)
    assert n.seconds("Pehredaar_Dhadkan_Samay") == 2
    assert n.seconds("Bot_Lease_Samay") == 4
    assert n.typed("Pehredaar_Dhadkan_Chhoot_Ginti") == (3, "dhadkan")
    assert n.get("Normal_Delta_Range").range == (0.45, 0.65)
    assert n.get("Aakhri_Entry_Samay").time_ist == "15:10"
    assert n.typed("Server_Mahina_Budget") == (1500, "inr")
    assert n.get("Malik_Max_Balance").range == (10000.0, 15000.0)
    assert n.seconds("Dashboard_Push_Samay") == 5


def test_code_never_guesses_undecided_numbers() -> None:
    n = load(NIYAM)
    with pytest.raises(NeedsDecision):
        n.typed("EMA_Slope_Hadd")  # Tay nahi
    with pytest.raises(NeedsDecision):
        n.typed("Data_Purana_Hadd")  # range, malik ka faisla baaki
    with pytest.raises(NiyamError):
        n.get("Aisa_Koi_Number_Nahi")


def test_lease_invariant_holds() -> None:
    issues = consistency_issues(load(NIYAM))
    assert not any("Bot_Lease_Samay" in i and "kam hona chahiye" in i for i in issues)


@pytest.mark.parametrize(
    ("mutate", "msg"),
    [
        (lambda d: d["number"]["Bot_Lease_Samay"].__setitem__("status", "Shayad"), "status"),
        (lambda d: d["number"]["EMA_Slope_Hadd"].__setitem__("value", 5), "Tay nahi"),
        (lambda d: d["number"]["Normal_Delta_Range"].__setitem__("range", [0.7, 0.4]), "range"),
        (lambda d: d["number"]["Bot_Lease_Samay"].__setitem__("unit", "ghante"), "unit"),
        (lambda d: d["number"]["Bot_Lease_Samay"].__setitem__("value", -1), "negative"),
        (lambda d: d["number"]["Bot_Lease_Samay"].__setitem__("jadoo", 1), "anjaan"),
        (lambda d: d["number"].pop("Bot_Lease_Samay"), "ginti"),
        (lambda d: d["meta"].__setitem__("source_sha256", "abc"), "meta"),
    ],
)
def test_bad_file_fails(mutate: object, msg: str) -> None:
    d = copy.deepcopy(_raw())
    mutate(d)  # type: ignore[operator]
    with pytest.raises(NiyamError, match=msg):
        parse(d)


def test_lease_violation_is_reported() -> None:
    d = copy.deepcopy(_raw())
    d["number"]["Bot_Lease_Samay"]["value"] = 6  # type: ignore[index]
    issues = consistency_issues(parse(d))
    assert any("Bot_Lease_Samay" in i for i in issues)


@given(st.text(max_size=80), st.sampled_from(["Pakka", "Andaza", "Prastaavit", "Tay nahi"]))
def test_generator_parser_never_crashes_and_respects_tay_nahi(text: str, status: str) -> None:
    from tools.niyam_from_idea import parse_kimat

    out = parse_kimat("X_Y", text, status)
    if status == "Tay nahi":
        assert out == {}
    if "range" in out:
        r = out["range"]
        assert isinstance(r, list) and len(r) == 2
