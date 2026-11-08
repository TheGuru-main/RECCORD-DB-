"""RECCORD DB GSP placement — phone uID + object name only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.identity import require_phone_uid

AccountType = Literal["regular", "organisation"]

GRID_ROWS = 54
GRID_COLS = 64


@dataclass(frozen=True)
class GSPPlacement:
    account_type: AccountType
    account_uid: str          # always phone uID
    normalized_name: str
    key: str
    start_row: int
    col: int
    cell_index: int


def normalize_name(name: str) -> str:
    normalized = "".join(name.split())
    if not normalized:
        raise ValueError("name must not be empty")
    return normalized


def compute_start_row_col(
    normalized_name: str,
    phone_uid: str,
    *,
    rows: int = GRID_ROWS,
    cols: int = GRID_COLS,
) -> tuple[int, int, int]:
    """Deterministic Startrow + column from object name + phone uID only."""
    seed = f"{normalized_name}:{phone_uid}"
    h = 0
    for ch in seed:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    cell_index = h % (rows * cols)
    start_row = cell_index // cols
    col = cell_index % cols
    return start_row, col, cell_index


def gsp_place(
    *,
    account_type: AccountType,
    account_uid: str,
    name: str,
) -> GSPPlacement:
    if account_type not in ("regular", "organisation"):
        raise ValueError("unsupported account_type")

    phone = require_phone_uid(account_uid, field="account_uid")
    normalized_name = normalize_name(name)
    start_row, col, cell_index = compute_start_row_col(normalized_name, phone)
    key = f"{normalized_name}:{phone}"

    return GSPPlacement(
        account_type=account_type,
        account_uid=phone,
        normalized_name=normalized_name,
        key=key,
        start_row=start_row,
        col=col,
        cell_index=cell_index,
    )
