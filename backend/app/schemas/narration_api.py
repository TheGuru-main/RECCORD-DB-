"""Public API schemas for RECCORD DB narrations."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NarrationCreateRequest(BaseModel):
    """Client-supplied fields for creating a narration."""

    model_config = ConfigDict(extra="forbid")

    object_id: UUID
    content: str = Field(min_length=1)
