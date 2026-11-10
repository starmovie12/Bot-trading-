from __future__ import annotations

import json
import os
import stat
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from bot.dashboard_push import push_headers, sign
from bot.login.secrets import CredentialsDirStore, MemoryStore, Secret, SecretError
from bot.login.totp import hotp, key_from_base32, totp
from bot.login.upstox_totp import (
    IST,
    TOTP_LOGIN_URL,
    LoginError,
    TokenExpired,
    TokenManager,
    build_request,
    expiry_after,
    parse_response,
)

# RFC 6238 Appendix B (https://www.rfc-editor.org/rfc/rfc6238.txt, dekha 10 Nov 2026): 8 digit, step 30, T0 0.
SEED_SHA1 = b"12345678901234567890"
SEED_SHA256 = SEED_SHA1 + b"123456789012"
SEED_SHA512 = SEED_SHA1 * 3 + b"1234"
RFC_VECTORS = [
    (59, "94287082", "46119246", "90693936"),
    (1111111109, "07081804", "68084774", "25091201"),
    (1111111111, "14050471", "67062674", "99943326"),
    (1234567890, "89005924", "91819424", "93441116"),
    (2000000000, "69279037", "90698825", "38618901"),
    (20000000000, "65353130", "77737706", "47863826"),
]


@pytest.mark.parametrize(("t", "s1", "s256", "s512"), RFC_VECTORS)
def test_totp_rfc6238_vectors(t: int, s1: str, s256: str, s512: str) -> None:
    assert totp(SEED_SHA1, t, digits=8, algo="sha1") == s1
    assert totp(SEED_SHA256, t, digits=8, algo="sha256") == s256
    assert totp(SEED_SHA512, t, digits=8, algo="sha512") == s512


def test_six_digit_is_last_six_of_eight() -> None:
    # Upstox 6 digit maangta hai; truncation wahi rehta hai, sirf modulus 10^6.
    assert totp(SEED_SHA1, 59) == "287082"
    assert hotp(SEED_SHA1, 1) == "287082"


def test_base32_secret_forms() -> None:
    # "12345678901234567890" ka base32
    b32 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
    assert key_from_base32(b32) == SEED_SHA1
    assert key_from_base32(" gezd gnbv gy3t qojq gezd gnbv gy3t qojq ") == SEED_SHA1
    with pytest.raises(ValueError):
        key_from_base32("")
    with pytest.raises(ValueError):
        key_from_base32("!!!")


def test_secret_never_prints_value() -> None:
    s = Secret("bahut-gupt")
    assert "bahut-gupt" not in repr(s)
    assert "bahut-gupt" not in str(s)
    assert "bahut-gupt" not in f"{s}"
    assert s.reveal() == "bahut-gupt"


def test_credentials_dir_store(tmp_path: Path) -> None:
    good = tmp_path / "upstox_pin"
    good.write_text("123456\n")
    os.chmod(good, stat.S_IRUSR)
    loose = tmp_path / "upstox_api_key"
    loose.write_text("x" * 20)
    os.chmod(loose, 0o644)
    store = CredentialsDirStore(tmp_path)
    assert store.get("upstox_pin").reveal() == "123456"
    with pytest.raises(SecretError, match="permission"):
        store.get("upstox_api_key")
    with pytest.raises(SecretError, match="nahi mila"):
        store.get("upstox_totp_secret")
    with pytest.raises(SecretError, match="naam"):
        store.get("../etc/passwd")


def test_build_request_matches_upstox_docs() -> None:
    req = build_request(Secret("APIKEY-TEST"), "123456", Secret("654321"))
    assert req.url == TOTP_LOGIN_URL == "https://api.upstox.com/v2/totp-login/authorization/token"
    assert req.headers["x-api-key"] == "APIKEY-TEST"
    assert req.headers["Content-Type"] == "application/json"
    assert json.loads(req.body) == {"totp": "123456", "pin": "654321"}
    assert "APIKEY-TEST" not in repr(req) and "654321" not in repr(req)
    with pytest.raises(LoginError):
        build_request(Secret("k"), "12345", Secret("654321"))
    with pytest.raises(LoginError):
        build_request(Secret("k"), "123456", Secret("12ab56"))


@pytest.mark.parametrize(
    ("issued", "expected"),
    [
        (datetime(2026, 11, 10, 9, 0, tzinfo=IST), datetime(2026, 11, 11, 3, 30, tzinfo=IST)),
        (datetime(2026, 11, 10, 2, 0, tzinfo=IST), datetime(2026, 11, 10, 3, 30, tzinfo=IST)),
        (datetime(2026, 11, 10, 3, 30, tzinfo=IST), datetime(2026, 11, 11, 3, 30, tzinfo=IST)),
    ],
)
def test_token_expiry_is_next_330_ist(issued: datetime, expected: datetime) -> None:
    assert expiry_after(issued) == expected


