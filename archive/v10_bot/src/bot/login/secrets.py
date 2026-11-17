"""Secrets (chaabi) padhne ka ek hi rasta.

Niyam (idea v4 §3, §5, F-80): TOTP secret, PIN aur API key sirf encrypted store se aate hain:
server par systemd ke `LoadCredentialEncrypted=` se decrypt hokar `$CREDENTIALS_DIRECTORY` mein.
Kabhi env variable, repo, log, Dashboard ya chat mein nahi. `Secret` ka print hamesha `****` dikhata hai.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Final, Protocol

_NAME = re.compile(r"^[a-z0-9_]{1,64}$")

# Bot ko chahiye wale secrets ki FILE ke naam (kimat kabhi code mein nahi).
UPSTOX_API_KEY: Final = "upstox_api_key"
UPSTOX_TOTP_SECRET: Final = "upstox_totp_secret"  # noqa: S105 (file ka naam, kimat nahi)
UPSTOX_PIN: Final = "upstox_pin"
DASHBOARD_PUSH_KEY: Final = "dashboard_push_key"


class SecretError(RuntimeError):
    """Secret nahi mila ya surakshit tareeke se nahi rakha."""


class Secret:
    """Ek chaabi. Galti se print/log ho toh bhi asli kimat nahi dikhti."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        if not value:
            raise SecretError("khaali secret")
        self._value = value

    def reveal(self) -> str:
        """Asli kimat. Sirf us jagah bulao jahan broker ko bhejna ho."""
        return self._value

    def __repr__(self) -> str:
        return "Secret(****)"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:  # galti se compare/log na ho
        return NotImplemented

    __hash__ = None  # type: ignore[assignment]


class SecretStore(Protocol):
    def get(self, name: str) -> Secret: ...


class CredentialsDirStore:
    """systemd credentials directory se secrets padhta hai."""

    def __init__(self, directory: str | Path | None = None) -> None:
        d = directory if directory is not None else os.environ.get("CREDENTIALS_DIRECTORY")
        if not d:
            raise SecretError("CREDENTIALS_DIRECTORY set nahi (service systemd credentials ke bina chali?)")
        self._dir = Path(d)

    def get(self, name: str) -> Secret:
        if not _NAME.fullmatch(name):
            raise SecretError(f"secret ka naam galat: {name!r}")
        path = self._dir / name
        try:
            st = path.lstat()
        except FileNotFoundError:
            raise SecretError(f"secret '{name}' nahi mila") from None
        if not stat.S_ISREG(st.st_mode):
            raise SecretError(f"secret '{name}' normal file nahi (symlink?)")
        if st.st_mode & 0o077:
            raise SecretError(f"secret '{name}' ki permission bahut khuli hai (sirf owner padh sake)")
        value = path.read_text(encoding="utf-8").strip()
        return Secret(value)


class MemoryStore:
    """Sirf tests ke liye."""

    def __init__(self, values: dict[str, str]) -> None:
        self._values = dict(values)

    def get(self, name: str) -> Secret:
        if name not in self._values:
            raise SecretError(f"secret '{name}' nahi mila")
        return Secret(self._values[name])
