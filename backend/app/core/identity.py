"""Canonical account identity validation."""

from __future__ import annotations

import re

_PHONE_UID = re.compile(r"\+[1-9][0-9]{7,14}\Z")


def require_phone_uid(value: str, *, field: str = "phone") -> str:
    """Validate an international phone uID without rewriting its value."""
    if not isinstance(value, str) or not _PHONE_UID.fullmatch(value):
        raise ValueError(
            f"{field} must be a full international phone identity, "
            "starting with + and containing digits only"
        )
    return value
