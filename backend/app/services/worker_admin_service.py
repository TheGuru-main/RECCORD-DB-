"""RECCORD DB worker administration service (Admin only)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organisation import Organisation
from app.models.user import User
from app.models.worker import Worker


@dataclass(frozen=True)
class WorkerApprovalResult:
    worker: Worker
    user: User
    organisation: Organisation


def list_pending_workers(
    db: Session,
    *,
    organisation_id: str,
) -> list[Worker]:
    """Return all pending workers for an organisation."""
    return list(
        db.scalars(
            select(Worker).where(
                Worker.organisation_id == organisation_id,
                Worker.status == "pending",
            )
        )
    )


def list_organisation_workers(
    db: Session,
    *,
    organisation_id: str,
) -> list[Worker]:
    """Return all workers belonging to an organisation."""
    return list(
        db.scalars(
            select(Worker).where(
                Worker.organisation_id == organisation_id,
            )
        )
    )


def approve_worker(
    db: Session,
    *,
    organisation_id: str,
    worker_id: str,
) -> WorkerApprovalResult:
    """Admin approves a pending worker."""
    worker = db.scalar(
        select(Worker).where(
            Worker.id == worker_id,
            Worker.organisation_id == organisation_id,
        )
    )

    if worker is None:
        raise ValueError("worker not found")

    if worker.status != "pending":
        raise ValueError("worker is not in pending state")

    worker.status = "approved"
    db.flush()

    user = db.get(User, worker.user_id)
    organisation = db.get(Organisation, worker.organisation_id)

    return WorkerApprovalResult(
        worker=worker,
        user=user,
        organisation=organisation,
    )


def reject_worker(
    db: Session,
    *,
    organisation_id: str,
    worker_id: str,
) -> WorkerApprovalResult:
    """Admin rejects a pending worker."""
    worker = db.scalar(
        select(Worker).where(
            Worker.id == worker_id,
            Worker.organisation_id == organisation_id,
        )
    )

    if worker is None:
        raise ValueError("worker not found")

    if worker.status != "pending":
        raise ValueError("worker is not in pending state")

    worker.status = "rejected"
    db.flush()

    user = db.get(User, worker.user_id)
    organisation = db.get(Organisation, worker.organisation_id)

    return WorkerApprovalResult(
        worker=worker,
        user=user,
        organisation=organisation,
    )
