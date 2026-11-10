#!/usr/bin/env python3
"""Throw-away: v4 ke cross-references poore hain ya nahi."""
import re
from pathlib import Path
R = Path(__file__).resolve().parents[2]
v4 = (R / "docs/01_Bot_Idea_v4.md").read_text(encoding="utf-8")
f01b = (R / "docs/01b_Audit_Findings.md").read_text(encoding="utf-8")
d3 = (R / "docs/03_Strategy_Edge_Plan.md").read_text(encoding="utf-8")
idea = v4[v4.index("# IDEA SHURU"):]
lines = idea.split("\n")
# 1) naam jo Numbers list / Check Suchi / check heading mein hone chahiye
num_rows = set(re.findall(r"^\| ([A-Za-z0-9_]+)(?: `\[PRASTAAVIT-CC\]`)? \|", idea, re.M))
checks = set(re.findall(r"^### ([A-Za-z0-9_]+)$", idea, re.M))
sec17 = idea[idea.index("## 17. Tayyar Code"):idea.index("## 18. Numbers ki list")]
names = set()
for m in re.finditer(r"`([A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+)`", idea):
    if m.start() >= idea.index("## 17. Tayyar Code") and m.start() < idea.index("## 18. Numbers ki list"):
        continue
    names.add(m.group(1))
missing_names = sorted(n for n in names if n not in num_rows and n not in checks)
# 2) F refs
f_refs = set(re.findall(r"\[?F-(\d+)", idea)) - {"xx"}
f_def = set(re.findall(r"^\| F-(\d+) \|", f01b, re.M))
missing_f = sorted((x for x in f_refs if x not in f_def), key=int)
# 3) TAKRAAV refs
t_refs = set(re.findall(r"TAKRAAV #(\d+)", idea))
t_def = set(re.findall(r"^- \*\*\[TAKRAAV #(\d+)\]", idea, re.M))
missing_t = sorted((x for x in t_refs if x not in t_def), key=int)
# 4) Sawal refs
s_refs = set(re.findall(r"Sawal (\d+)", idea))
s_def = set(re.findall(r"^- Sawal (\d+)", idea, re.M)) | set(re.findall(r"^(\d+)\. ", idea[idea.index("### Sawal: ab bhi khule"):idea.index("### Takraav")], re.M))
s_def |= set(re.findall(r"^- Sawal (\d+) (?:va|aur) (\d+)", idea, re.M) and [y for p in re.findall(r"^- Sawal (\d+) (?:va|aur) (\d+)", idea, re.M) for y in p])
s_def |= set(y for p in re.findall(r"^- Sawal (\d+), (\d+) aur (\d+)", idea, re.M) for y in p)
missing_s = sorted((x for x in s_refs if x not in s_def), key=int)
# 5) H refs
h_refs = set(re.findall(r"H-(\d\d)", idea))
h_def = set(re.findall(r"^\| H-(\d\d) \|", d3, re.M))
missing_h = sorted(x for x in h_refs if x not in h_def)
print("Naam bina Numbers/Check row:", missing_names)
print("F refs bina 01b entry:", missing_f)
print("TAKRAAV refs bina definition:", missing_t)
print("Sawal refs bina entry:", missing_s)
print("H refs bina D3 entry:", missing_h)
