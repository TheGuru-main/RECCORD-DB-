"""RECCORD DB worker registration and authentication service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gsp import GSPPlacement, gsp_place
from app.models.organisation import Organisation
from app.models.user import User
from app.models.worker import Worker
from app.services.auth_service import hash_password, verify_password
from app.services.token_service import create_access_token


@dataclass(frozen=True)
class WorkerRegistrationResult:
    """Result of successful worker registration."""

    user: User
    worker: Worker
    organisation: Organisation
    placement: GSPPlacement


@dataclass(frozen=True)
class WorkerLoginResult:
    """Authenticated worker context."""

    user: User
    worker: Worker
    organisation: Organisation
    access_token: str


def build_worker_credential_identity(
    *,
    organisation: Organisation,
    worker_id: str,
) -> str:
    """Build the canonical worker credential identity."""

    if not organisation.display_name.strip():
        raise ValueError("organisation full name must not be empty")

    if not str(organisation.id).strip():
        raise ValueError("organisation id must not be empty")

    if not worker_id.strip():
        raise ValueError("worker_id must not be empty")

    return (
        f"{organisation.display_name.strip()}:"
        f"{organisation.id}:"
        f"{worker_id.strip()}"
    )


def generate_worker_id() -> str:
    """Generate an organisation-tied worker registration identifier."""

    import secrets

    return f"WRK-{secrets.token_urlsafe(12)}"


def register_worker(
    db: Session,
    *,
    organisation_full_name: str,
    organisation_id: uuid.UUID,
    worker_id: str,
    worker_phone: str,
    worker_password: str,
    name: str,
    role: str,
) -> WorkerRegistrationResult:
    """Register a worker into an organisation."""

    organisation = db.scalar(
        select(Organisation).where(
            Organisation.id == organisation_id,
            Organisation.display_name == organisation_full_name,
            Organisation.worker_id == worker_id,
        )
    )

    if organisation is None:
        raise ValueError(
            "invalid organisation worker registration credential"
        )

    if not worker_phone.strip():
        raise ValueError("worker phone number must not be empty")

    if not worker_password:
        raise ValueError("worker password must not be empty")

    existing_user = db.scalar(
        select(User).where(User.phone == worker_phone)
    )

    if existing_user is not None:
        raise ValueError("worker phone number is already registered")

    user = User(
        username=worker_phone,
        password_hash=hash_password(worker_password),
        name=name,
        phone=worker_phone,
        account_type="worker",
        organisation_id=organisation.id,
        status="active",
    )

    db.add(user)
    db.flush()

    worker = Worker(
        user_id=user.id,
        organisation_id=organisation.id,
        role=role,
        status="active",
    )

    db.add(worker)
    db.flush()

    placement = gsp_place(
        account_type="organisation",
        account_id=str(organisation.id),
        name=organisation.display_name,
    )

    return WorkerRegistrationResult(
        user=user,
        worker=worker,
        organisation=organisation,
        placement=placement,
    )


def login_worker(
    db: Session,
    *,
    worker_phone: str,
    worker_password: str,
) -> WorkerLoginResult | None:
    """Authenticate a worker with their own phone and password."""

    user = db.scalar(
        select(User).where(
            User.phone == worker_phone,
            User.account_type == "worker",
            User.status == "active",
        )
    )

    if user is None or user.organisation_id is None:
        return None

    if not verify_password(
        worker_password,
        user.password_hash,
    ):
        return None

    worker = db.scalar(
        select(Worker).where(
            Worker.user_id == user.id,
            Worker.organisation_id == user.organisation_id,
            Worker.status == "active",
        )
    )

    if worker is None:
        return None

    organisation = db.get(
        Organisation,
        user.organisation_id,
    )

    if organisation is None:
        return None

    access_token = create_access_token(
        subject=str(user.id),
        account_type="worker",
        organisation_id=str(organisation.id),
    )

    return WorkerLoginResult(
        user=user,
        worker=worker,
        organisation=organisation,
        access_token=access_token,
    )
