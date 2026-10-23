"""RECCORD DB placement service."""

from __future__ import annotations

from app.core.gsp import GSPPlacement, gsp_place


def place_regular_commit(
    *,
    account_uid: str,
    object_name: str,
) -> GSPPlacement:
    """Calculate placement using the regular account's established uID."""

    return gsp_place(
        account_type="regular",
        account_uid=account_uid,
        name=object_name,
    )


def place_organisation_commit(
    *,
    account_uid: str,
    object_name: str,
) -> GSPPlacement:
    """Calculate placement using the organisation's established uID."""

    return gsp_place(
        account_type="organisation",
        account_uid=account_uid,
        name=object_name,
    )
