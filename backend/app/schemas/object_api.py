"""Public API schemas for RECCORD DB objects."""

from pydantic import BaseModel, ConfigDict, Field


class ObjectCreateRequest(BaseModel):
    """Client-supplied fields for creating an object."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
