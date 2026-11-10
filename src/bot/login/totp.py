"""TOTP (RFC 6238) aur HOTP (RFC 4226): sirf standard library.

Upstox ka TOTP login 6 digit code maangta hai. Yeh module malik ke TOTP secret se wahi code banata hai
jo authenticator app banata hai. Secret kabhi log ya print nahi hota.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import struct
from collections.abc import Callable
from typing import Final

_ALGOS: Final[dict[str, Callable[..., hashlib._Hash]]] = {
    "sha1": hashlib.sha1,
    "sha256": hashlib.sha256,
    "sha512": hashlib.sha512,
}


def key_from_base32(secret: str) -> bytes:
    """Authenticator wala base32 secret (spaces/lowercase/bina padding bhi chalega) bytes mein."""
    s = "".join(secret.split()).upper()
    if not s:
        raise ValueError("TOTP secret khaali hai")
    pad = (-len(s)) % 8
    try:
        return base64.b32decode(s + "=" * pad)
    except ValueError as e:  # binascii.Error ValueError ka hissa hai
        raise ValueError("TOTP secret base32 nahi hai") from e


def hotp(key: bytes, counter: int, digits: int = 6, algo: str = "sha1") -> str:
    if digits not in (6, 7, 8):
        raise ValueError("digits 6, 7 ya 8 hone chahiye")
    if counter < 0:
        raise ValueError("counter negative nahi ho sakta")
    if algo not in _ALGOS:
        raise ValueError(f"algo '{algo}' allowed nahi")
    # RFC 4226/6238 HMAC-SHA1 hi maangte hain; yeh password hashing nahi hai.
    mac = hmac.new(key, struct.pack(">Q", counter), _ALGOS[algo]).digest()
    offset = mac[-1] & 0x0F
    code = (int.from_bytes(mac[offset : offset + 4], "big") & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def totp(key: bytes, unix_time: float, *, digits: int = 6, step: int = 30, algo: str = "sha1", t0: int = 0) -> str:
    if step <= 0:
        raise ValueError("step positive hona chahiye")
    if unix_time < t0:
        raise ValueError("samay t0 se pehle nahi ho sakta")
    return hotp(key, int((unix_time - t0) // step), digits=digits, algo=algo)


def seconds_left_in_step(unix_time: float, step: int = 30) -> float:
    """Is TOTP code ke badalne mein kitne second bache (seema ke paas ho toh agla code lo)."""
    return step - (unix_time % step)
