"""tools/accept.py: every check passes on a good fixture and fails on its broken one (MISSION V19 PART ACC)."""

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from tools import accept, check_pins

ROOT = Path(__file__).resolve().parents[1]
COPY = (
    ".gitignore",
    "config/PINS.sha256",
    *check_pins.PINNED,
    "RECORDER_SPEC.md",
    "MISSION_V19.md",
    "OWNER_TODO.md",
    "PLAN.md",
    "STATE.md",
    "tools/check_recording.py",
    "tools/clock.sh",
    "results/net_check.txt",
    "results/scan_before_after.txt",
    "results/model_log.md",
    "docs/MAP.md",
    "tests/test_safety.py",
    ".githooks/pre-commit",
    ".githooks/pre-push",
)


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)  # noqa: S603, S607


def make_fixture(tmp: Path) -> Path:
    for rel in COPY:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp / rel)
    (tmp / "archive/v11_guards").mkdir(parents=True)
    (tmp / "archive/v11_guards/README.md").write_text("retired\n")
    (tmp / "src").mkdir()
    (tmp / "src/ok.py").write_text("X = 1\n")
    git(tmp, "init", "-q", "-b", "bot/banknifty-v1")
    git(tmp, "config", "user.email", "fixture@example.invalid")
    git(tmp, "config", "user.name", "fixture")
    git(tmp, "add", "--", *COPY, "archive/v11_guards/README.md", "src/ok.py")
    git(tmp, "commit", "-q", "-m", "fixture")
    git(tmp, "tag", accept.V11_TAG)
    return tmp


def _without(path: Path, prefix: str) -> None:
    path.write_text("".join(x for x in path.read_text().splitlines(keepends=True) if not x.startswith(prefix)))


BREAK: dict[str, Callable[[Path], object]] = {
    "F0-1": lambda r: _without(r / ".gitignore", "state/"),
    "F0-2": lambda r: (r / "limits.toml").write_text((r / "limits.toml").read_text() + "\n# loosened\n"),
    "F0-3": lambda r: _without(r / "STATE.md", "TOKEN="),
    "F0-4": lambda r: (r / "tools/mission_check.py").write_text("X = 1\n"),
    "F0-5": lambda r: (r / "src/ok.py").write_text("def place_order() -> None: ...\n"),
    "F0-6": lambda r: (r / "results/net_check.txt").unlink(),
    "F0-7": lambda r: git(r, "switch", "-q", "-c", "other"),
    "F0-8": lambda r: (r / "results/model_log.md").unlink(),
    "F0-9": lambda r: (r / "RECORDER_SPEC.md").write_text("changed\n"),
}


def test_every_phase0_check_passes_on_the_good_fixture(tmp_path: Path) -> None:
    rc, lines = accept.run("0", make_fixture(tmp_path))
    assert rc == 0, lines


@pytest.mark.parametrize("cid", sorted(BREAK))
def test_each_phase0_check_fails_on_its_broken_fixture(tmp_path: Path, cid: str) -> None:
    root = make_fixture(tmp_path)
    BREAK[cid](root)
    rc, lines = accept.run("0", root)
    assert rc == 1
    assert [x for x in lines if not x.startswith("PASS")] == [x for x in lines if x.startswith(f"FAIL {cid} ")], lines


def test_every_phase0_id_has_a_breaker() -> None:
    assert sorted(BREAK) == sorted(accept.PHASES["0"])


def test_an_id_without_a_check_function_fails(tmp_path: Path) -> None:
    rc, lines = accept.run("6post", tmp_path)
    assert rc == 1 and all(x.startswith("FAIL") for x in lines)


COPY_1B = (
    ".gitignore",
    "config/PINS.sha256",
    *check_pins.PINNED,
    "tools/redact.py",
    "tools/check_recording.py",
    "STATE.md",
    "RECORDER_SPEC.md",
    "OWNER_TODO.md",
    "PLAN.md",
    "DATA_REQUEST.md",
    "docs/REGULATORY.md",
    "docs/DATA_REPORT.md",
    "docs/DATA_GAPS.md",
    "results/feasibility_card.md",
    "results/power.json",
    "results/data_gaps.json",
    "results/api_vs_pack.json",
    "results/stage1_card.md",
)


def make_fixture_1b(tmp: Path) -> Path:
    for rel in COPY_1B:
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp / rel)
    for rel in ("src/bot/ok.py", "lab/ok.py", "tests/test_ok.py"):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).write_text("X = 1\n")
    (tmp / "data/banknifty/repo").mkdir(parents=True)
    git(tmp, "init", "-q", "-b", "bot/banknifty-v1")
    git(tmp, "add", "--", *COPY_1B, "src/bot/ok.py", "lab/ok.py", "tests/test_ok.py")
    return tmp


def _sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))


OTHER_INDEX = "NIF" + "TY50"  # built at run time so this file never matches the R1 scan itself
FAKE_JWT = "ey" + "J" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12

