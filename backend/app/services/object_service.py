"""RECCORD DB object service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.object import ObjectRecord
from app.schemas.object import ObjectCreate


def create_object(
    db: Session,
    *,
    data: ObjectCreate,
) -> ObjectRecord:
    """Create an object inside one account context."""

    record = ObjectRecord(
        name=data.name,
        status=data.status,
        owner_user_id=data.owner_user_id,
        organisation_id=data.organisation_id,
    )

    db.add(record)
    db.flush()

    return record


def get_object(
    db: Session,
    *,
    object_id: uuid.UUID,
    owner_user_id: uuid.UUID | None = None,
    organisation_id: uuid.UUID | None = None,
) -> ObjectRecord | None:
    """Retrieve an object only inside its owning account context."""

    if (owner_user_id is None) == (organisation_id is None):
        raise ValueError(
            "exactly one account context is required"
        )

    statement = select(ObjectRecord).where(
        ObjectRecord.id == object_id,
    )

    if owner_user_id is not None:
        statement = statement.where(
            ObjectRecord.owner_user_id == owner_user_id,
        )
    else:
        statement = statement.where(
            ObjectRecord.organisation_id == organisation_id,
        )

    return db.scalar(statement)
