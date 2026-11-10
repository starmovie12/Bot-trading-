"""Supply-chain aur suraksha ke sasta par zaroori checks (docs/02 Section F)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE_DIRS = ("src", "tools", "pehredaar")
TLS_OFF = re.compile(
    r"CERT_NONE|verify\s*=\s*False|check_hostname\s*=\s*False|InsecureSkipVerify"
    r"|rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED"
)
SECRET_LIKE = re.compile(
    r"(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}|eyJ[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}",
    re.IGNORECASE,
)


def _files() -> list[Path]:
    out: list[Path] = []
    for d in CODE_DIRS:
        out += [
            p
            for p in (ROOT / d).rglob("*")
            if p.is_file() and p.suffix in {".py", ".go", ".toml", ".mod", ".mjs", ".js", ".json", ".html"}
        ]
    return out


def test_no_tls_verification_disabled_anywhere() -> None:
    hits = [f"{p}:{i}" for p in _files() for i, ln in enumerate(p.read_text().splitlines(), 1) if TLS_OFF.search(ln)]
    assert hits == [], f"TLS jaanch band karne wala code mila: {hits}"


def test_no_secret_like_strings_in_code_or_config() -> None:
    paths = [*_files(), ROOT / "config" / "niyam.toml"]
    hits = [str(p) for p in paths if SECRET_LIKE.search(p.read_text())]
    assert hits == [], f"chaabi jaisa text mila: {hits}"


def test_no_order_endpoint_in_m0() -> None:
    # M0/M1 mein order lagane ka koi rasta code mein nahi hona chahiye (docs/04 M1).
    pat = re.compile(r"place[-_ ]?order|/order/place|api-hft\.upstox\.com", re.IGNORECASE)
    hits = [str(p) for p in _files() if pat.search(p.read_text())]
    assert hits == []
