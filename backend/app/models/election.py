"""RECCORD DB E-Voting Election model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Election(Base):
    """An election created by an Election Host."""

    __tablename__ = "elections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Unique credential given to voters (like worker credential)
    election_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # government | institution
    election_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    # e.g. National, State, Local, School, Faculty, Class
    level: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    total_candidates: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Host identity (from E-Voting signup, not main RECCORD)
    host_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    host_phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    host_photo_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    host_identity_number: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",  # draft | published | active | closed
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
