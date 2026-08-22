"""RECCORD DB access-token service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.config import settings


def create_access_token(
    *,
    subject: str,
    account_type: str,
    organisation_id: str | None = None,
) -> str:
    """Create a signed RECCORD DB access token."""

    if not subject.strip():
        raise ValueError("subject must not be empty")

    if not account_type.strip():
        raise ValueError("account_type must not be empty")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": subject,
        "account_type": account_type,
        "organisation_id": organisation_id,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a RECCORD DB access token."""

    if not token.strip():
        raise ValueError("token must not be empty")

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
