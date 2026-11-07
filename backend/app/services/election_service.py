"""RECCORD DB E-Voting election service."""

from __future__ import annotations

import secrets
import string
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.election import Election


def _generate_election_id(length: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_election(
    db: Session,
    *,
    title: str,
    description: str | None,
    election_type: str,
    level: str,
    host_name: str,
    host_phone: str,
    host_photo_url: str | None = None,
    host_identity_number: str | None = None,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
) -> Election:
    if election_type not in ("government", "institution"):
        raise ValueError("election_type must be 'government' or 'institution'")

    election = Election(
        election_id=_generate_election_id(),
        title=title.strip(),
        description=description,
        election_type=election_type,
        level=level.strip(),
        total_candidates=0,
        host_name=host_name.strip(),
        host_phone=host_phone.strip(),
        host_photo_url=host_photo_url,
        host_identity_number=host_identity_number,
        status="draft",
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db.add(election)
    db.flush()
    return election


def add_candidate(
    db: Session,
    *,
    election_id: str,
    name: str,
    party: str | None = None,
    details: str | None = None,
    image_url: str | None = None,
    position: int = 0,
    country: str | None = None,
    state: str | None = None,
    lga: str | None = None,
) -> Candidate:
    election = db.scalar(select(Election).where(Election.id == election_id))
    if election is None:
        raise ValueError("election not found")

    candidate = Candidate(
        election_id=election.id,
        name=name.strip(),
        party=party,
        details=details,
        image_url=image_url,
        country=country,
        state=state,
        lga=lga,
        position=position,
    )
    db.add(candidate)
    election.total_candidates = (election.total_candidates or 0) + 1
    db.flush()
    return candidate


def publish_election(db: Session, *, election_id: str) -> Election:
    election = db.scalar(select(Election).where(Election.id == election_id))
    if election is None:
        raise ValueError("election not found")
    if election.total_candidates < 1:
        raise ValueError("election must have at least one candidate")
    election.status = "published"
    db.flush()
    return election


def get_election_by_credential(db: Session, *, election_id: str) -> Election | None:
    return db.scalar(select(Election).where(Election.election_id == election_id))


def list_host_elections(db: Session, *, host_phone: str) -> list[Election]:
    return list(
        db.scalars(select(Election).where(Election.host_phone == host_phone))
    )
