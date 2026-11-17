#!/usr/bin/env python3
"""Acceptance checks (MISSION V19 PART ACC).

  accept.py --phase <0|1b|3e|4c|6pre|6post|7pre|7post> [--root DIR]
prints `PASS|FAIL <id> <what>` per check, saves results/accept_<phase>.txt and exits 0 only when every id of the
phase passes; an id without a check function counts as FAIL (checks arrive with their phase).
"""

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)

import hashlib
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import check_pins  # noqa: E402

Result = tuple[bool, str]
CHECKS: dict[str, Callable[[Path], Result]] = {}
PHASES = {
    "0": [f"F0-{i}" for i in range(1, 10)],
    "1b": [f"F1-{i}" for i in range(1, 10)],
    "3e": ["F6-1", "F6-2", "F6-3", "F6-11", "F3-1", "F3-2", "F3-3", "F3-4"],
    "4c": ["F6-9", *(f"F4-{i}" for i in range(1, 7))],
    "6pre": [f"F6-{i}" for i in range(1, 13)],
    "6post": [f"F6p-{i}" for i in range(1, 5)],
    "7pre": [f"F7-{i}" for i in range(1, 9)],
    "7post": [f"F6p-{i}" for i in range(1, 5)],
}
MANDATORY: tuple[str, ...] = (
    "STAGE",
    "NEXT",
    "BLOCK",
    "MODEL_NOW",
    "MODEL_NEXT",
    "SWITCH_PENDING",
    "FREEZE",
    "TRIALS",
    "HOLDOUT",
)
MANDATORY += ("HALT", "VISIBILITY", "TOKEN")
OPTIONAL = ("PREV_FREEZE", "FUNDS_GET_STATIC_IP_REQUIRED", "OWNER_CEILING_RS", "DATA_SHA", "OWNER_STOP_AT_STOP1")
IGNORED_SAMPLES: tuple[str, ...] = ("data/x", "data/banknifty/x", "data/recorded/x", "data/journal/x", "data/lab/x")
IGNORED_SAMPLES += ("recordings_private/x", "state/x", "config/params.local.toml")
RETIRED: tuple[str, ...] = (
    "mission_check.py",
    "seal.py",
    "make_report.py",
    "fullb_gate.py",
    "qcode.py",
    "callsite_allowlist.toml",
)
RETIRED += ("scan_allowlist.toml", "tag_scope.toml", "run_canary.py")
V11_TAG = "archive/v11-guards-final"


def check(cid: str) -> Callable[[Callable[[Path], Result]], Callable[[Path], Result]]:
    def register(fn: Callable[[Path], Result]) -> Callable[[Path], Result]:
        CHECKS[cid] = fn
        return fn

    return register


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)  # noqa: S603, S607


def state(root: Path) -> dict[str, str]:
    path = root / "STATE.md"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    return dict(x.split("=", 1) for x in lines if re.match(r"^[A-Z0-9_]+=", x))


def mission_file(root: Path) -> Path | None:
    found = sorted(root.glob("MISSION_V19*.md"))
    return found[0] if found else None


