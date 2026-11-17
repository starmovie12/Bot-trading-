"""Har test mein network band. M0 mein kisi broker ya internet se connection nahi hona chahiye."""

import os

os.environ.pop("UPSTOX_RO_TOKEN", None)  # MISSION V19 C3: this process never holds the token

import socket
from collections.abc import Iterator

import pytest


class NetworkBlockedError(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    def guard(*_args: object, **_kwargs: object) -> None:
        raise NetworkBlockedError("Tests mein network allowed nahi hai")

    monkeypatch.setattr(socket.socket, "connect", guard)
    monkeypatch.setattr(socket, "create_connection", guard)
    yield