def test_parse_response_ok_and_errors() -> None:
    now = datetime(2026, 11, 10, 8, 40, tzinfo=IST)
    tok = parse_response(200, json.dumps({"user_id": "AB1234", "access_token": "TOKEN-XYZ"}).encode(), now)
    assert tok.access.reveal() == "TOKEN-XYZ" and tok.user_id == "AB1234"
    wrapped = json.dumps({"status": "success", "data": {"access_token": "T2"}}).encode()
    assert parse_response(200, wrapped, now).access.reveal() == "T2"
    err = json.dumps({"status": "error", "errors": [{"errorCode": "UDAPI100096", "message": "x"}]}).encode()
    with pytest.raises(LoginError) as ei:
        parse_response(401, err, now)
    assert ei.value.code == "UDAPI100096" and ei.value.fatal
    with pytest.raises(LoginError):
        parse_response(200, b"not json", now)
    with pytest.raises(LoginError):
        parse_response(200, b"{}", now)


class FakeTransport:
    def __init__(self, replies: list[tuple[int, Mapping[str, object]]]) -> None:
        self.replies = list(replies)
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, headers: Mapping[str, str], body: bytes, timeout_s: float) -> tuple[int, bytes]:
        self.calls.append({"url": url, "headers": dict(headers), "body": json.loads(body)})
        status, data = self.replies.pop(0)
        return status, json.dumps(data).encode()


STORE = MemoryStore(
    {"upstox_api_key": "APIKEY-TEST", "upstox_pin": "654321", "upstox_totp_secret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"}
)


class Clock:
    def __init__(self, t: datetime) -> None:
        self.t = t

    def __call__(self) -> datetime:
        return self.t

    def sleep(self, s: float) -> None:
        self.t += timedelta(seconds=s)


def test_token_manager_success_sends_correct_totp_and_alerts() -> None:
    clock = Clock(datetime(2026, 11, 10, 8, 40, 5, tzinfo=IST))
    alerts: list[tuple[str, str]] = []
    tr = FakeTransport([(200, {"user_id": "AB1234", "access_token": "TOKEN-XYZ"})])
    tm = TokenManager(STORE, tr, clock, role="bot", sleep=clock.sleep, alert=lambda lv, m: alerts.append((lv, m)))
    tok = tm.login()
    expected = totp(SEED_SHA1, clock.t.timestamp())
    assert tr.calls[0]["body"] == {"totp": expected, "pin": "654321"}
    assert tm.current() is tok
    assert alerts and alerts[0][0] == "jaankari" and "TOKEN-XYZ" not in alerts[0][1]
    clock.t = datetime(2026, 11, 11, 3, 30, tzinfo=IST)
    with pytest.raises(TokenExpired):
        tm.current()


def test_token_manager_retries_wrong_totp_then_succeeds() -> None:
    clock = Clock(datetime(2026, 11, 10, 8, 40, 5, tzinfo=IST))
    bad = {"status": "error", "errors": [{"errorCode": "UDAPI100097"}]}
    tr = FakeTransport([(401, bad), (200, {"access_token": "T"})])
    tm = TokenManager(STORE, tr, clock, role="bot", sleep=clock.sleep)
    assert tm.login().access.reveal() == "T"
    assert len(tr.calls) == 2
    assert tr.calls[0]["body"] != tr.calls[1]["body"]  # agla TOTP window


def test_token_manager_stops_on_fatal_error_and_alerts() -> None:
    clock = Clock(datetime(2026, 11, 10, 8, 40, 5, tzinfo=IST))
    alerts: list[tuple[str, str]] = []
    tr = FakeTransport([(401, {"errors": [{"errorCode": "UDAPI100098"}]})])
    tm = TokenManager(STORE, tr, clock, role="bot", sleep=clock.sleep, alert=lambda lv, m: alerts.append((lv, m)))
    with pytest.raises(LoginError):
        tm.login()
    assert len(tr.calls) == 1
    assert alerts[-1][0] == "zaroori"


def test_pehredaar_can_never_login() -> None:
    with pytest.raises(LoginError, match="Pehredaar"):
        TokenManager(STORE, FakeTransport([]), Clock(datetime.now(IST)), role="pehredaar")


def test_dashboard_push_golden_vector() -> None:
    # Same vector dashboard/test/state.test.mjs mein bhi hai (Python aur website ek hi signature banayein).
    key = Secret("test-key-not-a-real-key")
    body = b'{"mode":"paper"}'
    assert sign(key, 1731220000000, body) == "8d83640c12bb02bb89809ef3960d4d8ceb698b5baae7dbad33893701184a46fd"
    h = push_headers(key, 1731220000000, body)
    assert h["X-Bot-Signature"].startswith("v1=") and h["X-Bot-Timestamp"] == "1731220000000"
