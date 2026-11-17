#!/usr/bin/env python3
"""Acceptance checks (MISSION V19 PART ACC).

  accept.py --phase <0|1b|3e|4c|6pre|6post|7pre|7post> [--root DIR]
prints `PASS|FAIL <id> <what>` per check, saves results/accept_<phase>.txt and exits 0 only when every id of the
phase passes; an id without a check function counts as FAIL (checks arrive with their phase).
"""

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)

import hashlib
import json
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


R1_NAMES = re.compile(r"(?<![a-z])(nifty|sensex|finnifty|midcpnifty|bankex)", re.IGNORECASE)
DATA_DERIVED = ("docs/DATA_REPORT.md", "docs/DATA_GAPS.md", "results/data_gaps.json", "results/api_vs_pack.json")
SKIP_LINE = "OWNER: STOP-1 skip (data OK) · STAGE 2 chalu"


def text(root: Path, rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def tree(root: Path) -> list[str]:
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard").stdout.splitlines()
    return [x for x in out if (root / x).is_file()]


@check("F1-1")
def data_request(root: Path) -> Result:
    req = text(root, "DATA_REQUEST.md")
    items = re.findall(r"^\d+\. .*$", req, re.MULTILINE)
    part_h = req.split("## Part H", 1)[-1].split("## Part R", 1)[0] if "## Part H" in req else ""
    h_items = re.findall(r"^\d+\. .*$", part_h, re.MULTILINE)
    part_r = req.split("## Part R", 1)[-1] if "## Part R" in req else ""
    ok = bool(items) and len(items) <= 10 and all("fallback_ok" in x for x in h_items) and "RECORDER_SPEC.md" in part_r
    return (
        ok,
        f"{len(items)} items, {len(h_items)} in Part H, Part R names RECORDER_SPEC.md: {'RECORDER_SPEC.md' in part_r}",
    )


@check("F1-2")
def feasibility_card(root: Path) -> Result:
    lines = text(root, "results/feasibility_card.md").splitlines()
    last = lines[-1] if lines else ""
    answer = bool(re.fullmatch(r"1 LOT: (kam se kam ₹[0-9,]+|NAHI|PATA NAHI)", last))
    ok = 0 < len(lines) <= 12 and all(len(x) <= 75 for x in lines) and answer
    return ok, f"{len(lines)} lines, longest {max((len(x) for x in lines), default=0)}, answer '{last}'"


@check("F1-3")
def regulatory(root: Path) -> Result:
    reg = text(root, "docs/REGULATORY.md")
    lic = re.search(r"^DATA-LICENCE \| (HAAN|NAHI|UNVERIFIED) \|", reg, re.MULTILINE)
    pub = re.search(r"^DATA-PUBLIC \| (HAAN|NAHI|UNVERIFIED) \|", reg, re.MULTILINE)
    present = [p for p in DATA_DERIVED if (root / p).exists()]
    ok = bool(lic and pub) and not (lic and lic.group(1) == "NAHI" and present)
    return (
        ok,
        f"DATA-LICENCE {lic.group(1) if lic else None}, DATA-PUBLIC {pub.group(1) if pub else None}"
        f", data files {len(present)}",
    )


@check("F1-4")
def power(root: Path) -> Result:
    p = root / "results/power.json"
    if not p.is_file():
        return False, "results/power.json missing"
    anchors = json.loads(p.read_text(encoding="utf-8")).get("anchors", {})
    want = {"sigma_1000_e_15": 34885, "sigma_1000_e_176": 254, "sigma_1000_n_30_mde": 511}
    return anchors == want, f"anchors {anchors}"


@check("F1-5")
def secrets_pins_state(root: Path) -> Result:
    scan = subprocess.run(  # noqa: S603
        [sys.executable, str(root / "tools/redact.py"), "--tree"], cwd=root, capture_output=True, text=True, check=False
    )
    pins_bad = check_pins.problems(root)
    st_ok, st_ev = state_and_files(root)
    ok = scan.returncode == 0 and not pins_bad and st_ok
    return (
        ok,
        f"secret scan rc {scan.returncode} ({len(scan.stdout.splitlines())} hits), pins {pins_bad or 'OK'}, {st_ev}",
    )


@check("F1-6")
def data_gaps(root: Path) -> Result:
    lic = re.search(r"^DATA-LICENCE \| (\w+)", text(root, "docs/REGULATORY.md"), re.MULTILINE)
    if lic and lic.group(1) == "NAHI":
        return True, "DATA-LICENCE NAHI: no gap files by design"
    raw = text(root, "results/data_gaps.json")
    if not raw or not (root / "docs/DATA_GAPS.md").is_file():
        return False, "docs/DATA_GAPS.md or results/data_gaps.json missing"
    g = json.loads(raw)
    rows = all(g.get(k, {}).get("verdict") in ("OK", "GAP", "NA") for k in ("G1", "G2", "G3", "G4", "G5"))
    g4 = g.get("G4", {})
    short_ok = "valid_days" in g4 and (g4["valid_days"] >= 125 or "days_short" in g4)
    part_h = text(root, "DATA_REQUEST.md").split("## Part H", 1)[-1].split("## Part R", 1)[0]
    gap_ids = all(re.search(r"gap G\d", x) for x in re.findall(r"^\d+\. .*$", part_h, re.MULTILINE))
    card_ok = True
    if state(root).get("STAGE") != "STOP-1":
        card = text(root, "results/stage1_card.md").splitlines()
        card_ok = len(card) == 5 and all(len(x) <= 70 for x in card) and card[-1] == SKIP_LINE
    ok = rows and "CALENDAR_UNVERIFIED" not in str(g.get("calendar")) and short_ok and gap_ids and card_ok
    return (
        ok,
        f"G1-G5 verdicts {rows}, calendar {g.get('calendar')}, valid_days {g4.get('valid_days')}"
        f", gap ids {gap_ids}, card {card_ok}",
    )


@check("F1-7")
def api_vs_pack(root: Path) -> Result:
    raw = text(root, "results/api_vs_pack.json")
    api = json.loads(raw).get("API_CHECK") if raw else None
    token_unset = state(root).get("TOKEN") == "not set"
    ok = api in ("MATCH", "DIFF", "NA") and (api == "NA" or not token_unset)
    return ok, f"API_CHECK {api}, TOKEN {state(root).get('TOKEN')}"


@check("F1-8")
def scope_banknifty(root: Path) -> Result:
    hits = []
    for rel in tree(root):
        source = rel.startswith(("bot/", "src/bot/", "lab/", "tools/")) and rel != "tools/accept.py"
        test = rel.startswith("tests/") and rel.endswith(".py") and rel != "tests/test_scope_banknifty.py"
        if (source or test) and R1_NAMES.search(text(root, rel)):
            hits.append(rel)
    return not hits, f"other-index names in {hits}" if hits else "BANKNIFTY only in bot/, lab/, tools/ and tests"


@check("F1-9")
def data_repo(root: Path) -> Result:
    if not (root / "data/banknifty/repo").exists():
        return True, "no data repo clone"
    sha = state(root).get("DATA_SHA", "")
    ignored = git(root, "check-ignore", "-q", "data/banknifty/repo").returncode == 0
    return bool(sha) and ignored, f"DATA_SHA {sha[:12] or 'missing'}, ignored {ignored}"


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
