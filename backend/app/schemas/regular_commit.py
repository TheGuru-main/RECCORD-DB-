"""RECCORD DB regular commit schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegularCommitCreate(BaseModel):
    """Schema for creating a regular-user commit."""

    user_id: uuid.UUID
    object_id: uuid.UUID
    narration_id: uuid.UUID
    status: str = "active"


class RegularCommitRead(BaseModel):
    """Schema returned for a regular-user commit."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    object_id: uuid.UUID
    narration_id: uuid.UUID
    status: str
    created_at: datetime
