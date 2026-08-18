"""RECCORD DB organisation/tenant model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Organisation(Base):
    """Organisation tenant and its admin account."""

    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="en",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # One organisation-wide worker registration identity.
    # This is shared by every worker belonging to this organisation.
    worker_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )

    worker_registration_credential_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )