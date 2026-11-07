"""Election host credentials (cross-device) stored on B2 host partition."""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.services.b2_service import b2_service

logger = logging.getLogger(__name__)


def _norm_phone(phone: str) -> str:
    return re.sub(r"\s+", "", (phone or "").strip())


def _profile_key(host_phone: str) -> str:
    return f"tenants/election-host/{_norm_phone(host_phone)}/profile.json"


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()


def register_host(
    *,
    host_phone: str,
    host_name: str,
    password: str,
    identity_number: str | None = None,
) -> dict[str, Any]:
    phone = _norm_phone(host_phone)
    if not phone or not password or len(password) < 6:
        raise ValueError("phone and password (min 6 chars) required")

    existing = b2_service.get_json(_profile_key(phone))
    if existing and existing.get("password_hash"):
        raise ValueError("host already registered for this phone — use Host login")

    salt = hashlib.sha256(f"{phone}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:32]
    profile = {
        "host_phone": phone,
        "host_name": (host_name or "").strip(),
        "identity_number": identity_number,
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ok = b2_service.put_json(_profile_key(phone), profile)
    if not ok and not b2_service.enabled:
        # Allow local/dev without B2: still return profile (caller stores session)
        logger.warning("B2 disabled — host profile not persisted to object storage")
    return {
        "host_phone": phone,
        "host_name": profile["host_name"],
        "registered": True,
    }


def login_host(*, host_phone: str, password: str) -> dict[str, Any]:
    phone = _norm_phone(host_phone)
    profile = b2_service.get_json(_profile_key(phone))
    if profile is None:
        raise ValueError("host not found — complete Host signup first")
    salt = profile.get("salt") or ""
    expected = profile.get("password_hash") or ""
    actual = _hash_password(password, salt)
    if not hmac.compare_digest(actual, expected):
        raise ValueError("invalid host phone or password")
    return {
        "host_phone": phone,
        "host_name": profile.get("host_name") or "",
        "identity_number": profile.get("identity_number"),
    }
