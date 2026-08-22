"""RECCORD DB authentication API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.account_auth_service import (
    login_organisation,
    login_regular_user,
    signup_organisation,
    signup_regular_user,
)
from app.services.worker_credential_service import (
    login_worker,
    register_worker,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


class RegularSignupRequest(BaseModel):
    username: str
    name: str
    phone: str | None = None
    password: str


class RegularLoginRequest(BaseModel):
    username: str
    password: str


class OrganisationSignupRequest(BaseModel):
    business_name: str
    display_name: str
    country: str
    phone: str
    language: str = "en"
    password: str


class OrganisationLoginRequest(BaseModel):
    phone: str
    password: str


class WorkerRegisterRequest(BaseModel):
    organisation_full_name: str
    organisation_id: uuid.UUID
    worker_id: str
    worker_phone: str
    worker_password: str
    name: str
    role: str


class WorkerLoginRequest(BaseModel):
    worker_phone: str
    worker_password: str


@router.post("/regular/signup")
def regular_signup(
    payload: RegularSignupRequest,
    db: Session = Depends(get_db),
):
    """Create a regular-user account and authenticate it."""

    try:
        result = signup_regular_user(
            db,
            username=payload.username,
            name=payload.name,
            phone=payload.phone,
            password=payload.password,
        )

        db.commit()
        db.refresh(result.user)

        return {
            "account_type": "regular",
            "user": result.user,
            "placement": result.placement,
            "access_token": result.access_token,
            "token_type": "bearer",
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/regular/login")
def regular_login(
    payload: RegularLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate a regular-user account."""

    result = login_regular_user(
        db,
        username=payload.username,
        password=payload.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )

    return {
        "account_type": "regular",
        "user": result.user,
        "access_token": result.access_token,
        "token_type": "bearer",
    }


@router.post("/organisation/signup")
def organisation_signup(
    payload: OrganisationSignupRequest,
    db: Session = Depends(get_db),
):
    """Create an organisation account and authenticate it."""

    try:
        result = signup_organisation(
            db,
            business_name=payload.business_name,
            display_name=payload.display_name,
            country=payload.country,
            phone=payload.phone,
            language=payload.language,
            password=payload.password,
        )

        db.commit()
        db.refresh(result.organisation)

        return {
            "account_type": "organisation",
            "organisation": result.organisation,
            "access_token": result.access_token,
            "token_type": "bearer",
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/organisation/login")
def organisation_login(
    payload: OrganisationLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate an organisation account."""

    result = login_organisation(
        db,
        phone=payload.phone,
        password=payload.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid phone number or password",
        )

    return {
        "account_type": "organisation",
        "organisation": result.organisation,
        "access_token": result.access_token,
        "token_type": "bearer",
    }


@router.post("/worker/register")
def worker_register(
    payload: WorkerRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a worker using the organisation-issued credential."""

    try:
        result = register_worker(
            db,
            organisation_full_name=payload.organisation_full_name,
            organisation_id=payload.organisation_id,
            worker_id=payload.worker_id,
            worker_phone=payload.worker_phone,
            worker_password=payload.worker_password,
            name=payload.name,
            role=payload.role,
        )

        db.commit()

        db.refresh(result.user)
        db.refresh(result.worker)

        return {
            "account_type": "worker",
            "user": result.user,
            "worker": result.worker,
            "organisation": result.organisation,
            "placement": result.placement,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/worker/login")
def worker_login(
    payload: WorkerLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate a worker with their own phone and password."""

    result = login_worker(
        db,
        worker_phone=payload.worker_phone,
        worker_password=payload.worker_password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid worker phone number or password",
        )

    return {
        "account_type": "worker",
        "user": result.user,
        "worker": result.worker,
        "organisation": result.organisation,
        "access_token": result.access_token,
        "token_type": "bearer",
    }
