#!/usr/bin/env python3
"""REPORT.md, memos and chat cards (MISSION V11 §5.3, §14, §15).

  make_report.py                   write REPORT.md
  make_report.py --stdout          print the REPORT render (used by mission_check #2)
  make_report.py --chat            print the 5-line chat card (each line at most 70 characters)
  make_report.py --memo CP1        write docs/MEMO_CP1.md (also CP2)
  make_report.py --recorder-card   print the 3-line Recorder card (T09)

Text comes only from report_templates/*.md and report_fields.json; numbers only from
EVIDENCE/numbers.json: {num:KEY} renders a value with its Hinglish tag label, {numen:KEY} with the
English tag. {field:KEY} is a free-text field, {auto:NAME} a block computed from the tracking files,
{include:PATH} a file written by a script (or a fixed "not computed yet" line).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TERMINAL = ("PASS", "BLOCKED", "SKIPPED_BY_GATE")
LABEL = {
    "SOURCE": "official source",
    "REAL": "asli data",
    "BACKTEST": "purane asli data par nakli fill",
    "SHADOW": "asli feed, nakli fill",
    "SIM": "nakli (sirf test)",
    "HISTORY": "purani baat",
    "POINTER": "sirf ishara",
    "ESTIMATE": "andaza",
    "ASSUMPTION": "maanyata",
    "OWNER": "tumhara niyam",
}
VERDICT = {
    "GO_PAPER": "PAPER PAR CHALAO (asli paisa nahi)",
    "NOT_YET": "ABHI NAHI",
    "STOP": "RUKO: is plan mein raasta nahi",
}
REASON = {
    "NO_DATA": "data kam",
    "UNDERPOWERED": "data hai, par saboot ke liye kam",
    "G0_CONDITIONAL": "kharche / niyam ka hisaab adhoora",
    "DATA_RIGHTS_OPEN": "data rakhne ki ijazat saaf nahi",
    "MISSING_INPUT": "tumhari file ya jawab chahiye",
    "OPEN_FINDINGS": "jaanch mein galti mili, theek nahi hui",
    "NOT_REVIEWED": "alag jaanch nahi hui",
    "BLOCKED_INPUT": "ek zaroori kaam atka hai",
    "G0_FAIL_ARITH": "₹15,000 mein hisaab hi nahi baithta",
    "G0_FAIL_CREDIBILITY": "itna munafa chahiye jitna lagbhag koi nahi kamata",
    "DATA_KILL": "asli data ne har idea gira diya",
}
STOP_INCIDENTS = ("secret", "sandbox_breach", "live_process", "class_c", "seal_mismatch")
SET_IDS = ("F-MAXLOSS", "F-S118", "F-S16", "F-DATAAGE", "F-H2PCT")


def text(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def load_json(rel: str, default: Any) -> Any:
    raw = text(rel)
    return json.loads(raw) if raw.strip() else default


def state(key: str) -> str:
    m = re.search(rf"^{re.escape(key)}: *(\S+)", text("STATE.md"), re.MULTILINE)
    return m.group(1) if m else ""


def indian(n: float) -> str:
    neg, n = n < 0, abs(n)
    whole = round(n) if abs(n - round(n)) < 0.005 else int(n)
    frac = "" if abs(n - round(n)) < 0.005 else f"{n:.2f}"[-3:]
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups: list[str] = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        s = ",".join([head, *groups, tail]) if head else ",".join([*groups, tail])
    return ("-" if neg else "") + s + frac


def fmt_value(entry: dict[str, Any]) -> str:
    v, unit = entry["value"], str(entry.get("unit", ""))
    if isinstance(v, bool) or not isinstance(v, int | float):
        return str(v)
    if unit == "INR":
        return "₹" + indian(v)
    if unit == "INR/month":
        return "₹" + indian(v) + "/mahina"
    if unit == "pct":
        return f"{v:.2f}".rstrip("0").rstrip(".") + "%"
    if unit == "count":
        return str(int(v))
    return f"{v:g} {unit}".strip()


def hinglish(tag: str) -> str:
    m = re.match(r"^CODE\(([A-Z]+)(·stressed)?\)$", tag)
    if m:
        return f"ginti ({LABEL.get(m.group(1), m.group(1))} par{', stress ke saath' if m.group(2) else ''})"
    return LABEL.get(tag, tag)


class Ctx:
    def __init__(self) -> None:
        self.fields: dict[str, Any] = load_json("report_fields.json", {})
        self.numbers: dict[str, Any] = load_json("EVIDENCE/numbers.json", {})
        self.tasks: list[dict[str, Any]] = load_json("TASKS.json", [])
        self.questions = self._questions()
        self.approvals = self._approvals()

    def _questions(self) -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        for block in re.split(r"^(?=## )", text("OWNER_QUESTIONS.md"), flags=re.MULTILINE):
            m = re.match(r"## (F-[A-Z0-9-]+) \| code ([0-9a-f]{4}) \|", block)
            if not m:
                continue
            q: dict[str, str] = {"code": m.group(2)}
            for line in block.splitlines()[1:]:
                k, sep, v = line.partition(": ")
                if sep:
                    q[k.removeprefix("UPDATE ")] = v
            out[m.group(1)] = q
        for block in re.split(r"^(?=## )", text("OWNER_QUESTIONS.md"), flags=re.MULTILINE):
            u = re.match(r"## UPDATE (F-[A-Z0-9-]+) \|", block)
            if u and u.group(1) in out:
                for line in block.splitlines()[1:]:
                    k, sep, v = line.partition(": ")
                    if sep:
                        out[u.group(1)][k] = v
        return out

    def _approvals(self) -> list[dict[str, str]]:
        out = []
        for block in re.split(r"^(?=## A-)", text("OWNER_APPROVALS.md"), flags=re.MULTILINE):
            m = re.match(r"## (A-\d{3}) \| session (\d+) \|[^|]*\| question (F-[A-Z0-9-]+)", block)
            cmd = re.search(r"^OWNER COMMAND \(verbatim line\): (.*)$", block, re.MULTILINE)
            if m:
                out.append(
                    {"id": m.group(1), "session": m.group(2), "qid": m.group(3), "cmd": cmd.group(1) if cmd else ""}
                )
        return out

    def answered(self) -> set[str]:
        return {a["qid"] for a in self.approvals}

    def open_questions(self) -> list[str]:
        return [q for q in self.questions if q not in self.answered()]

    def incidents(self) -> list[tuple[int, str, str]]:
        pat = r"^## #(\d+) · (\S+)[^\n]*· (OPEN|CLOSED)\s*$"
        return [(int(a), b, c) for a, b, c in re.findall(pat, text("INCIDENT.md"), re.MULTILINE)]

    # -------------------------------------------------------------- placeholders

    def num(self, key: str, english: bool) -> str:
        e = self.numbers[key]
        tag = str(e["tag"])
        return f"{fmt_value(e)} [{tag if english else hinglish(tag)}]"

    def field(self, key: str) -> str:
        v: Any = self.fields
        for part in key.split("."):
            v = v.get(part, "") if isinstance(v, dict) else ""
        if isinstance(v, list):
            v = "\n".join(f"- {x}" for x in v)
        return self.sub(str(v)) if v else "(abhi kuch nahi)"

    def sub(self, s: str) -> str:
        s = re.sub(r"\{num:([A-Za-z0-9_.]+)\}", lambda m: self.num(m.group(1), False), s)
        s = re.sub(r"\{numen:([A-Za-z0-9_.]+)\}", lambda m: self.num(m.group(1), True), s)
        return s

    def seal(self) -> str:
        m = re.search(r'^seal = "([0-9a-f]{8})"', text("PROTECTED.toml"), re.MULTILINE)
        return m.group(1) if m else ""

    def trials_head(self) -> str:
        lines = [x for x in text("trials.jsonl").splitlines() if x.strip()]
        return hashlib.sha256(lines[-1].encode()).hexdigest()[:8] if lines else ""

    def kind(self) -> str:
        done = all(str(t.get("status", "")).split("(")[0] in TERMINAL for t in self.tasks)
        return "FINAL" if self.tasks and done else "INTERIM"

    def verdict(self) -> tuple[str, list[str]]:
        """NOT_YET is the default until the T10 decision rule exists; reason codes come from the files."""
        reasons = ["NO_DATA"]  # no REAL market data in the repo yet
        g0 = load_json("EVIDENCE/T04/g0.json", {})
        if g0.get("g0") == "CONDITIONAL":
            reasons.append("G0_CONDITIONAL")
        rights = tomllib.loads(text("constants.toml")).get("data_rights", {}) if text("constants.toml") else {}
        if rights.get("value") != "OK":
            reasons.append("DATA_RIGHTS_OPEN")
        reasons += [str(r) for r in self.fields.get("extra_reasons", []) if str(r) not in reasons]
        return str(self.fields.get("verdict", "NOT_YET")), reasons

    def auto(self, name: str) -> str:
        fn = getattr(self, "a_" + name, None)
        if fn is not None:
            return str(fn())
        m = re.match(r"sawal_(\d)$", name)
        if m:
            return self.sawal(int(m.group(1)))
        raise KeyError(name)

    def a_line1(self) -> str:
        open_inc = [(n, k) for n, k, s in self.incidents() if s == "OPEN"]
        prefix = ""
        if open_inc:
            first = next((n for n, k in open_inc if k in STOP_INCIDENTS), open_inc[0][0])
            more = f" (kul {len(open_inc)} khule)" if len(open_inc) > 1 else ""
            prefix = f"DHYAN: INCIDENT #{first} khula hai{more} · "
        v, reasons = self.verdict()
        why = "; ".join(REASON.get(r, r) for r in reasons)
        return f"{prefix}FAISLA: {VERDICT.get(v, v)} ({why}) · {self.kind()}"

    def sawal(self, i: int) -> str:
        rank = [q for q in self.fields.get("sawal_rank", []) if q in self.open_questions()]
        rank += [q for q in self.open_questions() if q not in rank]
        if i > len(rank):
            return "SAWAL: (aur koi khula sawal nahi)"
        qid = rank[i - 1]
        code = self.questions[qid]["code"]
        info = self.fields.get("sawal", {}).get(qid, {})
        default = self.sub(str(info.get("default", "OWNER_QUESTIONS.md dekho")))
        asar = self.sub(str(info.get("asar", "OWNER_QUESTIONS.md dekho")))
        answer = f"haan / na{' / set' if qid in SET_IDS else ''} {qid}{' <value>' if qid in SET_IDS else ''} {code}"
        return f"SAWAL {qid} (code {code}): default {default} | ₹ asar {asar} | jawab: {answer}"

    def a_manzoori(self) -> str:
        mine = [a for a in self.approvals if a["session"] == state("SESSION_N")]
        return " | ".join(f"{a['id']} {a['qid']} ({a['cmd']})" for a in mine) or "koi nahi"

    def a_bharosa(self) -> str:
        r1 = next((t for t in self.tasks if t.get("id") == "T17-R1"), {})
        review = "hui" if r1.get("status") == "PASS" else "nahi hui"
        return (
            f"alag jaanch: {review} | khuli badi galtiyan: {self.fields.get('badi_galtiyan', 'koi nahi')} | "
            f"kya verify NAHI hua: {self.field('verify_nahi')} | final check laal: {self.field('check_laal')}"
        )

    def a_samay(self) -> str:
        start = state("SESSION_START")
        minutes = (int(time.time()) - int(start)) // 60 if start.isdigit() else 0
        left_tasks = sum(1 for t in self.tasks if str(t.get("status", "")).split("(")[0] not in TERMINAL)
        return (
            f"session {state('SESSION_N')} · {minutes} min chala · baad mein: {self.field('baad_mein')} · "
            f"SEAL: {self.seal() or 'abhi nahi'} · TRIALS: {self.trials_head() or 'khaali'} · "
            f"push: {self.a_push()} · baaki: {left_tasks} kaam, {len(self.open_questions())} sawal (OWNER_TODO.md)"
        )

    def a_push(self) -> str:
        return str(self.fields.get("push", "local only"))

    def a_kind(self) -> str:
        return self.kind()

    def a_verdict_code(self) -> str:
        v, reasons = self.verdict()
        return f"{v}({', '.join(reasons)})"

    def a_tasks_table(self) -> str:
        rows = ["| id | track | status | minutes_used / timebox | evidence files |", "|---|---|---|---|---|"]
        for t in self.tasks:
            rows.append(
                f"| {t['id']} | {t['track']} | {t['status']} | {t['minutes_used']} / {t['timebox_min']} | "
                f"{len(t.get('evidence', []))} |"
            )
        return "\n".join(rows)

    def a_incidents(self) -> str:
        rows = []
        for n, k, s in self.incidents():
            if s == "OPEN":
                q = self.questions.get(f"F-INC-{n}", {})
                rows.append(f"- #{n} · {k} · OPEN · closes with `haan F-INC-{n} {q.get('code', '????')}` (INCIDENT.md)")
        return "\n".join(rows) or "none"

    def a_numbers_table(self) -> str:
        if not self.numbers:
            return "(no numbers yet)"
        rows = ["| key | value [tag] | evidence |", "|---|---|---|"]
        rows += [f"| {k} | {self.num(k, True)} | {e['evidence']} |" for k, e in sorted(self.numbers.items())]
        return "\n".join(rows)

    def a_protected_changes(self) -> str:
        raw = text("PROTECTED.toml")
        entries = tomllib.loads(raw).get("file", []) if raw else []
        changed = []
        for e in entries:
            p = ROOT / str(e["path"])
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != e["sha256"]:
                changed.append(f"- {e['path']} (rule {e['rule']})")
        if not entries:
            return "no seal yet"
        return "\n".join(changed) or "none"

    def a_env_allowlist(self) -> str:
        names = [ln.split("#", 1)[0].strip() for ln in text("tools/env_allowlist.txt").splitlines()]
        return ", ".join(n for n in names if n) or "none"

    def a_scan_allowlist_count(self) -> str:
        raw = text("tools/scan_allowlist.toml")
        if not raw:
            return "0 (file arrives with T02b)"
        return str(len(tomllib.loads(raw).get("entry", [])))

    def a_session(self) -> str:
        return state("SESSION_N")

    def a_memo_id(self) -> str:
        return self.memo_id

    memo_id = "CP1"

    def a_memo_questions(self) -> str:
        rank = [q for q in self.fields.get("memo_rank", []) if q in self.open_questions()]
        rank += [q for q in self.open_questions() if q not in rank]
        blocks = []
        for qid in rank:
            q = self.questions[qid]
            blocks.append(
                "\n".join(
                    [
                        f"SAWAL {qid} (code {q['code']}): {q.get('SAWAL', '')}",
                        f"  DEFAULT JO MAINE LIYA: {q.get('DEFAULT JO MAINE LIYA', '')}",
                        f"  ₹ ASAR: {q.get('₹ ASAR', '')}",
                        f"  WAJAH: {q.get('WAJAH', '')}",
                        f"  ULTA KAISE KAREIN: {q.get('ULTA KAISE KAREIN', '')}",
                        f"  JAWAB: {q.get('JAWAB', '')}",
                    ]
                )
            )
        return "\n\n".join(blocks) or "(koi khula sawal nahi)"


def render(template: str, ctx: Ctx) -> str:
    def repl(m: re.Match[str]) -> str:
        kind, key = m.group(1), m.group(2)
        if kind == "field":
            return ctx.field(key)
        if kind == "auto":
            return ctx.auto(key)
        if kind == "include":
            body = text(key).rstrip("\n")
            return body or "(not computed yet)"
        return ctx.num(key, kind == "numen")

    return re.sub(r"\{(field|auto|include|num|numen):([^}]+)\}", repl, template)


def chat(ctx: Ctx) -> str:
    done = [str(t["id"]) for t in ctx.tasks if str(t.get("status")) == "PASS"]
    blocked = [str(t["id"]) for t in ctx.tasks if str(t.get("status", "")).startswith("BLOCKED")]
    v, _ = ctx.verdict()
    manz = ctx.a_manzoori()
    n_manz = 0 if manz == "koi nahi" else len(manz.split(" | "))
    lines = [
        "DONE: " + (" ".join(done) or "abhi kuch nahi"),
        "NEXT: " + ("FINAL" if ctx.kind() == "FINAL" else "likho: continue"),
        "BLOCKED: " + (" ".join(blocked) or "koi nahi"),
        "OWNER: " + " · ".join(str(x) for x in ctx.fields.get("owner_top3", [])),
        f"FAISLA: {VERDICT.get(v, v)} · SEAL {ctx.seal() or 'abhi nahi'} · manzoori {n_manz}",
    ]
    return "\n".join(x[:70] for x in lines)


def main(argv: list[str]) -> int:
    ctx = Ctx()
    if argv[:1] == ["--chat"]:
        print(chat(ctx))
        return 0
    if argv[:1] == ["--recorder-card"]:
        print(render(text("report_templates/recorder_card.md"), ctx).rstrip("\n"))
        return 0
    if argv[:1] == ["--memo"] and len(argv) == 2 and argv[1] in ("CP1", "CP2"):
        ctx.memo_id = argv[1]
        out = render(text("report_templates/memo.md"), ctx)
        (ROOT / "docs").mkdir(exist_ok=True)
        (ROOT / f"docs/MEMO_{argv[1]}.md").write_text(out, encoding="utf-8")
        print(f"wrote docs/MEMO_{argv[1]}.md")
        return 0
    out = render(text("report_templates/report.md"), ctx)
    if argv[:1] == ["--stdout"]:
        sys.stdout.write(out)
        return 0
    if argv:
        print(__doc__, file=sys.stderr)
        return 64
    (ROOT / "REPORT.md").write_text(out, encoding="utf-8")
    print("wrote REPORT.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
