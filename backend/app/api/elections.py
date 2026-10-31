"""RECCORD DB E-Voting API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.election_service import (
    add_candidate,
    create_election,
    get_election_by_credential,
    list_host_elections,
    publish_election,
)
from app.services.voting_service import (
    cast_vote,
    get_results,
    register_voter,
)

router = APIRouter(prefix="/elections", tags=["elections"])


# ---------- Schemas ----------

class CreateElectionRequest(BaseModel):
    title: str = Field(min_length=1)
    description: Optional[str] = None
    election_type: str                          # government | institution
    level: str
    host_name: str
    host_phone: str
    host_photo_url: Optional[str] = None
    host_identity_number: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class AddCandidateRequest(BaseModel):
    election_id: str
    name: str = Field(min_length=1)
    party: Optional[str] = None
    details: Optional[str] = None
    image_url: Optional[str] = None
    position: int = 0


class RegisterVoterRequest(BaseModel):
    election_credential: str
    full_name: str = Field(min_length=1)
    phone: str = Field(min_length=7)
    identity_number: str = Field(min_length=1)
    photo_url: Optional[str] = None


class CastVoteRequest(BaseModel):
    voter_id: str
    candidate_id: str


# ---------- Host endpoints ----------

@router.post("/create")
def create_election_endpoint(
    payload: CreateElectionRequest,
    db: Session = Depends(get_db),
):
    try:
        election = create_election(
            db,
            title=payload.title,
            description=payload.description,
            election_type=payload.election_type,
            level=payload.level,
            host_name=payload.host_name,
            host_phone=payload.host_phone,
            host_photo_url=payload.host_photo_url,
            host_identity_number=payload.host_identity_number,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )
        db.commit()
        db.refresh(election)
        return {
            "id": str(election.id),
            "election_id": election.election_id,
            "title": election.title,
            "status": election.status,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/candidates")
def add_candidate_endpoint(
    payload: AddCandidateRequest,
    db: Session = Depends(get_db),
):
    try:
        candidate = add_candidate(
            db,
            election_id=payload.election_id,
            name=payload.name,
            party=payload.party,
            details=payload.details,
            image_url=payload.image_url,
            position=payload.position,
        )
        db.commit()
        db.refresh(candidate)
        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "party": candidate.party,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{election_id}/publish")
def publish_election_endpoint(
    election_id: str,
    db: Session = Depends(get_db),
):
    try:
        election = publish_election(db, election_id=election_id)
        db.commit()
        db.refresh(election)
        return {
            "id": str(election.id),
            "election_id": election.election_id,
            "status": election.status,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/host/{host_phone}")
def list_host_elections_endpoint(
    host_phone: str,
    db: Session = Depends(get_db),
):
    elections = list_host_elections(db, host_phone=host_phone)
    return {
        "elections": [
            {
                "id": str(e.id),
                "election_id": e.election_id,
                "title": e.title,
                "status": e.status,
                "total_candidates": e.total_candidates,
            }
            for e in elections
        ]
    }


@router.get("/{election_id}/results")
def get_results_endpoint(
    election_id: str,
    db: Session = Depends(get_db),
):
    results = get_results(db, election_id=election_id)
    return {"results": results}


# ---------- Voter endpoints ----------

@router.get("/credential/{election_credential}")
def get_election_by_credential_endpoint(
    election_credential: str,
    db: Session = Depends(get_db),
):
    election = get_election_by_credential(db, election_id=election_credential)
    if election is None:
        raise HTTPException(status_code=404, detail="election not found")
    return {
        "id": str(election.id),
        "election_id": election.election_id,
        "title": election.title,
        "election_type": election.election_type,
        "level": election.level,
        "status": election.status,
    }


@router.post("/voters/register")
def register_voter_endpoint(
    payload: RegisterVoterRequest,
    db: Session = Depends(get_db),
):
    try:
        voter = register_voter(
            db,
            election_credential=payload.election_credential,
            full_name=payload.full_name,
            phone=payload.phone,
            identity_number=payload.identity_number,
            photo_url=payload.photo_url,
        )
        db.commit()
        db.refresh(voter)
        return {
            "voter_id": str(voter.id),
            "full_name": voter.full_name,
            "has_voted": voter.has_voted,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/vote")
def cast_vote_endpoint(
    payload: CastVoteRequest,
    db: Session = Depends(get_db),
):
    try:
        vote = cast_vote(
            db,
            voter_id=payload.voter_id,
            candidate_id=payload.candidate_id,
        )
        db.commit()
        db.refresh(vote)
        return {
            "vote_id": str(vote.id),
            "candidate_id": str(vote.candidate_id),
            "voter_name": vote.voter_name,
            "created_at": str(vote.created_at),
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{election_id}/candidates")
def list_candidates_endpoint(
    election_id: str,
    db: Session = Depends(get_db),
):
    from app.models.candidate import Candidate
    from sqlalchemy import select

    candidates = list(
        db.scalars(
            select(Candidate)
            .where(Candidate.election_id == election_id)
            .order_by(Candidate.position)
        )
    )
    return {
        "candidates": [
            {
                "id": str(c.id),
                "name": c.name,
                "party": c.party,
                "details": c.details,
                "image_url": c.image_url,
            }
            for c in candidates
        ]
    }
