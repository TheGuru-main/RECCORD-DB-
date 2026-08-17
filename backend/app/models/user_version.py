"""RECCORD DB user version model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserVersion(Base):
    """Immutable version of a user's recorded details."""

    __tablename__ = "user_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    account_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )