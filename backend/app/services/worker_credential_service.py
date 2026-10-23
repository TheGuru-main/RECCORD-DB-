"""RECCORD DB worker registration and authentication service."""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gsp import GSPPlacement, gsp_place
from app.core.identity import require_phone_uid
from app.models.organisation import Organisation
from app.models.role import Role
from app.models.user import User
from app.models.worker import Worker
from app.services.auth_service import hash_password, verify_password
from app.services.token_service import create_access_token


@dataclass(frozen=True)
class WorkerRegistrationResult:
    """Result of a successful pending worker registration."""

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


@dataclass(frozen=True)
class WorkerRoleLookupResult:
    """Organisation and currently active roles identified by a credential."""

    organisation: Organisation
    roles: list[Role]


def build_worker_credential_identity(
    *,
    organisation: Organisation,
    worker_id: str,
) -> str:
    """Build the canonical organisation Worker Credential."""

    organisation_name = organisation.display_name.strip()
    canonical_worker_id = worker_id.strip()

    if not organisation_name:
        raise ValueError("organisation full name must not be empty")

    if not str(organisation.id).strip():
        raise ValueError("organisation id must not be empty")

    if not canonical_worker_id:
        raise ValueError("worker_id must not be empty")

    return (
        f"{organisation_name}:"
        f"{organisation.id}:"
        f"{canonical_worker_id}"
    )


def generate_worker_id() -> str:
    """Generate the organisation's worker-registration identifier."""

    return f"WRK-{secrets.token_urlsafe(12)}"


def get_organisation_from_worker_credential(
    db: Session,
    *,
    worker_credential: str,
) -> Organisation:
    """Validate the exact submitted credential and identify its organisation."""

    credential = worker_credential.strip()

    if not credential:
        raise ValueError("invalid Worker Credential")

    try:
        display_name, organisation_id_text, worker_id = credential.rsplit(
            ":",
            2,
        )
        organisation_id = uuid.UUID(organisation_id_text)
    except (ValueError, AttributeError):
        raise ValueError("invalid Worker Credential") from None

    if not display_name or not worker_id:
        raise ValueError("invalid Worker Credential")

    organisation = db.scalar(
        select(Organisation).where(
            Organisation.id == organisation_id,
            Organisation.display_name == display_name,
            Organisation.worker_id == worker_id,
        )
    )

    if organisation is None:
        raise ValueError("invalid Worker Credential")

    if not verify_password(
        credential,
        organisation.worker_registration_credential_hash,
    ):
        raise ValueError("invalid Worker Credential")

    return organisation


def get_worker_registration_roles(
    db: Session,
    *,
    worker_credential: str,
) -> WorkerRoleLookupResult:
    """Return current active roles belonging to the identified organisation."""

    organisation = get_organisation_from_worker_credential(
        db,
        worker_credential=worker_credential,
    )

    roles = list(
        db.scalars(
            select(Role)
            .where(
                Role.organisation_id == organisation.id,
                Role.active.is_(True),
            )
            .order_by(Role.name.asc(), Role.id.asc())
        ).all()
    )

    return WorkerRoleLookupResult(
        organisation=organisation,
        roles=roles,
    )


def register_worker(
    db: Session,
    *,
    worker_credential: str,
    worker_phone: str,
    worker_password: str,
    name: str,
    role: str,
) -> WorkerRegistrationResult:
    """Register a worker as pending using an organisation Worker Credential."""

    worker_phone = require_phone_uid(
        worker_phone.strip(), field="worker_phone"
    )
    name = name.strip()
    requested_role = role.strip()

    if not worker_phone:
        raise ValueError("worker phone number must not be empty")

    if not worker_password:
        raise ValueError("worker password must not be empty")

    if not name:
        raise ValueError("worker name must not be empty")

    if not requested_role:
        raise ValueError("worker role must not be empty")

    organisation = get_organisation_from_worker_credential(
        db,
        worker_credential=worker_credential,
    )

    organisation_role = db.scalar(
        select(Role).where(
            Role.organisation_id == organisation.id,
            Role.name == requested_role,
            Role.active.is_(True),
        ).limit(1)
    )

    if organisation_role is None:
        raise ValueError(
            "selected role is not active for this organisation"
        )

    existing_phone = db.scalar(
        select(User.id)
        .where(User.phone == worker_phone)
        .limit(1)
    )

    if existing_phone is not None:
        raise ValueError("phone number is already registered")

    existing_username = db.scalar(
        select(User.id)
        .where(User.username == worker_phone)
        .limit(1)
    )

    if existing_username is not None:
        raise ValueError("phone number is already registered")

    user = User(
        username=worker_phone,
        password_hash=hash_password(worker_password),
        name=name,
        phone=worker_phone,
        account_type="worker",
        organisation_id=organisation.id,
        status="pending",
    )

    db.add(user)
    db.flush()

    worker = Worker(
        user_id=user.id,
        organisation_id=organisation.id,
        role=organisation_role.name,
        status="pending",
    )

    db.add(worker)
    db.flush()

    placement = gsp_place(
        account_type="organisation",
        account_uid=organisation.phone,
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
    """Authenticate an approved worker without the shared Worker Credential."""

    worker_phone = worker_phone.strip()

    user = db.scalar(
        select(User).where(
            User.phone == worker_phone,
            User.account_type == "worker",
            User.status == "active",
        )
    )

    if user is None or user.organisation_id is None:
        return None

    if not verify_password(worker_password, user.password_hash):
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

    organisation = db.get(Organisation, user.organisation_id)

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
