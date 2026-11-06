"""Authenticated object API routes."""

from __future__ import annotations

import logging
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
from app.services.grid_service import write_object_placement
from app.services.object_service import create_object, get_object

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/objects", tags=["objects"])


def _require_account_context(
    principal: AuthenticatedPrincipal,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    if principal.account_type == "regular" and principal.user is not None:
        return principal.user.id, None

    if (
        principal.account_type == "organisation"
        and principal.organisation is not None
    ):
        return None, principal.organisation.id

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
    """Create an object and write per-tenant GSP placement to B2."""

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
    except Exception:
        db.rollback()
        raise

    # B2 placement (non-fatal if B2 misconfigured)
    try:
        if principal.account_type == "regular" and principal.user is not None:
            account_uid = principal.user.phone or str(principal.user.id)
            write_object_placement(
                kind="regular",
                tenant_id=str(principal.user.id),
                account_uid=account_uid,
                object_id=str(record.id),
                object_name=record.name,
            )
        elif (
            principal.account_type == "organisation"
            and principal.organisation is not None
        ):
            account_uid = principal.organisation.phone or str(
                principal.organisation.id
            )
            write_object_placement(
                kind="organisation",
                tenant_id=str(principal.organisation.id),
                account_uid=account_uid,
                object_id=str(record.id),
                object_name=record.name,
            )
    except Exception as exc:
        logger.exception("B2 grid placement failed: %s", exc)

    return record


@router.get(
    "/{object_id}",
    response_model=ObjectRead,
)
def get_object_endpoint(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> ObjectRead:
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
