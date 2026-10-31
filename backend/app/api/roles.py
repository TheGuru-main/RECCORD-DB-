"""RECCORD DB organisation roles API (Admin only)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.role_service import create_role, list_roles


router = APIRouter(prefix="/roles", tags=["roles"])


class CreateRoleRequest(BaseModel):
    organisation_id: str
    name: str = Field(min_length=1)


def _value(value):
    if isinstance(value, (UUID, datetime, date, Decimal)):
        return str(value)
    return value


def safe_role(role) -> dict:
    fields = ("id", "organisation_id", "name", "active", "created_at", "updated_at")
    return {field: _value(getattr(role, field)) for field in fields}


@router.get("/{organisation_id}")
def get_roles(
    organisation_id: str,
    db: Session = Depends(get_db),
):
    """List active roles for an organisation."""
    roles = list_roles(db, organisation_id=organisation_id)
    return {
        "organisation_id": organisation_id,
        "roles": [safe_role(r) for r in roles],
    }


@router.post("")
def create_organisation_role(
    payload: CreateRoleRequest,
    db: Session = Depends(get_db),
):
    """Admin creates a new role for the organisation."""
    try:
        role = create_role(
            db,
            organisation_id=payload.organisation_id,
            name=payload.name,
        )
        db.commit()
        db.refresh(role)

        return {
            "role": safe_role(role),
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
