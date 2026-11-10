"""Upstox ka official TOTP login (malik ka niyam 10 Nov 2026: roz haath se login nahi).

Docs (dekha 10 Nov 2026): https://upstox.com/developer/api-documentation/get-token/
  POST https://api.upstox.com/v2/totp-login/authorization/token
  headers: accept, Content-Type: application/json, x-api-key: <app ki API key>
  body: {"totp": "<6 digit>", "pin": "<6 digit>"}
  token agle din 3:30 AM tak; naya token purana band karta hai; sirf "individual" app.

Niyam:
- Login SIRF Bot machine karti hai; Pehredaar kabhi nahi (F-76): Pehredaar ka login Bot ka token band kar dega.
- Token sirf memory mein. `Secret` print par `****`.
- Galat API key / TOTP band / app type galat par dobara koshish nahi (malik ko alert).
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Final, Protocol

from bot.login.secrets import UPSTOX_API_KEY, UPSTOX_PIN, UPSTOX_TOTP_SECRET, Secret, SecretStore
from bot.login.totp import key_from_base32, seconds_left_in_step, totp

TOTP_LOGIN_URL: Final = "https://api.upstox.com/v2/totp-login/authorization/token"
IST: Final = timezone(timedelta(hours=5, minutes=30))
TOKEN_EXPIRY_IST: Final = (3, 30)  # agle din 3:30 AM

# Upstox error codes (docs se). True = dobara koshish bekaar (malik ko theek karna hai).
ERROR_CODES: Final[dict[str, tuple[str, bool]]] = {
    "UDAPI100096": ("API key galat", True),
    "UDAPI100097": ("PIN ya TOTP galat", False),
    "UDAPI100098": ("account par TOTP chalu nahi", True),
    "UDAPI100099": ("rate limit (bahut zyada koshish)", False),
    "UDAPI100101": ("TOTP login sirf individual app ke liye", True),
    "UDAPI1241": ("PIN 6 digit ka nahi", True),
    "UDAPI1242": ("TOTP 6 digit ka nahi", True),
}


class LoginError(RuntimeError):
    def __init__(self, message: str, code: str | None = None, fatal: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.fatal = fatal


class TokenExpired(RuntimeError):
    """Token nahi hai ya khatam ho gaya. Naye entry band; Broker Stop broker par rehta hai."""


@dataclass(frozen=True, slots=True)
class PreparedRequest:
    url: str
    headers: Mapping[str, str] = field(repr=False)
    body: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class Token:
    access: Secret
    user_id: str
    issued_at: datetime
    expires_at: datetime


def _six_digits(value: str, what: str) -> None:
    if len(value) != 6 or not value.isdigit():
        raise LoginError(f"{what} 6 digit ka hona chahiye", fatal=True)


def build_request(api_key: Secret, totp_code: str, pin: Secret) -> PreparedRequest:
    _six_digits(totp_code, "TOTP")
    _six_digits(pin.reveal(), "PIN")
    body = json.dumps({"totp": totp_code, "pin": pin.reveal()}).encode("utf-8")
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": api_key.reveal(),
    }
    return PreparedRequest(url=TOTP_LOGIN_URL, headers=headers, body=body)


def expiry_after(issued_at: datetime) -> datetime:
    """Token kab khatam: `issued_at` ke baad ka pehla 3:30 AM IST."""
    if issued_at.tzinfo is None:
        raise ValueError("timezone wala datetime chahiye")
    t = issued_at.astimezone(IST)
    exp = t.replace(hour=TOKEN_EXPIRY_IST[0], minute=TOKEN_EXPIRY_IST[1], second=0, microsecond=0)
    if exp <= t:
        exp += timedelta(days=1)
    return exp


def _find_error_code(data: object) -> str | None:
    if isinstance(data, dict):
        for k in ("errorCode", "error_code", "code"):
            v = data.get(k)
            if isinstance(v, str) and v.startswith("UDAPI"):
                return v
        for v in data.values():
            found = _find_error_code(v)
            if found:
                return found
    elif isinstance(data, list):
        for v in data:
            found = _find_error_code(v)
            if found:
                return found
    return None


def parse_response(status: int, body: bytes, now: datetime) -> Token:
    try:
        data = json.loads(body.decode("utf-8")) if body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise LoginError(f"broker ka jawab JSON nahi (HTTP {status})") from None
    code = _find_error_code(data)
    if status != 200 or code:
        msg, fatal = ERROR_CODES.get(code or "", ("anjaan galti", False))
        raise LoginError(f"login fail: {msg} (HTTP {status}, {code})", code=code, fatal=fatal)
    payload = data.get("data", data) if isinstance(data, dict) else {}
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token:
        raise LoginError("jawab mein access_token nahi")
    user_id = payload.get("user_id", "")
    return Token(
        access=Secret(token),
        user_id=user_id if isinstance(user_id, str) else "",
        issued_at=now,
        expires_at=expiry_after(now),
    )


class Transport(Protocol):
    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout_s: float) -> tuple[int, bytes]: ...


class UrllibTransport:
    """Asli HTTPS call (TLS certificate jaanch hamesha ON). Tests mein kabhi nahi chalta."""

    def __init__(self) -> None:
        self._ctx = ssl.create_default_context()

    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout_s: float) -> tuple[int, bytes]:
        if not url.startswith("https://"):
            raise LoginError("sirf https allowed", fatal=True)
        req = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")  # noqa: S310 (https jaancha)
        try:
            with urllib.request.urlopen(req, timeout=timeout_s, context=self._ctx) as resp:  # noqa: S310
                return int(resp.status), resp.read()
        except urllib.error.HTTPError as e:
            return int(e.code), e.read()


Alert = Callable[[str, str], None]  # (darja: "jaankari"/"zaroori", sandesh)


class TokenManager:
    """Roz subah ka login aur din bhar token ki dekhbhaal."""

    def __init__(
        self,
        store: SecretStore,
        transport: Transport,
        clock: Callable[[], datetime],
        *,
        role: str,
        max_attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        alert: Alert | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        if role != "bot":
            raise LoginError("sirf Bot machine login karti hai; Pehredaar kabhi nahi (F-76)", fatal=True)
        if max_attempts < 1:
            raise ValueError("max_attempts kam se kam 1")
        self._store = store
        self._transport = transport
        self._clock = clock
        self._max = max_attempts
        self._sleep = sleep
        self._alert = alert or (lambda _level, _msg: None)
        self._timeout = timeout_s
        self._token: Token | None = None

    def login(self) -> Token:
        api_key = self._store.get(UPSTOX_API_KEY)
        pin = self._store.get(UPSTOX_PIN)
        key = key_from_base32(self._store.get(UPSTOX_TOTP_SECRET).reveal())
        last: LoginError | None = None
        for attempt in range(1, self._max + 1):
            now = self._clock()
            ts = now.timestamp()
            if seconds_left_in_step(ts) < 3:  # code badalne wala ho toh agle code ka intezaar
                self._sleep(seconds_left_in_step(ts) + 0.5)
                now = self._clock()
                ts = now.timestamp()
            req = build_request(api_key, totp(key, ts), pin)
            try:
                status, body = self._transport.post(req.url, req.headers, req.body, self._timeout)
                tok = parse_response(status, body, now)
            except LoginError as e:
                last = e
                if e.fatal:
                    break
                if attempt < self._max:
                    self._sleep(31.0 if e.code == "UDAPI100097" else 2.0**attempt)
                continue
            self._token = tok
            self._alert("jaankari", f"Upstox login ho gaya ({tok.user_id}); token {tok.expires_at:%d %b %H:%M} IST tak")
            return tok
        assert last is not None  # noqa: S101 (loop kam se kam ek baar chalta hai)
        self._alert("zaroori", f"Upstox login fail: {last}. Aaj naye entry band.")
        raise last

    def current(self) -> Token:
        tok = self._token
        if tok is None or self._clock() >= tok.expires_at:
            raise TokenExpired("token nahi hai ya khatam; naye entry band")
        return tok
