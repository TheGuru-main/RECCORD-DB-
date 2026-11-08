"""Authenticated object API routes."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.authentication import AuthenticatedPrincipal, get_current_principal
from app.core.database import get_db
from app.core.identity import require_phone_uid
from app.schemas.object import ObjectCreate, ObjectRead
from app.services.grid_service import write_object_placement
from app.services.object_service import create_object, get_object

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/objects", tags=["objects"])


class ObjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


def _require_account_context(
    principal: AuthenticatedPrincipal,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    if principal.account_type == "regular" and principal.user is not None:
        return principal.user.id, None
    if principal.account_type == "organisation" and principal.organisation is not None:
        return None, principal.organisation.id
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Object access is not enabled for this account role",
    )


@router.post("", response_model=ObjectRead, status_code=status.HTTP_201_CREATED)
def create_object_endpoint(
    payload: ObjectCreateRequest,
    db: Session = Depends(get_db),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> ObjectRead:
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

    try:
        if principal.account_type == "regular" and principal.user is not None:
            phone = require_phone_uid(principal.user.phone, field="phone")
            write_object_placement(
                kind="regular",
                tenant_id=str(principal.user.id),
                account_uid=phone,
                object_id=str(record.id),
                object_name=record.name,
                description=payload.description,
            )
        elif principal.account_type == "organisation" and principal.organisation is not None:
            phone = require_phone_uid(principal.organisation.phone, field="phone")
            write_object_placement(
                kind="organisation",
                tenant_id=str(principal.organisation.id),
                account_uid=phone,
                object_id=str(record.id),
                object_name=record.name,
                description=payload.description,
            )
    except Exception as exc:
        logger.exception("B2 grid placement failed: %s", exc)

    return record


@router.get("/{object_id}", response_model=ObjectRead)
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
        raise HTTPException(status_code=404, detail="Object not found")
    return record
