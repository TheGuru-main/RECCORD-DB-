"""RECCORD DB placement service."""

from __future__ import annotations

import uuid

from app.core.gsp import GSPPlacement, gsp_place


def place_regular_commit(
    *,
    user_id: uuid.UUID,
    object_name: str,
) -> GSPPlacement:
    """Calculate placement for a regular user's committed object."""

    return gsp_place(
        account_type="regular",
        account_id=str(user_id),
        name=object_name,
    )


def place_organisation_commit(
    *,
    organisation_id: uuid.UUID,
    object_name: str,
) -> GSPPlacement:
    """Calculate placement for an organisation's committed object."""

    return gsp_place(
        account_type="organisation",
        account_id=str(organisation_id),
        name=object_name,
    )
