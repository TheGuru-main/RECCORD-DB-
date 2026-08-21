"""RECCORD DB object schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class ObjectBase(BaseModel):
    """Shared object fields."""

    name: str
    status: str = "active"


class ObjectCreate(ObjectBase):
    """Schema for creating an object in one account context."""

    owner_user_id: uuid.UUID | None = None
    organisation_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_owner_context(self) -> "ObjectCreate":
        """Require exactly one ownership context."""

        has_user = self.owner_user_id is not None
        has_organisation = self.organisation_id is not None

        if has_user == has_organisation:
            raise ValueError(
                "exactly one of owner_user_id or organisation_id is required"
            )

        return self


class ObjectRead(ObjectBase):
    """Schema returned for an object."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID | None
    organisation_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
