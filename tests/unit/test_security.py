"""Security password hashing, verification and the settings guard."""
import hashlib
import re

import pytest

import main
from modules.core import passwords


def test_hash_is_salted_and_verifies():
    a, b = passwords.hash_password("hunter2"), passwords.hash_password("hunter2")
    assert a != b
    assert passwords.verify_password("hunter2", a)
    assert not passwords.verify_password("wrong", a)
    assert not passwords.needs_rehash(a)


def test_legacy_sha256_still_verifies():
    legacy = hashlib.sha256(b"hunter2").hexdigest()
    assert passwords.verify_password("hunter2", legacy)
    assert not passwords.verify_password("nope", legacy)
    assert passwords.needs_rehash(legacy)


def test_garbage_hash_rejected():
    assert not passwords.verify_password("x", "pbkdf2_sha256$bad")
    assert not passwords.verify_password("x", "")


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setattr(main.state, "security_mode", "lockdown")
    monkeypatch.setattr(main.state, "security_password_hash", hashlib.sha256(b"pw").hexdigest())
    monkeypatch.setattr(main.state, "save", lambda: None)

    async def no_sleep(_):
        return None
    monkeypatch.setattr(main.asyncio, "sleep", no_sleep)


@pytest.mark.asyncio
async def test_cannot_disable_security_without_password(async_client, secured):
    r = await async_client.patch("/api/settings", json={"security": {"mode": "off"}})
    assert r.status_code == 403
    assert main.state.security_mode == "lockdown"

    r = await async_client.patch("/api/settings", json={"security": {"mode": "off", "current_password": "pw"}})
    assert r.status_code == 200
    assert main.state.security_mode == "off"


@pytest.mark.asyncio
async def test_verify_upgrades_legacy_hash(async_client, secured):
    r = await async_client.post("/api/security/verify", json={"password": "bad"})
    assert r.json() == {"valid": False}
    r = await async_client.post("/api/security/verify", json={"password": "pw"})
    assert r.json() == {"valid": True}
    assert main.state.security_password_hash.startswith("pbkdf2_sha256$")


@pytest.mark.parametrize("origin,allowed", [
    ("http://dune-weaver.local", True),
    ("http://192.168.1.50:8080", True),
    ("http://10.0.0.7", True),
    ("http://172.20.1.1", True),
    ("http://localhost:5173", True),
    ("http://sandtable", True),
    ("https://evil.example.com", False),
    ("http://8.8.8.8", False),
    ("http://172.32.0.1", False),
    ("null", False),
])
def test_cors_origin_regex(origin, allowed):
    assert bool(re.fullmatch(main.LAN_ORIGIN_REGEX, origin)) is allowed
