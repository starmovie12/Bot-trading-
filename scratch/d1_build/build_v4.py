#!/usr/bin/env python3
"""Throw-away doc builder (production code nahi).

docs/00_input/bot_idea_final.md (original, read-only) + scratch/d1_build/add_*.md
=> docs/01_Bot_Idea_v4.md

Additions file format (ek op = ek marker line + text):
  @@AFTER_BLOCK <exact heading line>   -> heading ke block ke ant mein (agli same/upar level heading se pehle)
  @@BEFORE_LINE <exact line>           -> us line se pehle (text + khaali line)
  @@AFTER_LINE <line prefix>           -> us line ke turant baad (table rows ke liye, khaali line nahi)
  @@REPLACE_LINE <exact line>          -> poori line badlo (sirf header ke liye; verify mein whitelist)
Phir verify: original ki har line (replace wali chhod kar) usi kram mein v4 mein maujood hai.
"""
import glob
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIG = ROOT / "docs/00_input/bot_idea_final.md"
OUT = ROOT / "docs/01_Bot_Idea_v4.md"
EXPECTED_SHA = "c8770e6791923dcb9f03786371a3dbe9ae91a92f00164f90fc982239df0dabb1"


def parse_ops(path):
    ops, cur = [], None
    for raw in Path(path).read_text(encoding="utf-8").split("\n"):
        if raw.startswith("@@"):
            kind, _, arg = raw[2:].partition(" ")
            cur = [kind, arg, []]
            ops.append(cur)
        elif cur is not None:
            cur[2].append(raw)
    for op in ops:  # trailing khaali lines hatao
        while op[2] and op[2][-1].strip() == "":
            op[2].pop()
    return ops


def level(line):
    m = re.match(r"^(#+) ", line)
    return len(m.group(1)) if m else None


def apply(lines, op):
    kind, arg, text = op
    if kind == "REPLACE_LINE":
        idx = [i for i, l in enumerate(lines) if l == arg]
        assert len(idx) == 1, f"REPLACE target not unique/missing: {arg!r} -> {idx}"
        lines[idx[0]:idx[0] + 1] = text
    elif kind == "BEFORE_LINE":
        idx = [i for i, l in enumerate(lines) if l == arg]
        assert len(idx) == 1, f"BEFORE target not unique/missing: {arg!r}"
        lines[idx[0]:idx[0]] = text + [""]
    elif kind == "AFTER_LINE":
        idx = [i for i, l in enumerate(lines) if l.startswith(arg)]
        assert len(idx) == 1, f"AFTER_LINE prefix not unique/missing: {arg!r} -> {idx}"
        lines[idx[0] + 1:idx[0] + 1] = text
    elif kind == "AFTER_BLOCK":
        idx = [i for i, l in enumerate(lines) if l == arg]
        assert len(idx) == 1, f"AFTER_BLOCK heading not unique/missing: {arg!r}"
        i, lv = idx[0], level(arg)
        j = i + 1
        while j < len(lines):
            l2 = level(lines[j])
            if l2 is not None and l2 <= lv:
                break
            j += 1
        # j = agli heading (ya file ka ant). Pehle khaali line ho toh uske baad text.
        ins = text + [""]
        if j > 0 and lines[j - 1].strip() != "":
            ins = [""] + ins
        lines[j:j] = ins
    else:
        raise SystemExit(f"unknown op {kind}")


def main():
    raw = ORIG.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == EXPECTED_SHA, f"ORIGINAL BADAL GAYA! sha={sha}"
    orig = raw.decode("utf-8").split("\n")
    lines = list(orig)
    replaced = set()
    files = sorted(glob.glob(str(Path(__file__).parent / "add_*.md")))
    nops = 0
    for f in files:
        for op in parse_ops(f):
            if op[0] == "REPLACE_LINE":
                replaced.add(op[1])
            apply(lines, op)
            nops += 1
    OUT.write_text("\n".join(lines), encoding="utf-8")

    # VERIFY 1: original ki har line usi kram mein (subsequence)
    j = 0
    missing = []
    for ol in orig:
        if ol in replaced:
            continue
        while j < len(lines) and lines[j] != ol:
            j += 1
        if j == len(lines):
            missing.append(ol)
            j = 0  # reset taaki baaki bhi gine
        else:
            j += 1
    # VERIFY 2: instruction block bilkul same
    end = orig.index("</idea_file_instructions>")
    block_same = lines[: end + 1] == orig[: end + 1]
    print(f"ops applied: {nops} from {len(files)} files")
    print(f"original lines: {len(orig)}  v4 lines: {len(lines)}")
    print(f"replaced (header, whitelisted): {sorted(replaced)}")
    print(f"instruction block unchanged: {block_same}")
    print(f"MISSING original lines: {len(missing)}")
    for m in missing[:10]:
        print("   MISSING:", m[:120])
    ok = block_same and not missing
    print("VERIFY:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
