"""Bot se Dashboard (Vercel) ko haalat bhejne ka signature (HMAC-SHA256).

Bot khud HTTPS POST karta hai (outbound); website bot ki machine mein kabhi kuch nahi bhejti.
Signature = hex(HMAC-SHA256(key, f"{timestamp_ms}." + body)).
Website `Command_Max_Umar` se purana signature nahi maanti.
Same tareeka branch `website` ki lib/state.mjs mein hai; dono ka golden test vector ek hi hai.
"""

from __future__ import annotations

import hashlib
import hmac

from bot.login.secrets import Secret

SIGNATURE_VERSION = "v1"


def sign(key: Secret, timestamp_ms: int, body: bytes) -> str:
    if timestamp_ms <= 0:
        raise ValueError("timestamp galat")
    msg = f"{timestamp_ms}.".encode() + body
    return hmac.new(key.reveal().encode("utf-8"), msg, hashlib.sha256).hexdigest()


def push_headers(key: Secret, timestamp_ms: int, body: bytes) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Bot-Timestamp": str(timestamp_ms),
        "X-Bot-Signature": f"{SIGNATURE_VERSION}={sign(key, timestamp_ms, body)}",
    }
