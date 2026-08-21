"""RECCORD DB GSP placement primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AccountType = Literal["regular", "organisation"]


@dataclass(frozen=True)
class GSPPlacement:
    """Calculated placement within a RECCORD DB account domain."""

    account_type: AccountType
    account_id: str
    normalized_name: str
    key: str


def normalize_name(name: str) -> str:
    """Normalize a record name by removing spaces."""

    normalized = "".join(name.split())

    if not normalized:
        raise ValueError("name must not be empty")

    return normalized


def gsp_place(
    *,
    account_type: AccountType,
    account_id: str,
    name: str,
) -> GSPPlacement:
    """Calculate deterministic placement from account UUID and name."""

    if not account_id.strip():
        raise ValueError("account_id must not be empty")

    if account_type not in ("regular", "organisation"):
        raise ValueError("unsupported account_type")

    normalized_name = normalize_name(name)

    key = f"{normalized_name}:{account_id}"

    return GSPPlacement(
        account_type=account_type,
        account_id=account_id,
        normalized_name=normalized_name,
        key=key,
    )
