#!/usr/bin/env python3
"""Idea file ki "Numbers ki list" se config/niyam.toml banata hai.

Use (idea file `idea` branch par hai):
    git show idea:docs/01_Bot_Idea_v4.md > /tmp/idea.md
    python tools/niyam_from_idea.py /tmp/idea.md config/niyam.toml

Niyam:
- Har kimat ka asli text `kimat` mein waisa hi rehta hai (malik ka likha kabhi nahi badalta).
- Typed `value`/`range`/`time_ist` sirf tab bharta hai jab text mein saaf ek number + jaana-pehchana unit ho.
- "Tay nahi" status par kabhi koi typed value nahi. Code ko guess nahi karna hai.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ALLOWED_STATUS = ("Pakka", "Andaza", "Prastaavit", "Tay nahi")

UNITS: dict[str, str] = {
    "milliseconds": "ms",
    "second": "s",
    "minute": "min",
    "percent": "pct",
    "points": "points",
    "guna": "x",
    "trading din": "trading_din",
    "din": "din",
    "saal": "saal",
    "dhadkan lagatar": "dhadkan",
    "koshish": "koshish",
    "signal": "signal",
    "trade": "trade",
    "rupaye": "inr",
}
_UNIT_ALT = "|".join(sorted((re.escape(u) for u in UNITS), key=len, reverse=True))
_NUM = r"\d+(?:,\d{3})*(?:\.\d+)?"
_SINGLE = re.compile(rf"^(?:Har |Kam se kam )?(?P<n>{_NUM}) (?P<u>{_UNIT_ALT})(?![A-Za-z])")
_RANGE = re.compile(rf"^(?P<a>{_NUM}) se (?P<b>{_NUM})(?: (?P<u>{_UNIT_ALT})(?![A-Za-z]))?")
_TIME = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2}) (?P<ap>AM|PM)\b")
_CC = "`[PRASTAAVIT-CC]`"


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def parse_kimat(name: str, kimat: str, status: str) -> dict[str, object]:
    """Text se typed field nikaalo. Kuch saaf na ho toh khaali dict."""
    if status == "Tay nahi":
        return {}
    text = kimat.strip()
    m = _TIME.match(text)
    if m and " se " not in text[: m.end() + 4]:
        h = int(m.group("h")) % 12 + (12 if m.group("ap") == "PM" else 0)
        return {"time_ist": f"{h:02d}:{m.group('m')}"}
    m = _RANGE.match(text)
    if m:
        a, b = _num(m.group("a")), _num(m.group("b"))
        out: dict[str, object] = {"range": [a, b]}
        if m.group("u"):
            out["unit"] = UNITS[m.group("u")]
        elif name.endswith("Delta_Range"):
            out["unit"] = "delta"
        return out
    m = _SINGLE.match(text)
    if m:
        rest = text[m.end() :].lstrip()
        if rest.startswith("se "):  # "500 milliseconds se 1 second" jaisi range: guess nahi
            return {}
        v = _num(m.group("n"))
        return {"value": int(v) if v.is_integer() else v, "unit": UNITS[m.group("u")]}
    return {}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _clean_name(raw: str) -> tuple[str, bool]:
    cc = _CC in raw
    name = raw.replace(_CC, "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"ajeeb naam: {raw!r}")
    return name, cc


def parse_idea(text: str) -> tuple[list[dict[str, object]], list[dict[str, object]], str]:
    version_line = next(ln for ln in text.splitlines() if ln.startswith("**Idea ka Version:**"))
    version = re.search(r"(\d+\.\d+)", version_line)
    aam = text[text.index("### Aam Numbers ki Suchi") : text.index("### Teeno Index ke Alag Numbers ki Suchi")]
    teeno = text[text.index("### Teeno Index ke Alag Numbers ki Suchi") : text.index("## 19. Abhi tay nahi hua")]
    rows: list[dict[str, object]] = []
    for ln in aam.splitlines():
        if not ln.startswith("| ") or ln.startswith("| Naam") or ln.startswith("| :---"):
            continue
        c = _cells(ln)
        if len(c) != 5:
            raise ValueError(f"5 column chahiye: {ln[:80]}")
        name, cc = _clean_name(c[0])
        status = c[2]
        if status not in ALLOWED_STATUS:
            raise ValueError(f"galat status {status!r} ({name})")
        row: dict[str, object] = {
            "name": name,
            "kimat": c[1],
            "status": status,
            "prastaavit_cc": cc,
            "kahan": c[3],
            "wajah": c[4],
        }
        row.update(parse_kimat(name, c[1], status))
        rows.append(row)
    idx: list[dict[str, object]] = []
    for ln in teeno.splitlines():
        if not ln.startswith("| ") or ln.startswith("| Naam") or ln.startswith("| :---"):
            continue
        c = _cells(ln)
        if len(c) != 6:
            raise ValueError(f"6 column chahiye: {ln[:80]}")
        name, cc = _clean_name(c[0])
        idx.append(
            {
                "name": name,
                "banknifty": c[1],
                "nifty50": c[2],
                "sensex": c[3],
                "status_text": c[4],
                "prastaavit_cc": cc,
                "wajah": c[5],
            }
        )
    return rows, idx, (version.group(1) if version else "?")


def _toml_value(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)  # JSON string = valid TOML basic string


def to_toml(rows: list[dict[str, object]], idx: list[dict[str, object]], version: str, sha: str) -> str:
    out = [
        "# AUTO-GENERATED: tools/niyam_from_idea.py se bana. Is file ko haath se mat badlo.",
        "# Badlaav: pehle idea file (branch `idea`) mein malik ki manzoori se, phir generator dobara chalao.",
        "",
        "[meta]",
        f"idea_version = {_toml_value(version)}",
        'source_file = "docs/01_Bot_Idea_v4.md (branch: idea)"',
        f"source_sha256 = {_toml_value(sha)}",
        f"number_count = {len(rows)}",
        f"index_number_count = {len(idx)}",
        "",
    ]
    for r in rows:
        out.append(f"[number.{r['name']}]")
        for k in ("kimat", "status", "prastaavit_cc", "kahan", "wajah", "value", "unit", "range", "time_ist"):
            if k in r:
                out.append(f"{k} = {_toml_value(r[k])}")
        out.append("")
    for r in idx:
        out.append(f"[index_number.{r['name']}]")
        for k in ("banknifty", "nifty50", "sensex", "status_text", "prastaavit_cc", "wajah"):
            out.append(f"{k} = {_toml_value(r[k])}")
        out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(argv[1]), Path(argv[2])
    raw = src.read_bytes()
    rows, idx, version = parse_idea(raw.decode("utf-8"))
    dst.write_text(to_toml(rows, idx, version, hashlib.sha256(raw).hexdigest()), encoding="utf-8")
    typed = sum(1 for r in rows if {"value", "range", "time_ist"} & r.keys())
    print(f"{len(rows)} numbers ({typed} typed), {len(idx)} index numbers -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
