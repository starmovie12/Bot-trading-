#!/usr/bin/env python3
"""MISSION V11 guard (§5.5). One file, standard library only, no local imports.

Tier 1 (default; pre-commit hook, after every task and checkpoint): the CORE checks
#1 #2 #3 #5 #6 #7 #9 #11 #12 #14 #15 #17 #18 #19 and the FULL checks #4 #8 #10 #13 #16 (T02b).
--history adds #6h, the secrets scan of the git history (pre-push hook and CI only).
Tier 2 (--final): Tier 1 plus constants TTL, the holdout open-counter and gate-input eligibility.

usage: mission_check.py [--root PATH] [--final] [--record-tests] [--history]
Exit 0 = green, 1 = red. One line per check. A red line names path:line, never a value.
"""

from __future__ import annotations

import ast
import datetime as dt
import fnmatch
import hashlib
import itertools
import json
import math
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

TAGS = ("SOURCE", "REAL", "BACKTEST", "SHADOW", "SIM", "HISTORY", "POINTER", "ESTIMATE", "ASSUMPTION", "OWNER")
TAG_RE = re.compile(r"^(?:(?:%s)|CODE\((?:%s)(?:·stressed)?\))$" % ("|".join(TAGS), "|".join(TAGS)))  # noqa: UP031
GATE_ELIGIBLE = re.compile(r"^(SOURCE|REAL|OWNER|CODE\((SOURCE|REAL|OWNER)\)|CODE\([A-Z]+·stressed\))$")
TERMINAL = ("PASS", "BLOCKED", "SKIPPED_BY_GATE")
STOP_INCIDENTS = ("secret", "sandbox_breach", "live_process", "class_c", "seal_mismatch")
COMMAND = re.compile(
    r"^(?:(?P<yn>haan|ha|haa|han|yes|na|nahi|nhi|nai|no) (?P<id1>F-[A-Z0-9-]+) (?P<c1>[0-9a-f]{4})"
    r"|set (?P<id2>F-[A-Z0-9-]+) (?P<val>\S+) (?P<c2>[0-9a-f]{4}))$",
    re.IGNORECASE,
)


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, rel: str) -> Path:
        return self.root / rel

    def text(self, rel: str) -> str:
        p = self.path(rel)
        return p.read_bytes().decode("utf-8", "replace") if p.is_file() else ""

    def git(self, *args: str) -> tuple[int, str]:
        r = subprocess.run(["git", *args], cwd=self.root, capture_output=True, check=False)  # noqa: S603, S607
        return r.returncode, r.stdout.decode("utf-8", "replace")

    def sha(self, rel: str) -> str:
        return hashlib.sha256(self.path(rel).read_bytes()).hexdigest()

    def tasks(self) -> list[dict[str, Any]]:
        raw = self.text("TASKS.json")
        data = json.loads(raw) if raw else []
        return data if isinstance(data, list) else []

    def state(self, key: str) -> str:
        m = re.search(rf"^{re.escape(key)}: *(\S+)", self.text("STATE.md"), re.MULTILINE)
        return m.group(1) if m else ""

    def toml(self, rel: str) -> dict[str, Any]:
        return tomllib.loads(self.text(rel)) if self.path(rel).is_file() else {}


# ---------------------------------------------------------------- shared helpers


def load_rules(repo: Repo) -> list[tuple[str, str, str]]:
    rules = []
    for raw in repo.text("tools/secret_patterns.txt").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            parts = line.split(None, 2)
            if len(parts) == 3:
                rules.append((parts[0], parts[1], parts[2]))
    return rules


def secret_named(path: str, rules: list[tuple[str, str, str]]) -> str | None:
    base = Path(path).name.lower()
    if any(k == "exempt" and fnmatch.fnmatchcase(base, p.lower()) for k, _, p in rules):
        return None
    return next((n for k, n, p in rules if k == "name" and fnmatch.fnmatchcase(base, p.lower())), None)


def _high_entropy(token: str, spec: str) -> bool:
    min_len, min_bits, min_switch = spec.split()
    classes = ["u" if c.isupper() else "l" if c.islower() else "d" for c in token if c.isalnum()]
    switches = sum(1 for a, b in itertools.pairwise(classes) if a != b)
    if switches / max(1, len(classes) - 1) < float(min_switch):
        return False
    if len(token) < int(min_len) or not (
        any(c.isupper() for c in token) and any(c.islower() for c in token) and any(c.isdigit() for c in token)
    ):
        return False
    bits = -sum(token.count(c) / len(token) * math.log2(token.count(c) / len(token)) for c in set(token))
    return bits >= float(min_bits)


