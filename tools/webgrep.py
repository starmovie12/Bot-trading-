#!/usr/bin/env python3
"""webgrep.py FILE REGEX: strip tags and scripts from a saved page; print matching lines +-1 (at most 30)."""

import html
import re
import sys
from pathlib import Path


def text_lines(raw: str) -> list[str]:
    raw = re.sub(r"(?s)<[^>]+>", "\n", re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw))
    return [x for x in (html.unescape(y).strip() for y in raw.splitlines()) if x]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 64
    lines = text_lines(Path(argv[0]).read_text(encoding="utf-8", errors="replace"))
    hits = [i for i, x in enumerate(lines) if re.search(argv[1], x, re.IGNORECASE)]
    keep = sorted({j for i in hits for j in range(max(0, i - 1), min(len(lines), i + 2))})
    print("\n".join(f"{j + 1}: {lines[j][:200]}" for j in keep[:30]) or "no match")
    return 0 if keep else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
