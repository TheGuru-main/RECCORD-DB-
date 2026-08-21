"""RECCORD DB regular commit version schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegularCommitVersionCreate(BaseModel):
    """Schema for recording a regular commit version."""

    commit_id: uuid.UUID
    version: int
    snapshot: dict


class RegularCommitVersionRead(BaseModel):
    """Schema returned for a regular commit version."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    commit_id: uuid.UUID
    version: int
    snapshot: dict
    created_at: datetime
