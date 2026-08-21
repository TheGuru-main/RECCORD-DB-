"""RECCORD DB organisation commit schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganisationCommitCreate(BaseModel):
    """Schema for creating an organisation commit."""

    organisation_id: uuid.UUID
    object_id: uuid.UUID
    narration_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    status: str = "active"


class OrganisationCommitRead(BaseModel):
    """Schema returned for an organisation commit."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID
    object_id: uuid.UUID
    narration_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    status: str
    created_at: datetime
