"""RECCORD DB narration schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class NarrationBase(BaseModel):
    """Shared narration fields."""

    content: str


class NarrationCreate(NarrationBase):
    """Schema for creating narration within one account context."""

    organisation_id: uuid.UUID | None = None
    owner_user_id: uuid.UUID | None = None
    object_id: uuid.UUID

    @model_validator(mode="after")
    def validate_owner_context(self) -> "NarrationCreate":
        """Require exactly one ownership context."""

        has_user = self.owner_user_id is not None
        has_organisation = self.organisation_id is not None

        if has_user == has_organisation:
            raise ValueError(
                "exactly one of owner_user_id or organisation_id is required"
            )

        return self


class NarrationRead(NarrationBase):
    """Schema returned for a narration."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisation_id: uuid.UUID | None
    owner_user_id: uuid.UUID | None
    object_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