def scan_lines(text: str, rules: list[tuple[str, str, str]], kinds: tuple[str, ...]) -> Iterator[tuple[int, str]]:
    compiled = [(n, re.compile(p)) for k, n, p in rules if k in kinds and k != "entropy"]
    entropy = [(n, p) for k, n, p in rules if k == "entropy" and "entropy" in kinds]
    token = re.compile(r"[A-Za-z0-9+/=_-]{16,}")
    for number, line in enumerate(text.splitlines(), start=1):
        for name, rx in compiled:
            if rx.search(line):
                yield number, name
        for name, spec in entropy:
            if any(_high_entropy(m.group(0), spec) for m in token.finditer(line)):
                yield number, name


def candidate_files(repo: Repo) -> list[str]:
    _, out = repo.git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted({p for p in out.split("\0") if p})


def open_incidents(repo: Repo) -> list[tuple[int, str, str]]:
    found = []
    for m in re.finditer(r"^## #(\d+) · (\S+)[^\n]*· (OPEN|CLOSED)\s*$", repo.text("INCIDENT.md"), re.MULTILINE):
        found.append((int(m.group(1)), m.group(2), m.group(3)))
    return found


def questions(repo: Repo) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    blocks = re.split(r"^(?=## )", repo.text("OWNER_QUESTIONS.md"), flags=re.MULTILINE)
    for block in blocks:
        m = re.match(r"## (F-[A-Z0-9-]+) \| code ([0-9a-f]{4}) \|", block)
        if not m:
            continue
        q = re.search(r"^SAWAL: (.*)$", block, re.MULTILINE)
        v = re.search(r"^PROPOSED: (.*)$", block, re.MULTILINE)
        out[m.group(1)] = {"code": m.group(2), "question": q.group(1) if q else "", "proposed": v.group(1) if v else ""}
    return out


def approvals(repo: Repo) -> list[dict[str, str]]:
    out = []
    for block in re.split(r"^(?=## A-)", repo.text("OWNER_APPROVALS.md"), flags=re.MULTILINE):
        m = re.match(
            r"## (A-\d{3}) \| session (\d+) \| received ([^|]+)\| question (F-[A-Z0-9-]+) \(code ([0-9a-f]{4})\)", block
        )
        if not m:
            continue
        cmd = re.search(r"^OWNER COMMAND \(verbatim line\): (.*)$", block, re.MULTILINE)
        out.append(
            {
                "id": m.group(1),
                "session": m.group(2),
                "qid": m.group(4),
                "code": m.group(5),
                "command": cmd.group(1).strip() if cmd else "",
                "block": block,
            }
        )
    return out


def last_seal(repo: Repo) -> dict[str, Any] | None:
    lines = [x for x in repo.text("EVIDENCE/seal_log.jsonl").splitlines() if x.strip()]
    return json.loads(lines[-1]) if lines else None


def seal_of(entries: list[dict[str, Any]]) -> str:
    canon = "\n".join(f"{e['path']}  {e['sha256']}" for e in sorted(entries, key=lambda e: str(e["path"])))
    return hashlib.sha256(canon.encode()).hexdigest()[:8]


def in_progress(repo: Repo) -> set[str]:
    return {str(t.get("id")) for t in repo.tasks() if t.get("status") == "IN_PROGRESS"}


# ---------------------------------------------------------------- checks


def check_1(repo: Repo) -> list[str]:
    scope = repo.toml("tools/tag_scope.toml")
    if not scope:
        return ["tools/tag_scope.toml missing"]
    nums = [re.compile(p) for p in scope["numbers"].values()]
    tag_re = re.compile(scope["tags"]["pattern"])
    ev_re = re.compile(scope["tags"]["evidence"])
    self_re = re.compile(scope["tags"]["self_linked"])
    problems = []
    for rel in scope["scope"]["files"]:
        lines = repo.text(rel).splitlines()
        start = int(scope["scope"]["report_top_lines"]) if rel == "REPORT.md" else 0
        heads = [i for i, x in enumerate(lines) if x.startswith("## ")] + [len(lines)]
        for i in range(start, len(lines)):
            line = lines[i]
            lo = max([h for h in heads if h <= i], default=0)
            hi = min(h for h in heads if h > i)
            section = "\n".join(lines[lo:hi])
            for rx in nums:
                for m in rx.finditer(line):
                    tail = line[m.end() :]
                    t = tag_re.search(tail)
                    if t is None:
                        problems.append(f"{rel}:{i + 1}: number without a tag")
                    elif not self_re.match(tail[t.start() :]) and not ev_re.search(section):
                        problems.append(f"{rel}:{i + 1}: tagged number without an evidence link in its section")
            for m in re.finditer(r"EVIDENCE/[A-Za-z0-9_./-]+", line):
                target = m.group(0).rstrip(".,)")
                if not repo.path(target).exists():
                    problems.append(f"{rel}:{i + 1}: evidence link does not exist: {target}")
    return problems


