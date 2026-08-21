"""RECCORD DB organisation commit version schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganisationCommitVersionCreate(BaseModel):
    """Schema for recording an organisation commit version."""

    commit_id: uuid.UUID
    version: int
    snapshot: dict


class OrganisationCommitVersionRead(BaseModel):
    """Schema returned for an organisation commit version."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    commit_id: uuid.UUID
    version: int
    snapshot: dict
    created_at: datetime
