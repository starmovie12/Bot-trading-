#!/usr/bin/env python3
"""Throw-away lint: v4 ke [PRASTAAVIT-CC] paragraphs ke likhne ke niyam jaancho."""
import re, sys
from pathlib import Path
v4 = Path(__file__).resolve().parents[2] / "docs/01_Bot_Idea_v4.md"
lines = v4.read_text(encoding="utf-8").split("\n")
sec = None
ALLOW_NUM = {"12", "17", "18", "19", "20", "21"}
ID = re.compile(r"(F-\d+|H-\d+|TAKRAAV #\d+|Sawal \d+|\d+\.\d+ ka saar|Version \d+\.\d+|`[^`]*`|01b_|02_|03_|04_|R_[a-e]_|\[F-xx[^\]]*\]|H-xx)")
issues = {"num": [], "long": [], "para": []}
start = lines.index("# IDEA SHURU")
for i, l in enumerate(lines[start:], start + 1):
    m = re.match(r"^## (\d+)\.", l)
    if m: sec = m.group(1)
    if "[PRASTAAVIT-CC]" not in l or l.startswith("|") or l.startswith("- **") and sec == "2":
        continue
    body = ID.sub("", l)
    if sec not in ALLOW_NUM and re.search(r"\d", body):
        issues["num"].append((i, sec, re.findall(r"\S*\d\S*", body)[:4]))
    sents = [s for s in re.split(r"(?<=[.?!])\s+", l) if s.strip()]
    if len(sents) > 5 and sec not in {"17", "20"}:
        issues["para"].append((i, sec, len(sents)))
    for s in sents:
        w = len(ID.sub("X", s).split())
        if w > 32 and sec not in {"17", "20", "21"}:
            issues["long"].append((i, sec, w))
for k, v in issues.items():
    print(f"{k}: {len(v)}")
    for x in v[:15]: print("   ", x)