def part(text: str, pid: str) -> str:
    m = re.search(rf'^<part id="{pid}".*?\n(.*?)^</part>', text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


@check("F0-1")
def ignored(root: Path) -> Result:
    missing = [p for p in IGNORED_SAMPLES if git(root, "check-ignore", "-q", p).returncode != 0]
    return not missing, f"not ignored: {missing}" if missing else "all sample paths ignored"


@check("F0-2")
def pins(root: Path) -> Result:
    bad = check_pins.problems(root)
    return not bad, "; ".join(bad) or "pins OK"


@check("F0-3")
def state_and_files(root: Path) -> Result:
    need = ("RECORDER_SPEC.md", "OWNER_TODO.md", "PLAN.md", "STATE.md", "tools/check_recording.py")
    missing = [p for p in need if not (root / p).is_file()]
    if missing:
        return False, f"missing {missing}"
    lines = (root / "STATE.md").read_text(encoding="utf-8").splitlines()
    keys = state(root)
    absent, extra = [k for k in MANDATORY if k not in keys], [k for k in keys if k not in MANDATORY + OPTIONAL]
    ok = len(lines) <= 40 and not absent and not extra
    return ok, f"STATE.md {len(lines)} lines, absent {absent}, unknown {extra}"


@check("F0-4")
def retired(root: Path) -> Result:
    tag = git(root, "rev-parse", "-q", "--verify", f"refs/tags/{V11_TAG}").returncode == 0
    left = [n for n in RETIRED if (root / "tools" / n).exists()]
    hooks = root / ".githooks"
    called = (
        [h.name for h in hooks.glob("*") if any(n.split(".")[0] in h.read_text() for n in RETIRED)]
        if hooks.is_dir()
        else []
    )
    ok = tag and (root / "archive/v11_guards").is_dir() and not left and not called
    return ok, f"tag {tag}, archive {(root / 'archive/v11_guards').is_dir()}, left in tools {left}, in hooks {called}"


@check("F0-5")
def order_scan(root: Path) -> Result:
    test = "tests/test_safety.py"
    run = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
            f"{test}::test_no_order_endpoint_in_m0",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    old = git(root, "show", f"{V11_TAG}:{test}").stdout.encode()
    same = (root / test).is_file() and hashlib.sha256((root / test).read_bytes()).hexdigest() == hashlib.sha256(
        old
    ).hexdigest()
    return run.returncode == 0 and same, f"scan test rc {run.returncode}, file unchanged since {V11_TAG}: {same}"


@check("F0-6")
def phase0_results(root: Path) -> Result:
    missing = [p for p in ("results/net_check.txt", "results/scan_before_after.txt") if not (root / p).is_file()]
    return not missing, f"missing {missing}" if missing else "net check and scan record present"


@check("F0-7")
def branch(root: Path) -> Result:
    name = git(root, "symbolic-ref", "--quiet", "--short", "HEAD").stdout.strip()
    return name == "bot/banknifty-v1", f"branch {name or 'DETACHED'}"


@check("F0-8")
def model_fields(root: Path) -> Result:
    keys = state(root)
    absent = [k for k in ("BLOCK", "MODEL_NOW", "MODEL_NEXT", "SWITCH_PENDING") if k not in keys]
    log = (root / "results/model_log.md").is_file()
    return not absent and log, f"absent {absent}, model_log {log}"


@check("F0-9")
def map_spec_clock(root: Path) -> Result:
    mf = mission_file(root)
    spec = root / "RECORDER_SPEC.md"
    rec = part(mf.read_text(encoding="utf-8"), "REC") if mf is not None else None
    same = spec.is_file() and spec.read_text(encoding="utf-8") == rec
    mp = root / "docs/MAP.md"
    map_ok = mp.is_file() and len(mp.read_text(encoding="utf-8").splitlines()) <= 60
    clock = (root / "tools/clock.sh").is_file()
    return same and map_ok and clock, f"MAP.md ok {map_ok}, RECORDER_SPEC = PART REC {same}, clock.sh {clock}"


def run(phase: str, root: Path) -> tuple[int, list[str]]:
    lines = []
    for cid in PHASES[phase]:
        try:
            ok, ev = CHECKS[cid](root) if cid in CHECKS else (False, "no check function yet")
        except Exception as e:  # a crashing check is a FAIL, never a PASS
            ok, ev = False, f"check crashed: {type(e).__name__}: {e}"
        lines.append(f"{'PASS' if ok else 'FAIL'} {cid} {ev}")
    failed = sum(not x.startswith("PASS") for x in lines)
    return (1 if failed or len(lines) != len(PHASES[phase]) else 0), lines


def main(argv: list[str]) -> int:
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    if "--phase" not in argv or argv[argv.index("--phase") + 1] not in PHASES:
        print(__doc__, file=sys.stderr)
        return 64
    phase = argv[argv.index("--phase") + 1]
    rc, lines = run(phase, root)
    (root / "results").mkdir(exist_ok=True)
    (root / "results" / f"accept_{phase}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
