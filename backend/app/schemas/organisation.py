"""RECCORD DB organisation schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrganisationBase(BaseModel):
    """Shared organisation fields."""

    business_name: str
    display_name: str
    country: str
    phone: str
    language: str = "en"


class OrganisationCreate(OrganisationBase):
    """Schema for creating an organisation account."""

    password: str


class OrganisationRead(OrganisationBase):
    """Schema returned for an organisation account."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    worker_id: str
    created_at: datetime
    updated_at: datetime
