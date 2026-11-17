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
