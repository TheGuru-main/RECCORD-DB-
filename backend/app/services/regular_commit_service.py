"""RECCORD DB regular-user commit service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.narration import Narration
from app.models.object import ObjectRecord
from app.models.regular_commit import RegularCommit
from app.schemas.regular_commit import RegularCommitCreate


def create_regular_commit(
    db: Session,
    *,
    data: RegularCommitCreate,
) -> RegularCommit:
    """Create a commit inside a regular user's account context."""

    object_record = db.scalar(
        select(ObjectRecord).where(
            ObjectRecord.id == data.object_id,
            ObjectRecord.owner_user_id == data.user_id,
        )
    )

    if object_record is None:
        raise ValueError(
            "object does not belong to this user"
        )

    narration = db.scalar(
        select(Narration).where(
            Narration.id == data.narration_id,
            Narration.object_id == data.object_id,
            Narration.owner_user_id == data.user_id,
        )
    )

    if narration is None:
        raise ValueError(
            "narration does not belong to this user's object"
        )

    commit = RegularCommit(
        user_id=data.user_id,
        object_id=data.object_id,
        narration_id=data.narration_id,
        status=data.status,
    )

    db.add(commit)
    db.flush()

    return commit


def get_regular_commit(
    db: Session,
    *,
    commit_id: uuid.UUID,
    user_id: uuid.UUID,
) -> RegularCommit | None:
    """Retrieve a regular commit inside its user's account context."""

    statement = select(RegularCommit).where(
        RegularCommit.id == commit_id,
        RegularCommit.user_id == user_id,
    )

    return db.scalar(statement)
