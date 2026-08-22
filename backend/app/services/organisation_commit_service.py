"""RECCORD DB organisation commit service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.narration import Narration
from app.models.object import ObjectRecord
from app.models.organisation_commit import OrganisationCommit
from app.schemas.organisation_commit import OrganisationCommitCreate


def create_organisation_commit(
    db: Session,
    *,
    data: OrganisationCommitCreate,
) -> OrganisationCommit:
    """Create a commit inside an organisation's shared context."""

    object_record = db.scalar(
        select(ObjectRecord).where(
            ObjectRecord.id == data.object_id,
            ObjectRecord.organisation_id == data.organisation_id,
        )
    )

    if object_record is None:
        raise ValueError(
            "object does not belong to this organisation"
        )

    narration = db.scalar(
        select(Narration).where(
            Narration.id == data.narration_id,
            Narration.object_id == data.object_id,
            Narration.organisation_id == data.organisation_id,
        )
    )

    if narration is None:
        raise ValueError(
            "narration does not belong to this organisation's object"
        )

    commit = OrganisationCommit(
        organisation_id=data.organisation_id,
        object_id=data.object_id,
        narration_id=data.narration_id,
        user_id=data.user_id,
        role=data.role,
        status=data.status,
    )

    db.add(commit)
    db.flush()

    return commit


def get_organisation_commit(
    db: Session,
    *,
    commit_id: uuid.UUID,
    organisation_id: uuid.UUID,
) -> OrganisationCommit | None:
    """Retrieve a commit inside the organisation's shared context."""

    statement = select(OrganisationCommit).where(
        OrganisationCommit.id == commit_id,
        OrganisationCommit.organisation_id == organisation_id,
    )

    return db.scalar(statement)
