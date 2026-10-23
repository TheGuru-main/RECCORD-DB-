"""RECCORD DB GSP placement primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.identity import require_phone_uid


AccountType = Literal["regular", "organisation"]


@dataclass(frozen=True)
class GSPPlacement:
    """Calculated placement within a RECCORD DB account domain."""

    account_type: AccountType
    account_uid: str
    normalized_name: str
    key: str


def normalize_name(name: str) -> str:
    """Normalize a record name by removing whitespace."""

    normalized = "".join(name.split())
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


def gsp_place(
    *,
    account_type: AccountType,
    account_uid: str,
    name: str,
) -> GSPPlacement:
    """Calculate deterministic placement from the established account uID."""

    if account_type not in ("regular", "organisation"):
        raise ValueError("unsupported account_type")

    account_uid = require_phone_uid(account_uid, field="account_uid")
    normalized_name = normalize_name(name)
    key = f"{normalized_name}:{account_uid}"

    return GSPPlacement(
        account_type=account_type,
        account_uid=account_uid,
        normalized_name=normalized_name,
        key=key,
    )