def _walk(obj: Any, key: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(obj, str):
        yield key, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{key}.{k}" if key else str(k))
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from _walk(v, f"{key}[{n}]")


def check_2(repo: Repo) -> list[str]:
    problems = []
    scope = repo.toml("tools/tag_scope.toml")
    id_re = re.compile(scope["ids"]["pattern"]) if scope else re.compile(r"$^")
    placeholder = re.compile(r"\{(?:num|numen):([A-Za-z0-9_.]+)\}")
    try:
        fields = json.loads(repo.text("report_fields.json") or "{}")
        numbers = json.loads(repo.text("EVIDENCE/numbers.json") or "{}")
    except json.JSONDecodeError as e:
        return [f"report_fields.json or EVIDENCE/numbers.json is not valid JSON ({e.msg})"]
    used = set()
    for key, value in _walk(fields):
        used.update(placeholder.findall(value))
        rest = id_re.sub("", placeholder.sub("", value))
        if re.search(r"[0-9]", rest):
            problems.append(f"report_fields.json: {key}: digit outside an ID token or a placeholder")
    for tpl in sorted(repo.path("report_templates").glob("*.md")):
        used.update(placeholder.findall(tpl.read_text(encoding="utf-8")))
    for key, entry in numbers.items():
        if not isinstance(entry, dict) or not {"value", "tag", "evidence"} <= set(entry):
            problems.append(f"numbers.json: {key}: needs value, tag and evidence")
            continue
        if not TAG_RE.match(str(entry["tag"])):
            problems.append(f"numbers.json: {key}: unknown tag")
        if not repo.path(str(entry["evidence"])).exists():
            problems.append(f"numbers.json: {key}: evidence file missing")
    problems += [f"placeholder {{num:{k}}} has no numbers.json entry" for k in sorted(used - set(numbers))]
    report = repo.text("REPORT.md")
    if len(report.splitlines()) < 15:
        problems.append("REPORT.md has fewer than 15 lines")
    if repo.path("tools/make_report.py").is_file():
        r = subprocess.run(  # noqa: S603
            [sys.executable, str(repo.path("tools/make_report.py")), "--stdout"],
            cwd=repo.root,
            capture_output=True,
            check=False,
        )
        fresh = r.stdout.decode("utf-8", "replace")

        def norm(s: str) -> str:
            return re.sub(r"\b[0-9]+ min chala\b", "N min chala", s)

        if r.returncode != 0:
            problems.append("tools/make_report.py --stdout failed")
        elif norm(fresh) != norm(report):
            problems.append("REPORT.md differs from a fresh render (hand edit or stale: run tools/make_report.py)")
    return problems


def _values(text: str) -> dict[str, Any]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    return {k: (v.get("value") if isinstance(v, dict) else v) for k, v in data.items()}


def _directions(text: str) -> dict[str, str]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    return {k: str(v.get("direction", "exact")) for k, v in data.items() if isinstance(v, dict)}


def check_3(repo: Repo) -> list[str]:
    problems: list[str] = []
    prot = repo.toml("PROTECTED.toml")
    entries = prot.get("file", [])
    seal = last_seal(repo)
    if not entries:
        return ["seal log has entries but PROTECTED.toml is empty"] if seal else []
    if seal is None:
        return ["PROTECTED.toml has entries but EVIDENCE/seal_log.jsonl is empty"]
    if prot.get("seal") != seal_of(entries) or prot.get("seal") != seal.get("new_seal"):
        problems.append("PROTECTED.toml seal does not match its entries or the seal log")
    if repo.sha("PROTECTED.toml") != seal.get("protected_toml_sha256"):
        problems.append("PROTECTED.toml changed outside tools/seal.py")
    busy = in_progress(repo)
    appr = approvals(repo)
    decisions = repo.text("DECISIONS.md")
    base = str(seal.get("commit", ""))
    for e in entries:
        rel, rule = str(e["path"]), str(e["rule"])
        if not repo.path(rel).is_file():
            problems.append(f"{rel}: protected file missing")
            continue
        if repo.sha(rel) == e["sha256"]:
            continue
        approved = any(rel in a["block"] for a in appr if a["qid"].startswith("F-PROT-"))
        owner_busy = bool(busy & set(e.get("owner_tasks", [])))
        rc, old = repo.git("show", f"{base}:{rel}")
        if rule == "exact" and not (owner_busy or approved):
            problems.append(f"{rel}: protected (exact) change without an owner approval")
        elif rule == "append_only":
            if rc != 0 or not repo.text(rel).startswith(old):
                problems.append(f"{rel}: append-only file had existing lines changed")
        elif rule == "per_value":
            new_v, old_v = _values(repo.text(rel)), _values(old)
            dirs = {**_directions(old), **_directions(repo.text(rel))}
            for key in sorted(set(old_v) | set(new_v)):
                a, b = old_v.get(key), new_v.get(key)
                if a == b:
                    continue
                d = dirs.get(key, "exact")
                tighter = (
                    (b is not None and a is None)
                    or (d == "lower_is_tighter" and _num(b) < _num(a))
                    or (d == "higher_is_tighter" and _num(b) > _num(a))
                )
                key_approved = any(key in x["block"] for x in appr)
                if tighter and key not in decisions:
                    problems.append(f"{rel}: {key} tightened without a DECISIONS entry")
                elif not tighter and not key_approved:
                    problems.append(f"{rel}: {key} loosened or changed without an owner approval")
    return problems


def _num(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def check_5(repo: Repo, record: bool) -> list[str]:
    problems = []
    ban = re.compile(
        r"pytest\.mark\.(skip|skipif|xfail)\b|pytest\.(skip|xfail|importorskip)\s*\(|unittest\.skip|@skip\b"
    )
    for p in sorted(repo.path("tests").rglob("*.py")):
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if ban.search(line):
                problems.append(f"{p.relative_to(repo.root)}:{n}: skip / xfail is banned")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=repo.root,
        capture_output=True,
        check=False,
    )
    collected = r.stdout.decode("utf-8", "replace")
    m = re.search(r"(\d+) tests? collected", collected)
    per_file = [int(x) for x in re.findall(r"^\S+\.py: (\d+)$", collected, re.MULTILINE)]
    if r.returncode != 0 or (m is None and not per_file):
        problems.append("pytest collection failed")
    else:
        count = int(m.group(1)) if m else sum(per_file)
        rec = repo.path("EVIDENCE/test_count.json")
        floor = int(json.loads(rec.read_text())["min"]) if rec.is_file() else 0
        if count < floor:
            problems.append(f"test count fell below the recorded minimum ({count} < {floor})")
        elif record and count > floor:
            rec.write_text(json.dumps({"min": count}) + "\n")
    seal = last_seal(repo)
    if repo.path("BASELINE_RED.txt").is_file():
        rc, old = repo.git("show", f"{seal.get('commit', '')}:BASELINE_RED.txt") if seal else (1, "")
        new_set = set(repo.text("BASELINE_RED.txt").split())
        if seal and (rc != 0 or not new_set <= set(old.split())):
            problems.append("BASELINE_RED.txt grew (it may only shrink)")
    return problems


def check_6(repo: Repo) -> list[str]:
    rules = load_rules(repo)
    problems = []
    for rel in candidate_files(repo):
        if (n := secret_named(rel, rules)) is not None:
            problems.append(f"{rel}: secret-named file (not opened): name/{n}")
            continue
        if repo.path(rel).is_file():
            problems += [f"{rel}:{ln}: content/{name}" for ln, name in scan_lines(repo.text(rel), rules, ("content",))]
    return problems


def check_7(repo: Repo) -> list[str]:
    text = repo.text("OWNER_TODO.md")
    if not text:
        return ["OWNER_TODO.md missing"]
    nums = [int(x) for x in re.findall(r"^(\d+)\. ", text, re.MULTILINE)]
    problems = []
    if not nums or nums != list(range(nums[0], nums[0] + len(nums))) or nums[0] not in (0, 1):
        problems.append("OWNER_TODO.md items are not ranked 0/1, 2, 3 …")
    stop = [n for n, kind, status in open_incidents(repo) if status == "OPEN" and kind in STOP_INCIDENTS]
    first = re.search(r"^0\. (.*)$", text, re.MULTILINE)
    if stop and (first is None or "INCIDENT" not in first.group(1)):
        problems.append("a STOP-THE-LINE incident is open but OWNER_TODO item 0 does not name it")
    return problems


def check_9(repo: Repo) -> list[str]:
    problems = []
    for t in repo.tasks():
        rel, want = str(t.get("verify", "")), str(t.get("verify_sha256", ""))
        exists = bool(rel) and repo.path(rel).is_file()
        if want and (not exists or repo.sha(rel) != want):
            problems.append(f"{t.get('id')}: verify script hash differs from TASKS.json")
        if t.get("status") == "PASS" and not want:
            problems.append(f"{t.get('id')}: PASS without a recorded verify_sha256")
        if t.get("status") == "PASS" and not t.get("evidence"):
            problems.append(f"{t.get('id')}: PASS without evidence")
    return problems


def check_11(repo: Repo) -> list[str]:
    problems, listed = [], set()
    for n, line in enumerate(repo.text("SHA256SUMS").splitlines(), start=1):
        m = re.match(r"^([0-9a-f]{64})  (.+)$", line)
        if not m:
            problems.append(f"SHA256SUMS:{n}: malformed line")
            continue
        listed.add(m.group(2))
        if not repo.path(m.group(2)).is_file() or repo.sha(m.group(2)) != m.group(1):
            problems.append(f"SHA256SUMS:{n}: {m.group(2)} missing or changed")
    for p in sorted(repo.path("docs/00_input").rglob("*")):
        rel = str(p.relative_to(repo.root))
        if p.is_file() and rel not in listed:
            problems.append(f"{rel}: input not listed in SHA256SUMS")
    return problems


def check_12(repo: Repo) -> list[str]:
    n = len(repo.text("STATE.md").splitlines())
    return [] if 0 < n <= 120 else [f"STATE.md has {n} lines (limit 120)"]


def check_14(repo: Repo) -> list[str]:
    t07 = next((t for t in repo.tasks() if t.get("id") == "T07"), {})
    if str(t07.get("status", "")).split("(")[0] not in TERMINAL:
        return []
    track = repo.state("TRACK")
    need = ["12", "8"] + (["4", "11", "13"] if track == "FULL" else [])
    cov = repo.text("tests/invariants/COVERAGE.md")
    problems = []
    for i in need:
        has_test = any(repo.path("tests/invariants").glob(f"test_i{int(i):02d}_*.py"))
        if not has_test and not re.search(rf"^\| I{i} \| N/A\(", cov, re.MULTILINE):
            problems.append(f"I{i}: no tests/invariants/test_i{int(i):02d}_*.py and no N/A row")
    return problems


def check_15(repo: Repo) -> list[str]:
    rules = load_rules(repo)
    problems = []
    for p in sorted(repo.path("EVIDENCE").rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(repo.root))
            text = p.read_bytes().decode("utf-8", "replace")
            problems += [f"{rel}:{ln}: {name}" for ln, name in scan_lines(text, rules, ("content", "pii", "entropy"))]
    return problems


def check_17(repo: Repo) -> list[str]:
    problems = []
    qs = questions(repo)
    for qid, q in qs.items():
        code = hashlib.sha256(f"{qid}|{q['question']}|{q['proposed']}".encode()).hexdigest()[:4]
        if not q["question"] or not q["proposed"] or code != q["code"]:
            problems.append(f"OWNER_QUESTIONS.md: {qid}: code does not match its SAWAL and PROPOSED lines")
    session = repo.state("SESSION_N")
    report_13 = (repo.text("REPORT.md").splitlines() + [""] * 15)[12]
    approved_inc = set()
    for a in approvals(repo):
        asked = qs.get(a["qid"])
        m = COMMAND.match(a["command"])
        cmd_id = (m.group("id1") or m.group("id2")) if m else ""
        cmd_code = (m.group("c1") or m.group("c2")) if m else ""
        if asked is None or asked["code"] != a["code"]:
            problems.append(f"OWNER_APPROVALS.md: {a['id']}: no OWNER_QUESTIONS id with that code")
        elif m is None or cmd_id.upper() != a["qid"].upper() or cmd_code != a["code"]:
            problems.append(f"OWNER_APPROVALS.md: {a['id']}: the verbatim command line does not match id and code")
        elif a["session"] == session and a["id"] not in report_13:
            problems.append(f"OWNER_APPROVALS.md: {a['id']}: approval of this session missing on REPORT line 13")
        if m and (m.group("yn") or "").lower() in ("haan", "ha", "haa", "han", "yes") and a["qid"].startswith("F-INC-"):
            approved_inc.add(a["qid"][len("F-INC-") :])
    for n, _, status in open_incidents(repo):
        if status == "CLOSED" and str(n) not in approved_inc:
            problems.append(f"INCIDENT.md: #{n} marked CLOSED without `haan F-INC-{n} <code>`")
    return problems


def check_18(repo: Repo) -> list[str]:
    problems = []
    rows = repo.toml("constants.toml")
    for name, row in rows.items():
        if not isinstance(row, dict):
            continue
        if row.get("status") not in ("VERIFIED", "UNVERIFIED", "NA"):
            problems.append(f"constants.toml: {name}: status must be VERIFIED, UNVERIFIED or NA")
        if row.get("tag") != "SOURCE":
            continue
        missing = [k for k in ("value", "unit", "source_url", "fetched", "ttl_days", "extract") if k not in row]
        if missing:
            problems.append(f"constants.toml: {name}: SOURCE row lacks {', '.join(missing)}")
            continue
        extract = repo.text(str(row["extract"]))
        forms = [str(row["value"]), *[str(x) for x in row.get("value_forms", [])]]
        if not extract:
            problems.append(f"constants.toml: {name}: extract file missing")
        elif not any(f in extract for f in forms):
            problems.append(f"constants.toml: {name}: value not found in its evidence extract")
    return problems


def check_19(repo: Repo) -> list[str]:
    gate = "CLOSED"
    if repo.path("tools/fullb_gate.py").is_file():
        r = subprocess.run(  # noqa: S603
            [sys.executable, str(repo.path("tools/fullb_gate.py"))], cwd=repo.root, capture_output=True, check=False
        )
        gate = "OPEN" if re.search(r"\bOPEN\b", r.stdout.decode("utf-8", "replace")) else "CLOSED"
    problems = []
    for t in repo.tasks():
        status = str(t.get("status", ""))
        if (
            t.get("track") == "FULL-B"
            and gate != "OPEN"
            and status.split("(", maxsplit=1)[0] in ("IN_PROGRESS", "PASS")
        ):
            problems.append(f"{t.get('id')}: FULL-B task is {status} while the FULL-B gate is CLOSED")
        if status.startswith("SKIPPED_BY_GATE"):
            ev = [str(x) for x in t.get("evidence", [])]
            if "(" not in status or not ev or not all(repo.path(x).exists() for x in ev):
                problems.append(f"{t.get('id')}: SKIPPED_BY_GATE without its reason and gate evidence")
    return problems


# ---------------------------------------------------------------- FULL checks (T02b)

CLASS_CD = [
    ("D1 martingale / double-down", r"(?i)martingale|double[_ ]?down|doubling[_ ]?down"),
    ("D2 averaging into a loser", r"(?i)average[_ ]?down|averag(e|ing)[_ ]?(into|on)[_ ]?(a[_ ]?)?los"),
    ("D3 stop moved away or removed", r"(?i)(remove|widen|loosen)[_ ]?(the[_ ]?)?stop"),
    ("D6 revenge trade", r"(?i)revenge"),
    ("D7 refill / top-up", r"(?i)\brefill|\btop[_ -]?up"),
    ("D8 raise a limit to continue", r"(?i)(raise|increase|bump)[_ ]?(the[_ ]?)?(loss[_ ]?)?limit"),
    ("D9 bet bigger", r"(?i)bet[_ ]?bigger|(size|lots?|qty)\s*\*=\s*[2-9]"),
    (
        "C spoof / layering / wash / ramp / insider",
        r"(?i)spoof|layering|wash[_ ]?trade|circular[_ ]?trade|\bramping\b|insider|front[_ ]?run",
    ),
]
ORDER_API = re.compile(
    r"(?i)/v[23]/order/|/order/(place|modify|cancel|multi)|/positions/exit|/v[23]/gtt|place_order|modify_order"
    r"|cancel_order|exit_all_positions|\bOrderApi(V3)?\b|\bGTTApi\b"
)
BROKER_NAME = re.compile(r"(?i)upstox|api-hft")


def check_4(repo: Repo) -> list[str]:
    problems = []
    compiled = [(n, re.compile(p)) for n, p in CLASS_CD]
    for rel in candidate_files(repo):
        if not rel.startswith(("src/", "tools/", "pehredaar/")) or rel == "tools/mission_check.py":
            continue
        if not rel.endswith((".py", ".go", ".sh", ".toml")) or not repo.path(rel).is_file():
            continue
        for n, line in enumerate(repo.text(rel).splitlines(), start=1):
            if "classcd-ok:" in line:
                continue
            problems += [f"{rel}:{n}: {name}" for name, rx in compiled if rx.search(line)]
    return problems


def _sites(tree: ast.AST) -> Iterator[tuple[str, int, str]]:
    """(enclosing function, line, text) for every string, name, attribute and import in the tree."""

    def visit(node: ast.AST, func: str) -> Iterator[tuple[str, int, str]]:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            func = node.name
        text = ""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
        elif isinstance(node, ast.Attribute):
            text = node.attr
        elif isinstance(node, ast.Name):
            text = node.id
        elif isinstance(node, ast.Import | ast.ImportFrom):
            text = " ".join(a.name for a in node.names) + " " + str(getattr(node, "module", "") or "")
        if text:
            yield func, int(getattr(node, "lineno", 0)), text
        for child in ast.iter_child_nodes(node):
            yield from visit(child, func)

    yield from visit(tree, "")


def check_8(repo: Repo) -> list[str]:
    sites = repo.toml("tools/callsite_allowlist.toml").get("site", [])
    allowed = {(str(x.get("file")), str(x.get("function"))) for x in sites}
    problems = [] if len(allowed) <= 3 else ["tools/callsite_allowlist.toml lists more than three sites"]
    for rel in candidate_files(repo):
        if not repo.path(rel).is_file():
            continue
        if rel.startswith("src/") and rel.endswith(".py"):
            try:
                tree = ast.parse(repo.text(rel))
            except SyntaxError:
                problems.append(f"{rel}: does not parse")
                continue
            for func, line, text in _sites(tree):
                if ORDER_API.search(text) and (rel, func) not in allowed:
                    problems.append(f"{rel}:{line}: broker order API outside the allowlist ({func or 'module level'})")
            for n, raw in enumerate(repo.text(rel).splitlines(), start=1):
                if re.search(r"\bLIVE[A-Z_]*\s*(:\s*[A-Za-z_]+\s*)?=\s*True\b", raw):
                    problems.append(f"{rel}:{n}: a live flag defaults to True")
        elif rel.startswith("pehredaar/") and rel.endswith(".go"):
            for n, raw in enumerate(repo.text(rel).splitlines(), start=1):
                if BROKER_NAME.search(raw) or ORDER_API.search(raw):
                    problems.append(f"{rel}:{n}: Go code names the broker (the watchdog may only call reduce_only)")
    if 'os.environ.get("BOT_MODE", "paper")' not in repo.text("src/bot/__main__.py"):
        problems.append("src/bot/__main__.py: the mode switch does not default to paper (live flag OFF)")
    return problems


def check_10(repo: Repo) -> list[str]:
    rules = load_rules(repo)
    entries = repo.toml("tools/scan_allowlist.toml").get("entry", [])
    problems = [
        f"tools/scan_allowlist.toml: entry {n} has no reason" for n, e in enumerate(entries) if not e.get("reason")
    ]
    for rel in candidate_files(repo):
        if rel.startswith("EVIDENCE/") or secret_named(rel, rules) is not None or not repo.path(rel).is_file():
            continue
        for ln, name in scan_lines(repo.text(rel), rules, ("pii",)):
            ok = any(e.get("path") == rel and e.get("pattern") == f"pii/{name}" for e in entries)
            if not ok:
                problems.append(f"{rel}:{ln}: pii/{name}")
    return problems


def check_13(repo: Repo) -> list[str]:
    prev, problems = "0" * 64, []
    for n, line in enumerate([x for x in repo.text("trials.jsonl").splitlines() if x.strip()], start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return [f"trials.jsonl:{n}: not JSON"]
        if row.get("prev_hash") != prev:
            problems.append(f"trials.jsonl:{n}: prev_hash breaks the chain (a hidden or edited trial)")
        prev = hashlib.sha256(line.encode()).hexdigest()
    return problems


def check_16(repo: Repo) -> list[str]:
    folder = repo.path("tests/adversary")
    if not folder.is_dir():
        return []
    manifest = repo.text("tests/adversary/MANIFEST.sha256")
    if not manifest:
        return ["tests/adversary exists without MANIFEST.sha256"]
    listed: dict[str, str] = {
        m.group(2): m.group(1) for m in re.finditer(r"^([0-9a-f]{64})  (\S+)$", manifest, re.MULTILINE)
    }
    problems = []
    for p in sorted(folder.rglob("*")):
        rel = str(p.relative_to(repo.root))
        if p.is_file() and p.name != "MANIFEST.sha256" and "__pycache__" not in rel:
            if rel not in listed:
                problems.append(f"{rel}: not in MANIFEST.sha256")
            elif repo.sha(rel) != listed[rel]:
                problems.append(f"{rel}: changed since the adversary wrote it")
    report = repo.text("tests/adversary/ADVERSARY_REPORT.md")
    if report:
        problems += [
            f"{rel}: hash missing from the adversary's own report" for rel, h in listed.items() if h not in report
        ]
    return problems


def check_6_history(repo: Repo) -> list[str]:
    rules = load_rules(repo)
    entries = repo.toml("tools/scan_allowlist.toml").get("entry", [])
    content = [(n, re.compile(p)) for k, n, p in rules if k == "content"]
    rc, out = repo.git("log", "--no-color", "-p", "--format=commit %H", "HEAD")
    if rc != 0:
        return ["git log failed"]
    problems: set[str] = set()
    commit, path = "", ""
    for line in out.splitlines():
        if line.startswith("commit "):
            commit = line[7:47]
        elif line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
            if path and secret_named(path, rules) is not None:
                problems.add(f"{commit[:12]}: {path}: secret-named file in history (not opened)")
        elif line.startswith("+") and path:
            for name, rx in content:
                if rx.search(line[1:]):
                    ok = any(
                        e.get("kind") == "history"
                        and e.get("commit") == commit
                        and e.get("path") == path
                        and e.get("pattern") == f"content/{name}"
                        for e in entries
                    )
                    if not ok:
                        problems.add(f"{commit[:12]}: {path}: content/{name}")
    return sorted(problems)


def tier2(repo: Repo) -> list[str]:
    problems = []
    today = dt.datetime.now(dt.UTC).date()
    for name, row in repo.toml("constants.toml").items():
        if isinstance(row, dict) and row.get("fetched") and row.get("ttl_days") is not None:
            fetched = dt.date.fromisoformat(str(row["fetched"])[:10])
            if fetched + dt.timedelta(days=int(row["ttl_days"])) < today:
                problems.append(f"constants.toml: {name}: stale (TTL passed): refresh before a gate uses it")
    opens = [x for x in repo.text("holdout_log.jsonl").splitlines() if '"open"' in x]
    if len(opens) > 1:
        problems.append("holdout opened more than once")
    numbers = json.loads(repo.text("EVIDENCE/numbers.json") or "{}")
    for key, entry in numbers.items():
        if isinstance(entry, dict) and entry.get("gate_input") and not GATE_ELIGIBLE.match(str(entry.get("tag"))):
            problems.append(f"numbers.json: {key}: gate input with a tag that is not gate-eligible")
    return problems


def ttl_warnings(repo: Repo) -> list[str]:
    return [p for p in tier2(repo) if "stale" in p]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1]).resolve()
    repo = Repo(root)
    record = "--record-tests" in argv
    history = "--history" in argv
    checks: list[tuple[str, str, Callable[[], list[str]]]] = [
        ("1", "numbers tagged + linked", lambda: check_1(repo)),
        ("2", "REPORT from numbers.json + templates", lambda: check_2(repo)),
        ("3", "protected files vs seal", lambda: check_3(repo)),
        ("4", "Class C/D static lint", lambda: check_4(repo)),
        ("5", "tests: count, no skip, baseline", lambda: check_5(repo, record)),
        ("6", "secrets scan (tree)", lambda: check_6(repo)),
        ("7", "OWNER_TODO ranked", lambda: check_7(repo)),
        ("8", "order call sites + live flag OFF", lambda: check_8(repo)),
        ("9", "verify-script hashes", lambda: check_9(repo)),
        ("10", "PII scan", lambda: check_10(repo)),
        ("11", "docs/00_input vs SHA256SUMS", lambda: check_11(repo)),
        ("12", "STATE.md <= 120 lines", lambda: check_12(repo)),
        ("13", "trials.jsonl hash chain", lambda: check_13(repo)),
        ("14", "invariant coverage", lambda: check_14(repo)),
        ("15", "EVIDENCE has no secret", lambda: check_15(repo)),
        ("16", "adversary manifest", lambda: check_16(repo)),
        ("17", "approvals", lambda: check_17(repo)),
        ("18", "constants vs extracts", lambda: check_18(repo)),
        ("19", "track gates", lambda: check_19(repo)),
    ]
    if history:
        checks.insert(6, ("6h", "secrets scan (git history)", lambda: check_6_history(repo)))
    if "--final" in argv:
        checks.append(("T2", "tier 2: TTL, holdout, gate inputs", lambda: tier2(repo)))
    red = []
    for num, name, fn in checks:
        try:
            problems = fn()
        except Exception as e:  # a crashing check is a red check
            problems = [f"check crashed: {type(e).__name__}"]
        print(f"#{num} {name}: " + ("OK" if not problems else f"RED ({len(problems)})"))
        for p in problems[:20]:
            print(f"    {p}")
        if problems:
            red.append(f"#{num}")
    if "--final" not in argv:
        for w in ttl_warnings(repo):
            print(f"    warning: {w}")
    print("mission_check: " + ("GREEN" if not red else "RED " + " ".join(red)))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
