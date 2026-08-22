"""RECCORD DB narration service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.narration import Narration
from app.schemas.narration import NarrationCreate


def create_narration(
    db: Session,
    *,
    data: NarrationCreate,
) -> Narration:
    """Create narration inside one account context."""

    record = Narration(
        organisation_id=data.organisation_id,
        owner_user_id=data.owner_user_id,
        object_id=data.object_id,
        content=data.content,
    )

    db.add(record)
    db.flush()

    return record


def get_narration(
    db: Session,
    *,
    narration_id: uuid.UUID,
    owner_user_id: uuid.UUID | None = None,
    organisation_id: uuid.UUID | None = None,
) -> Narration | None:
    """Retrieve narration only inside its owning account context."""

    if (owner_user_id is None) == (organisation_id is None):
        raise ValueError(
            "exactly one account context is required"
        )

    statement = select(Narration).where(
        Narration.id == narration_id,
    )

    if owner_user_id is not None:
        statement = statement.where(
            Narration.owner_user_id == owner_user_id,
        )
    else:
        statement = statement.where(
            Narration.organisation_id == organisation_id,
        )

    return db.scalar(statement)

