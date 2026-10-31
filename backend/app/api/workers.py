"""RECCORD DB workers API (Admin only)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.worker_admin_service import (
    approve_worker,
    list_organisation_workers,
    list_pending_workers,
    reject_worker,
)


router = APIRouter(prefix="/workers", tags=["workers"])


class WorkerActionRequest(BaseModel):
    organisation_id: str
    worker_id: str


def _value(value):
    if isinstance(value, (UUID, datetime, date, Decimal)):
        return str(value)
    return value


def safe_worker(worker) -> dict:
    fields = (
        "id",
        "user_id",
        "organisation_id",
        "role",
        "status",
        "created_at",
        "updated_at",
    )
    return {field: _value(getattr(worker, field)) for field in fields}


@router.get("/pending/{organisation_id}")
def get_pending_workers(
    organisation_id: str,
    db: Session = Depends(get_db),
):
    """List all pending workers for an organisation."""
    workers = list_pending_workers(db, organisation_id=organisation_id)
    return {
        "organisation_id": organisation_id,
        "workers": [safe_worker(w) for w in workers],
    }


@router.get("/organisation/{organisation_id}")
def get_organisation_workers(
    organisation_id: str,
    db: Session = Depends(get_db),
):
    """List all workers belonging to an organisation."""
    workers = list_organisation_workers(db, organisation_id=organisation_id)
    return {
        "organisation_id": organisation_id,
        "workers": [safe_worker(w) for w in workers],
    }


@router.post("/approve")
def approve(
    payload: WorkerActionRequest,
    db: Session = Depends(get_db),
):
    """Admin approves a pending worker."""
    try:
        result = approve_worker(
            db,
            organisation_id=payload.organisation_id,
            worker_id=payload.worker_id,
        )
        db.commit()
        db.refresh(result.worker)

        return {
            "status": "approved",
            "worker": safe_worker(result.worker),
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/reject")
def reject(
    payload: WorkerActionRequest,
    db: Session = Depends(get_db),
):
    """Admin rejects a pending worker."""
    try:
        result = reject_worker(
            db,
            organisation_id=payload.organisation_id,
            worker_id=payload.worker_id,
        )
        db.commit()
        db.refresh(result.worker)

        return {
            "status": "rejected",
            "worker": safe_worker(result.worker),
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
