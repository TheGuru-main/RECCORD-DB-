"""RECCORD DB E-Voting Vote model (Immutable)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Vote(Base):
    """An immutable vote.

    Placement on the grid uses voter Name + uID (phone).
    Vote counting is a normal tally per candidate.
    """

    __tablename__ = "votes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    election_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    voter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("election_voters.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # one vote per voter per election
    )

    # Used for GSP grid placement identity
    voter_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    voter_phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    # GSP placement reference (optional, can be filled by placement service)
    grid_position: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
