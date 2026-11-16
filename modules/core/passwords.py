"""Salted password hashing for the app's security mode.

Stored format: ``pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>``.
Older installs stored a bare unsalted SHA-256 hex digest; those still verify,
and callers should re-hash on successful login (``needs_rehash``).
"""
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 100_000  # ~0.1-0.3 s on a Raspberry Pi 3/4


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or password is None:
        return False
    if stored.startswith(ALGORITHM + "$"):
        try:
            _, iterations, salt_hex, digest_hex = stored.split("$")
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
            )
        except ValueError:
            return False
        return hmac.compare_digest(digest.hex(), digest_hex)
    # Legacy: unsalted SHA-256
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored)


def needs_rehash(stored: str) -> bool:
    return bool(stored) and not stored.startswith(f"{ALGORITHM}${ITERATIONS}$")
