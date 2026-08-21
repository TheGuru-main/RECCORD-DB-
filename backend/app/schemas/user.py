"""RECCORD DB user schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    """Shared user fields."""

    username: str
    name: str
    phone: str | None = None
    account_type: str


class UserCreate(UserBase):
    """Schema for creating a user account."""

    password: str
    organisation_id: uuid.UUID | None = None


class UserRead(UserBase):
    """Schema returned for an authenticated user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime
