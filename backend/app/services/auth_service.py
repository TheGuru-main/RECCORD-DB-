"""RECCORD DB authentication service."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""

    if not password:
        raise ValueError("password must not be empty")

    salt = secrets.token_bytes(32)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )

    return (
        f"pbkdf2_sha256$310000$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Verify a password against a stored PBKDF2 hash."""

    if not password or not password_hash:
        return False

    try:
        algorithm, iterations, salt_hex, digest_hex = (
            password_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)

        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(
            actual_digest,
            expected_digest,
        )

    except (ValueError, TypeError):
        return False
