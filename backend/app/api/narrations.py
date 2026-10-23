"""Authenticated narration API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.authentication import (
    AuthenticatedPrincipal,
    get_current_principal,
)
from app.core.database import get_db
from app.schemas.narration import NarrationCreate, NarrationRead
from app.schemas.narration_api import NarrationCreateRequest
from app.services.narration_service import (
    create_narration,
    get_narration,
)
from app.services.object_service import get_object


router = APIRouter(prefix="/narrations", tags=["narrations"])


def _require_account_context(
    principal: AuthenticatedPrincipal,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """Return the authenticated account's ownership context."""

    if principal.account_type == "regular" and principal.user is not None:
        return principal.user.id, None

    if (
        principal.account_type == "organisation"
        and principal.organisation is not None
    ):
        return None, principal.organisation.id

    # Workers remain blocked until their organisation's role permissions
    # are checked by an authoritative backend permission service.
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Narration access is not enabled for this account role",
    )


@router.post(
    "",
    response_model=NarrationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_narration_endpoint(
    payload: NarrationCreateRequest,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> NarrationRead:
    """Create a narration attached to an object owned by the account."""

    owner_user_id, organisation_id = _require_account_context(principal)

    object_record = get_object(
        db,
        object_id=payload.object_id,
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )

    if object_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object not found",
        )

    data = NarrationCreate(
        object_id=object_record.id,
        content=payload.content,
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )

    try:
        record = create_narration(db, data=data)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise


@router.get(
    "/{narration_id}",
    response_model=NarrationRead,
)
def get_narration_endpoint(
    narration_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> NarrationRead:
    """Retrieve narration only within the authenticated account context."""

    owner_user_id, organisation_id = _require_account_context(principal)

    record = get_narration(
        db,
        narration_id=narration_id,
        owner_user_id=owner_user_id,
        organisation_id=organisation_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Narration not found",
        )

    return record
