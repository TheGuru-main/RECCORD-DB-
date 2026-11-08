"""RECCORD DB authentication API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.account_auth_service import (
    login_organisation,
    login_regular_user,
    signup_organisation,
    signup_regular_user,
)
from app.services.worker_credential_service import (
    get_worker_registration_roles,
    login_worker,
    register_worker,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegularSignupRequest(BaseModel):
    name: str
    phone: str
    password: str
    language: str | None = "en"


class RegularLoginRequest(BaseModel):
    phone: str | None = None
    username: str | None = None
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


class WorkerRolesRequest(BaseModel):
    worker_credential: str = Field(min_length=1)


class WorkerRegisterRequest(BaseModel):
    worker_credential: str = Field(min_length=1)
    worker_phone: str
    worker_password: str
    name: str
    role: str


class WorkerLoginRequest(BaseModel):
    worker_phone: str
    worker_password: str


def _value(value):
    if isinstance(value, (UUID, datetime, date, Decimal)):
        return str(value)
    return value


def safe_user(user) -> dict:
    fields = (
        "id", "username", "name", "phone", "account_type",
        "organisation_id", "status", "created_at", "updated_at",
    )
    return {field: _value(getattr(user, field)) for field in fields}


def safe_organisation(organisation) -> dict:
    fields = (
        "id", "business_name", "display_name", "country", "phone",
        "language", "created_at", "updated_at",
    )
    return {field: _value(getattr(organisation, field)) for field in fields}


def safe_worker(worker) -> dict:
    fields = (
        "id", "user_id", "organisation_id", "role", "status",
        "created_at", "updated_at",
    )
    return {field: _value(getattr(worker, field)) for field in fields}


def safe_role(role) -> dict:
    fields = ("id", "name", "active", "created_at", "updated_at")
    return {field: _value(getattr(role, field)) for field in fields}


def safe_placement(placement) -> dict:
    if placement is None:
        return {}
    return {
        "kind": getattr(placement, "kind", None),
        "account_type": getattr(placement, "account_type", None),
        "account_uid": getattr(placement, "account_uid", None),
        "label": getattr(placement, "label", None),
        "L": getattr(placement, "L", None),
        "S": getattr(placement, "S", None),
        "c": getattr(placement, "c", None),
        "start_row": getattr(placement, "start_row", None),
        "start_col": getattr(placement, "start_col", None),
        "cell_index": getattr(placement, "cell_index", None),
        "key": getattr(placement, "key", None),
        "alphabet_len": getattr(placement, "alphabet_len", None),
        "language": getattr(placement, "language", None),
    }


@router.post("/regular/signup")
def regular_signup(payload: RegularSignupRequest, db: Session = Depends(get_db)):
    try:
        result = signup_regular_user(
            db,
            name=payload.name,
            phone=payload.phone,
            password=payload.password,
            language=payload.language or "en",
        )
        db.commit()
        db.refresh(result.user)
        return {
            "account_type": "regular",
            "user": safe_user(result.user),
            "placement": safe_placement(result.placement),
            "access_token": result.access_token,
            "token_type": "bearer",
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/regular/login")
def regular_login(payload: RegularLoginRequest, db: Session = Depends(get_db)):
    result = login_regular_user(
        db,
        username=payload.username,
        phone=payload.phone,
        password=payload.password,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid phone number or password",
        )
    return {
        "account_type": "regular",
        "user": safe_user(result.user),
        "access_token": result.access_token,
        "token_type": "bearer",
    }


@router.post("/organisation/signup")
def organisation_signup(payload: OrganisationSignupRequest, db: Session = Depends(get_db)):
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
            "organisation": safe_organisation(result.organisation),
            "worker_credential": result.worker_credential,
            "placement": safe_placement(result.placement),
            "access_token": result.access_token,
            "token_type": "bearer",
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/organisation/login")
def organisation_login(payload: OrganisationLoginRequest, db: Session = Depends(get_db)):
    result = login_organisation(db, phone=payload.phone, password=payload.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid phone number or password",
        )
    return {
        "account_type": "organisation",
        "organisation": safe_organisation(result.organisation),
        "access_token": result.access_token,
        "token_type": "bearer",
    }


@router.post("/worker/roles")
def worker_roles(payload: WorkerRolesRequest, db: Session = Depends(get_db)):
    try:
        result = get_worker_registration_roles(
            db, worker_credential=payload.worker_credential
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid Worker Credential",
        ) from None
    return {
        "account_type": "worker_registration",
        "organisation": safe_organisation(result.organisation),
        "roles": [safe_role(role) for role in result.roles],
    }


@router.post("/worker/register")
def worker_register(payload: WorkerRegisterRequest, db: Session = Depends(get_db)):
    try:
        result = register_worker(
            db,
            worker_credential=payload.worker_credential,
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
            "user": safe_user(result.user),
            "worker": safe_worker(result.worker),
            "organisation": safe_organisation(result.organisation),
            "placement": safe_placement(result.placement),
            "registration_status": "pending",
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/worker/login")
def worker_login(payload: WorkerLoginRequest, db: Session = Depends(get_db)):
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
        "user": safe_user(result.user),
        "worker": safe_worker(result.worker),
        "organisation": safe_organisation(result.organisation),
        "access_token": result.access_token,
        "token_type": "bearer",
    }
