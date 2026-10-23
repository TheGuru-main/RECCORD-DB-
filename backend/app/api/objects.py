"""Authenticated object API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.authentication import (
    AuthenticatedPrincipal,
    get_current_principal,
)
from app.core.database import get_db
from app.schemas.object import ObjectCreate, ObjectRead
from app.schemas.object_api import ObjectCreateRequest
from app.services.object_service import create_object, get_object


router = APIRouter(prefix="/objects", tags=["objects"])


def _require_account_context(
    principal: AuthenticatedPrincipal,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """Return the trusted ownership context for a permitted account."""

    if principal.account_type == "regular" and principal.user is not None:
        return principal.user.id, None

    if (
        principal.account_type == "organisation"
        and principal.organisation is not None
    ):
        return None, principal.organisation.id

    # Worker permissions must be checked against the organisation's
    # authoritative role and permission configuration before access is allowed.
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Object access is not enabled for this account role",
    )


@router.post(
    "",
    response_model=ObjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_object_endpoint(
    payload: ObjectCreateRequest,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> ObjectRead:
    """Create an object owned by the authenticated account."""

    owner_user_id, organisation_id = _require_account_context(principal)

    data = ObjectCreate(
        name=payload.name,
        status="active",
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )

    try:
        record = create_object(db, data=data)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{object_id}",
    response_model=ObjectRead,
)
def get_object_endpoint(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> ObjectRead:
    """Retrieve an object only within the authenticated account context."""

    owner_user_id, organisation_id = _require_account_context(principal)

    record = get_object(
        db,
        object_id=object_id,
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object not found",
        )

    return record