BREAK_1B: dict[str, Callable[[Path], object]] = {
    "F1-1": lambda r: _sub(r / "DATA_REQUEST.md", "fallback_ok", "fallback"),
    "F1-2": lambda r: (r / "results/feasibility_card.md").write_text("x" * 90 + "\n1 LOT: NAHI\n"),
    "F1-3": lambda r: _sub(r / "docs/REGULATORY.md", "DATA-LICENCE | UNVERIFIED", "DATA-LICENCE | NAHI"),
    "F1-4": lambda r: _sub(r / "results/power.json", "254", "255"),
    "F1-5": lambda r: (r / "notes.md").write_text(f"token {FAKE_JWT}\n"),
    "F1-6": lambda r: _sub(
        r / "results/data_gaps.json", '"calendar": "2026 SOURCE', '"calendar": "CALENDAR_UNVERIFIED'
    ),
    "F1-7": lambda r: _sub(r / "results/api_vs_pack.json", '"NA"', '"MAYBE"'),
    "F1-8": lambda r: (r / "tools/x.py").write_text(f"{OTHER_INDEX} = 1\n"),
    "F1-9": lambda r: _without(r / "STATE.md", "DATA_SHA="),
}


def test_every_1b_check_passes_on_the_good_fixture(tmp_path: Path) -> None:
    rc, lines = accept.run("1b", make_fixture_1b(tmp_path))
    assert rc == 0, lines


@pytest.mark.parametrize("cid", sorted(BREAK_1B))
def test_each_1b_check_fails_on_its_broken_fixture(tmp_path: Path, cid: str) -> None:
    root = make_fixture_1b(tmp_path)
    BREAK_1B[cid](root)
    rc, lines = accept.run("1b", root)
    assert rc == 1
    assert [x for x in lines if not x.startswith("PASS")] == [x for x in lines if x.startswith(f"FAIL {cid} ")], lines


def test_every_1b_id_has_a_breaker() -> None:
    assert sorted(BREAK_1B) == sorted(accept.PHASES["1b"])


COPY_3E = (
    "limits.toml",
    "trials.jsonl",
    "holdout_log.jsonl",
    "DECISIONS.md",
    "results/prefilter.md",
    "results/scoreboard.md",
    "results/market_facts.md",
    "results/replay_agreement.json",
    "results/loss_first_rank.json",
    "results/verdict.json",
    "src/bot/__init__.py",
    "src/bot/contracts.py",
    "tools/__init__.py",
    "tools/engine_of_record.py",
    "tools/bn_economics.py",
    "lab/__init__.py",
    "lab/data.py",
    "constants.toml",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/test_engine_of_record.py",
    "pyproject.toml",
)


def make_fixture_3e(tmp: Path) -> Path:
    for rel in (*COPY_3E, "PLAN.md"):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp / rel)
    git(tmp, "init", "-q", "-b", "bot/banknifty-v1")
    git(tmp, "config", "user.email", "fixture@example.invalid")
    git(tmp, "config", "user.name", "fixture")
    git(tmp, "add", "--", "PLAN.md")
    git(tmp, "commit", "-q", "-m", "prereg")  # §PREREG-0 first, then the trials (ST1, N4)
    git(tmp, "add", "--", *COPY_3E)
    git(tmp, "commit", "-q", "-m", "trials")
    return tmp


def _append(path: Path, line: str) -> None:
    path.write_text(path.read_text() + line)


BREAK_3E: dict[str, Callable[[Path], object]] = {
    "F6-1": lambda r: _sub(r / "limits.toml", "[LIVE_POSSIBLE]\nvalue = false", "[LIVE_POSSIBLE]\nvalue = true"),
    "F6-2": lambda r: _append(r / "trials.jsonl", (r / "trials.jsonl").read_text().splitlines()[0] + "\n"),
    "F6-3": lambda r: _append(r / "holdout_log.jsonl", '{"event": "open"}\n'),
    "F6-11": lambda r: (r / "results/scoreboard.md").write_text(
        (r / "results/scoreboard.md").read_text().split("## Finalists")[0]
    ),
    "F3-1": lambda r: _sub(r / "PLAN.md", "A10", "Z10"),
    "F3-2": lambda r: (r / "results/market_facts.md").write_text("x\n" * 41),
    "F3-3": lambda r: _append(r / "tools/engine_of_record.py", "# padding\n# padding\n"),
    "F3-4": lambda r: (r / "results/verdict.json").write_text('{"label": "MAYBE"}\n'),
}


def test_every_3e_check_passes_on_the_good_fixture(tmp_path: Path) -> None:
    rc, lines = accept.run("3e", make_fixture_3e(tmp_path))
    assert rc == 0, lines


@pytest.mark.parametrize("cid", sorted(BREAK_3E))
def test_each_3e_check_fails_on_its_broken_fixture(tmp_path: Path, cid: str) -> None:
    root = make_fixture_3e(tmp_path)
    BREAK_3E[cid](root)
    rc, lines = accept.run("3e", root)
    assert rc == 1
    assert [x for x in lines if not x.startswith("PASS")] == [x for x in lines if x.startswith(f"FAIL {cid} ")], lines


def test_every_3e_id_has_a_breaker() -> None:
    assert sorted(BREAK_3E) == sorted(accept.PHASES["3e"])
