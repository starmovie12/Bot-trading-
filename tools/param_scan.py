#!/usr/bin/env python3
"""Hidden-parameter scan (MISSION V11 §8.2): live parameters <= 12, counted from params.toml and from the
numeric literals in strategy / risk code that live outside the registries (params.toml, limits.toml,
constants.toml).

  param_scan.py [--max N] [--paths FILE...]   print per-module counts; exit 1 when the params.toml
                                              entries plus the non-exempt literals exceed N (default 12)

A literal is exempt with a trailing comment `# param-exempt: <reason>` (at most 5 per module; more is a
violation). Structural literals 0, 1, -1 and 100 (percent) are not counted.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCOPE = ("src/bot/strategy", "src/bot/dimaag", "src/bot/haath")
IGNORED = {0, 1, -1, 100}
MAX_EXEMPT = 5


def literals(path: Path) -> tuple[list[int], list[int]]:
    """(counted line numbers, exempt line numbers) of numeric literals in one module."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    counted: list[int] = []
    exempt: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
            continue  # the operand is visited on its own
        if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
            continue
        if not isinstance(node.value, int | float) or node.value in IGNORED:
            continue
        line = lines[node.lineno - 1] if 0 < node.lineno <= len(lines) else ""
        (exempt if "param-exempt:" in line else counted).append(node.lineno)
    return counted, exempt


def main(argv: list[str]) -> int:
    limit = int(argv[argv.index("--max") + 1]) if "--max" in argv else 12
    if "--paths" in argv:
        files = [Path(p) for p in argv[argv.index("--paths") + 1 :]]
    else:
        files = sorted(p for d in SCOPE for p in (ROOT / d).rglob("*.py") if "__pycache__" not in p.parts)
    params_file = ROOT / "params.toml"
    params = len(tomllib.loads(params_file.read_text(encoding="utf-8"))) if params_file.is_file() else 0
    total, problems = 0, []
    for f in files:
        counted, exempt = literals(f)
        total += len(counted)
        name = str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f)
        print(f"{name}: {len(counted)} literal(s) counted, {len(exempt)} exempt")
        if len(exempt) > MAX_EXEMPT:
            problems.append(f"{name}: {len(exempt)} exemptions (max {MAX_EXEMPT})")
    live = params + total
    print(f"params.toml entries: {params} · literals counted: {total} · live parameters: {live} (max {limit})")
    for p in problems:
        print(f"VIOLATION {p}")
    return 1 if live > limit or problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
