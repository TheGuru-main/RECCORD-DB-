"""RECCORD DB worker schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkerBase(BaseModel):
    """Shared worker fields."""

    user_id: uuid.UUID
    organisation_id: uuid.UUID
    role: str
    status: str = "active"


class WorkerCreate(WorkerBase):
    """Schema for creating a worker account."""

    pass


class WorkerRead(WorkerBase):
    """Schema returned for a worker account."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
