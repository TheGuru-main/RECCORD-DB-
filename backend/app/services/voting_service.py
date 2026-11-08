"""RECCORD DB E-Voting voter signup and vote casting service."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.election import Election
from app.models.election_voter import ElectionVoter
from app.models.user import User
from app.models.vote import Vote
from app.services.placement_service import place_vote


def _phone_exists_in_main_reccord(db: Session, phone: str) -> bool:
    return db.scalar(select(User).where(User.phone == phone)) is not None


def register_voter(
    db: Session,
    *,
    election_credential: str,
    full_name: str,
    phone: str,
    identity_number: str,
    photo_url: str | None = None,
    country: str | None = None,
    state: str | None = None,
    lga: str | None = None,
) -> ElectionVoter:
    phone = phone.strip()
    full_name = full_name.strip()
    identity_number = identity_number.strip()

    if _phone_exists_in_main_reccord(db, phone):
        raise ValueError("this phone number is already registered on RECCORD DB")

    election = db.scalar(select(Election).where(Election.election_id == election_credential))
    if election is None:
        raise ValueError("invalid election ID")
    if election.status not in ("published", "active"):
        raise ValueError("election is not open for registration")

    existing_voter = db.scalar(
        select(ElectionVoter).where(
            ElectionVoter.election_id == election.id,
            ElectionVoter.phone == phone,
        )
    )
    if existing_voter is not None:
        raise ValueError("this phone number has already registered for this election")

    voter = ElectionVoter(
        election_id=election.id,
        full_name=full_name,
        phone=phone,
        identity_number=identity_number,
        photo_url=photo_url,
        country=country,
        state=state,
        lga=lga,
        has_voted=False,
    )
    db.add(voter)
    db.flush()
    return voter


def list_election_voters(db: Session, *, election_id: str) -> list[ElectionVoter]:
    return list(
        db.scalars(
            select(ElectionVoter)
            .where(ElectionVoter.election_id == election_id)
            .order_by(ElectionVoter.created_at.desc())
        )
    )


def get_voter(db: Session, *, voter_id: str) -> ElectionVoter | None:
    return db.get(ElectionVoter, voter_id)


def cast_vote(db: Session, *, voter_id: str, candidate_id: str) -> Vote:
    voter = db.get(ElectionVoter, voter_id)
    if voter is None:
        raise ValueError("voter not found")
    if voter.has_voted:
        raise ValueError("voter has already voted")

    election = db.get(Election, voter.election_id)
    if election is None:
        raise ValueError("election not found")
    if election.status not in ("published", "active"):
        raise ValueError("election is not open for voting")

    candidate = db.scalar(
        select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.election_id == election.id,
        )
    )
    if candidate is None:
        raise ValueError("candidate not found in this election")

    placement = place_vote(voter_name=voter.full_name, voter_phone=voter.phone)
    vote = Vote(
        election_id=election.id,
        candidate_id=candidate.id,
        voter_id=voter.id,
        voter_name=voter.full_name,
        voter_phone=voter.phone,
        grid_position=placement.primary_key,
    )
    db.add(vote)
    voter.has_voted = True
    db.flush()
    return vote


def get_results(db: Session, *, election_id: str) -> list[dict]:
    rows = db.execute(
        select(
            Candidate.id,
            Candidate.name,
            Candidate.party,
            func.count(Vote.id).label("votes"),
        )
        .outerjoin(Vote, Vote.candidate_id == Candidate.id)
        .where(Candidate.election_id == election_id)
        .group_by(Candidate.id, Candidate.name, Candidate.party)
        .order_by(func.count(Vote.id).desc())
    ).all()
    return [
        {
            "candidate_id": str(row.id),
            "name": row.name,
            "party": row.party,
            "votes": row.votes,
        }
        for row in rows
    ]
